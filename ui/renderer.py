import pygame
import math
import config.game_config as settings
from utils.resource_manager import resource_manager
from ui.widgets import Camera
from ui.hud import HUDRenderer
from ui.inventory_ui import InventoryRenderer
from ui.upgrade_ui import UpgradeRenderer
from ui.menus import MenuRenderer
from ui.dev_ui import DevUIRenderer
from ui.splash import SplashRenderer

# Get theme color helper
get_theme_color = settings.get_theme_color

class GameRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.camera = Camera()
        
        # Sub-renderers
        self.hud = HUDRenderer(screen)
        self.inventory_ui = InventoryRenderer(screen)
        self.upgrade_ui = UpgradeRenderer(screen)
        self.menu_ui = MenuRenderer(screen)
        self.dev_ui = DevUIRenderer(screen)
        self.splash_ui = SplashRenderer(screen)

    def draw_entity(self, entity):
        screen_pos = self.camera.apply(entity.pos)
        
        # 绘制阴影
        shadow_rect = pygame.Rect(0, 0, entity.width, entity.height // 3)
        shadow_rect.center = (screen_pos.x, screen_pos.y + entity.height // 2)
        s = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 100), s.get_rect())
        self.screen.blit(s, shadow_rect)
        
        # 绘制实体主体
        draw_rect = pygame.Rect(0, 0, entity.width, entity.height)
        draw_rect.center = screen_pos
        
        # 玩家无敌反馈：绘制环形光圈
        if hasattr(entity, 'is_player') and entity.is_player and getattr(entity, 'invincible_timer', 0) > 0:
            radius = max(entity.width, entity.height) // 2 + 8
            # 轻微脉动
            pulse = 2 * math.sin(pygame.time.get_ticks() * 0.02)
            r = int(radius + pulse)
            s = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
            center = (r+2, r+2)
            color = (0, 255, 255, 80)
            pygame.draw.circle(s, color, center, r, 4)
            self.screen.blit(s, (screen_pos.x - center[0], screen_pos.y - center[1]))
        
        # 闪烁效果 (受击)
        if entity.flash_timer > 0:
            if (pygame.time.get_ticks() // 50) % 2 == 0:
                color = settings.WHITE
            else:
                color = entity.color
        else:
            color = entity.color

        # 尝试使用 Animation
        anim_key = None
        is_flipped = False
        
        if hasattr(entity, 'is_player') and entity.is_player:
            char_id = entity.data.get('id', 'square') if hasattr(entity, 'data') else getattr(entity, 'char_id', 'square')
            state = getattr(entity, 'animation_state', 'idle')
            anim_key = f"anim_player_{char_id}_{state}"
            
            # Flip logic for player
            # We don't have direct access to input here, but maybe we can check last move dir?
            # Or just assume right facing default.
            
        elif hasattr(entity, 'type'):
            # Enemy
            anim_key = f"anim_enemy_{entity.type}_{getattr(entity, 'animation_state', 'idle')}"

        frames = resource_manager.get_animation(anim_key)
        
        image = None
        
        if frames:
            # Calculate frame index
            frame_idx = int(getattr(entity, 'animation_frame', 0))
            if frame_idx >= len(frames):
                if getattr(entity, 'animation_loop', True):
                    frame_idx = frame_idx % len(frames)
                else:
                    frame_idx = len(frames) - 1
            
            image = frames[frame_idx]
        else:
            # Fallback to Static Sprite
            sprite_key = None
            if hasattr(entity, 'is_player') and entity.is_player:
                if hasattr(entity, 'data') and 'id' in entity.data:
                    sprite_key = f"player_{entity.data['id']}"
                else:
                    sprite_key = f"player_{entity.char_id}"
            elif hasattr(entity, 'type'):
                sprite_key = f"enemy_{entity.type}"
                
            image = resource_manager.get_image(sprite_key) if sprite_key else None
        
        if image:
            scaled_img = pygame.transform.scale(image, (int(entity.width), int(entity.height)))
            if entity.flash_timer > 0 and (pygame.time.get_ticks() // 50) % 2 == 0:
                scaled_img.fill((255, 255, 255, 200), special_flags=pygame.BLEND_RGBA_MULT)
                
            # 旋转 (如果需要)
            if hasattr(entity, 'angle') and entity.angle != 0:
                scaled_img = pygame.transform.rotate(scaled_img, -entity.angle)
                draw_rect = scaled_img.get_rect(center=screen_pos)
            
            self.screen.blit(scaled_img, draw_rect)
        else:
            # 形状绘制 Fallback
            # Get ID/Shape
            shape_id = 'square'
            if hasattr(entity, 'data') and 'id' in entity.data:
                shape_id = entity.data['id']
            elif hasattr(entity, 'char_id'):
                shape_id = entity.char_id
            elif hasattr(entity, 'shape'):
                shape_id = entity.shape
            
            if shape_id == 'circle':
                pygame.draw.circle(self.screen, color, screen_pos, entity.width // 2)
                pygame.draw.circle(self.screen, settings.BLACK, screen_pos, entity.width // 2, 2)
            elif shape_id == 'triangle':
                points = [
                    (screen_pos.x, screen_pos.y - entity.height // 2),
                    (screen_pos.x - entity.width // 2, screen_pos.y + entity.height // 2),
                    (screen_pos.x + entity.width // 2, screen_pos.y + entity.height // 2)
                ]
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, settings.BLACK, points, 2)
            else: # Default square
                pygame.draw.rect(self.screen, color, draw_rect)
                pygame.draw.rect(self.screen, settings.BLACK, draw_rect, 2)

        # 绘制血条 (仅敌人)
        if not (hasattr(entity, 'is_player') and entity.is_player) and entity.max_hp > 0:
            hp_ratio = entity.current_hp / entity.max_hp
            bar_w = entity.width + 10
            bar_h = 5
            bar_x = screen_pos.x - bar_w // 2
            bar_y = screen_pos.y - entity.height // 2 - 10
            
            pygame.draw.rect(self.screen, (50, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(self.screen, (255, 0, 0), (bar_x, bar_y, bar_w * hp_ratio, bar_h))

    def draw_projectile(self, proj):
        screen_pos = self.camera.apply(proj.pos)
        
        img = resource_manager.get_image(f"proj_{proj.shape}")
        if img:
            scaled = pygame.transform.scale(img, (int(proj.width), int(proj.height)))
            # Rotate
            angle = math.degrees(math.atan2(proj.vel.y, proj.vel.x))
            rotated = pygame.transform.rotate(scaled, -angle)
            rect = rotated.get_rect(center=screen_pos)
            self.screen.blit(rotated, rect)
        else:
            # Code drawing
            if proj.shape == 'circle':
                pygame.draw.circle(self.screen, proj.color, screen_pos, proj.width/2)
            else:
                rect = pygame.Rect(0, 0, proj.width, proj.height)
                rect.center = screen_pos
                pygame.draw.rect(self.screen, proj.color, rect)

    def draw_pickup(self, pickup):
        screen_pos = self.camera.apply(pickup.pos)
        
        # Bobbing
        offset_y = math.sin(pygame.time.get_ticks() * 0.005) * 5
        screen_pos.y += offset_y
        
        img = resource_manager.get_image(f"pickup_{pickup.type}")
        if img:
            scaled = pygame.transform.scale(img, (int(pickup.width), int(pickup.height)))
            rect = scaled.get_rect(center=screen_pos)
            self.screen.blit(scaled, rect)
        else:
            pygame.draw.circle(self.screen, pickup.color, screen_pos, pickup.width/2)
            pygame.draw.circle(self.screen, settings.WHITE, screen_pos, pickup.width/2, 2)

    def draw_melee_swing(self, player, angle, swing_progress):
        # 绘制近战挥砍扇形
        # swing_progress: 0.0 -> 1.0
        # 简单的半透明扇形
        
        screen_pos = self.camera.apply(player.pos)
        radius = player.stats.get('attack_range', 100)
        
        start_angle = math.radians(angle - 45)
        end_angle = math.radians(angle + 45)
        
        # Pygame arc draws border only, we need polygon for fill
        points = [screen_pos]
        steps = 10
        for i in range(steps + 1):
            t = i / steps
            current_a = start_angle + (end_angle - start_angle) * t
            # Mirror Y because screen coords
            px = screen_pos.x + math.cos(current_a) * radius
            py = screen_pos.y + math.sin(current_a) * radius
            points.append((px, py))
            
        s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        color = (255, 255, 255, 100) # White swing
        if swing_progress > 0.5:
            alpha = int(100 * (1.0 - swing_progress) * 2)
            color = (255, 255, 255, alpha)
            
        pygame.draw.polygon(s, color, points)
        self.screen.blit(s, (0, 0))

    # --- Delegates ---

    def draw_player_ui(self, player):
        self.hud.draw_player_ui(player)

    def draw_floating_texts(self, texts):
        self.hud.draw_floating_texts(self.camera, texts)

    def draw_game_time(self, game_time, wave_count=0):
        self.hud.draw_game_time(game_time, wave_count)

    def draw_mission_ui(self, mission_manager):
        self.hud.draw_mission_ui(mission_manager)
        
    def draw_achievement_popup(self, mission_manager):
        self.hud.draw_achievement_popup(mission_manager)

    def draw_statistics_panel(self, game_manager):
        self.hud.draw_statistics_panel(game_manager)
        
    def draw_tutorial(self, text, is_transition=False):
        self.hud.draw_tutorial(text, is_transition)

    def draw_inventory(self, inventory):
        self.inventory_ui.draw_inventory(inventory)

    def draw_level_up_anim(self, progress):
        self.upgrade_ui.draw_level_up_anim(progress)
        
    def draw_level_up_choices(self, choices, hovered=None):
        self.upgrade_ui.draw_level_up_choices(choices, hovered)

    def draw_dev_panel(self, dev_manager):
        self.dev_ui.draw_dev_panel(dev_manager)

    # Menu delegates... usually called directly by main loop using menu_ui, 
    # but if GameRenderer is the single point of entry:
    
    def draw_menu(self, *args, **kwargs):
        self.menu_ui.draw_menu(*args, **kwargs)

    def draw_char_select(self, *args, **kwargs):
        self.menu_ui.draw_char_select(*args, **kwargs)

    def draw_settings(self, *args, **kwargs):
        self.menu_ui.draw_settings(*args, **kwargs)

    def draw_pause(self, *args, **kwargs):
        self.menu_ui.draw_pause(*args, **kwargs)

    def draw_save_load(self, *args, **kwargs):
        self.menu_ui.draw_save_load(*args, **kwargs)

    def draw_save_confirm(self, *args, **kwargs):
        self.menu_ui.draw_save_confirm(*args, **kwargs)

    def draw_game_over(self, *args, **kwargs):
        self.menu_ui.draw_game_over(*args, **kwargs)

    def draw_changelog(self, *args, **kwargs):
        self.menu_ui.draw_changelog(*args, **kwargs)

    def draw_guide(self, *args, **kwargs):
        self.menu_ui.draw_guide(*args, **kwargs)

    def draw_credits(self, *args, **kwargs):
        self.menu_ui.draw_credits(*args, **kwargs)

    def draw_donate(self, *args, **kwargs):
        self.menu_ui.draw_donate(*args, **kwargs)

    def draw_splash(self):
        self.splash_ui.draw()

    def update_splash(self, dt):
        if hasattr(self.splash_ui, 'update'):
            self.splash_ui.update(dt)

    def is_splash_finished(self):
        return getattr(self.splash_ui, 'finished', False)

    def is_splash_video_mode(self):
        return getattr(self.splash_ui, 'mode', 'static') == 'video'
