import pygame

class ItemType:
    GENERIC = "generic"
    EQUIPMENT = "equipment"
    CELL = "cell"
    SKILL = "skill"
    EXCLUSIVE_SKILL = "exclusive_skill"

class Item:
    def __init__(self, id, name, item_type, description="", rarity="white", icon=None, remark=""):
        self.id = id
        self.name = name
        self.item_type = item_type
        self.description = description
        self.rarity = rarity # white, green, blue, purple, orange
        self.icon = icon # Pygame surface or path
        self.count = 1
        self.devour_progress = 0
        self.awakened_level = 0
        self.remark = remark
        
        # Color based on rarity
        self.color = (200, 200, 200)
        if rarity == 'green': self.color = (50, 200, 50)
        elif rarity == 'blue': self.color = (50, 50, 200)
        elif rarity == 'purple': self.color = (200, 50, 200)
        elif rarity == 'orange': self.color = (255, 165, 0)

    def to_dict(self):
        return {
            'id': self.id,
            'count': self.count,
            'devour_progress': self.devour_progress,
            'awakened_level': self.awakened_level
        }

class SkillItem(Item):
    def __init__(self, id, name, description, mp_cost, cooldown, effect_func_name, rarity="white", exclusive_id=None, is_passive=False, damage=0, remark=""):
        itype = ItemType.EXCLUSIVE_SKILL if exclusive_id else ItemType.SKILL
        super().__init__(id, name, itype, description, rarity, remark=remark)
        self.mp_cost = mp_cost
        self.cooldown = cooldown
        self.effect_func_name = effect_func_name # Name of function in skill_system
        self.exclusive_id = exclusive_id # 'square', 'triangle', 'circle' or None
        self.is_passive = is_passive
        self.damage = damage

class Equipment(Item):
    def __init__(self, id, name, slot_type, main_stat=None, sub_stats=None, neg_stats=None, description="", rarity="white", remark=""):
        super().__init__(id, name, ItemType.EQUIPMENT, description, rarity, remark=remark)
        self.slot_type = slot_type # head, body, hand_l, etc.
        
        # New Stat Structure
        self.main_stat = main_stat # Tuple: (key, value)
        self.sub_stats = sub_stats if sub_stats else [] # List of (key, value)
        self.neg_stats = neg_stats if neg_stats else [] # List of (key, value)
        
        self.devour_count = 0 # Max 5

    @property
    def stats(self):
        """Aggregate all stats for gameplay calculation"""
        total = {}
        
        # 1. Main Stat (Apply Devour Bonus)
        if self.main_stat:
            key, val = self.main_stat
            # Devour Bonus: +20% per count
            multiplier = 1.0 + (self.devour_count * 0.2)
            total[key] = total.get(key, 0) + (val * multiplier)
            
        # 2. Sub Stats
        for key, val in self.sub_stats:
            total[key] = total.get(key, 0) + val
            
        # 3. Negative Stats
        for key, val in self.neg_stats:
            total[key] = total.get(key, 0) + val # val should be negative
            
        return total

class Cell(Item):
    def __init__(self, id, name, stats, description="", rarity="white", remark=""):
        super().__init__(id, name, ItemType.CELL, description, rarity, remark=remark)
        self.stats = stats
