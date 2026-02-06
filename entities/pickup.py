import pygame
import math
from entities.base_entity import Entity

class Pickup(Entity):
    def __init__(self, x, y, p_type, item=None):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.type = p_type
        self.item = item # Optional item data
        self.radius = 8
        self.color = (255, 255, 255)
        self.magnet_radius = 100
        self.speed = 400
        self.auto_magnet = False # If true, always flies to player
        
        # Bobbing animation
        self.bob_timer = 0
        self.base_y = y
        
        # If item provided, use its color
        if self.item:
             if hasattr(self.item, 'rarity'):
                r = self.item.rarity
                if r == 'white': self.color = (200, 200, 200)
                elif r == 'green': self.color = (50, 200, 50)
                elif r == 'blue': self.color = (50, 50, 200)
                elif r == 'purple': self.color = (200, 50, 200)
                elif r == 'orange': self.color = (255, 165, 0)
        
    def update(self, dt_sec, player_pos, pickup_range=100):
        self.bob_timer += dt_sec
        # Visual bobbing
        self.pos.y = self.base_y + math.sin(self.bob_timer * 3) * 3
        
        to_player = player_pos - self.pos
        dist = to_player.length()
        
        should_magnet = self.auto_magnet or (dist < pickup_range)
        
        if should_magnet:
            if dist > 0:
                self.pos += to_player.normalize() * self.speed * dt_sec
                # Update base_y to follow movement
                self.base_y = self.pos.y
            
            if dist < 15: # Pickup radius
                return True 
        return False

    def draw(self, surface, camera):
        screen_pos = camera.apply(self.pos)
        r = int(self.radius * camera.zoom)
        pygame.draw.circle(surface, self.color, (int(screen_pos.x), int(screen_pos.y)), r)
        pygame.draw.circle(surface, (0,0,0), (int(screen_pos.x), int(screen_pos.y)), r, 1)

class XPOrb(Pickup):
    def __init__(self, x, y, amount):
        super().__init__(x, y, 'xp')
        self.amount = amount
        self.radius = 5
        self.color = (100, 255, 255) # Cyan
        self.magnet_radius = 100

class ItemPickup(Pickup):
    def __init__(self, x, y, item):
        super().__init__(x, y, 'item')
        self.item = item
        self.radius = 12
        self.color = item.color if hasattr(item, 'color') else (200, 200, 200)
        self.auto_magnet = False # Items usually don't magnet automatically unless specified
        
    def draw(self, surface, camera):
        # Draw item icon or box
        super().draw(surface, camera)
        # Could add rarity glow here
