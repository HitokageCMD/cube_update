import pygame
import config.game_config as settings

class DevUIRenderer:
    def __init__(self, screen):
        self.screen = screen
        
        # Colors
        self.bg_color = (30, 30, 30, 230)
        self.panel_border = (100, 100, 100)
        self.text_color = (255, 255, 255)
        self.btn_color = (60, 60, 60)
        self.btn_hover = (80, 80, 80)
        self.btn_border = (120, 120, 120)
        
        # Fonts
        self.title_font = pygame.font.SysFont("SimHei", 32)
        self.font = pygame.font.SysFont("SimHei", 18)
        self.small_font = pygame.font.SysFont("Arial", 14)

    def draw_dev_panel(self, dev_manager):
        if not dev_manager.show_console:
            return

        # 1. Background Overlay
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.bg_color)
        self.screen.blit(overlay, (0, 0))
        
        # 2. Header
        title_surf = self.title_font.render("开发者菜单 (按F4关闭)", True, (255, 100, 100))
        self.screen.blit(title_surf, (20, 20))
        
        # Status Text (Right aligned)
        player = dev_manager.game_manager.player
        god_status = "开启" if getattr(player, 'god_mode', False) else "关闭"
        status_text = f"速度: x1.0 | 上帝模式: {god_status}"
        status_surf = self.font.render(status_text, True, (200, 200, 200))
        self.screen.blit(status_surf, (settings.SCREEN_WIDTH - status_surf.get_width() - 20, 30))

        # Clear button lists for rebuilding (simple immediate mode GUI approach)
        dev_manager.buttons.clear()
        dev_manager.stat_buttons.clear()

        # 3. Layout Configuration
        panel_y = 80
        panel_h = settings.SCREEN_HEIGHT - 100
        col_1_w = 200
        col_2_w = 400
        col_3_w = 250
        gap = 20
        
        # --- Column 1: Game Control ---
        x = 20
        self.draw_panel_box(x, panel_y, col_1_w, panel_h, "游戏控制")
        
        # Control Buttons
        btn_start_y = panel_y + 40
        btn_h = 35
        btn_gap = 10
        
        controls = [
            ("上帝模式: " + god_status, dev_manager.action_god_mode),
            ("秒杀全屏", dev_manager.action_kill_all),
            ("状态全满", dev_manager.action_full_restore),
            ("立即升级", dev_manager.action_level_up),
            (f"生成类型: {dev_manager.spawn_types[dev_manager.current_spawn_type_idx]}", dev_manager.action_cycle_spawn_type),
            (f"生成数量: {dev_manager.spawn_count} [+]", dev_manager.action_inc_spawn_count),
            (f"生成数量: {dev_manager.spawn_count} [-]", dev_manager.action_dec_spawn_count),
            ("执行生成", dev_manager.action_spawn_enemy)
        ]
        
        for i, (text, action) in enumerate(controls):
            rect = pygame.Rect(x + 10, btn_start_y + i * (btn_h + btn_gap), col_1_w - 20, btn_h)
            self.draw_button(rect, text, dev_manager, action)
            
        # --- Column 2: Attribute Edit ---
        x += col_1_w + gap
        self.draw_panel_box(x, panel_y, col_2_w, panel_h, "属性编辑")
        
        stat_y = panel_y + 40
        row_h = 30
        col_w = (col_2_w - 30) // 2 # 2 columns of stats
        
        for i, key in enumerate(dev_manager.stat_keys):
            # Calculate grid position
            col_idx = i % 2
            row_idx = i // 2
            
            stat_x = x + 10 + col_idx * (col_w + 10)
            curr_y = stat_y + row_idx * row_h
            
            # Label
            label = dev_manager.stat_labels.get(key, key)
            val = getattr(player, key, 0)
            if isinstance(val, float):
                val_str = f"{val:.2f}"
            else:
                val_str = str(val)
                
            # [-] Button
            minus_rect = pygame.Rect(stat_x, curr_y + 5, 20, 20)
            self.draw_stat_button(minus_rect, "-", dev_manager, key, -1)
            
            # Value Text
            text_surf = self.font.render(f"{label}: {val_str}", True, self.text_color)
            self.screen.blit(text_surf, (stat_x + 25, curr_y + 5))
            
            # [+] Button (Align right of column)
            plus_rect = pygame.Rect(stat_x + col_w - 25, curr_y + 5, 20, 20)
            self.draw_stat_button(plus_rect, "+", dev_manager, key, 1)

        # --- Column 3: Item Spawn ---
        x += col_2_w + gap
        self.draw_panel_box(x, panel_y, col_3_w, panel_h, "物品生成")
        
        # Tabs
        tab_h = 25
        tab_y = panel_y + 40
        tab_names = {'skills': '技能', 'equip': '装备', 'cores': '核心', 'others': '其他'}
        
        tab_w = (col_3_w - 20) // 4
        
        for i, tab_key in enumerate(dev_manager.item_tabs):
            tab_x = x + 10 + i * tab_w
            rect = pygame.Rect(tab_x, tab_y, tab_w, tab_h)
            
            # Highlight active tab
            is_active = (tab_key == dev_manager.current_item_tab)
            color = (100, 100, 200) if is_active else self.btn_color
            
            # Action to switch tab
            def switch_tab(tk=tab_key):
                dev_manager.current_item_tab = tk
                dev_manager.item_scroll_y = 0
                
            self.draw_button(rect, tab_names.get(tab_key, tab_key), dev_manager, switch_tab)

        # Rarity Selector (Only for Equip Tab)
        list_y = tab_y + tab_h + 10
        if dev_manager.current_item_tab == 'equip':
            rarity_h = 25
            rarity_rect = pygame.Rect(x + 10, list_y, col_3_w - 20, rarity_h)
            
            current_rarity = dev_manager.equip_rarity_options[dev_manager.current_equip_rarity_idx]
            
            # Color mapping
            r_colors = {'white': (200,200,200), 'green': (100,255,100), 'blue': (100,100,255), 'purple': (255,100,255), 'orange': (255,165,0)}
            r_text_color = r_colors.get(current_rarity, (255,255,255))
            
            self.draw_button(rarity_rect, f"品质: {current_rarity.upper()} (点击切换)", dev_manager, dev_manager.action_cycle_equip_rarity)
            
            list_y += rarity_h + 10

        # Item List Area
        list_h = panel_h - (list_y - panel_y) - 20
        list_rect = pygame.Rect(x + 10, list_y, col_3_w - 20, list_h)
        
        # Clip area for scrolling
        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_rect)
        
        items = dev_manager.get_items_by_category()
        item_btn_h = 30
        item_gap = 5
        
        start_draw_y = list_y - dev_manager.item_scroll_y
        
        for i, item in enumerate(items):
            curr_y = start_draw_y + i * (item_btn_h + item_gap)
            
            # Optimization: Don't draw if out of view
            if curr_y + item_btn_h < list_y: continue
            if curr_y > list_y + list_h: break
            
            rect = pygame.Rect(x + 10, curr_y, col_3_w - 20, item_btn_h)
            
            # Add item action
            self.draw_button(rect, f"添加 {item.name}", dev_manager, lambda iid=item.id: dev_manager.action_add_item(iid))
            
        self.screen.set_clip(old_clip)

    def draw_panel_box(self, x, y, w, h, title):
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, self.bg_color, rect)
        pygame.draw.rect(self.screen, self.panel_border, rect, 1)
        
        title_surf = self.font.render(title, True, (200, 200, 200))
        self.screen.blit(title_surf, (x + 10, y + 10))
        
    def draw_button(self, rect, text, dev_manager, action):
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        
        color = self.btn_hover if hover else self.btn_color
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, self.btn_border, rect, 1)
        
        text_surf = self.font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
        
        dev_manager.buttons.append({
            'rect': rect,
            'text': text,
            'action': action,
            'hover': hover
        })

    def draw_stat_button(self, rect, text, dev_manager, stat_key, change):
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        
        color = self.btn_hover if hover else self.btn_color
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, self.btn_border, rect, 1)
        
        text_surf = self.font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
        
        dev_manager.stat_buttons.append({
            'rect': rect,
            'stat': stat_key,
            'change': change
        })
