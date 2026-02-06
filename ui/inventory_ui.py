import pygame
import config.game_config as settings
from utils.resource_manager import resource_manager
from utils.sound_manager import SoundManager

get_theme_color = settings.get_theme_color

class InventoryRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.hovered_item = None
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

    def get_stat_name(self, key):
        return self.stat_labels.get(key, key)

    def draw_tooltip(self, item, mouse_pos):
        if not item: return

        # Gather data
        name = "Unknown"
        desc = ""
        rarity = "common"
        stats = {}
        
        if hasattr(item, 'name'): name = item.name
        elif isinstance(item, dict): name = item.get('name', 'Unknown')
        elif isinstance(item, str): name = item

        if hasattr(item, 'description'): desc = item.description
        elif isinstance(item, dict): desc = item.get('desc', '')
        
        if hasattr(item, 'rarity'): rarity = item.rarity
        elif isinstance(item, dict): rarity = item.get('rarity', 'common')
        
        if hasattr(item, 'stats'): stats = item.stats
        elif isinstance(item, dict): stats = item.get('stats', {})

        # Devour Progress
        devour_progress = getattr(item, 'devour_progress', 0)
        awakened_level = getattr(item, 'awakened_level', 0)

        # Colors
        rarity_color = (200, 200, 200)
        if rarity == 'rare': rarity_color = (100, 100, 255)
        elif rarity == 'epic': rarity_color = (200, 50, 200)
        elif rarity == 'legendary': rarity_color = (255, 215, 0)
        
        # Render Fonts
        font = settings.small_font
        title_font = settings.medium_font
        
        lines = []
        # Title
        lines.append((name, title_font, rarity_color))
        
        # Item Type
        item_type = getattr(item, 'item_type', 'generic')
        type_str = "道具"
        if item_type == 'skill': type_str = "技能"
        elif item_type == 'exclusive_skill': type_str = "专属技能"
        elif item_type == 'equipment': type_str = "装备"
        elif item_type == 'cell': 
            # Distinguish Core vs Cell
            item_id = getattr(item, 'id', '')
            if item_id.startswith('core_'):
                type_str = "核心"
            else:
                type_str = "细胞"
        elif item_type == 'heart': type_str = "机械心脏"
        elif item_type == 'key': type_str = "关键道具"
        elif item_type == 'enemy': type_str = "敌人"
        elif item_type == 'reaction': type_str = "元素反应"
        
        lines.append((f"道具类型: {type_str}", font, (200, 200, 200)))

        # Equipment Slot
        if item_type == 'equipment':
            slot_type = getattr(item, 'slot_type', '')
            # Simple mapping
            slot_name = slot_type
            if slot_type == 'head': slot_name = "头部"
            elif slot_type == 'body': slot_name = "身体"
            elif slot_type == 'hand': slot_name = "手部"
            elif slot_type == 'leg': slot_name = "腿部"
            elif slot_type == 'special': slot_name = "特殊"
            
            if slot_name:
                lines.append((f"部位: {slot_name}", font, (200, 200, 200)))

        # Awakening / Devour Info
        if awakened_level > 0:
            lines.append((f"Awakened Lv.{awakened_level} (+{awakened_level * 100}%)", font, (255, 100, 100)))
        
        # Only show legacy devour progress if NOT equipment
        if devour_progress > 0 and getattr(item, 'item_type', '') != 'equipment':
            lines.append((f"吞噬进度: {devour_progress}/5", font, (255, 215, 0)))
        elif getattr(item, 'item_type', '') != 'equipment':
            pass 

        is_exclusive = False
        exclusive_id = getattr(item, 'exclusive_id', None)
        if hasattr(item, 'item_type') and getattr(item, 'item_type', '') == 'exclusive_skill':
            is_exclusive = True
        elif exclusive_id:
            is_exclusive = True
        elif isinstance(item, dict):
            t = item.get('item_type') or item.get('type')
            if t == 'exclusive_skill' or item.get('exclusive_id'):
                is_exclusive = True
                exclusive_id = item.get('exclusive_id')

        if is_exclusive:
            ex_str = "*专属技能*"
            if exclusive_id == 'triangle': ex_str = "三角形的专属技能"
            elif exclusive_id == 'square': ex_str = "正方形的专属技能"
            elif exclusive_id == 'circle': ex_str = "圆形的专属技能"
            lines.append((ex_str, font, (255, 215, 0)))
        
        # Damage
        dmg = getattr(item, 'damage', None)
        if dmg:
            lines.append((f"伤害: {dmg}", font, (255, 100, 100)))

        # Cooldown
        cd = getattr(item, 'cooldown', None)
        if cd:
            lines.append((f"冷却: {cd}cd", font, (100, 255, 255)))

        # MP Cost
        mp = getattr(item, 'mp_cost', None)
        if mp:
            lines.append((f"魔力消耗: {mp}mp", font, (100, 100, 255)))

        # Stats
        if hasattr(item, 'main_stat') and item.main_stat:
            # New Structured Display
            
            # 1. Main Stat
            key, val = item.main_stat
            # Calculate current value with devour bonus
            devour_count = getattr(item, 'devour_count', 0)
            mult = 1.0 + (devour_count * 0.2)
            current_val = val * mult
            
            # Formatting
            val_str = f"{current_val:.1f}" if isinstance(current_val, float) else f"{int(current_val)}"
            if devour_count > 0:
                val_str += f" (+{int(devour_count*20)}%)"
            
            stat_name = self.get_stat_name(key)
            lines.append((f"{stat_name}: {val_str}", font, (100, 255, 100))) # Green for Main
            
            # 2. Sub Stats
            if hasattr(item, 'sub_stats') and item.sub_stats:
                for k, v in item.sub_stats:
                    s_name = self.get_stat_name(k)
                    v_str = f"+{v:.1f}" if isinstance(v, float) else f"+{v}"
                    # Percentage formatting for some stats?
                    if k in ['crit_chance', 'crit_dmg', 'damage_bonus', 'skill_haste', 'attack_speed']:
                        v_str = f"+{v*100:.1f}%"
                        
                    lines.append((f"{s_name} {v_str}", font, (100, 100, 255))) # Blue for Sub
            
            # 3. Negative Stats
            if hasattr(item, 'neg_stats') and item.neg_stats:
                for k, v in item.neg_stats:
                    s_name = self.get_stat_name(k)
                    v_str = f"{v:.1f}" if isinstance(v, float) else f"{v}"
                    if k in ['move_speed', 'attack_speed', 'skill_haste']: # Percentages usually?
                        # Wait, move_speed is usually flat in this game, but attack_speed is multiplier/percent?
                        # Based on generator, attack_speed is 0.15 (15%).
                        if abs(v) < 1.0: # Heuristic for percentage
                             v_str = f"{v*100:.1f}%"
                    
                    lines.append((f"{s_name} {v_str}", font, (255, 100, 100))) # Red for Neg
                    
        elif stats:
            # Legacy / Generic Stats
            for k, v in stats.items():
                val_str = f"+{v}"
                lines.append((f"{k}: {val_str}", font, (150, 255, 150)))
        
        # Devour Level (Equipment)
        if hasattr(item, 'devour_count') and item.devour_count > 0:
             lines.append((f"强化等级: +{item.devour_count} (Max 5)", font, (255, 215, 0)))

        # Description (Wrapped)
        if desc:
            lines.append(("技能介绍:", font, (200, 200, 200)))
            max_width = 250
            wrapped = []
            words = desc.split()
            if not words: words = [desc]
            
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                w, h = font.size(test_line)
                if w <= max_width:
                    current_line = test_line
                else:
                    if current_line: wrapped.append(current_line)
                    current_line = word
            if current_line:
                wrapped.append(current_line)
            
            for line in wrapped:
                lines.append((line, font, (200, 200, 200)))

        # Remark
        remark = getattr(item, 'remark', "")
        lines.append(("备注:", font, (150, 150, 150)))
        if remark:
             lines.append((f"{remark}", font, (150, 150, 150)))
        else:
             lines.append(("(空)", font, (100, 100, 100)))

        # Calculate Box Size
        box_w = 0
        box_h = 20 # Padding
        
        rendered_lines = []
        for text, f, color in lines:
            surf = f.render(text, True, color)
            rendered_lines.append(surf)
            box_w = max(box_w, surf.get_width())
            box_h += surf.get_height() + 5
            
        box_w += 30 # Padding
        
        # Position
        x, y = mouse_pos
        x += 15 # Offset
        y += 15
        
        # Clamp to screen
        if x + box_w > settings.SCREEN_WIDTH:
            x = mouse_pos[0] - box_w - 10
            if x < 0: x = 0
            
        if y + box_h > settings.SCREEN_HEIGHT:
            y = settings.SCREEN_HEIGHT - box_h - 10
            if y < 0: y = 0
            
        # Draw
        rect = pygame.Rect(x, y, box_w, box_h)
        s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 230))
        self.screen.blit(s, (x, y))
        
        # Border Color based on Rarity
        pygame.draw.rect(self.screen, rarity_color, rect, 2)
        
        # Rarity Tag (Top Right)
        rarity_text = "普通"
        if rarity == 'white': rarity_text = "普通"
        elif rarity == 'green': rarity_text = "优秀"
        elif rarity == 'blue': rarity_text = "稀有"
        elif rarity == 'purple': rarity_text = "史诗"
        elif rarity == 'orange': rarity_text = "传说"
        elif rarity == 'red': rarity_text = "神话"
        
        r_surf = font.render(rarity_text, True, rarity_color)
        self.screen.blit(r_surf, (x + box_w - r_surf.get_width() - 10, y + 10))
        
        curr_y = y + 10
        for surf in rendered_lines:
            self.screen.blit(surf, (x + 15, curr_y))
            curr_y += surf.get_height() + 5

    def draw_inventory(self, inventory):
        self.draw_merge_dialog(inventory)

        self.hovered_item = None

        # 绘制半透明背景
        s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        self.screen.blit(s, (0, 0))

        # 绘制面板背景
        panel_bg = resource_manager.get_image("ui_panel_bg")
        if panel_bg:
            scaled_bg = pygame.transform.scale(panel_bg, (inventory.rect.width, inventory.rect.height))
            self.screen.blit(scaled_bg, inventory.rect)
        else:
            pygame.draw.rect(self.screen, get_theme_color('ui_bg'), inventory.rect)
            pygame.draw.rect(self.screen, get_theme_color('panel_border'), inventory.rect, 3) # 边框
        
        # 绘制切换按钮
        btn_color = (100, 100, 150) if inventory.toggle_btn_rect.collidepoint(pygame.mouse.get_pos()) else (80, 80, 80)
        pygame.draw.rect(self.screen, btn_color, inventory.toggle_btn_rect)
        pygame.draw.rect(self.screen, get_theme_color('panel_border'), inventory.toggle_btn_rect, 2)
        
        btn_str = "切换:细胞" if inventory.view_mode == 'equipment' else "切换:装备"
        btn_text = settings.small_font.render(btn_str, True, settings.WHITE)
        text_rect = btn_text.get_rect(center=inventory.toggle_btn_rect.center)
        self.screen.blit(btn_text, text_rect)
        
        # 绘制整理按钮
        sort_color = (100, 150, 100) if inventory.sort_btn_rect.collidepoint(pygame.mouse.get_pos()) else (80, 100, 80)
        pygame.draw.rect(self.screen, sort_color, inventory.sort_btn_rect)
        pygame.draw.rect(self.screen, get_theme_color('panel_border'), inventory.sort_btn_rect, 2)
        
        sort_text = settings.small_font.render("整理", True, settings.WHITE)
        sort_rect = sort_text.get_rect(center=inventory.sort_btn_rect.center)
        self.screen.blit(sort_text, sort_rect)
        
        # 分隔线
        pygame.draw.line(self.screen, get_theme_color('panel_border'), 
                         (inventory.x + inventory.equip_width, inventory.y + 10),
                         (inventory.x + inventory.equip_width, inventory.y + inventory.height - 10), 2)

        if inventory.view_mode == 'equipment':
            self.draw_inventory_equipment_panel(inventory)
        else:
            self.draw_inventory_cells_panel(inventory)

        # --- 右侧背包区域 ---
        title = settings.medium_font.render("背包", True, get_theme_color('text'))
        title_rect = title.get_rect(midbottom=(inventory.x + inventory.equip_width + inventory.grid_width // 2, inventory.y + 10))
        self.screen.blit(title, title_rect)
        
        grid_start_x = inventory.x + inventory.equip_width + inventory.padding
        grid_start_y = inventory.y + inventory.padding + 30 
        
        slot_img = resource_manager.get_image("ui_slot")
        
        for i in range(inventory.rows * inventory.cols):
            row = i // inventory.cols
            col = i % inventory.cols
            x = grid_start_x + col * (inventory.slot_size + inventory.padding)
            y = grid_start_y + row * (inventory.slot_size + inventory.padding)
            
            rect = pygame.Rect(x, y, inventory.slot_size, inventory.slot_size)
            
            if slot_img:
                scaled_slot = pygame.transform.scale(slot_img, (inventory.slot_size, inventory.slot_size))
                self.screen.blit(scaled_slot, rect)
            else:
                pygame.draw.rect(self.screen, get_theme_color('grid'), rect)
                pygame.draw.rect(self.screen, get_theme_color('panel_border'), rect, 1)
            
            item = inventory.items[i]
            if item and item is not inventory.dragging_item:
                if rect.collidepoint(pygame.mouse.get_pos()):
                    self.hovered_item = item

                icon_key = f"items_{item.id}"
                icon = resource_manager.get_image(icon_key)
                
                if icon:
                     scaled_icon = pygame.transform.scale(icon, (inventory.slot_size-6, inventory.slot_size-6))
                     self.screen.blit(scaled_icon, (rect.x + 3, rect.y + 3))
                else:
                    color = (200, 200, 200)
                    if hasattr(item, 'color'): color = item.color
                    elif isinstance(item, dict) and 'color' in item: color = item['color']
                    
                    pygame.draw.rect(self.screen, color, rect.inflate(-10, -10))
                    
                    name = ""
                    if hasattr(item, 'name'): name = item.name
                    elif isinstance(item, str): name = item
                    elif isinstance(item, dict): name = item.get('name', '')
                    
                    if name:
                        text = settings.small_font.render(name[:1], True, get_theme_color('text'))
                        self.screen.blit(text, text.get_rect(center=rect.center))
                    
        # --- 技能栏区域 (Inventory) ---
        stitle = settings.medium_font.render("技能栏", True, get_theme_color('text'))
        stitle_rect = stitle.get_rect(midbottom=(inventory.x + inventory.equip_width + inventory.grid_width // 2, inventory.y + inventory.height - inventory.skill_bar_height + 10))
        self.screen.blit(stitle, stitle_rect)
        
        for i, rect in enumerate(inventory.skill_slots_rects):
            pygame.draw.rect(self.screen, (50, 50, 60), rect)
            pygame.draw.rect(self.screen, get_theme_color('panel_border'), rect, 1)
            
            item = inventory.skill_slots[i]
            if item and item is not inventory.dragging_item:
                if rect.collidepoint(pygame.mouse.get_pos()):
                    self.hovered_item = item

                color = (200, 200, 200)
                if hasattr(item, 'color'): color = item.color
                
                pygame.draw.rect(self.screen, color, rect.inflate(-10, -10))
                
                name = item.name if hasattr(item, 'name') else str(item)
                text = settings.small_font.render(name[:1], True, settings.WHITE)
                self.screen.blit(text, text.get_rect(center=rect.center))
                
        # --- 拖拽物品 ---
        if inventory.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            x = mouse_pos[0] + inventory.dragging_offset[0]
            y = mouse_pos[1] + inventory.dragging_offset[1]
            
            drag_rect = pygame.Rect(x, y, inventory.slot_size, inventory.slot_size)
            
            item = inventory.dragging_item
            color = (200, 200, 200)
            if hasattr(item, 'color'): color = item.color
            elif isinstance(item, dict): color = item.get('color', color)
            
            pygame.draw.rect(self.screen, color, drag_rect.inflate(-5, -5))
            pygame.draw.rect(self.screen, settings.WHITE, drag_rect, 2)

        # Draw Tooltip on top of everything
        if self.hovered_item and not inventory.dragging_item:
            self.draw_tooltip(self.hovered_item, pygame.mouse.get_pos())
            
        # Draw Dialog LAST so it's on top of everything
        self.draw_merge_dialog(inventory)

    def draw_merge_dialog(self, inventory):
        if not hasattr(inventory, 'merge_dialog') or not inventory.merge_dialog: return
        
        rect = inventory.merge_dialog['rect']
        
        # Background
        pygame.draw.rect(self.screen, (30, 30, 30), rect)
        pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
        
        # Title
        font_title = settings.medium_font
        title = font_title.render("强化确认", True, (255, 255, 255))
        self.screen.blit(title, (rect.x + 20, rect.y + 10))
        
        # Content
        font_desc = settings.small_font
        desc1 = font_desc.render("强化只提升主属性数值", True, (200, 200, 200))
        desc2 = font_desc.render("是否确定消耗物品进行强化？", True, (200, 200, 200))
        self.screen.blit(desc1, (rect.x + 20, rect.y + 40))
        self.screen.blit(desc2, (rect.x + 20, rect.y + 60))
        
        # Checkbox
        chk_rect = pygame.Rect(rect.x + 20, rect.y + 85, 16, 16)
        pygame.draw.rect(self.screen, (100, 100, 100), chk_rect, 1)
        if inventory.suppress_merge_confirm:
            pygame.draw.line(self.screen, (0, 255, 0), (chk_rect.x+2, chk_rect.y+8), (chk_rect.x+6, chk_rect.y+12), 2)
            pygame.draw.line(self.screen, (0, 255, 0), (chk_rect.x+6, chk_rect.y+12), (chk_rect.x+14, chk_rect.y+2), 2)
            
        chk_text = font_desc.render("本局不再提示", True, (150, 150, 150))
        self.screen.blit(chk_text, (rect.x + 45, rect.y + 85))
        
        # Buttons
        btn_font = settings.small_font
        
        # Confirm
        confirm_rect = pygame.Rect(rect.x + 20, rect.y + 110, 80, 30)
        pygame.draw.rect(self.screen, (50, 150, 50), confirm_rect)
        confirm_txt = btn_font.render("确定", True, (255, 255, 255))
        self.screen.blit(confirm_txt, (confirm_rect.centerx - confirm_txt.get_width()//2, confirm_rect.centery - confirm_txt.get_height()//2))
        
        # Cancel
        cancel_rect = pygame.Rect(rect.x + 200, rect.y + 110, 80, 30)
        pygame.draw.rect(self.screen, (150, 50, 50), cancel_rect)
        cancel_txt = btn_font.render("取消", True, (255, 255, 255))
        self.screen.blit(cancel_txt, (cancel_rect.centerx - cancel_txt.get_width()//2, cancel_rect.centery - cancel_txt.get_height()//2))

    def draw_inventory_equipment_panel(self, inventory):
        title = settings.medium_font.render("装备", True, get_theme_color('text'))
        title_rect = title.get_rect(midbottom=(inventory.x + inventory.equip_width // 2, inventory.y + 10))
        self.screen.blit(title, title_rect)
        
        for slot_name, rect_rel in inventory.equip_slots_rects.items():
            rect = rect_rel.move(inventory.x, inventory.y)
            
            pygame.draw.rect(self.screen, get_theme_color('grid'), rect)
            pygame.draw.rect(self.screen, get_theme_color('panel_border'), rect, 1)
            
            label = inventory.slot_labels[slot_name]
            l_text = settings.small_font.render(label, True, get_theme_color('text'))
            l_rect = l_text.get_rect(center=rect.center)
            self.screen.blit(l_text, l_rect)
            
            item = inventory.equipment[slot_name]
            if item:
                if rect.collidepoint(pygame.mouse.get_pos()):
                    self.hovered_item = item

                color = (200, 200, 200)
                if hasattr(item, 'color'): color = item.color
                elif isinstance(item, dict) and 'color' in item: color = item['color']
                
                pygame.draw.rect(self.screen, color, rect.inflate(-5, -5))

    def draw_inventory_cells_panel(self, inventory):
        title = settings.medium_font.render("细胞系统", True, get_theme_color('text'))
        title_rect = title.get_rect(midbottom=(inventory.x + inventory.equip_width // 2, inventory.y + 10))
        self.screen.blit(title, title_rect)
        
        # 1. 绘制连线
        upper_core_slot = next((s for s in inventory.cell_slots_layout if s['id'] == 0), None)
        lower_core_slot = next((s for s in inventory.cell_slots_layout if s['id'] == 5), None)
        
        if upper_core_slot and lower_core_slot:
            start_rect = upper_core_slot['rect'].move(inventory.x, inventory.y)
            end_rect = lower_core_slot['rect'].move(inventory.x, inventory.y)
            pygame.draw.line(self.screen, get_theme_color('panel_border'), start_rect.center, end_rect.center, 5)

        for slot_info in inventory.cell_slots_layout:
            start_rect = slot_info['rect'].move(inventory.x, inventory.y)
            start_center = start_rect.center
            
            for target_id in slot_info['connections']:
                target_slot = next((s for s in inventory.cell_slots_layout if s['id'] == target_id), None)
                if target_slot:
                    end_rect = target_slot['rect'].move(inventory.x, inventory.y)
                    pygame.draw.line(self.screen, get_theme_color('panel_border'), start_center, end_rect.center, 5)

        # 2. 绘制特殊槽位
        if inventory.gene_lock_rect:
            g_rect = inventory.gene_lock_rect.move(inventory.x, inventory.y)
            
            if not inventory.gene_unlocked:
                pygame.draw.rect(self.screen, (50, 0, 0), g_rect)
                pygame.draw.rect(self.screen, (200, 0, 0), g_rect, 2)
                text = settings.small_font.render("锁", True, (255, 100, 100))
                self.screen.blit(text, text.get_rect(center=g_rect.center))
                
                if g_rect.collidepoint(pygame.mouse.get_pos()) and inventory.dragging_item and inventory.dragging_item.id == 'gene_potion':
                    pygame.draw.rect(self.screen, (0, 255, 0), g_rect, 3)
        
        if inventory.heart_slot_rect:
            h_rect = inventory.heart_slot_rect.move(inventory.x, inventory.y)
            pygame.draw.rect(self.screen, (40, 0, 0), h_rect)
            pygame.draw.rect(self.screen, (200, 50, 50), h_rect, 2)
            
            if inventory.heart_slot:
                item = inventory.heart_slot
                if item is not inventory.dragging_item:
                    color = (255, 100, 100)
                    if hasattr(item, 'color'): color = item.color
                    
                    pygame.draw.rect(self.screen, color, h_rect.inflate(-6, -6))
                    
                    if h_rect.collidepoint(pygame.mouse.get_pos()):
                        self.hovered_item = item
            else:
                text = settings.small_font.render("心", True, (150, 50, 50))
                self.screen.blit(text, text.get_rect(center=h_rect.center))

        # 3. 绘制细胞槽位
        for slot_info in inventory.cell_slots_layout:
            rect = slot_info['rect'].move(inventory.x, inventory.y)
            slot_id = slot_info['id']
            is_locked = inventory.is_slot_locked(slot_id)
            
            bg_color = get_theme_color('grid')
            border_color = get_theme_color('panel_border')
            
            if slot_id in [0, 5]:
                border_color = (0, 255, 255)
                if not is_locked:
                    bg_color = (30, 50, 50)

            if is_locked:
                bg_color = (30, 30, 30)
                border_color = (100, 50, 50)
                
            pygame.draw.circle(self.screen, bg_color, rect.center, 25)
            pygame.draw.circle(self.screen, border_color, rect.center, 25, 2)
            
            if is_locked:
                text = settings.small_font.render("LOCK", True, (150, 50, 50))
                self.screen.blit(text, text.get_rect(center=rect.center))
            else:
                item = inventory.cells[slot_id]
                if item and item is not inventory.dragging_item:
                    if rect.collidepoint(pygame.mouse.get_pos()):
                        self.hovered_item = item
    
                    icon_key = f"items_{item.id}"
                    icon = resource_manager.get_image(icon_key)
                    
                    if icon:
                        scaled_icon = pygame.transform.scale(icon, (40, 40))
                        icon_rect = scaled_icon.get_rect(center=rect.center)
                        self.screen.blit(scaled_icon, icon_rect)
                    else:
                        color = (200, 200, 200)
                        if hasattr(item, 'color'): color = item.color
                        elif isinstance(item, dict) and 'color' in item: color = item['color']
                        
                        pygame.draw.circle(self.screen, color, rect.center, 20)
