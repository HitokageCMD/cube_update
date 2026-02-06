import pygame
import config.game_config as settings
from entities.projectile import Projectile

class Trail(Projectile):
    """
    A stationary projectile that lingers on the ground and deals damage/effects.
    """
    def __init__(self, x, y, duration, element, damage, owner):
        # Initialize as a stationary projectile (speed=0)
        color = (200, 200, 200)
        if element == 'fire': color = (255, 100, 0)
        elif element == 'water': color = (0, 100, 255)
        elif element == 'lightning': color = (200, 0, 255)
        
        super().__init__(x, y, 0, 0, damage, duration, color, p_type="trail", damage_type="magic", owner=owner)
        
        self.radius = 15
        self.element = element
        self.damage_interval = 0.5 # Deal damage every 0.5s
        
        # Add effects based on element
        if element == 'fire':
            self.effects.append({'type': 'burn', 'duration': 3.0, 'intensity': 0.2})
        elif element == 'water':
            self.knockback_force = 100
        elif element == 'lightning':
            self.on_hit_effect = 'lightning' # Trigger lightning logic in EnemyManager
            
    def update(self, dt_sec, enemies=None):
        self.duration -= dt_sec
        
        # Fade out alpha logic could go here if using surfaces
        
        # Update hit timers
        if self.hit_timers:
            for entity in list(self.hit_timers.keys()):
                self.hit_timers[entity] -= dt_sec
                if self.hit_timers[entity] <= 0:
                    del self.hit_timers[entity]
                    
    def draw(self, surface, camera):
        screen_pos = camera.apply(self.pos)
        r = int(self.radius * camera.zoom)
        
        # Draw fading circle
        alpha = int(255 * (self.duration / 2.0)) # Assuming max duration ~2-3s
        if alpha > 255: alpha = 255
        if alpha < 0: alpha = 0
        
        # Need a surface for alpha
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        surface.blit(s, (int(screen_pos.x - r), int(screen_pos.y - r)))
