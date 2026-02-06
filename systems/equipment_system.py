import pygame
import math
import config.game_config as settings
from core.item import Item, SkillItem, Equipment, Cell
# from data.item_data import get_item_by_id # Avoid circular import if possible

class Inventory:
    def __init__(self, player, rows=4, cols=6):
        self.player = player
        self.rows = rows
        self.cols = cols
        self.items = [None] * (rows * cols) # Backpack items
        
        # Skill Bar (4 slots)
        self.skill_slots = [None] * 4 
        
        self.view_mode = 'equipment' # equipment, cells
        
        # Equipment Slots
        self.equipment = {
            'head': None, 'body': None, 
            'hand_l': None, 'hand_r': None,
            'leg_l': None, 'leg_r': None,
            'special_1': None, 'special_2': None, 'special_3': None
        }
        
        # Cell Slots
        self.cells = [None] * 9 # Expanded to 9 slots
        self.cell_slots_layout = []
        
        # New System States
        self.gene_unlocked = False
        self.heart_slot = None # Stores the Heart Item
        self.gene_lock_rect = None
        self.heart_slot_rect = None
        
        # UI Metrics
        self.slot_size = 50
        self.padding = 10
        self.equip_width = 300 
        self.grid_width = cols * (self.slot_size + self.padding) + self.padding
        
        # Add space for Skill Bar at bottom
        self.skill_bar_height = 80
        
        self.width = self.equip_width + self.grid_width
        self.height = max(rows * (self.slot_size + self.padding) + self.padding, 450) + self.skill_bar_height
        
        self.x = (settings.SCREEN_WIDTH - self.width) // 2
        self.y = (settings.SCREEN_HEIGHT - self.height) // 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        self.toggle_btn_rect = pygame.Rect(self.x + 10, self.y + 10, 100, 30)
        
        # Sort Button
        self.sort_btn_rect = pygame.Rect(self.x + self.equip_width + self.grid_width - 80, self.y + 10, 60, 30)
        
        self.init_equipment_slots()
        self.init_cell_slots()
        self.init_skill_slots()
        
        # Dragging State
        self.dragging_item = None
        self.dragging_from = None # ('backpack', index) or ('skill', index)
        self.dragging_offset = (0, 0)
        
        # Merge Confirmation Dialog State
        self.merge_dialog = None # None or {'source': item, 'target': item, 'rect': Rect, ...}
        self.suppress_merge_confirm = False

    def get_stat_bonus(self, stat_name):
        bonus = 0
        # Equipment Bonus
        for slot, item in self.equipment.items():
            if item and hasattr(item, 'stats'):
                val = item.stats.get(stat_name, 0)
                # Apply Awakening Multiplier
                # Level 0 = 100%, Level 1 = 200%, Level 2 = 300%
                level = getattr(item, 'awakened_level', 0)
                mult = 1.0 + level * 1.0
                bonus += val * mult
                
        # Cell Bonus (If implemented)
        if hasattr(self, 'cells'):
            for item in self.cells:
                if item and hasattr(item, 'stats'):
                    val = item.stats.get(stat_name, 0)
                    level = getattr(item, 'awakened_level', 0)
                    mult = 1.0 + level * 1.0
                    bonus += val * mult
                    
        return bonus

    def get_active_mechanisms(self):
        """
        Returns a list of active mechanisms derived from connected Cores and Cells.
        Structure: [{'type': 'tracking', 'element': 'fire', 'core_item': item_obj}, ...]
        Logic: 
        1. Check connections between Center (0) and Satellites (1-6).
        2. Pair 'Mechanism Cells' with 'Elemental Cores'.
        """
        mechanisms = []
        if not hasattr(self, 'cells'): return mechanisms
        
        # Center Slot
        center_item = self.cells[0]
        
        # Helper to identify item type
        def get_item_subtype(item):
            if not item: return None
            if item.id.startswith('core_'): return 'element' # core_fire, core_water...
            if item.id.startswith('cell_'): return 'mechanism' # cell_tracking, cell_chain...
            return None
            
        def get_element_type(item):
            if 'fire' in item.id: return 'fire'
            if 'water' in item.id: return 'water'
            if 'lightning' in item.id: return 'lightning'
            return None
            
        def get_mechanism_type(item):
            if 'tracking' in item.id: return 'tracking'
            if 'chain' in item.id: return 'chain'
            if 'exhaust' in item.id: return 'exhaust'
            return None

        # Check satellites (1-6)
        for i in range(1, 7):
            sat_item = self.cells[i]
            if not sat_item: continue
            
            pair = (center_item, sat_item)
            mech_item = None
            elem_item = None
            
            # Identify which is mechanism and which is element
            # Case 1: Center is Element, Satellite is Mechanism
            if get_item_subtype(center_item) == 'element' and get_item_subtype(sat_item) == 'mechanism':
                elem_item = center_item
                mech_item = sat_item
            # Case 2: Center is Mechanism, Satellite is Element
            elif get_item_subtype(center_item) == 'mechanism' and get_item_subtype(sat_item) == 'element':
                mech_item = center_item
                elem_item = sat_item
            
            if mech_item and elem_item:
                mechanisms.append({
                    'type': get_mechanism_type(mech_item),
                    'element': get_element_type(elem_item),
                    'mech_item': mech_item,
                    'elem_item': elem_item
                })
                
        try:
            for idx, item in enumerate(self.cells):
                if not item: continue
                item_id = getattr(item, 'id', '')
                if idx in (0, 5) and item_id.startswith('core_'):
                    continue
                if item_id == 'mech_split':
                    mechanisms.append({'type': 'split', 'mech_item': item})
                elif item_id == 'mech_giant':
                    mechanisms.append({'type': 'giant', 'mech_item': item})
        except Exception:
            pass
                
        return mechanisms

    def update(self, dt, game_manager):
        pass

    def add_item(self, item):
        """Add an item to the first available slot in the backpack."""
        for i in range(len(self.items)):
            if self.items[i] is None:
                self.items[i] = item
                return True
        return False

    def init_equipment_slots(self):
        cx = self.equip_width // 2
        cy = (self.height - self.skill_bar_height) // 2 - 20 # Adjust center ignoring skill bar
        
        self.equip_slots_rects = {
            'head': pygame.Rect(cx - 25, cy - 130, 50, 50),
            'body': pygame.Rect(cx - 25, cy - 50, 50, 50),
            'hand_l': pygame.Rect(cx - 100, cy - 50, 50, 50),
            'hand_r': pygame.Rect(cx + 50, cy - 50, 50, 50),
            'leg_l': pygame.Rect(cx - 60, cy + 30, 50, 50),
            'leg_r': pygame.Rect(cx + 10, cy + 30, 50, 50),
            'special_1': pygame.Rect(cx - 85, cy + 110, 50, 50),
            'special_2': pygame.Rect(cx - 25, cy + 110, 50, 50),
            'special_3': pygame.Rect(cx + 35, cy + 110, 50, 50),
        }
        
        self.slot_labels = {
            'head': "头", 'body': "身", 
            'hand_l': "左手", 'hand_r': "右手",
            'leg_l': "左脚", 'leg_r': "右脚",
            'special_1': "特1", 'special_2': "特2", 'special_3': "特3"
        }

    def init_cell_slots(self):
        cx = self.equip_width // 2
        cy = (self.height - self.skill_bar_height) // 2 
        
        # --- Upper System (ID 0-4) ---
        upper_cy = cy - 80
        
        # Upper Core (ID 0)
        self.cell_slots_layout.append({
            'id': 0, 
            'rect': pygame.Rect(cx - 25, upper_cy - 25, 50, 50),
            'connections': [1, 2, 3, 4]
        })
        
        # Upper Surrounding (ID 1-4)
        radius = 70
        for i in range(4):
            angle = math.radians(90 * i - 45) # X shape
            x = cx + math.cos(angle) * radius
            y = upper_cy + math.sin(angle) * radius
            self.cell_slots_layout.append({
                'id': i + 1,
                'rect': pygame.Rect(x - 25, y - 25, 50, 50),
                'connections': []
            })
            
        # --- Lower System (ID 5-8) ---
        lower_cy = cy + 80
        
        # Lower Core (ID 5)
        self.cell_slots_layout.append({
            'id': 5, 
            'rect': pygame.Rect(cx - 25, lower_cy - 25, 50, 50),
            'connections': [6, 7, 8]
        })
        
        # Lower Surrounding (ID 6-8)
        # 3 cells below/around
        angles = [30, 90, 150] # Bottom semi-circle
        for i, ang_deg in enumerate(angles):
            angle = math.radians(ang_deg)
            x = cx + math.cos(angle) * radius
            y = lower_cy + math.sin(angle) * radius
            self.cell_slots_layout.append({
                'id': i + 6,
                'rect': pygame.Rect(x - 25, y - 25, 50, 50),
                'connections': []
            })
            
        # --- Special Slots ---
        # Gene Lock (Center)
        self.gene_lock_rect = pygame.Rect(cx - 20, cy - 20, 40, 40)
        
        # Heart Slot (Top Right of Lower Core)
        # Lower Core is at (cx, lower_cy)
        # Top Right relative to it: +50, -50 roughly
        self.heart_slot_rect = pygame.Rect(cx + 40, lower_cy - 60, 40, 40)

    def is_slot_locked(self, slot_id):
        # Upper System (0-4) always unlocked
        if slot_id <= 4:
            return False
            
        # Lower System (5-8)
        # Slot 5 (Lower Core) is unlocked if Gene Lock is open OR Heart is equipped
        if slot_id == 5: 
             return not (self.gene_unlocked or self.heart_slot)
            
        # For Cell Slots (6, 7, 8), they depend on Heart Presence and Level
        if slot_id in [6, 7, 8]:
            if not self.heart_slot:
                return True
            
            heart_level = getattr(self.heart_slot, 'awakened_level', 0)
            
            if slot_id == 6: return False        # Level 0+ unlocks Slot 6
            if slot_id == 7: return heart_level < 1
            if slot_id == 8: return heart_level < 2
            
        return True
            
    def init_skill_slots(self):
        # Position at bottom of backpack area
        # Center the 4 slots in the grid area width
        grid_area_width = self.grid_width
        slots_width = 4 * (self.slot_size + self.padding) - self.padding
        
        start_x = self.x + self.equip_width + (grid_area_width - slots_width) // 2
        start_y = self.y + self.height - self.skill_bar_height + 15
        
        self.skill_slots_rects = []
        for i in range(4):
            rect = pygame.Rect(start_x + i * (self.slot_size + self.padding), start_y, self.slot_size, self.slot_size)
            self.skill_slots_rects.append(rect)

    def sort_items(self):
        # Sort items: Skills first, then Equipment, then others
        valid_items = [i for i in self.items if i is not None]
        
        def sort_key(item):
            # If item is string (legacy), treat as generic
            if isinstance(item, str):
                return (99, item) 
            
            # Type priority
            type_priority = {
                'skill': 0,
                'exclusive_skill': 0,
                'equipment': 1,
                'cell': 2,
                'generic': 3
            }
            # Access item_type safely
            itype = getattr(item, 'item_type', 'generic')
            rarity = getattr(item, 'rarity', 'white')
            name = getattr(item, 'name', str(item))
            
            p = type_priority.get(itype, 4)
            return (p, rarity, name)
            
        valid_items.sort(key=sort_key)
        
        # Fill back
        self.items = valid_items + [None] * (len(self.items) - len(valid_items))
        print("Backpack sorted!")

    def _try_merge(self, target):
        """Attempts to merge dragging_item into target."""
        if target and self.dragging_item and target.id == self.dragging_item.id and target is not self.dragging_item:
            
            # 1. Equipment Merge Logic
            if getattr(target, 'item_type', '') == 'equipment':
                # Requirement: Same Rarity
                if target.rarity != self.dragging_item.rarity:
                    print("Equipment merge requires same rarity!")
                    return False
                    
                # Requirement: Max Devour Count 5
                current_count = getattr(target, 'devour_count', 0)
                if current_count >= 5:
                    print("Equipment has reached max merge limit (5)!")
                    return False
                
                # Check Confirmation
                if not self.suppress_merge_confirm:
                    # Trigger Dialog
                    self.merge_dialog = {
                        'target': target,
                        'source': self.dragging_item,
                        'source_from': self.dragging_from, # Store where source came from to clear it later
                        'rect': pygame.Rect(settings.SCREEN_WIDTH//2 - 150, settings.SCREEN_HEIGHT//2 - 80, 300, 160)
                    }
                    return True # Return True to stop the drop logic from swapping items
                    
                # Execute Merge (If suppressed)
                return self._execute_merge(target, self.dragging_item)

            # 2. Legacy/Other Item Merge Logic (Cells, Hearts, etc.)
            # Progressive Devour Logic
            # Transfer progress from source to target
            source_progress = getattr(self.dragging_item, 'devour_progress', 0)
            target_progress = getattr(target, 'devour_progress', 0)
            
            # Total progress = target + source + 1 (the source item itself counts as 1 material)
            total_progress = target_progress + source_progress + 1
            
            print(f"Merging: Target({target_progress}) + Source({source_progress}) + 1 = {total_progress}")
            
            # Update target
            target.devour_progress = total_progress
            
            # Sound Effect
            from utils.sound_manager import SoundManager
            SoundManager().play_sound("ui_upgrade")
            
            # Handle Level Ups
            while target.devour_progress >= 5:
                target.devour_progress -= 5
                target.awakened_level += 1
                print(f"{target.name} Upgraded to Level {target.awakened_level}!")
                
                # Visual update for awakening
                if target.awakened_level == 1:
                    target.rarity = 'orange'
                elif target.awakened_level == 2:
                    target.rarity = 'red'
                
                # Check for Heart Level Unlock (If this is the Heart)
                if getattr(target, 'id', '') == 'heart':
                    # Notify Unlock
                    unlocked_slot = None
                    if target.awakened_level == 1: unlocked_slot = 7
                    elif target.awakened_level == 2: unlocked_slot = 8
                    
                    if unlocked_slot and self.player and hasattr(self.player, 'game_manager'):
                        pass
                        
            print(f"New Progress: {target.devour_progress}/5")
            
            # Consume the source item
            self._consume_dragging_item()
                
            return True
        return False

    def _execute_merge(self, target, source):
        # Merge
        target.devour_count += 1
        print(f"Equipment Merged! Devour Count: {target.devour_count}/5")
        
        # Sound
        from utils.sound_manager import SoundManager
        SoundManager().play_sound("ui_upgrade")
        
        # Consume source
        # Note: If called from dialog, self.dragging_item might be None or cleared already
        # But we need to clear the slot where source was.
        # Use stored info if available, else standard
        
        # If executing from dialog, we need to clear based on stored source_from
        # If executing directly, self.dragging_from is valid
        
        if hasattr(self, 'merge_dialog') and self.merge_dialog:
             src_from = self.merge_dialog['source_from']
             # Clear source slot
             if src_from[0] == 'backpack':
                 self.items[src_from[1]] = None
             elif src_from[0] == 'equipment':
                 self.equipment[src_from[1]] = None
                 if self.player and hasattr(self.player, 'check_equipment_effects'):
                     self.player.check_equipment_effects()
        else:
             self._consume_dragging_item()
             
        return True

    def _consume_dragging_item(self):
        if self.dragging_from[0] == 'backpack':
            self.items[self.dragging_from[1]] = None
        elif self.dragging_from[0] == 'equipment':
            self.equipment[self.dragging_from[1]] = None
            if self.player and hasattr(self.player, 'check_equipment_effects'):
                self.player.check_equipment_effects()
        elif self.dragging_from[0] == 'skill':
            self.skill_slots[self.dragging_from[1]] = None
        elif self.dragging_from[0] == 'cell':
            self.cells[self.dragging_from[1]] = None

    def _feed_heart(self, heart_item, food_item):
        """Feed an item to the Heart to increase its progress."""
        if not heart_item or not food_item: return False
        
        # Calculate progress to add
        # Different items could give different progress, currently just 1
        progress_to_add = 1
        
        # If food is also a heart, maybe give more?
        if getattr(food_item, 'id', '') == 'heart':
            progress_to_add = 5 # Instant level up? Or just more?
            # User implied normal merge logic for hearts, but let's stick to "devour" concept
            # If it's a heart, we can use the stored progress in it too
            progress_to_add += getattr(food_item, 'devour_progress', 0)
        
        heart_item.devour_progress += progress_to_add
        print(f"Heart Devoured {food_item.name}! Progress: {heart_item.devour_progress}/5")
        
        # Sound
        from utils.sound_manager import SoundManager
        SoundManager().play_sound("ui_upgrade")
        
        # Level Up Logic
        while heart_item.devour_progress >= 5:
            heart_item.devour_progress -= 5
            heart_item.awakened_level += 1
            print(f"Heart Upgraded to Level {heart_item.awakened_level}!")
            
            # Visual update
            if heart_item.awakened_level == 1: heart_item.rarity = 'orange'
            elif heart_item.awakened_level == 2: heart_item.rarity = 'red'
            
        return True

    def handle_event(self, event, screen):
        # Dialog Interaction
        if self.merge_dialog:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dialog_rect = self.merge_dialog['rect']
                mx, my = event.pos
                
                # Button Positions (Hardcoded matching renderer logic)
                # Confirm: (x+20, y+110, 80, 30)
                # Cancel: (x+200, y+110, 80, 30)
                # Checkbox: (x+20, y+80, 20, 20)
                
                x, y = dialog_rect.x, dialog_rect.y
                
                # Confirm
                if pygame.Rect(x + 20, y + 110, 80, 30).collidepoint(mx, my):
                    self._execute_merge(self.merge_dialog['target'], self.merge_dialog['source'])
                    self.merge_dialog = None
                    return
                
                # Cancel
                if pygame.Rect(x + 200, y + 110, 80, 30).collidepoint(mx, my):
                    # Cancel merge: Do nothing, items remain in original slots
                    # (Because we returned True in _try_merge, the logic didn't swap them, but dragging ended.
                    # The dragging_item was dropped. It returns to source?
                    # Wait, if _try_merge returned True, handle_event set dropped=True.
                    # So the system thinks the drop was successful and CLEARS the dragging_item.
                    # BUT, _try_merge didn't actually clear the source slot (unless _execute_merge called _consume).
                    # So the item is STILL in the source slot.
                    # So "Cancel" just means closing dialog. Correct.
                    self.merge_dialog = None
                    return
                
                # Checkbox (Don't show again)
                if pygame.Rect(x + 20, y + 80, 200, 20).collidepoint(mx, my):
                    self.suppress_merge_confirm = not self.suppress_merge_confirm
                    return
                    
            # Block other input while dialog is open
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Toggle View
                if self.toggle_btn_rect.collidepoint(event.pos):
                    self.view_mode = 'cells' if self.view_mode == 'equipment' else 'equipment'
                    return
                
                # Sort Button
                if self.sort_btn_rect.collidepoint(event.pos):
                    self.sort_items()
                    return
                
                # Check Equipment Slots (Drag Start)
                if self.view_mode == 'equipment':
                    for slot_name, rect in self.equip_slots_rects.items():
                        rect_abs = rect.move(self.x, self.y)
                        if rect_abs.collidepoint(event.pos) and self.equipment[slot_name]:
                            self.dragging_item = self.equipment[slot_name]
                            self.dragging_from = ('equipment', slot_name)
                            self.dragging_offset = (rect_abs.x - event.pos[0], rect_abs.y - event.pos[1])
                            return

                # Check Heart Slot (Drag Start)
                if self.view_mode == 'cells' and self.heart_slot:
                    rect = self.heart_slot_rect.move(self.x, self.y)
                    if rect.collidepoint(event.pos):
                        self.dragging_item = self.heart_slot
                        self.dragging_from = ('heart_slot', 0)
                        self.dragging_offset = (rect.x - event.pos[0], rect.y - event.pos[1])
                        return

                # Check Cell Slots (Drag Start)
                if self.view_mode == 'cells':
                    for cell_slot in self.cell_slots_layout:
                        rect = cell_slot['rect'].move(self.x, self.y)
                        if rect.collidepoint(event.pos) and self.cells[cell_slot['id']]:
                            self.dragging_item = self.cells[cell_slot['id']]
                            self.dragging_from = ('cell', cell_slot['id'])
                            self.dragging_offset = (rect.x - event.pos[0], rect.y - event.pos[1])
                            return

                # Check Backpack Slots (Drag Start)
                grid_start_x = self.x + self.equip_width + self.padding
                grid_start_y = self.y + self.padding + 30 
                for i in range(len(self.items)):
                    row = i // self.cols
                    col = i % self.cols
                    x = grid_start_x + col * (self.slot_size + self.padding)
                    y = grid_start_y + row * (self.slot_size + self.padding)
                    rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                    
                    if rect.collidepoint(event.pos) and self.items[i]:
                        self.dragging_item = self.items[i]
                        self.dragging_from = ('backpack', i)
                        self.dragging_offset = (x - event.pos[0], y - event.pos[1])
                        return
                        
                # Check Skill Slots (Drag Start)
                for i, rect in enumerate(self.skill_slots_rects):
                    if rect.collidepoint(event.pos) and self.skill_slots[i]:
                        self.dragging_item = self.skill_slots[i]
                        self.dragging_from = ('skill', i)
                        self.dragging_offset = (rect.x - event.pos[0], rect.y - event.pos[1])
                        return

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_item:
                # Drop Logic
                dropped = False
                
                # 1. Check Drop on Equipment Slots
                if self.view_mode == 'equipment':
                    for slot_name, rect in self.equip_slots_rects.items():
                        rect_abs = rect.move(self.x, self.y)
                        if rect_abs.collidepoint(event.pos):
                            # Check compatibility
                            item_slot = getattr(self.dragging_item, 'slot_type', 'none')
                            valid = False
                            if item_slot == slot_name: valid = True
                            elif item_slot == 'hand' and slot_name in ['hand_l', 'hand_r']: valid = True
                            elif item_slot == 'leg' and slot_name in ['leg_l', 'leg_r']: valid = True
                            elif item_slot == 'special' and slot_name.startswith('special'): valid = True
                            
                            if valid:
                                target = self.equipment[slot_name]
                                
                                # Try Merge first
                                if self._try_merge(target):
                                    dropped = True
                                    break
                                
                                self.equipment[slot_name] = self.dragging_item
                                
                                # Restore target
                                if self.dragging_from[0] == 'backpack':
                                    self.items[self.dragging_from[1]] = target
                                elif self.dragging_from[0] == 'skill':
                                    self.skill_slots[self.dragging_from[1]] = target
                                elif self.dragging_from[0] == 'equipment':
                                    self.equipment[self.dragging_from[1]] = target
                                elif self.dragging_from[0] == 'cell':
                                    self.cells[self.dragging_from[1]] = target
                                    
                                dropped = True
                                
                                # Update player effects
                                if self.player and hasattr(self.player, 'check_equipment_effects'):
                                    self.player.check_equipment_effects()
                            break
                
                # 1.5. Check Drop on Gene Lock & Heart Slot
                if not dropped and self.view_mode == 'cells':
                    # Gene Lock
                    gene_rect = self.gene_lock_rect.move(self.x, self.y)
                    if gene_rect.collidepoint(event.pos):
                        if not self.gene_unlocked and self.dragging_item.id == 'gene_potion':
                            self.gene_unlocked = True
                            print("Gene Lock Unlocked!")
                            # Play Sound
                            from utils.sound_manager import SoundManager
                            SoundManager().play_sound("ui_upgrade")
                            
                            dropped = True
                            # Consume item (don't return to source)
                            # Only need to set dropped = True, and NOT restore to source logic below
                            # BUT current logic restores if 'not dropped'. Since dropped=True, it won't restore.
                            # So we just need to ensure we don't accidentally restore or keep it.
                            # The dragging_item reference is lost after this frame.
                            # We just need to ensure the source slot is cleared.
                            if self.dragging_from[0] == 'backpack':
                                self.items[self.dragging_from[1]] = None
                            return # Done
                        else:
                            if self.gene_unlocked:
                                print("Already unlocked!")
                            else:
                                print("Need Gene Potion to unlock!")

                    # Heart Slot
                    heart_rect = self.heart_slot_rect.move(self.x, self.y)
                    if heart_rect.collidepoint(event.pos):
                        # Removed Gene Lock check as per request
                        
                        is_heart = getattr(self.dragging_item, 'id', '') == 'heart'
                        if is_heart:
                            target = self.heart_slot
                            
                            # If slot has a heart, feed it
                            if target:
                                if self._feed_heart(target, self.dragging_item):
                                    dropped = True
                                    # Consume source (handled by logic below if dropped=True)
                            else:
                                # Place new heart
                                self.heart_slot = self.dragging_item
                                
                                # Restore target (if we were swapping, but here we just placed)
                                # Actually logic below handles clearing source if dropped=True.
                                # But wait, if we are swapping or placing, we need to handle the source clearing.
                                # The original code did:
                                # self.heart_slot = self.dragging_item
                                # dropped = True
                                # And then relied on the "not dropped" check at the end to restore.
                                # Since dropped=True, it WON'T restore, effectively moving it.
                                # But we need to ensure we don't duplicate.
                                # The code below:
                                # if not dropped: restore...
                                # So if dropped=True, the item is gone from source.
                                # But we haven't cleared the source slot index in self.items/equipment yet?
                                # Ah, look at lines 381-391 in _try_merge, it clears the source.
                                # But here (Line 551 in original) we just set self.heart_slot = item.
                                # We need to clear the source!
                                # The original code had:
                                # if self.dragging_from[0] == 'backpack': self.items[...] = target (which was None?)
                                # Wait, if target was None (empty slot), it restores None to source? That clears it.
                                # Yes.
                                
                                # So if we place it:
                                if self.dragging_from[0] == 'backpack':
                                    self.items[self.dragging_from[1]] = None
                                elif self.dragging_from[0] == 'heart_slot':
                                    self.heart_slot = None # Should not happen if we are dragging TO heart slot
                                
                                dropped = True
                        else:
                            # Allow feeding OTHER items to Heart if Heart exists
                            if self.heart_slot:
                                # Feed dragging item to Heart
                                if self._feed_heart(self.heart_slot, self.dragging_item):
                                    dropped = True
                                    # We need to clear source manually because _feed_heart doesn't know about source
                                    if self.dragging_from[0] == 'backpack':
                                        self.items[self.dragging_from[1]] = None
                                    elif self.dragging_from[0] == 'equipment':
                                        self.equipment[self.dragging_from[1]] = None
                                        if self.player and hasattr(self.player, 'check_equipment_effects'):
                                            self.player.check_equipment_effects()
                                    elif self.dragging_from[0] == 'skill':
                                        self.skill_slots[self.dragging_from[1]] = None
                                    elif self.dragging_from[0] == 'cell':
                                        self.cells[self.dragging_from[1]] = None
                            else:
                                print("Only Heart can be placed here!")

                # 2. Check Drop on Cell Slots
                if not dropped and self.view_mode == 'cells':
                    for cell_slot in self.cell_slots_layout:
                        if cell_slot['rect'].move(self.x, self.y).collidepoint(event.pos):
                            # Check Lock
                            if self.is_slot_locked(cell_slot['id']):
                                print("Slot is locked!")
                                break
                                
                            # Only allow 'cell' items
                            is_cell = False
                            if getattr(self.dragging_item, 'item_type', '') == 'cell': is_cell = True
                            
                            # Additional Logic: Core vs Cell
                            # Core Slots: 0, 5
                            # Cell Slots: 1, 2, 3, 4, 6, 7, 8
                            is_core_slot = (cell_slot['id'] in [0, 5])
                            is_core_item = self.dragging_item.id.startswith('core_')
                            
                            if is_cell:
                                # Validation
                                if is_core_slot and not is_core_item:
                                    print("Only Cores (Cyan) can be placed here!")
                                    is_cell = False
                                elif not is_core_slot and is_core_item:
                                    print("Cores can only be placed in Core Slots (Cyan)!")
                                    is_cell = False
                            
                            if is_cell:
                                target = self.cells[cell_slot['id']]
                                
                                # Try Merge first
                                if self._try_merge(target):
                                    dropped = True
                                    break
                                
                                self.cells[cell_slot['id']] = self.dragging_item
                                
                                # Restore target to source
                                if self.dragging_from[0] == 'backpack':
                                    self.items[self.dragging_from[1]] = target
                                elif self.dragging_from[0] == 'cell': # Dragging from another cell
                                    self.cells[self.dragging_from[1]] = target
                                elif self.dragging_from[0] == 'equipment':
                                    self.equipment[self.dragging_from[1]] = target
                                
                                dropped = True
                            else:
                                print("Only Cells can be placed here!")
                            break

                # 3. Check Drop on Skill Slots
                if not dropped:
                    for i, rect in enumerate(self.skill_slots_rects):
                        if rect.collidepoint(event.pos):
                            # Only allow Skills
                            is_skill = False
                            if isinstance(self.dragging_item, SkillItem): is_skill = True
                            elif isinstance(self.dragging_item, str) and self.dragging_item.startswith('skill_'): is_skill = True 
                            elif hasattr(self.dragging_item, 'item_type') and self.dragging_item.item_type in ['skill', 'exclusive_skill']: is_skill = True
                            
                            if is_skill:
                                # Check Unique Equip Constraint
                                skill_id = self.dragging_item.id
                                already_equipped = False
                                for slot_idx, slot_item in enumerate(self.skill_slots):
                                    if slot_item and slot_item.id == skill_id and slot_idx != i:
                                        already_equipped = True
                                        break
                                
                                if already_equipped:
                                    print(f"Skill {self.dragging_item.name} is already equipped!")
                                    break 

                                # Check Exclusive Restriction
                                exclusive_id = getattr(self.dragging_item, 'exclusive_id', None)
                                if exclusive_id:
                                    player_char_id = self.player.data.get('id')
                                    if player_char_id != exclusive_id:
                                        print(f"Cannot equip exclusive skill for {exclusive_id} on {player_char_id}")
                                        break

                                target = self.skill_slots[i]
                                
                                # Try Merge first
                                if self._try_merge(target):
                                    dropped = True
                                    break
                                    
                                self.skill_slots[i] = self.dragging_item
                                
                                # Restore target to source
                                if self.dragging_from[0] == 'backpack':
                                    self.items[self.dragging_from[1]] = target
                                elif self.dragging_from[0] == 'skill':
                                    self.skill_slots[self.dragging_from[1]] = target
                                
                                dropped = True
                            break
                
                # 4. Check Drop on Backpack
                if not dropped:
                    grid_start_x = self.x + self.equip_width + self.padding
                    grid_start_y = self.y + self.padding + 30 
                    for i in range(len(self.items)):
                        row = i // self.cols
                        col = i % self.cols
                        x = grid_start_x + col * (self.slot_size + self.padding)
                        y = grid_start_y + row * (self.slot_size + self.padding)
                        rect = pygame.Rect(x, y, self.slot_size, self.slot_size)
                        
                        if rect.collidepoint(event.pos):
                            target = self.items[i]
                            
                            # --- Merge Logic ---
                            merged = self._try_merge(target)
                            
                            if merged:
                                dropped = True
                            else:
                                self.items[i] = self.dragging_item
                                
                                if self.dragging_from[0] == 'backpack':
                                    self.items[self.dragging_from[1]] = target
                                elif self.dragging_from[0] == 'skill':
                                    self.skill_slots[self.dragging_from[1]] = target
                                elif self.dragging_from[0] == 'equipment':
                                    self.equipment[self.dragging_from[1]] = target
                                elif self.dragging_from[0] == 'cell':
                                    self.cells[self.dragging_from[1]] = target
                                    
                                dropped = True
                                
                                # Update player effects
                                if self.dragging_from[0] == 'equipment' and self.player and hasattr(self.player, 'check_equipment_effects'):
                                    self.player.check_equipment_effects()
                            break
                            
                # If dropped outside valid slot, return to source
                if not dropped:
                    if self.dragging_from[0] == 'backpack':
                        self.items[self.dragging_from[1]] = self.dragging_item
                    elif self.dragging_from[0] == 'skill':
                        self.skill_slots[self.dragging_from[1]] = self.dragging_item
                    elif self.dragging_from[0] == 'equipment':
                        self.equipment[self.dragging_from[1]] = self.dragging_item
                    elif self.dragging_from[0] == 'cell':
                        self.cells[self.dragging_from[1]] = self.dragging_item
                
                self.dragging_item = None
                self.dragging_from = None
