import pygame
import random
import math
import config.game_config as settings
from .base_entity import Entity
from .projectile import Projectile
from core.map import BIOME_FOREST

class Enemy(Entity):
    def __init__(self, x, y, enemy_type, wave, is_elite=False, mission_stats=None, elite_type=None):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.type = enemy_type
        self.wave = wave
        self.is_elite = is_elite
        self.elite_type = elite_type
        self.size = 40
        self.width = self.size
        self.height = self.size
        self.color = (200, 50, 50) # Red-ish
        
        # New Stats System (0.0.5)
        # Base Stats (Lv1)
        base_hp = 30
        base_atk = 6
        base_def = 1
        base_speed = 220
        
        # Growth Formulas
        # HP = Base * (1 + 0.25 * Wave)
        self.max_hp = base_hp * (1 + 0.25 * wave)
        
        # Atk = Base * (1 + 0.2 * Wave)
        self.phys_atk = base_atk * (1 + 0.20 * wave)
        self.magic_atk = 0 # Default 0
        
        # Def = Base + floor(Wave / 3)
        self.phys_def = base_def + math.floor(wave / 3)
        self.magic_def = self.phys_def # Assume similar scaling for now
        
        self.speed = base_speed
        
        # Elite Scaling
        if is_elite:
            self.max_hp *= 5.0 # Elites are much tougher
            self.phys_atk *= 1.5
            self.size *= 1.5
            self.xp_value = 50 * wave
        else:
            self.xp_value = 5 * wave

        self.current_hp = self.max_hp
        
        # Base attributes for modifiers
        self.phys_pen = 0
        self.magic_pen = 0
        self.true_dmg = 0
        
        # --- Dynamic Growth System (Mission Stats) ---
        if mission_stats:
            completions = mission_stats.get('completions', 0)
            max_dmg = mission_stats.get('max_damage', 0)
            max_combo = mission_stats.get('max_combo', 0)
            
            # 1. Base Stats Growth
            # Def (+8% per mission)
            def_growth = 1.0 + completions * 0.08
            self.phys_def *= def_growth
            self.magic_def *= def_growth
            
            # Atk (+12% per mission)
            atk_growth = 1.0 + completions * 0.12
            self.phys_atk *= atk_growth
            self.magic_atk = self.magic_atk * atk_growth if self.magic_atk > 0 else 0
            
            # HP (+5% per mission)
            hp_growth = 1.0 + completions * 0.05
            self.max_hp *= hp_growth
            
            # 2. Dynamic Adjustment
            # Extra Def = Max Dmg * 0.001%
            extra_def = max_dmg * 0.00001
            self.phys_def += extra_def
            self.magic_def += extra_def
            
            # Extra HP = Max Combo * 0.5%
            hp_combo_bonus = 1.0 + max_combo * 0.005
            self.max_hp *= hp_combo_bonus
            
            # 3. Combat Stats (Soft Cap)
            # Speed +1.5% per mission
            self.speed *= (1.0 + completions * 0.015)
            
            self.current_hp = self.max_hp

        # Elite Type Setup
        self.skill_cooldown = 0
        self.skill_timer = 0
        self.is_using_skill = False
        self.name = "" # Initialize name
        
        if elite_type == 'bone_crusher':
            self.skill_cooldown = 5.0
            self.color = (100, 0, 0) # Dark Red
            self.name = "碎骨者"
        elif elite_type == 'hunter_eye':
            self.skill_cooldown = 8.0
            self.color = (255, 215, 0) # Gold
            self.name = "猎杀之眼"
        elif elite_type == 'void_whisperer':
            self.skill_cooldown = 8.0
            self.color = (75, 0, 130) # Indigo
            self.name = "虚空低语者"

        self.status_effects = []
        
        self.is_ranged = False
        self.attack_timer = 0
        self.attack_interval = 2.0
        self.attack_range = 0
        
        if enemy_type == 'square':
            self.color = (200, 50, 50)
            self.hp_mult = 1.2
            self.speed_mult = 0.8
            
            # Dynamic Buff: Phys Atk +10% per wave
            self.phys_atk *= (1.0 + 0.1 * wave)
            
        elif enemy_type == 'triangle':
            self.color = (200, 200, 50)
            self.hp_mult = 0.8
            self.speed_mult = 1.2
            self.is_ranged = True
            self.attack_range = 400 
            self.attack_interval = 1.2 # Strengthened: Faster attacks (was 1.5)
            
            # Dynamic Buff: Attack Speed (Interval decrease)
            # Decrease by 5% per wave, max 60% reduction (0.4 multiplier)
            reduction = min(0.6, 0.05 * wave)
            self.attack_interval *= (1.0 - reduction)
            
        elif enemy_type == 'circle':
            self.color = (255, 0, 255) # Magenta
            self.hp_mult = 0.6
            self.speed_mult = 1.0
            self.is_ranged = True
            self.attack_range = 350
            self.attack_interval = 2.0
            
            # Magic Stats
            # Using Base * (1 + 0.2 * Wave) as a reference, but magic might scale differently
            # Let's keep consistent with formula but use magic_atk base
            self.magic_atk = 10 * (1 + 0.20 * wave)
            self.phys_atk = 0
            
        self.max_hp *= self.hp_mult
        self.current_hp = self.max_hp
        self.speed *= self.speed_mult
        
        # Legacy aliases
        self.atk = self.phys_atk
        self.defense = self.phys_def
        
        self.base_speed = self.speed
        self.base_size = self.size
        self.base_color = self.color
        
        self.knockback_velocity = pygame.math.Vector2(0, 0)
        
        # Animation State
        self.animation_state = 'idle'
        self.animation_frame = 0.0
        self.animation_speed = 10.0 # FPS
        self.animation_loop = True
        self.animation_finished = False

    @property
    def is_dying(self):
        return self.animation_state == 'die'

    def set_animation(self, state, loop=True, speed=10.0):
        if self.animation_state != state:
            self.animation_state = state
            self.animation_frame = 0.0
            self.animation_loop = loop
            self.animation_speed = speed
            self.animation_finished = False

    def die(self):
        if not self.is_dying:
            self.set_animation('die', loop=False, speed=10.0)

    def take_damage(self, amount, damage_type='physical', penetration=0, source=None, knockback=None):
        dmg = super().take_damage(amount, damage_type, penetration, source)
        if knockback and knockback.length() > 0:
            self.knockback_velocity += knockback
        
        # Trigger hurt animation if not dying
        if not self.is_dying and dmg > 0:
            # Only switch to hurt if not already hurting or attacking (priority?)
            # Let's say hurt interrupts everything except death
            self.set_animation('hurt', loop=False, speed=15.0)
            
        return dmg

    def apply_status_effect(self, effect_type, duration, intensity=1.0):
        for effect in self.status_effects:
            if effect['type'] == effect_type:
                effect['duration'] = max(effect['duration'], duration)
                effect['intensity'] = max(effect['intensity'], intensity)
                return
        
        self.status_effects.append({
            'type': effect_type,
            'duration': duration,
            'intensity': intensity,
            'timer': 0,
            'tick_timer': 0
        })

    def update_status_effects(self, dt_sec, damage_callback=None):
        speed_modifier = 1.0
        size_modifier = 1.0
        color_override = None
        
        for effect in self.status_effects[:]:
            effect['timer'] += dt_sec
            effect['tick_timer'] += dt_sec
            
            if effect['timer'] >= effect['duration']:
                self.status_effects.remove(effect)
                continue
                
            if effect['type'] == 'compress':
                size_modifier *= 0.6
                speed_modifier *= 0.5
                if effect['tick_timer'] >= 0.5:
                    effect['tick_timer'] = 0
                    dmg = 5 * effect['intensity']
                    self.take_damage(dmg, 'true')
                    if damage_callback: damage_callback(self.pos, dmg)
                        
            elif effect['type'] == 'burn':
                color_override = (255, 100, 0)
                if effect['tick_timer'] >= 0.5:
                    effect['tick_timer'] = 0
                    dmg = 10 * effect['intensity']
                    self.take_damage(dmg, 'magic')
                    if damage_callback: damage_callback(self.pos, dmg)
            
            elif effect['type'] == 'wet':
                color_override = (50, 100, 255) # Blue
                speed_modifier *= 0.9 # Slight slow to indicate wetness
                        
            elif effect['type'] == 'freeze':
                color_override = (100, 100, 255)
                speed_modifier = 0
                
            elif effect['type'] == 'slow':
                color_override = (150, 150, 150)
                speed_modifier *= (1.0 - effect['intensity'])
                
            elif effect['type'] == 'bleed':
                color_override = (150, 0, 0)
                if effect['tick_timer'] >= 0.5:
                    effect['tick_timer'] = 0
                    dmg = 5 * effect['intensity']
                    self.take_damage(dmg, 'physical')
                    if damage_callback: damage_callback(self.pos, dmg)

        self.speed = self.base_speed * speed_modifier
        self.size = self.base_size * size_modifier
        self.width = self.size
        self.height = self.size
        if color_override: self.color = color_override
        else: self.color = self.base_color

    def update(self, dt_sec, player_pos, other_enemies, projectiles=None, map_manager=None, damage_callback=None):
        # Elite Skill Logic
        if self.is_elite and self.elite_type:
            self.skill_timer += dt_sec
            if self.skill_timer >= self.skill_cooldown:
                used = False
                if self.elite_type == 'bone_crusher':
                    # Vengeful Charge
                    if self.current_hp < self.max_hp * 0.3: self.skill_cooldown = 2.5
                    to_player = player_pos - self.pos
                    if to_player.length() > 0:
                        self.pos += to_player.normalize() * 300 * dt_sec * 5 # Burst move
                        used = True
                elif self.elite_type == 'hunter_eye':
                    # Deadly Lock
                    if projectiles is not None:
                        to_player = player_pos - self.pos
                        angle = math.atan2(to_player.y, to_player.x)
                        # Changed type to sniper_shot
                        proj = Projectile(self.pos.x, self.pos.y, angle, 900, self.phys_atk * 2.5, 3.0, (255, 50, 50), "sniper_shot", "physical")
                        proj.radius = 15 # Larger bullet
                        projectiles.append(proj)
                        used = True
                elif self.elite_type == 'void_whisperer':
                    # Stagnant Abyss
                    if projectiles is not None:
                        proj = Projectile(player_pos.x, player_pos.y, 0, 0, self.magic_atk * 0.2, 5.0, (50, 0, 100), "void_zone", "true")
                        proj.radius = 120 # Slightly larger
                        proj.effects = [{'type': 'slow', 'duration': 1.0, 'intensity': 0.75}]
                        proj.damage_interval = 0.5 # Tick faster
                        projectiles.append(proj)
                        used = True
                if used: self.skill_timer = 0

        # Update Animation Frame
        self.animation_frame += self.animation_speed * dt_sec
        
        # Check animation finish
        # We need to know max frames to loop correctly. 
        # But we don't have access to resource_manager here easily without importing or passing it.
        # However, Renderer handles the modulo/clamping. 
        # Here we just increment. But for 'loop=False' logic (hurt/die), we need to know when to stop.
        # Simple workaround: Assume 5 frames for now since we generated them.
        # Ideally, we should check with ResourceManager, but let's assume standard 5 frames for generated assets.
        # If we exceed 5 frames:
        if self.animation_loop:
            pass # Renderer handles modulo
        else:
            if self.animation_frame >= 5.0: # 5 frames
                self.animation_frame = 4.9 # Clamp to last
                self.animation_finished = True
                
                # If hurt finished, go back to idle/run
                if self.animation_state == 'hurt':
                    self.set_animation('idle', loop=True)

        if self.is_dying:
            return # Skip movement/AI if dying

        self.update_status_effects(dt_sec, damage_callback)
        
        # Apply Knockback
        if self.knockback_velocity.length() > 10:
            self.pos += self.knockback_velocity * dt_sec
            self.knockback_velocity *= 0.9 # Damping
        else:
            self.knockback_velocity = pygame.math.Vector2(0, 0)
        
        to_player = player_pos - self.pos
        dist_to_player = to_player.length()
        
        target_dist = 0
        if self.is_ranged:
            target_dist = self.attack_range * 0.8
            
        # Forest Behavior: Triangle and Circle kite more effectively
        if map_manager and map_manager.get_biome_at(self.pos) == BIOME_FOREST:
            if self.type in ['triangle', 'circle']:
                target_dist = self.attack_range * 0.9 # Stay further away
                # self.speed is already set by status effects, we can boost it
                self.speed *= 1.1

        direction = pygame.math.Vector2(0, 0)
        if dist_to_player > 0:
             if self.is_ranged and dist_to_player < target_dist - 50:
                 direction = -to_player.normalize()
             elif dist_to_player > target_dist + 50:
                 direction = to_player.normalize()
             else:
                 pass
             
             if not self.is_ranged:
                 direction = to_player.normalize()

        separation = pygame.math.Vector2(0, 0)
        for other in other_enemies:
            if other != self:
                dist_vec = self.pos - other.pos
                dist = dist_vec.length()
                if dist < self.size:
                    if dist > 0:
                        separation += dist_vec.normalize() / dist
                    else:
                        separation += pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        
        final_dir = direction + separation * 2
        if final_dir.length() > 0:
            final_dir = final_dir.normalize()
            
        self.pos += final_dir * self.speed * dt_sec
        
        if self.is_ranged and projectiles is not None:
            self.attack_timer += dt_sec
            if self.attack_timer >= self.attack_interval:
                if dist_to_player <= self.attack_range:
                    # Trigger Attack Animation
                    self.set_animation('attack', loop=False, speed=15.0)
                    
                    self.attack_timer = 0
                    angle = math.atan2(to_player.y, to_player.x)
                    
                    if self.type == 'circle':
                        proj = Projectile(
                            self.pos.x, self.pos.y, 
                            angle, 
                            speed=250, 
                            damage=self.magic_atk, 
                            duration=3.0, 
                            color=self.color, 
                            p_type="enemy_orb",
                            damage_type="magic",
                            effects=[{'type': 'slow', 'duration': 0.75, 'intensity': 0.5}]
                        )
                        projectiles.append(proj)
                    else:
                        proj = Projectile(
                            self.pos.x, self.pos.y, 
                            angle, 
                            speed=350, # Strengthened: Faster projectile (was 300)
                            damage=self.atk, 
                            duration=3.0, 
                            color=self.color, 
                            p_type="enemy_bullet"
                        )
                        proj.damage = self.atk 
                        projectiles.append(proj)

    def draw(self, surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_size = int(self.size * camera.zoom)
        
        if self.type == 'square':
            rect = pygame.Rect(0, 0, draw_size, draw_size)
            rect.center = (int(screen_pos.x), int(screen_pos.y))
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, settings.BLACK, rect, 1)
        elif self.type == 'triangle':
            half_w = draw_size // 2
            points = [
                (screen_pos.x, screen_pos.y - half_w),
                (screen_pos.x - half_w, screen_pos.y + half_w),
                (screen_pos.x + half_w, screen_pos.y + half_w)
            ]
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, settings.BLACK, points, 1)
            
        elif self.type == 'circle':
            # Draw as Diamond (Rhombus) - Purple
            half_w = max(10, draw_size // 2)
            points = [
                (screen_pos.x, screen_pos.y - half_w), # Top
                (screen_pos.x + half_w, screen_pos.y), # Right
                (screen_pos.x, screen_pos.y + half_w), # Bottom
                (screen_pos.x - half_w, screen_pos.y)  # Left
            ]
            purple_color = (150, 0, 200)
            pygame.draw.polygon(surface, purple_color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
            
        else:
            # Fallback for unknown types - Draw a Gray Circle
            radius = max(10, draw_size // 2)
            pygame.draw.circle(surface, (100, 100, 100), (int(screen_pos.x), int(screen_pos.y)), radius)
            pygame.draw.circle(surface, (255, 0, 0), (int(screen_pos.x), int(screen_pos.y)), radius, 2)

        # Draw Elite Name
        if self.is_elite and hasattr(self, 'name') and self.name:
            # Gold color for name
            name_surf = settings.small_font.render(self.name, True, (255, 215, 0))
            # Black outline
            stroke_surf = settings.small_font.render(self.name, True, (0, 0, 0))
            
            name_pos = (screen_pos.x, screen_pos.y - draw_size//2 - 25)
            name_rect = name_surf.get_rect(center=name_pos)
            
            # Draw stroke
            for offset in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                surface.blit(stroke_surf, (name_rect.x + offset[0], name_rect.y + offset[1]))
            
            surface.blit(name_surf, name_rect)

        hp_ratio = self.current_hp / self.max_hp
        bar_w = draw_size
        bar_h = 5
        bar_pos = (screen_pos.x - bar_w//2, screen_pos.y - draw_size//2 - 10)
        pygame.draw.rect(surface, (50, 0, 0), (*bar_pos, bar_w, bar_h))
        pygame.draw.rect(surface, (0, 200, 0), (*bar_pos, bar_w * hp_ratio, bar_h))

class ExperienceOrb:
    def __init__(self, x, y, amount):
        self.pos = pygame.math.Vector2(x, y)
        self.amount = amount
        self.radius = 5
        self.color = (100, 255, 255) 
        self.magnet_radius = 100
        self.speed = 400
        
    def update(self, dt_sec, player_pos, pickup_range=100):
        to_player = player_pos - self.pos
        dist = to_player.length()
        
        if dist < pickup_range:
            self.pos += to_player.normalize() * self.speed * dt_sec
            if dist < 10:
                return True 
        return False

    def draw(self, surface, camera):
        screen_pos = camera.apply(self.pos)
        pygame.draw.circle(surface, self.color, (int(screen_pos.x), int(screen_pos.y)), int(self.radius * camera.zoom))
