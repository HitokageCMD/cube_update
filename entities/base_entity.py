import pygame
import config.game_config as settings
from core import damage as combat

class Entity:
    def __init__(self):
        self.max_hp = 100
        self.current_hp = 100
        # New Stats
        self.phys_atk = 10
        self.magic_atk = 0
        self.phys_def = 0
        self.magic_def = 0
        self.phys_pen = 0
        self.magic_pen = 0
        self.true_dmg = 0
        self.pickup_range = 100
        
        # Legacy/Alias support
        self.atk = 10 
        self.defense = 0
        
        self.pos = pygame.math.Vector2(0, 0)
        self.size = 40
        self.width = self.size
        self.height = self.size
        self.color = settings.WHITE
        self.alive = True
        
        # Visual effects
        self.flash_timer = 0

    def take_damage(self, amount, damage_type='physical', penetration=0, source=None):
        # 真正伤害结算系统
        final_dmg, _ = combat.calculate_damage(amount, damage_type, self, source)
        self.current_hp -= final_dmg
        if self.current_hp <= 0:
            self.current_hp = 0
            self.alive = False
            self.on_death(source)
        return final_dmg

    def on_death(self, source):
        pass
