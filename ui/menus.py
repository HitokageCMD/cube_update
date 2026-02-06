import pygame
import config.game_config as settings
from utils.resource_manager import resource_manager
from utils.sound_manager import SoundManager
from ui.widgets import Button, Slider, CharacterCard, SaveSlotButton, ThemeButton, KeybindButton
from data.item_data import SKILL_ITEMS

get_theme_color = settings.get_theme_color

class MenuRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.bg_offset = 0
        self.particles = [] # Background particles

    def draw_menu(self, buttons, title_text="Cube Upgrade"):
        # Draw dynamic background
        self.bg_offset = (self.bg_offset + 0.5) % 100
        self.screen.fill(get_theme_color('bg'))
        
        # Grid
        grid_color = get_theme_color('grid')
        for x in range(0, settings.SCREEN_WIDTH, 50):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, settings.SCREEN_HEIGHT))
        for y in range(int(self.bg_offset) - 100, settings.SCREEN_HEIGHT, 50):
            pygame.draw.line(self.screen, grid_color, (0, y), (settings.SCREEN_WIDTH, y))

        # Floating Particles (Small Cubes)
        # Spawn logic
        import random
        if random.random() < 0.05:
            self.particles.append({
                'x': random.randint(0, settings.SCREEN_WIDTH),
                'y': settings.SCREEN_HEIGHT + 20,
                'size': random.randint(10, 30),
                'speed': random.uniform(1, 3),
                'color': (random.randint(50, 100), random.randint(50, 100), random.randint(100, 200))
            })
            
        # Update and Draw Particles
        for p in self.particles[:]:
            p['y'] -= p['speed']
            # Draw cube
            rect = pygame.Rect(p['x'], p['y'], p['size'], p['size'])
            pygame.draw.rect(self.screen, p['color'], rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 1) # Border
            
            if p['y'] < -50:
                self.particles.remove(p)

        # Title
        title = settings.title_font.render(title_text, True, get_theme_color('text'))
        title_rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, 120)) # Moved up slightly
        
        # Shadow
        shadow = settings.title_font.render(title_text, True, (100, 100, 100))
        self.screen.blit(shadow, title_rect.move(4, 4))
        self.screen.blit(title, title_rect)
        
        # Version
        ver = settings.small_font.render(f"v{settings.VERSION}", True, settings.GRAY)
        self.screen.blit(ver, (settings.SCREEN_WIDTH - 60, settings.SCREEN_HEIGHT - 30))

        # Buttons
        for btn in buttons:
            btn.draw(self.screen)

    def draw_char_select(self, char_cards, confirm_btn, back_btn):
        self.screen.fill(get_theme_color('bg'))
        
        title = settings.font.render("选择你的角色", True, get_theme_color('text'))
        rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, rect)
        
        for card in char_cards:
            card.draw(self.screen)
            
        def wrap_text_ch(s, font, max_w):
            lines = []
            curr = ""
            for ch in s:
                test = curr + ch
                if font.size(test)[0] > max_w and curr:
                    lines.append(curr)
                    curr = ch
                else:
                    curr = test
            if curr:
                lines.append(curr)
            return lines
        
        selected = next((c for c in char_cards if c.selected), None)
        if selected:
            data = selected.data
            name_h = settings.medium_font.get_height()
            class_h = settings.small_font.get_height()
            text_bottom = 0
            for c in char_cards:
                nb = int(c.rect.bottom + 20 + name_h * 0.5)
                cb = int(c.rect.bottom + 50 + class_h * 0.5)
                text_bottom = max(text_bottom, nb, cb)
            info_y = text_bottom + 20
            
            max_w = int(settings.SCREEN_WIDTH * 0.8)
            desc_lines = wrap_text_ch(data.get('desc', ''), settings.medium_font, max_w)
            curr_y = info_y
            for ln in desc_lines[:2]:
                desc_surf = settings.medium_font.render(ln, True, get_theme_color('text'))
                desc_rect = desc_surf.get_rect(midtop=(settings.SCREEN_WIDTH // 2, curr_y))
                self.screen.blit(desc_surf, desc_rect)
                curr_y = desc_rect.bottom + 6
            
            stats_info = data.get('stats', {})
            hp = stats_info.get('max_hp', 100)
            speed = stats_info.get('move_speed', 300)
            char_class = data.get('class', 'Unknown')
            
            stats_str = f"基础属性:  HP {hp}   速度 {speed}"
            stats = settings.small_font.render(stats_str, True, (200, 200, 200))
            stats_rect = stats.get_rect(midtop=(settings.SCREEN_WIDTH // 2, curr_y))
            self.screen.blit(stats, stats_rect)
            curr_y = stats_rect.bottom + 6
            
            sid = None
            if data['id'] == 'square':
                sid = 'skill_area_slash'
            elif data['id'] == 'triangle':
                sid = 'skill_overload'
            elif data['id'] == 'circle':
                sid = 'skill_black_hole'
            skill_item = SKILL_ITEMS.get(sid)
            if skill_item:
                line1 = f"专属技能: {skill_item.name}  消耗 {skill_item.mp_cost}  冷却 {skill_item.cooldown}s"
                l1_surf = settings.small_font.render(line1, True, (255, 215, 0))
                l1_rect = l1_surf.get_rect(midtop=(settings.SCREEN_WIDTH // 2, curr_y))
                self.screen.blit(l1_surf, l1_rect)
                curr_y = l1_rect.bottom + 4
                
                desc_text = getattr(skill_item, 'description', '') or ''
                brief_lines = wrap_text_ch(desc_text, settings.small_font, max_w)
                for ln in brief_lines[:2]:
                    l_surf = settings.small_font.render(ln, True, (200, 200, 200))
                    l_rect = l_surf.get_rect(midtop=(settings.SCREEN_WIDTH // 2, curr_y))
                    self.screen.blit(l_surf, l_rect)
                    curr_y = l_rect.bottom + 4
            
        confirm_btn.draw(self.screen)
        back_btn.draw(self.screen)

    def draw_settings(self, sub_state, back_btn, main_buttons=None, display_buttons=None, theme_btn=None, audio_sliders=None, audio_buttons=None, control_buttons=None):
        # Draw semi-transparent overlay if in-game, else solid
        s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        s.fill(get_theme_color('bg')) 
        self.screen.blit(s, (0, 0))
        
        title_str = "设置"
        if sub_state == 'display': title_str = "界面设置"
        elif sub_state == 'audio': title_str = "声音设置"
        elif sub_state == 'controls': title_str = "控制设置"
        
        title = settings.font.render(title_str, True, get_theme_color('text'))
        self.screen.blit(title, (50, 30))
        
        back_btn.draw(self.screen)
        
        if sub_state == 'main':
            if main_buttons:
                for btn in main_buttons:
                    btn.draw(self.screen)
                    
        elif sub_state == 'display':
            if display_buttons:
                for btn in display_buttons:
                    btn.draw(self.screen)
            if theme_btn:
                theme_btn.draw(self.screen)
                
        elif sub_state == 'audio':
            if audio_sliders:
                for slider in audio_sliders:
                    slider.draw(self.screen)
            if audio_buttons:
                for btn in audio_buttons:
                    btn.draw(self.screen)
                    
        elif sub_state == 'controls':
            if control_buttons:
                for btn in control_buttons:
                    btn.draw(self.screen)

    def draw_pause(self, buttons):
        # Overlay
        s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        self.screen.blit(s, (0, 0))
        
        title = settings.title_font.render("暂停", True, settings.WHITE)
        rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, rect)
        
        for btn in buttons:
            btn.draw(self.screen)

    def draw_save_load(self, mode, slot_buttons, back_btn):
        self.screen.fill(get_theme_color('bg'))
        
        text = "保存游戏" if mode == 'save' else "读取游戏"
        title = settings.font.render(text, True, get_theme_color('text'))
        self.screen.blit(title, (50, 30))
        
        for btn in slot_buttons:
            btn.draw(self.screen)
            
        back_btn.draw(self.screen)

    def draw_save_confirm(self, mode, slot_idx, yes_btn, no_btn):
        # Popup overlay
        s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.screen.blit(s, (0, 0))
        
        box_w, box_h = 400, 200
        box_rect = pygame.Rect((settings.SCREEN_WIDTH - box_w)//2, (settings.SCREEN_HEIGHT - box_h)//2, box_w, box_h)
        
        pygame.draw.rect(self.screen, settings.WHITE, box_rect)
        pygame.draw.rect(self.screen, settings.BLACK, box_rect, 2)
        
        msg = f"覆盖存档 {slot_idx+1}?" if mode == 'save' else f"读取存档 {slot_idx+1}?"
        if mode == 'load' and slot_idx == -1: msg = "读取失败?" # Should not happen
        
        text = settings.medium_font.render(msg, True, settings.BLACK)
        text_rect = text.get_rect(center=(settings.SCREEN_WIDTH//2, settings.SCREEN_HEIGHT//2 - 20))
        self.screen.blit(text, text_rect)
        
        if mode == 'save':
            sub = settings.small_font.render("(旧存档将丢失)", True, (200, 0, 0))
            sub_rect = sub.get_rect(center=(settings.SCREEN_WIDTH//2, settings.SCREEN_HEIGHT//2 + 10))
            self.screen.blit(sub, sub_rect)
            
        yes_btn.draw(self.screen)
        no_btn.draw(self.screen)

    def draw_game_over(self, score, buttons):
        s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((50, 0, 0, 200))
        self.screen.blit(s, (0, 0))
        
        title = settings.title_font.render("GAME OVER", True, (255, 0, 0))
        title_rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        score_text = settings.font.render(f"生存时间: {score}", True, settings.WHITE)
        score_rect = score_text.get_rect(center=(settings.SCREEN_WIDTH // 2, 250))
        self.screen.blit(score_text, score_rect)
        
        for btn in buttons:
            btn.draw(self.screen)

    def draw_changelog(self, scroll_y, back_btn):
        self.screen.fill(get_theme_color('bg'))
        
        title = settings.font.render("更新日志", True, get_theme_color('text'))
        self.screen.blit(title, (50, 30))
        
        # Load logs from data/changelog.py if possible, but here we just render passed text or static
        # Assuming we just use what's in settings or data
        # For now, placeholder or render logic
        
        # Clipping rect
        clip_rect = pygame.Rect(50, 100, settings.SCREEN_WIDTH - 100, settings.SCREEN_HEIGHT - 150)
        self.screen.set_clip(clip_rect)
        
        # Render text (simplified)
        # In a real impl, we'd pass lines or text object
        
        self.screen.set_clip(None)
        back_btn.draw(self.screen)

    def draw_guide(self, tabs, current_tab_index, items, selected_item, scroll_y, back_btn):
        self.screen.fill(get_theme_color('bg'))
        
        title = settings.font.render(f"游戏图鉴", True, get_theme_color('text'))
        self.screen.blit(title, (50, 30))
        
        # Draw Tabs
        tab_w = 120
        tab_h = 40
        total_tabs_width = len(tabs) * tab_w + (len(tabs) - 1) * 10
        start_x = (settings.SCREEN_WIDTH - total_tabs_width) // 2
        start_y = 80
        
        for i, tab_name in enumerate(tabs):
            x = start_x + i * (tab_w + 10)
            rect = pygame.Rect(x, start_y, tab_w, tab_h)
            
            # Highlight current tab
            color = (100, 100, 255) if i == current_tab_index else (60, 60, 60)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            pygame.draw.rect(self.screen, settings.BLACK, rect, 2, border_radius=5)
            
            # Map tab key to display name
            display_name = tab_name
            if tab_name == 'skills': display_name = "技能"
            elif tab_name == 'equipment': display_name = "装备"
            elif tab_name == 'cores': display_name = "核心/细胞"
            elif tab_name == 'reactions': display_name = "元素反应"
            elif tab_name == 'enemies': display_name = "敌人"
            elif tab_name == 'drops': display_name = "掉落表"
            
            text = settings.small_font.render(display_name, True, settings.WHITE)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

        # Content Area
        content_rect = pygame.Rect(50, start_y + tab_h + 20, settings.SCREEN_WIDTH - 100, settings.SCREEN_HEIGHT - (start_y + tab_h + 20) - 50)
        pygame.draw.rect(self.screen, (30, 30, 30), content_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), content_rect, 2)
        
        # Clip content
        self.screen.set_clip(content_rect)
        
        # Draw Grid Items
        if tabs[current_tab_index] not in ['reactions', 'drops']:
            slot_size = 60
            gap = 15
            cols = 6
            start_content_y = content_rect.top + 20 - scroll_y
            start_content_x = content_rect.left + 20
            
            for i, item in enumerate(items):
                col = i % cols
                row = i // cols
                x = start_content_x + col * (slot_size + gap)
                y = start_content_y + row * (slot_size + gap)
                
                # Check visibility
                if y + slot_size < content_rect.top or y > content_rect.bottom:
                    continue
                    
                rect = pygame.Rect(x, y, slot_size, slot_size)
                
                # Draw Item Box
                color = (60, 60, 60)
                if selected_item == item:
                    color = (100, 100, 150)
                    
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)
                
                # Draw Icon/Name
                # Try icon first
                icon_key = None
                if hasattr(item, 'id'): icon_key = f"items_{item.id}"
                elif isinstance(item, dict): icon_key = f"items_{item.get('id')}"
                
                icon = resource_manager.get_image(icon_key) if icon_key else None
                
                if icon:
                     scaled = pygame.transform.scale(icon, (slot_size-6, slot_size-6))
                     self.screen.blit(scaled, (x+3, y+3))
                else:
                    name = "?"
                    if hasattr(item, 'name'): name = item.name
                    elif isinstance(item, dict): name = item.get('name', '?')
                    
                    text = settings.small_font.render(name[:1], True, settings.WHITE)
                    self.screen.blit(text, text.get_rect(center=rect.center))

        elif tabs[current_tab_index] == 'reactions':
             # List view for reactions
             start_content_y = content_rect.top + 20 - scroll_y
             for i, reaction in enumerate(items):
                 y = start_content_y + i * 80
                 if y + 80 < content_rect.top or y > content_rect.bottom: continue
                 
                 pygame.draw.rect(self.screen, (50, 50, 50), (content_rect.left + 20, y, content_rect.width - 40, 70))
                 
                 # Safely get data
                 if isinstance(reaction, dict):
                     name = reaction.get('name', 'Unknown')
                     desc = reaction.get('description', '') or reaction.get('desc', '')
                     recipe = reaction.get('recipe', '')
                 else:
                     name = getattr(reaction, 'name', 'Unknown')
                     desc = getattr(reaction, 'description', '')
                     recipe = getattr(reaction, 'recipe', '')
                 
                 # Draw text
                 name_surf = settings.medium_font.render(name, True, (255, 215, 0))
                 self.screen.blit(name_surf, (content_rect.left + 30, y + 10))
                 
                 desc_surf = settings.small_font.render(desc, True, (200, 200, 200))
                 self.screen.blit(desc_surf, (content_rect.left + 30, y + 40))
                 
                 # Draw Recipe
                 if recipe:
                     recipe_surf = settings.small_font.render(f"配方: {recipe}", True, (100, 255, 100))
                     recipe_rect = recipe_surf.get_rect(topright=(content_rect.right - 30, y + 10))
                     self.screen.blit(recipe_surf, recipe_rect)

        self.screen.set_clip(None)

        # Draw Details Panel (if item selected)
        if selected_item and tabs[current_tab_index] not in ['reactions', 'drops']:
             # Draw a floating panel on the right or center
             panel_w = 300
             panel_h = 400
             panel_x = settings.SCREEN_WIDTH - panel_w - 60
             panel_y = content_rect.top + 20
             
             panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
             pygame.draw.rect(self.screen, (40, 40, 50), panel_rect)
             pygame.draw.rect(self.screen, (255, 215, 0), panel_rect, 2)
             
             # Extract Data safely
             if isinstance(selected_item, dict):
                 name = selected_item.get('name', 'Unknown')
                 desc = selected_item.get('description', '') or selected_item.get('desc', '')
                 stats = selected_item.get('stats', {})
             else:
                 name = getattr(selected_item, 'name', 'Unknown')
                 desc = getattr(selected_item, 'description', '')
                 stats = getattr(selected_item, 'stats', {})
             
             # Render
             curr_y = panel_y + 20
             name_surf = settings.medium_font.render(name, True, (255, 215, 0))
             self.screen.blit(name_surf, (panel_x + 20, curr_y))
             curr_y += 40
             
             # Desc wrapped
             words = desc.split()
             line = []
             for word in words:
                 line.append(word)
                 if settings.small_font.size(" ".join(line))[0] > panel_w - 40:
                     line.pop()
                     l_surf = settings.small_font.render(" ".join(line), True, (200, 200, 200))
                     self.screen.blit(l_surf, (panel_x + 20, curr_y))
                     curr_y += 20
                     line = [word]
             if line:
                 l_surf = settings.small_font.render(" ".join(line), True, (200, 200, 200))
                 self.screen.blit(l_surf, (panel_x + 20, curr_y))
                 curr_y += 30
                 
             # Stats
             for k, v in stats.items():
                 s_surf = settings.small_font.render(f"{k}: {v}", True, (100, 255, 100))
                 self.screen.blit(s_surf, (panel_x + 20, curr_y))
                 curr_y += 20
        
        back_btn.draw(self.screen)

    def draw_credits(self, back_btn):
        self.screen.fill(settings.BLACK)
        
        title = settings.font.render("制作人员", True, settings.WHITE)
        title_rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        lines = [
            "程序: LYP",
            "美术: LYP & Assets",
            "音效: Generated",
            "引擎: Pygame & Python",
            "",
            "感谢游玩!"
        ]
        
        y = 200
        for line in lines:
            text = settings.medium_font.render(line, True, settings.GRAY)
            rect = text.get_rect(center=(settings.SCREEN_WIDTH // 2, y))
            self.screen.blit(text, rect)
            y += 40
            
        back_btn.draw(self.screen)

    def draw_donate(self, back_btn):
        self.screen.fill(get_theme_color('bg'))
        
        title = settings.font.render("支持作者", True, get_theme_color('text'))
        self.screen.blit(title, (50, 30))
        
        msg = "如果喜欢这个游戏，请考虑..."
        text = settings.medium_font.render(msg, True, get_theme_color('text'))
        self.screen.blit(text, (100, 150))
        
        back_btn.draw(self.screen)
