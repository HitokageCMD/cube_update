import pygame
import math
import config.game_config as settings
from utils.sound_manager import SoundManager

class SkillSystem:
    def __init__(self, player):
        self.player = player

    def execute_skill(self, skill_item):
        func_name = skill_item.effect_func_name
        if hasattr(self, func_name):
            # Play Skill Sound
            SoundManager().play_sound(skill_item.id)
            return getattr(self, func_name)(skill_item)
        else:
            print(f"Skill effect {func_name} not implemented")
            return False

    def get_aim_direction(self):
        # Calculate direction from player to mouse
        # Since player is always center screen in this game:
        screen_center = pygame.math.Vector2(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
        mouse_pos = pygame.mouse.get_pos()
        aim_vec = pygame.math.Vector2(mouse_pos) - screen_center
        if aim_vec.length() == 0:
            return pygame.math.Vector2(1, 0)
        return aim_vec.normalize()

    def get_skill_multiplier(self, skill_item):
        if not skill_item: return 1.0
        level = getattr(skill_item, 'awakened_level', 0)
        return 1.0 + level * 1.0

    def dash_effect(self, skill):
        # Dash: Move player rapidly in aim direction, increase collision resistance
        mult = self.get_skill_multiplier(skill)
        
        direction = self.get_aim_direction()
        dash_speed = 1000 * mult # Faster dash? Or just range?
        # Maybe just range
        base_range = 200 * mult
        total_range = base_range + self.player.skill_range
        duration = total_range / 1000 # Constant speed
        
        # Set dash state on player
        self.player.dash_timer = duration
        self.player.dash_velocity = direction * 1000
        self.player.is_dashing = True
        
        return True

    def fan_shot_effect(self, skill):
        mult = self.get_skill_multiplier(skill)
        direction = self.get_aim_direction()
        angle_base = math.atan2(direction.y, direction.x)
        
        from entities.projectile import Projectile
        
        def fire_burst():
            spread = math.radians(60)
            count = 5
            start_angle = angle_base - spread / 2
            step = spread / (count - 1)
            
            speed = 600
            base_range = 1200
            total_range = base_range + self.player.skill_range
            duration = total_range / speed
            
            for i in range(count):
                angle = start_angle + i * step
                dmg = max(1, self.player.phys_atk * 0.8) * mult
                p = Projectile(self.player.pos.x, self.player.pos.y, angle, speed, dmg, duration, self.player.data['color'], "bullet", damage_type="physical")
                self.player.projectiles.append(p)
        
        fire_burst()
        
        if not hasattr(self.player, 'scheduled_actions'):
            self.player.scheduled_actions = []
            
        self.player.scheduled_actions.append({'timer': 0.2, 'func': fire_burst})
        self.player.scheduled_actions.append({'timer': 0.4, 'func': fire_burst})
            
        return True

    def compression_state_effect(self, skill):
        # Compression State: High density field, Single Direction Burst, True Damage
        # Formula: 40% Magic + 10% Phys
        mult = self.get_skill_multiplier(skill)
        dmg = (self.player.magic_atk * 0.4 + self.player.phys_atk * 0.1) * mult
        
        from entities.projectile import Projectile
        
        speed = 500
        base_range = 600
        total_range = base_range + self.player.skill_range
        duration = total_range / speed
        
        # Fire in aim direction
        direction = self.get_aim_direction()
        angle = math.atan2(direction.y, direction.x)
        
        p = Projectile(self.player.pos.x, self.player.pos.y, angle, speed, dmg, duration, (75, 0, 130), "shrink_ball", damage_type="true")
        p.piercing = True 
        p.damage_interval = 0.5 # Hit every 0.5s
        p.radius = 12
        self.player.projectiles.append(p)

        return True

    # --- New Skills ---

    def area_slash_effect(self, skill):
        # 1.5s Invincible + 150% AOE after delay
        self.player.invincible_timer = 1.5
        
        # Show Channeling Text
        from core.game import FloatingText # Need access or use game_manager reference if available
        # Since SkillSystem doesn't have game_manager directly, we might need a workaround or add it to player
        # But player usually doesn't spawn text directly. 
        # Let's add a visual indicator via a temporary projectile or status
        self.player.apply_status_effect('channeling', 1.5, 0)
        
        def trigger_slash():
            from entities.projectile import Projectile
            dmg = self.player.phys_atk * 1.5
            
            p = Projectile(self.player.pos.x, self.player.pos.y, 0, 0, dmg, 0.2, (255, 200, 0), "aoe_slash", damage_type="physical",
                           follow_owner=True, owner=self.player)
            p.radius = 250
            p.piercing = True 
            self.player.projectiles.append(p)
            
        if not hasattr(self.player, 'scheduled_actions'): self.player.scheduled_actions = []
        self.player.scheduled_actions.append({'timer': 1.5, 'func': trigger_slash})
        
        return True

    def ground_slam_effect(self, skill):
        # Jump towards mouse + 75% AOE
        direction = self.get_aim_direction() # Normalized vector
        
        # Dash/Jump Logic
        dash_speed = 800
        dash_dist = 200
        duration = dash_dist / dash_speed
        
        self.player.is_dashing = True
        self.player.dash_timer = duration
        self.player.dash_velocity = direction * dash_speed
        
        def trigger_slam():
            from entities.projectile import Projectile
            dmg = self.player.phys_atk * 0.75
            
            p = Projectile(self.player.pos.x, self.player.pos.y, 0, 0, dmg, 0.2, (139, 69, 19), "ground_slam", damage_type="physical",
                           knockback_force=500)
            p.radius = 180
            p.piercing = True
            self.player.projectiles.append(p)
            
        if not hasattr(self.player, 'scheduled_actions'): self.player.scheduled_actions = []
        self.player.scheduled_actions.append({'timer': duration, 'func': trigger_slam})
        
        return True

    def overload_effect(self, skill):
        # Buff: High Atk Speed, Low Dmg
        self.player.apply_status_effect('overload', 5.0, 1.0)
        return True

    def storm_effect(self, skill):
        # 16 directions, 70% damage
        from entities.projectile import Projectile
        
        count = 16
        step = (math.pi * 2) / count
        speed = 700
        
        for i in range(count):
            angle = i * step
            dmg = self.player.phys_atk * 0.7
            p = Projectile(self.player.pos.x, self.player.pos.y, angle, speed, dmg, 1.5, (0, 255, 255), "triangle_bullet", damage_type="physical")
            self.player.projectiles.append(p)
            
        return True

    def black_hole_effect(self, skill):
        # 1s Channel -> Spawn at Mouse -> Pull
        mx, my = pygame.mouse.get_pos()
        # Need to convert screen pos to world pos? 
        # SkillSystem doesn't have camera reference.
        # But player.pos is world pos.
        # Assuming mouse_pos needs camera adjustment.
        # Simple hack: calculate relative to center of screen (player)
        screen_center = pygame.math.Vector2(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
        offset = pygame.math.Vector2(mx, my) - screen_center
        target_pos = self.player.pos + offset
        
        # Visual indicator for channeling?
        self.player.apply_status_effect('channeling', 1.0, 0)
        
        def trigger_black_hole():
            from entities.projectile import Projectile
            
            speed = 0 # Stationary
            dmg = self.player.magic_atk * 0.5 # DOT
            duration = 5.0
            
            # Spawn at target_pos
            p = Projectile(target_pos.x, target_pos.y, 0, speed, dmg, duration, (20, 0, 40), "black_hole", damage_type="magic",
                           pull_radius=300, pull_strength=50) # Slow pull
            p.piercing = True
            p.damage_interval = 0.5
            p.radius = 50 # Visual radius
            
            self.player.projectiles.append(p)
            
        if not hasattr(self.player, 'scheduled_actions'): self.player.scheduled_actions = []
        self.player.scheduled_actions.append({'timer': 1.0, 'func': trigger_black_hole})
        
        return True

    def fire_ring_effect(self, skill):
        # Fire ring following player
        from entities.projectile import Projectile
        dmg = self.player.magic_atk * 0.8
        duration = 5.0
        
        # Alpha color handled in Projectile.draw or specific type logic
        # Here we pass a color with alpha? Standard Pygame colors are RGB or RGBA.
        # Let's pass RGBA tuple.
        color = (255, 100, 0, 100) 
        
        p = Projectile(self.player.pos.x, self.player.pos.y, 0, 0, dmg, duration, color, "fire_ring", damage_type="magic",
                       follow_owner=True, owner=self.player, burn_chance=0.5)
        p.radius = 120
        p.piercing = True
        p.damage_interval = 0.5
        
        self.player.projectiles.append(p)
        return True
