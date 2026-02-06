import pygame
import math
import config.game_config as settings

class Projectile:
    def __init__(self, x, y, angle, speed, damage, duration, color, p_type="bullet", damage_type="physical", effects=None, knockback_force=0, **kwargs):
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed
        self.damage = damage
        self.damage_type = damage_type
        self.duration = duration # 秒
        self.width = 10 # Default width
        self.height = 10 # Default height
        self.color = color
        self.type = p_type
        self.shape = 'circle' # Default shape
        if p_type == 'bullet': self.shape = 'circle'
        elif p_type == 'sword_wave': self.shape = 'arc'
        elif p_type == 'rune': self.shape = 'rhombus'
        elif p_type == 'fire_ring': self.shape = 'ring'
        elif p_type == 'sniper_shot': self.shape = 'long_bullet'
        elif p_type == 'void_zone': self.shape = 'circle'
        
        self.radius = 5 if p_type == "bullet" else 10
        self.effects = effects if effects else []
        self.knockback_force = knockback_force
        
        # New properties
        self.piercing = False
        
        # Special properties
        self.pull_radius = kwargs.get('pull_radius', 0)
        self.pull_strength = kwargs.get('pull_strength', 0)
        self.follow_owner = kwargs.get('follow_owner', False)
        self.owner = kwargs.get('owner', None)
        self.burn_chance = kwargs.get('burn_chance', 0)
        self.piercing_count = 0
        self.damage_interval = 0 # 0 means deal damage once then destroy
        self.hit_timers = {} # Entity -> timer
        
        # Tracking Properties
        self.is_tracking = kwargs.get('is_tracking', False)
        self.tracking_angle = kwargs.get('tracking_angle', 30) # Degrees
        self.tracking_target = None
        self.tracking_scan_timer = 0
        
        # Chain Properties
        self.chain_info = kwargs.get('chain_info', None) # {'range': 100, 'pct': 0.3, 'element': 'fire'}
        self.wet_stats = kwargs.get('wet_stats', None)

    def update(self, dt_sec, enemies=None):
        # Handle Tracking
        if self.is_tracking:
            self.tracking_scan_timer -= dt_sec
            
            # Find target if none or dead
            if not self.tracking_target or getattr(self.tracking_target, 'current_hp', 0) <= 0:
                if self.tracking_scan_timer <= 0 and enemies:
                    self.tracking_scan_timer = 0.2 # Scan every 0.2s
                    self._find_tracking_target(enemies)
            
            # Steer towards target
            if self.tracking_target and getattr(self.tracking_target, 'current_hp', 0) > 0:
                to_target = self.tracking_target.pos - self.pos
                if to_target.length() > 0:
                    desired_vel = to_target.normalize() * self.vel.length()
                    # Steer factor (turn speed)
                    steer_strength = 5.0 * dt_sec # Adjust turn speed
                    new_vel = self.vel.lerp(desired_vel, steer_strength)
                    if new_vel.length() > 0:
                        self.vel = new_vel.normalize() * self.vel.length()

        if self.follow_owner and self.owner:
            self.pos = pygame.math.Vector2(self.owner.pos.x, self.owner.pos.y)
        else:
            self.pos += self.vel * dt_sec
            
        self.duration -= dt_sec
        
        # Update hit timers
        if self.hit_timers:
            for entity in list(self.hit_timers.keys()):
                self.hit_timers[entity] -= dt_sec
                if self.hit_timers[entity] <= 0:
                    del self.hit_timers[entity]

    def _find_tracking_target(self, enemies):
        # Filter enemies within cone
        # Current velocity is forward direction
        forward = self.vel.normalize()
        best_target = None
        min_dist = 9999
        
        # Convert angle to radians/2 for check
        cone_threshold = math.cos(math.radians(self.tracking_angle / 2))
        
        for enemy in enemies:
            to_enemy = enemy.pos - self.pos
            dist = to_enemy.length()
            if dist > 600: continue # Max tracking range
            
            if dist > 0:
                dir_to_enemy = to_enemy.normalize()
                dot = forward.dot(dir_to_enemy)
                
                if dot >= cone_threshold:
                    if dist < min_dist:
                        min_dist = dist
                        best_target = enemy
        
        self.tracking_target = best_target

    def draw(self, surface, camera):
        screen_pos = camera.apply(self.pos)
        
        # Check for Alpha (RGBA color)
        has_alpha = len(self.color) == 4
        
        if self.type == "rune":
            # 绘制菱形符文
            r = int(self.radius * camera.zoom)
            cx, cy = int(screen_pos.x), int(screen_pos.y)
            points = [
                (cx, cy - r),
                (cx + r, cy),
                (cx, cy + r),
                (cx - r, cy)
            ]
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, (255, 255, 255), points, 1) # 白色描边
        elif self.type == "sword_wave":
            # 绘制剑气/弧形波 (类似 "))" 形状)
            # 需要根据速度方向旋转
            angle = math.atan2(self.vel.y, self.vel.x)
            
            # 定义相对坐标点 (假设向右为0度)
            # 绘制两层弧线以增加视觉厚度
            base_scale = self.radius * camera.zoom * 1.5
            
            # 旋转函数
            def rotate_point(px, py, ang):
                cos_a = math.cos(ang)
                sin_a = math.sin(ang)
                return (px * cos_a - py * sin_a, px * sin_a + py * cos_a)

            cx, cy = screen_pos.x, screen_pos.y
            
            # 弧形点集 (月牙状)
            # 外弧
            outer_points_base = [
                (-0.2, -1.0), (0.5, -0.7), (0.8, 0.0), (0.5, 0.7), (-0.2, 1.0)
            ]
            # 内弧 (闭合用)
            inner_points_base = [
                (0.0, 0.7), (0.3, 0.0), (0.0, -0.7)
            ]
            
            poly_points = []
            for px, py in outer_points_base:
                rx, ry = rotate_point(px * base_scale, py * base_scale, angle)
                poly_points.append((cx + rx, cy + ry))
            
            for px, py in inner_points_base:
                rx, ry = rotate_point(px * base_scale, py * base_scale, angle)
                poly_points.append((cx + rx, cy + ry))
                
            pygame.draw.polygon(surface, self.color, poly_points)
            pygame.draw.polygon(surface, (255, 255, 255), poly_points, 1)
            
        elif self.type == "fire_ring" or has_alpha:
            # Draw circle with alpha
            r = int(self.radius * camera.zoom)
            cx, cy = int(screen_pos.x), int(screen_pos.y)
            
            # Create surface for alpha
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, self.color, (r, r), r)
            surface.blit(s, (cx - r, cy - r))
            
        else:
            # Default Circle
            r = int(self.radius * camera.zoom)
            pygame.draw.circle(surface, self.color, (int(screen_pos.x), int(screen_pos.y)), r)
            if self.type == "black_hole":
                 pygame.draw.circle(surface, (0, 0, 0), (int(screen_pos.x), int(screen_pos.y)), max(1, r - 2))

class MeleeSwing:
    def __init__(self, owner, angle, duration, range_val, color):
        self.owner = owner
        self.base_angle = angle # 攻击方向（弧度）
        self.duration = duration
        self.max_duration = duration
        self.range = range_val
        self.color = color
        self.sweep_angle = math.pi / 2 # 90度扇形
        
    def update(self, dt_sec):
        self.duration -= dt_sec
        
    def draw(self, surface, camera):
        # 绘制扇形/弧形
        # 这里用多边形模拟扇形
        if self.duration <= 0: return
        
        start_pos = camera.apply(self.owner.pos)
        points = [start_pos]
        
        # 随时间变化的角度偏移（挥动效果）
        # 比如从 -45度 挥到 +45度
        progress = 1 - (self.duration / self.max_duration)
        current_sweep = self.sweep_angle
        
        # 计算扇形顶点
        num_points = 10
        start_angle = self.base_angle - current_sweep / 2
        
        # 视觉效果：透明度随时间降低 (需要Surface)
        # alpha = int(255 * (self.duration / self.max_duration))
        s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        draw_points = [start_pos]
        for i in range(num_points + 1):
            a = start_angle + (current_sweep * i / num_points)
            # 挥动动画：稍微旋转整体角度
            # a += (progress - 0.5) * 1.0 
            
            offset = pygame.math.Vector2(math.cos(a), math.sin(a)) * (self.range * camera.zoom)
            draw_points.append(start_pos + offset)
            
        pygame.draw.polygon(s, (*self.color, 150), draw_points)
        surface.blit(s, (0, 0))
