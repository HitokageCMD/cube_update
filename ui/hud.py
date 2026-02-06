import pygame
import config.game_config as settings
from utils.resource_manager import resource_manager
from utils.sound_manager import SoundManager

game_config = settings.game_config
get_theme_color = settings.get_theme_color

class HUDRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.show_stats = False
        self.stats_toggle_rect = None
        self.prev_stats = {}
        self.stat_change_times = {}
        self.stat_change_types = {}

    def get_real_stat_value(self, player, stat_name):
        if hasattr(player, stat_name):
             val = getattr(player, stat_name)
             if not callable(val):
                 return val
        return player.stats.get(stat_name, 0)

    def draw_player_ui(self, player):
        # 绘制HUD
        # 血条
        bar_w = 200
        bar_h = 20
        x = 20
        y = 20
        
        # 尝试使用图片绘制血条
        bg_img = resource_manager.get_image("ui_bar_hp_bg")
        fill_img = resource_manager.get_image("ui_bar_hp_fill")
        
        if bg_img and fill_img:
            # HP
            hp_ratio = max(0, min(1, player.current_hp / player.max_hp))
            
            # Draw BG
            scaled_bg = pygame.transform.scale(bg_img, (bar_w, bar_h))
            self.screen.blit(scaled_bg, (x, y))
            
            # Draw Fill (Crop area)
            if hp_ratio > 0:
                fill_w = int(bar_w * hp_ratio)
                scaled_fill = pygame.transform.scale(fill_img, (bar_w, bar_h))
                self.screen.blit(scaled_fill, (x, y), (0, 0, fill_w, bar_h))
        else:
            # Code Fallback
            hp_ratio = player.current_hp / player.max_hp
            pygame.draw.rect(self.screen, (50, 0, 0), (x, y, bar_w, bar_h))
            pygame.draw.rect(self.screen, (200, 0, 0), (x, y, bar_w * hp_ratio, bar_h))
            pygame.draw.rect(self.screen, settings.BLACK, (x, y, bar_w, bar_h), 2)
        
        hp_text = settings.small_font.render(f"HP: {int(player.current_hp)}/{int(player.max_hp)}", True, get_theme_color('text'))
        self.screen.blit(hp_text, (x + bar_w + 10, y))
        
        # MP
        y += 30
        mp_ratio = player.current_mp / player.max_mp
        pygame.draw.rect(self.screen, (0, 0, 50), (x, y, bar_w, bar_h))
        pygame.draw.rect(self.screen, (0, 100, 255), (x, y, bar_w * mp_ratio, bar_h))
        pygame.draw.rect(self.screen, settings.BLACK, (x, y, bar_w, bar_h), 2)
        
        mp_text = settings.small_font.render(f"MP: {int(player.current_mp)}/{int(player.max_mp)}", True, get_theme_color('text'))
        self.screen.blit(mp_text, (x + bar_w + 10, y))
        
        # XP
        y += 30
        xp_ratio = player.current_xp / player.xp_to_next_level
        pygame.draw.rect(self.screen, (50, 50, 0), (x, y, bar_w, bar_h))
        pygame.draw.rect(self.screen, (255, 215, 0), (x, y, bar_w * xp_ratio, bar_h))
        pygame.draw.rect(self.screen, settings.BLACK, (x, y, bar_w, bar_h), 2)
        
        xp_text = settings.small_font.render(f"LV.{player.level} ({int(player.current_xp)}/{int(player.xp_to_next_level)})", True, get_theme_color('text'))
        self.screen.blit(xp_text, (x + bar_w + 10, y))
        
        # DPS Display
        y += 25
        dps_val = int(getattr(player, 'dps', 0))
        dps_text = settings.small_font.render(f"秒伤: {dps_val}", True, (255, 100, 100))
        self.screen.blit(dps_text, (x, y))

        # 属性面板开关
        y += 30
        self.stats_toggle_rect = pygame.Rect(x, y, 20, 20)
        
        # 绘制开关图标
        pygame.draw.rect(self.screen, (100, 100, 100), self.stats_toggle_rect)
        pygame.draw.rect(self.screen, get_theme_color('text'), self.stats_toggle_rect, 1)
        
        center = self.stats_toggle_rect.center
        arrow_color = get_theme_color('text')
        if self.show_stats:
            # 向上箭头 (隐藏)
            points = [(center[0], center[1]-5), (center[0]-5, center[1]+5), (center[0]+5, center[1]+5)]
        else:
            # 向下箭头 (展开)
            points = [(center[0], center[1]+5), (center[0]-5, center[1]-5), (center[0]+5, center[1]-5)]
        pygame.draw.polygon(self.screen, arrow_color, points)
        
        # 提示文字
        toggle_text = settings.small_font.render("属性详情", True, get_theme_color('text'))
        self.screen.blit(toggle_text, (x + 30, y))

        if self.show_stats:
            y += 25
            current_time = pygame.time.get_ticks()
            
            for name, key in [
                ("物理攻击", 'phys_atk'),
                ("魔法攻击", 'magic_atk'),
                ("物理穿透", 'phys_pen'),
                ("魔法穿透", 'magic_pen'),
                ("物理防御", 'phys_def'),
                ("魔法防御", 'magic_def'),
                ("真实伤害", 'true_dmg'),
                ("拾取范围", 'pickup_range'),
                ("攻速", 'attack_speed'),
                ("范围", 'attack_range'),
                ("技能范围", 'skill_range'),
                ("穿透", 'piercing_count'),
                ("暴击率", 'crit_chance'),
                ("暴击伤害", 'crit_dmg'),
                ("伤害加成", 'damage_bonus'),
                ("幸运", 'luck'),
                ("移速", 'move_speed'),
                ("生命回复", 'hp_regen'),
                ("魔力回复", 'mp_regen'),
                ("碰撞减免", 'collision_damage_reduction'),
                ("碰撞伤害", 'collision_dmg_pct'),
                ("技能急速", 'skill_haste'),
                ("急速上限", 'skill_haste_cap'),
                ("冷却缩减", 'cooldown_reduction')
            ]:
                # 获取基础值和实时值
                base_val = player.stats.get(key, 0)
                # 特殊处理计算属性
                if key == 'cooldown_reduction':
                    base_val = player.cooldown_reduction
                
                real_val = self.get_real_stat_value(player, key)
                
                # 格式化显示字符串
                if key in ['crit_dmg', 'damage_bonus', 'skill_haste_cap', 'collision_dmg_pct']:
                    val_str = f"{real_val}%"
                elif key == 'cooldown_reduction':
                    val_str = f"{real_val*100:.1f}%"
                elif isinstance(real_val, float):
                    val_str = f"{real_val:.3f}"
                else:
                    val_str = str(real_val)
                
                # --- 属性变化检测 ---
                prev_val = self.prev_stats.get(name)
                
                if prev_val is not None:
                    diff = real_val - prev_val
                    if abs(diff) > 0.001:
                        self.stat_change_times[name] = current_time
                        
                        if diff > 0:
                            self.stat_change_types[name] = 'up'
                        else:
                            if real_val < base_val - 0.001: 
                                self.stat_change_types[name] = 'down_bad'
                            else:
                                self.stat_change_types[name] = 'neutral'

                self.prev_stats[name] = real_val
                
                text_color = get_theme_color('text')
                
                last_change_time = self.stat_change_times.get(name, 0)
                if current_time - last_change_time < 3000:
                    change_type = self.stat_change_types.get(name, 'neutral')
                    if change_type == 'up':
                        text_color = (0, 255, 0)
                    elif change_type == 'down_bad':
                        text_color = (255, 50, 50)
                    
                text = settings.small_font.render(f"{name}: {val_str}", True, text_color)
                self.screen.blit(text, (x, y))
                y += 20

        # --- 绘制右下角技能栏 (HUD) ---
        if hasattr(player, 'inventory') and hasattr(player.inventory, 'skill_slots'):
            skill_box_size = 50
            skill_gap = 10
            start_x = settings.SCREEN_WIDTH - 4 * (skill_box_size + skill_gap) - 20
            start_y = settings.SCREEN_HEIGHT - skill_box_size - 20
            
            # 闪避UI在技能栏左侧
            dodge_x = start_x - (skill_box_size + skill_gap)
            dodge_rect = pygame.Rect(dodge_x, start_y, skill_box_size, skill_box_size)
            pygame.draw.rect(self.screen, (60, 60, 60), dodge_rect)
            pygame.draw.rect(self.screen, (200, 200, 200), dodge_rect, 2)
            # 键位显示
            kb = settings.game_config['key_bindings']
            dodge_key = kb.get('dodge', 0)
            dodge_key_name = "无" if dodge_key == 0 else (pygame.key.name(dodge_key).upper() if dodge_key > 0 else "鼠标")
            dk_surf = settings.small_font.render(dodge_key_name[:2], True, settings.WHITE)
            dk_rect = dk_surf.get_rect(center=dodge_rect.center)
            self.screen.blit(dk_surf, dk_rect)
            # 冷却遮罩
            if getattr(player, 'dodge_cooldown_timer', 0) > 0 and getattr(player, 'dodge_last_cd', 0) > 0:
                ratio = player.dodge_cooldown_timer / max(0.0001, player.dodge_last_cd)
                mask_h = int(skill_box_size * max(0.0, min(1.0, ratio)))
                s = pygame.Surface((skill_box_size, mask_h), pygame.SRCALPHA)
                s.fill((0, 0, 0, 150))
                self.screen.blit(s, (dodge_x, start_y + skill_box_size - mask_h))
                cd_text = settings.small_font.render(f"{player.dodge_cooldown_timer:.1f}", True, settings.WHITE)
                cd_rect = cd_text.get_rect(center=dodge_rect.center)
                self.screen.blit(cd_text, cd_rect)
            
            for i in range(4):
                x = start_x + i * (skill_box_size + skill_gap)
                box_rect = pygame.Rect(x, start_y, skill_box_size, skill_box_size)
                
                color = (50, 50, 50)
                skill = player.inventory.skill_slots[i]
                
                if i == player.selected_skill_slot:
                    pygame.draw.rect(self.screen, (255, 215, 0), box_rect.inflate(6, 6), 3)
                
                pygame.draw.rect(self.screen, color, box_rect)
                pygame.draw.rect(self.screen, (200, 200, 200), box_rect, 2)
                
                if skill:
                    skill_color = skill.color if hasattr(skill, 'color') else (200, 200, 200)
                    pygame.draw.rect(self.screen, skill_color, box_rect.inflate(-10, -10))
                    
                    name = skill.name if hasattr(skill, 'name') else str(skill)
                    name_surf = settings.small_font.render(name[:1], True, settings.WHITE)
                    name_rect = name_surf.get_rect(center=box_rect.center)
                    self.screen.blit(name_surf, name_rect)
                    
                    cd = player.skill_cooldowns.get(skill.id, 0)
                    if cd > 0:
                        ratio = cd / skill.cooldown
                        mask_height = int(skill_box_size * ratio)
                        s = pygame.Surface((skill_box_size, mask_height), pygame.SRCALPHA)
                        s.fill((0, 0, 0, 150))
                        self.screen.blit(s, (x, start_y + skill_box_size - mask_height))
                        
                        cd_text = settings.small_font.render(f"{cd:.1f}", True, settings.WHITE)
                        cd_rect = cd_text.get_rect(center=box_rect.center)
                        self.screen.blit(cd_text, cd_rect)
                else:
                    text_surf = settings.small_font.render(str(i+1), True, (100, 100, 100))
                    text_rect = text_surf.get_rect(center=box_rect.center)
                    self.screen.blit(text_surf, text_rect)
            
            # 提示文字
            kb = settings.game_config['key_bindings']
            
            def get_key_display(action_name):
                code = kb.get(action_name, 0)
                if code == 0: return "无"
                if code == settings.MOUSE_LEFT: return "左键"
                if code == settings.MOUSE_RIGHT: return "右键"
                if code == settings.MOUSE_MIDDLE: return "中键"
                if code < 0: return "鼠标"
                return pygame.key.name(code).upper()

            key_q = get_key_display('skill_1')
            key_e = get_key_display('skill_2')
            key_f = get_key_display('use_skill')
            key_shift = get_key_display('dodge')
            
            tip_str = f"[{key_shift}] 闪避   [{key_q}/{key_e}] 切换   [{key_f}] 释放"
            tip = settings.small_font.render(tip_str, True, get_theme_color('text'))
            
            tip_rect = tip.get_rect()
            skill_bar_right = start_x + 4 * (skill_box_size + skill_gap) - skill_gap
            tip_rect.bottomright = (skill_bar_right, start_y - 10)
            
            if tip_rect.left < 10:
                tip_rect.left = 10
            
            self.screen.blit(tip, tip_rect)

    def draw_floating_texts(self, camera, texts):
        for ft in texts:
            screen_pos = camera.apply(ft.pos)
            text_surf = settings.font.render(ft.text, True, ft.color)
            # 描边
            stroke_surf = settings.font.render(ft.text, True, settings.BLACK)
            
            x, y = int(screen_pos.x), int(screen_pos.y)
            
            # 绘制描边
            for offset in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                self.screen.blit(stroke_surf, (x + offset[0], y + offset[1]))
            
            self.screen.blit(text_surf, (x, y))

    def draw_fps(self, clock):
        if settings.game_config.get('show_fps', True):
            fps = int(clock.get_fps())
            color = (0, 255, 0)
            if fps < 30: color = (255, 0, 0)
            elif fps < 50: color = (255, 255, 0)
            
            fps_text = settings.small_font.render(f"FPS: {fps}", True, color)
            # Top right corner
            self.screen.blit(fps_text, (settings.SCREEN_WIDTH - 80, 10))

    def draw_game_time(self, game_time_min, wave_count=0):
        minutes = int(game_time_min)
        seconds = int((game_time_min * 60) % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Draw at top center
        text = settings.font.render(time_str, True, settings.WHITE)
        rect = text.get_rect(center=(settings.SCREEN_WIDTH // 2, 30))
        
        # Background for time
        bg_rect = rect.inflate(20, 10)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        
        self.screen.blit(s, bg_rect)
        self.screen.blit(text, rect)

    def draw_mission_ui(self, mission_manager):
        if not mission_manager: return
        
        width = 220 
        x = settings.SCREEN_WIDTH - width - 20
        y = 100
        
        height = 110 
        if mission_manager.just_completed:
            height += 30
            
        rect = pygame.Rect(x, y, width, height)
        
        s = pygame.Surface((width, height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150)) 
        self.screen.blit(s, (x, y))
        
        title = settings.small_font.render("当前任务", True, (255, 215, 0))
        self.screen.blit(title, (x + 10, y + 10))
        
        current_y = y + 35
        line_height = 25
        
        def draw_text_with_shadow(text, color, x, y):
            shadow = settings.small_font.render(text, True, settings.BLACK)
            self.screen.blit(shadow, (x + 1, y + 1))
            surf = settings.small_font.render(text, True, color)
            self.screen.blit(surf, (x, y))

        # Targets
        kill_target = mission_manager.get_current_target('kill')
        kill_current = mission_manager.current_progress['kill']
        kill_str = f"击杀: {kill_current}/{kill_target}"
        color = settings.WHITE if kill_current < kill_target else (0, 255, 0)
        draw_text_with_shadow(kill_str, color, x + 10, current_y)
        current_y += line_height
        
        dmg_target = mission_manager.get_current_target('damage_dealt')
        dmg_current = mission_manager.current_progress['damage_dealt']
        dmg_str = f"造成伤害: {dmg_current}/{dmg_target}"
        color = settings.WHITE if dmg_current < dmg_target else (0, 255, 0)
        draw_text_with_shadow(dmg_str, color, x + 10, current_y)
        current_y += line_height
        
        taken_target = mission_manager.get_current_target('damage_taken')
        taken_current = mission_manager.current_progress['damage_taken']
        taken_str = f"承受伤害: {taken_current}/{taken_target}"
        color = settings.WHITE if taken_current < taken_target else (0, 255, 0)
        draw_text_with_shadow(taken_str, color, x + 10, current_y)
        current_y += line_height
        
        if mission_manager.just_completed:
            popup_w = 400
            popup_h = 100
            popup_x = (settings.SCREEN_WIDTH - popup_w) // 2
            popup_y = 150 
            
            popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
            
            s = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
            s.fill((0, 0, 0, 200))
            self.screen.blit(s, (popup_x, popup_y))
            
            pygame.draw.rect(self.screen, (255, 215, 0), popup_rect, 3, border_radius=10)
            
            title = settings.font.render("任务完成！", True, (255, 215, 0))
            title_rect = title.get_rect(center=(popup_x + popup_w//2, popup_y + 30))
            self.screen.blit(title, title_rect)
            
            font = settings.medium_font
            reward_text_surf = font.render(mission_manager.last_reward_text, True, settings.WHITE)
            reward_rect = reward_text_surf.get_rect(center=(popup_x + popup_w//2, popup_y + 70))
            self.screen.blit(reward_text_surf, reward_rect)

    def draw_achievement_popup(self, mission_manager):
        if not mission_manager or not mission_manager.achievement_popup:
            return
            
        popup = mission_manager.achievement_popup
        
        width = 400
        height = 150
        x = (settings.SCREEN_WIDTH - width) // 2
        y = 150 
        
        rect = pygame.Rect(x, y, width, height)
        
        s = pygame.Surface((width, height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 220))
        self.screen.blit(s, (x, y))
        
        color = popup.get('color', (255, 215, 0))
        pygame.draw.rect(self.screen, color, rect, 4, border_radius=10)
        
        title = settings.font.render(popup['title'], True, color)
        title_rect = title.get_rect(center=(x + width // 2, y + 30))
        self.screen.blit(title, title_rect)
        
        text = settings.medium_font.render(popup['text'], True, settings.WHITE)
        text_rect = text.get_rect(center=(x + width // 2, y + 75))
        self.screen.blit(text, text_rect)
        
        reward = settings.medium_font.render(popup['reward'], True, (0, 255, 0))
        reward_rect = reward.get_rect(center=(x + width // 2, y + 110))
        self.screen.blit(reward, reward_rect)

    def draw_statistics_panel(self, game_manager):
        s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        
        w, h = 600, 450
        x = (settings.SCREEN_WIDTH - w) // 2
        y = (settings.SCREEN_HEIGHT - h) // 2
        rect = pygame.Rect(x, y, w, h)
        
        pygame.draw.rect(self.screen, (40, 40, 45), rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 215, 0), rect, 2, border_radius=10)
        
        title = settings.font.render("战斗统计", True, (255, 215, 0))
        title_rect = title.get_rect(center=(x + w//2, y + 40))
        self.screen.blit(title, title_rect)
        
        stats = [
            ("游戏时间", f"{int(game_manager.game_time // 60):02d}:{int(game_manager.game_time % 60):02d}"),
            ("总击杀数", str(game_manager.mission_manager.total_kills)),
            ("环境破坏", str(game_manager.destruction_count)),
            ("造成伤害", str(game_manager.mission_manager.current_progress['damage_dealt'])),
            ("承受伤害", str(game_manager.mission_manager.current_progress['damage_taken'])),
            ("当前等级", str(game_manager.player.level) if game_manager.player else "N/A"),
        ]
        
        if game_manager.mission_manager.total_kills >= 300:
             stats.append(("300杀成就", "已完成"))
        else:
             stats.append(("300杀成就", f"{game_manager.mission_manager.total_kills}/300"))
             
        start_y = y + 90
        for label, value in stats:
            l_surf = settings.medium_font.render(label, True, (200, 200, 200))
            self.screen.blit(l_surf, (x + 80, start_y))
            
            color = (255, 255, 255)
            if label == "300杀成就" and value == "已完成":
                color = (0, 255, 0)
            
            v_surf = settings.medium_font.render(value, True, color)
            v_rect = v_surf.get_rect(topright=(x + w - 80, start_y))
            self.screen.blit(v_surf, v_rect)
            
            pygame.draw.line(self.screen, (60, 60, 60), (x + 50, start_y + 35), (x + w - 50, start_y + 35), 1)
            
            start_y += 45
            
        tip = settings.small_font.render("按 [TAB] 关闭", True, (150, 150, 150))
        tip_rect = tip.get_rect(center=(x + w//2, y + h - 30))
        self.screen.blit(tip, tip_rect)

    def draw_tutorial(self, step_text, is_transition=False):
        box_width = 600
        box_height = 150
        x = (settings.SCREEN_WIDTH - box_width) // 2
        y = 100
        
        rect = pygame.Rect(x, y, box_width, box_height)
        
        bg_color = (0, 0, 0, 200)
        border_color = (255, 215, 0)
        
        if is_transition:
            bg_color = (50, 100, 50, 230)
            border_color = (100, 255, 100)
            
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=15)
        pygame.draw.rect(self.screen, border_color, rect, 3, border_radius=15)
        
        title_str = "新手教学"
        if is_transition: title_str = "完成！"
        
        title = settings.medium_font.render(title_str, True, border_color)
        title_rect = title.get_rect(center=(x + box_width // 2, y + 30))
        self.screen.blit(title, title_rect)
        
        lines = step_text.split('\n')
        start_text_y = y + 70
        for line in lines:
            text = settings.font.render(line, True, settings.WHITE)
            text_rect = text.get_rect(center=(x + box_width // 2, start_text_y))
            self.screen.blit(text, text_rect)
            start_text_y += 40
