import random
from entities.pickup import Pickup, XPOrb
from data.item_data import OTHER_ITEMS, EQUIPMENT_ITEMS, SKILL_ITEMS, CELL_ITEMS, get_item_by_id, EQUIPMENT_TEMPLATES
from utils.item_generator import generate_equipment

class LootManager:
    def __init__(self):
        pass
        
    @staticmethod
    def drop_enemy_loot(game_manager, pos, enemy_type, is_elite, player):
        # Item Drops
        # Base chance
        drop_chance = 0.05
        if is_elite:
            drop_chance = 1.0 # Elites always drop something
            
        if random.random() < drop_chance:
            # Randomly select item type
            roll = random.random()
            item = None
            
            if roll < 0.4: # 40% chance for food/potion
                keys = list(OTHER_ITEMS.keys())
                if keys:
                    key = random.choice(keys)
                    item = get_item_by_id(key)
            elif roll < 0.7: # 30% chance for equipment
                keys = list(EQUIPMENT_ITEMS.keys())
                if keys:
                    key = random.choice(keys)
                    item = get_item_by_id(key)
            elif roll < 0.9: # 20% chance for skill
                keys = list(SKILL_ITEMS.keys())
                if keys:
                    key = random.choice(keys)
                    item = get_item_by_id(key)
            else: # 10% chance for core
                keys = list(CELL_ITEMS.keys())
                if keys:
                    key = random.choice(keys)
                    item = get_item_by_id(key)
                    
            if item:
                pickup = Pickup(pos.x, pos.y, 'item', item=item)
                game_manager.pickups.append(pickup)

    def check_drops(self, enemy, game_manager):
        # Legacy/Instance method wrapper if needed, or remove if unused
        pass

    @staticmethod
    def drop_chest_loot(game_manager, pos, chest_rarity, player_luck):
        rarity_map = {
            'white': 'white',
            'green': 'green',
            'blue': 'blue',
            'purple': 'purple',
            'gold': 'orange',
            'orange': 'orange'
        }
        rarity = rarity_map.get(chest_rarity, 'white')
        
        # Pick a random equipment template and generate item using new generator
        if not EQUIPMENT_TEMPLATES:
            return
        key = random.choice(list(EQUIPMENT_TEMPLATES.keys()))
        template = EQUIPMENT_TEMPLATES[key]
        item = generate_equipment(template, rarity=rarity)
        
        pickup = Pickup(pos.x, pos.y, 'item', item=item)
        game_manager.pickups.append(pickup)
