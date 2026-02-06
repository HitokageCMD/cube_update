import pygame
import config.game_config as settings
from data.item_data import get_item_by_id, SKILL_ITEMS, EQUIPMENT_ITEMS, OTHER_ITEMS, CELL_ITEMS, EQUIPMENT_TEMPLATES
from utils.item_generator import generate_equipment

class DevManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.show_console = False
        
        # UI State
        self.buttons = [] # List of dicts: {'rect': Rect, 'text': str, 'action': callable, 'hover': bool}
        self.stat_buttons = [] # {'rect': Rect, 'text': str, 'action': callable, 'type': '+/-'}
        
        self.item_tabs = ['skills', 'equip', 'cores', 'others']
        self.current_item_tab = 'skills'
        self.item_scroll_y = 0

        # Equipment Generation State
        self.equip_rarity_options = ['white', 'green', 'blue', 'purple', 'orange']
        self.current_equip_rarity_idx = 0
        
        # Spawn Configuration
        self.spawn_types = ['square', 'triangle', 'pentagon', 'hexagon', 'circle']
        self.current_spawn_type_idx = 0
        self.spawn_count = 1
        
        # Stats Configuration
        self.stat_keys = [
            'max_hp', 'max_mp', 'phys_atk', 'magic_atk', 
            'phys_def', 'magic_def', 'attack_speed', 'move_speed',
            'pickup_range', 'attack_range', 'skill_range', 'crit_chance',
            'phys_pen', 'magic_pen', 'damage_bonus', 'hp_regen',
            'mp_regen', 'skill_haste', 'luck', 'collision_damage_reduction',
            'collision_dmg_pct', 'skill_haste_cap', 'crit_dmg', 'piercing_count'
        ]
        
        self.stat_labels = {
            'max_hp': '最大生命', 'max_mp': '最大魔力',
            'phys_atk': '物理攻击', 'magic_atk': '魔法攻击',
            'phys_def': '物理防御', 'magic_def': '魔法防御',
            'attack_speed': '攻击速度', 'move_speed': '移动速度',
            'pickup_range': '拾取范围', 'attack_range': '攻击范围',
            'skill_range': '技能范围', 'crit_chance': '暴击率',
            'phys_pen': '物理穿透', 'magic_pen': '魔法穿透',
            'damage_bonus': '伤害加成', 'hp_regen': '生命恢复',
            'mp_regen': '魔力恢复', 'skill_haste': '技能急速',
            'luck': '幸运', 'collision_damage_reduction': '碰撞减免',
            'collision_dmg_pct': '碰撞伤害', 'skill_haste_cap': '技能急速上限',
            'crit_dmg': '暴击伤害', 'piercing_count': '穿透数量'
        }
        
    def get_items_by_category(self):
        items = []
        if self.current_item_tab == 'skills':
            items = list(SKILL_ITEMS.values())
        elif self.current_item_tab == 'equip':
            # Instead of static EQUIPMENT_ITEMS, we use templates to allow generation
            # But we wrap them in simple Item objects for display list, or use base template dict
            # We need to return objects that have 'name' and 'id'
            # Let's create dummy items from templates
            for t_id, template in EQUIPMENT_TEMPLATES.items():
                # Create a preview item (using current selected rarity)
                rarity = self.equip_rarity_options[self.current_equip_rarity_idx]
                # We can't generate full items here every frame, it's expensive?
                # Actually get_items_by_category is called every frame in draw loop.
                # Just use static list for ID/Name, but action will use generation.
                # Let's return a list of objects that behave like items
                
                # Using generate_equipment is fine for display, it's not that heavy
                item = generate_equipment(template, rarity=rarity)
                items.append(item)
                
        elif self.current_item_tab == 'cores':
            items = list(CELL_ITEMS.values())
        elif self.current_item_tab == 'others':
            items = list(OTHER_ITEMS.values())
        return items

    def toggle(self):
        self.show_console = not self.show_console

    def update_ui(self):
        # Alias for toggle or specific update logic if needed
        self.toggle()
        
    def handle_input(self, event):
        if not self.show_console:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                
                # Check Control Buttons
                for btn in self.buttons:
                    if btn['rect'].collidepoint(mouse_pos):
                        if btn.get('action'):
                            btn['action']()
                        return True
                        
                # Check Stat Buttons
                for btn in self.stat_buttons:
                    if btn['rect'].collidepoint(mouse_pos):
                        self.modify_stat(btn['stat'], btn['change'])
                        return True
            
            # Scroll handling for item list
            if event.button == 4: # Scroll Up
                self.item_scroll_y = max(0, self.item_scroll_y - 30)
                return True
            elif event.button == 5: # Scroll Down
                # Max scroll logic should ideally be in renderer or calculated here based on list size
                # For simplicity, we just increment and renderer will clamp or handle empty space
                self.item_scroll_y += 30 
                return True
                    
            return True # Consume click if in dev mode
            
        return False
        
    def modify_stat(self, stat_key, change):
        if not self.game_manager.player: return
        
        current = getattr(self.game_manager.player, stat_key, 0)
        
        # Determine step size based on stat type
        step = 1
        if stat_key in ['attack_speed', 'move_speed', 'hp_regen', 'mp_regen']:
            step = 0.5 if 'speed' not in stat_key else 10
        elif stat_key in ['crit_chance', 'crit_dmg', 'phys_pen', 'magic_pen', 'damage_bonus']:
            step = 5
        elif stat_key in ['pickup_range', 'attack_range', 'skill_range']:
            step = 10
            
        new_val = current + (step * change)
        setattr(self.game_manager.player, stat_key, new_val)
        
        # Special handling for HP/MP to update current values if max increases
        if stat_key == 'max_hp' and change > 0:
            self.game_manager.player.current_hp += step
        if stat_key == 'max_mp' and change > 0:
            self.game_manager.player.current_mp += step

    # Actions
    def action_god_mode(self):
        if self.game_manager.player:
            self.game_manager.player.is_invulnerable = not getattr(self.game_manager.player, 'is_invulnerable', False) # Logic might be different in actual player class
            # Actually Player class uses invincible_timer usually, let's set a flag
            self.game_manager.player.god_mode = not getattr(self.game_manager.player, 'god_mode', False)

    def action_kill_all(self):
        for enemy in self.game_manager.enemy_manager.enemies:
            enemy.current_hp = 0

    def action_full_restore(self):
        if self.game_manager.player:
            self.game_manager.player.current_hp = self.game_manager.player.max_hp
            self.game_manager.player.current_mp = self.game_manager.player.max_mp

    def action_level_up(self):
        self.game_manager.trigger_level_up(skip_anim=True)

    def action_spawn_enemy(self):
        e_type = self.spawn_types[self.current_spawn_type_idx]
        if self.game_manager.player:
            self.game_manager.enemy_manager.spawn_enemy(self.game_manager.player, 0, force_type=e_type, count=self.spawn_count)

    def action_cycle_spawn_type(self):
        self.current_spawn_type_idx = (self.current_spawn_type_idx + 1) % len(self.spawn_types)

    def action_inc_spawn_count(self):
        self.spawn_count += 1
        if self.spawn_count > 10: self.spawn_count = 10 # Cap at 10 for safety
        
    def action_dec_spawn_count(self):
        self.spawn_count -= 1
        if self.spawn_count < 1: self.spawn_count = 1

    def action_cycle_equip_rarity(self):
        self.current_equip_rarity_idx = (self.current_equip_rarity_idx + 1) % len(self.equip_rarity_options)

    def action_add_item(self, item_id):
        if self.game_manager.player:
            # Special logic for Equipment Generation
            if item_id in EQUIPMENT_TEMPLATES:
                template = EQUIPMENT_TEMPLATES[item_id]
                rarity = self.equip_rarity_options[self.current_equip_rarity_idx]
                item = generate_equipment(template, rarity=rarity)
                self.game_manager.player.inventory.add_item(item)
            else:
                # Normal items
                item = get_item_by_id(item_id)
                if item:
                    self.game_manager.player.inventory.add_item(item)
