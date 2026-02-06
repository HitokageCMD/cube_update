import pygame
import math
import config.game_config as settings
from entities.base_entity import Entity

class Interactable(Entity):
    def __init__(self, x, y):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.radius = 20
        self.interact_radius = 60
        self.can_interact = False
        
    def update(self, dt_sec, player):
        dist = (player.pos - self.pos).length()
        self.can_interact = dist < self.interact_radius
        
    def interact(self, player, game_manager):
        pass
        
    def draw(self, surface, camera):
        pass

class Chest(Interactable):
    def __init__(self, x, y, rarity='white'):
        super().__init__(x, y)
        self.type = 'chest' # Added type attribute
        self.rarity = rarity
        self.is_opened = False
        self.color = (150, 100, 50) # Brown
        if rarity == 'gold': self.color = (255, 215, 0)
        
    def interact(self, player, game_manager):
        if self.is_opened: return
        
        self.is_opened = True
        print(f"Chest opened! Rarity: {self.rarity}")
        
        # Drop loot
        from systems.drop_system import LootManager
        LootManager.drop_chest_loot(game_manager, self.pos, self.rarity, player.luck)
        
    def draw(self, surface, camera):
        screen_pos = camera.apply(self.pos)
        size = int(self.radius * 2 * camera.zoom)
        rect = pygame.Rect(0, 0, size, size * 0.8)
        rect.center = (int(screen_pos.x), int(screen_pos.y))
        
        col = self.color
        if self.is_opened:
            col = (100, 100, 100) # Greyed out
            
        pygame.draw.rect(surface, col, rect)
        pygame.draw.rect(surface, (255, 255, 255), rect, 2)
        
        if self.can_interact and not self.is_opened:
            # Draw 'F' hint
            font = pygame.font.SysFont('Arial', 20)
            text = font.render("F", True, (255, 255, 255))
            surface.blit(text, (rect.centerx - text.get_width()//2, rect.top - 20))

class Tree(Entity):
    def __init__(self, x, y):
        super().__init__()
        self.pos = pygame.math.Vector2(x, y)
        self.radius = 30
        self.hp = 50
        self.max_hp = 50
        self.color = (34, 139, 34) # Forest Green
        
    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            return True # Destroyed
        return False
        
    def draw(self, surface, camera):
        screen_pos = camera.apply(self.pos)
        r = int(self.radius * camera.zoom)
        pygame.draw.circle(surface, self.color, (int(screen_pos.x), int(screen_pos.y)), r)
        
        # HP Bar
        if self.hp < self.max_hp:
            bar_w = r * 2
            bar_h = 4
            ratio = self.hp / self.max_hp
            pygame.draw.rect(surface, (200, 0, 0), (screen_pos.x - r, screen_pos.y - r - 10, bar_w, bar_h))
            pygame.draw.rect(surface, (0, 200, 0), (screen_pos.x - r, screen_pos.y - r - 10, bar_w * ratio, bar_h))
