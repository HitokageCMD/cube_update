import random
from data.attributes import STATS
from data.rarity import RARITY_ORDER, BASE_RARITY_RATE, RARITY_COLORS, RARITY_MULTIPLIERS
from data.luck import LUCK_SHIFT, LUCK_MAX
from utils.logger import logger

class UpgradeSystem:
    def __init__(self):
        pass

    def calculate_rarity_weights(self, luck):
        luck = min(luck, LUCK_MAX)
        rates = BASE_RARITY_RATE.copy()
        
        # Calculate shift amount from White
        # Luck = 1 -> 1% shift
        total_shift = luck * 1.0 # 1% per luck point
        
        # Cap shift at available white rate
        if total_shift > rates['white']:
            total_shift = rates['white']
            
        rates['white'] -= total_shift
        
        # Distribute shift
        for rarity, factor in LUCK_SHIFT.items():
            amount = luck * factor # e.g. 5 * 0.6 = 3.0
            rates[rarity] += amount
            
        return rates

    def roll_rarity(self, weights):
        # Weighted random choice
        items = list(weights.keys())
        probs = list(weights.values())
        return random.choices(items, weights=probs, k=1)[0]

    def get_layer_weights(self, rarity):
        if rarity == 'white': return {1: 100, 2: 0, 3: 0}
        if rarity == 'green': return {1: 80, 2: 20, 3: 0}
        if rarity == 'blue': return {1: 50, 2: 50, 3: 0}
        if rarity == 'purple': return {1: 0, 2: 80, 3: 20}
        if rarity == 'yellow': return {1: 0, 2: 50, 3: 50}
        if rarity == 'orange': return {1: 0, 2: 0, 3: 100} 
        if rarity == 'black': return {1: 0, 2: 0, 3: 100}
        return {1: 100, 2: 0, 3: 0}

    def generate_upgrade_options(self, player):
        luck = getattr(player, 'luck', 0)
        rarity_weights = self.calculate_rarity_weights(luck)
        
        options = []
        for _ in range(3):
            rarity = self.roll_rarity(rarity_weights)
            layer_weights = self.get_layer_weights(rarity)
            
            # Roll layer
            layer = random.choices(list(layer_weights.keys()), weights=list(layer_weights.values()), k=1)[0]
            
            # Filter stats
            valid_stats = []
            for k, v in STATS.items():
                if v['layer'] == layer:
                    # Check min rarity
                    if RARITY_ORDER.index(rarity) >= RARITY_ORDER.index(v['min_rarity']):
                        valid_stats.append(k)
            
            if not valid_stats:
                # Fallback to white/layer1
                rarity = 'white'
                valid_stats = [k for k, v in STATS.items() if v['layer'] == 1]
                
            stat_key = random.choice(valid_stats)
            stat_def = STATS[stat_key]
            
            # Apply Rarity Multiplier
            rarity_mult = RARITY_MULTIPLIERS.get(rarity, 1.0)
            val = stat_def['upgrade_value'] * rarity_mult
            
            # Apply class growth scaling
            if hasattr(player, 'data') and 'growth' in player.data:
                growth = player.data['growth']
                if stat_key in growth:
                    scale = growth[stat_key]
                    val = val * scale
                    
            # Keep type consistency
            if isinstance(stat_def['upgrade_value'], int):
                val = max(1, int(round(val))) # Ensure at least +1 for int stats
            else:
                val = round(val, 3)
            
            # Format value string
            if isinstance(val, float):
                val_str = f"{val:.2f}"
                # If small float, maybe percent
                if val < 1.0 and stat_key != 'attack_speed': 
                     val_str = f"{val*100:.1f}%"
            else:
                val_str = str(val)
                
            options.append({
                'rarity': rarity,
                'color': RARITY_COLORS[rarity],
                'attr': stat_key,
                'name': stat_def['name'],
                'value': val,
                'desc': f"{stat_def['name']} +{val_str}"
            })
            
        return options

    def apply_upgrade(self, player, stat_key, value=None):
        try:
            if stat_key not in STATS:
                logger.error(f"Invalid stat key: {stat_key}")
                return
            
            stat_def = STATS[stat_key]
            if value is None:
                value = stat_def['upgrade_value']
                
            current = getattr(player, stat_key, 0) 
            
            # Cap check
            if 'max' in stat_def:
                new_val = min(current + value, stat_def['max'])
            else:
                new_val = current + value
                
            setattr(player, stat_key, new_val)
            
            # Special handling for derived stats or restoration
            if stat_key == 'max_hp':
                player.current_hp += value
            elif stat_key == 'max_mp':
                player.current_mp += value
                
            logger.info(f"Player upgraded {stat_key} by {value}. New value: {new_val}")
            
        except Exception as e:
            logger.error(f"Error applying upgrade {stat_key}: {e}")

upgrade_system = UpgradeSystem()
