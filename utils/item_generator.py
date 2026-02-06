import random
import copy
from core.item import Equipment

# --- Configuration ---

# Number of Sub-Stats per Rarity
RARITY_RULES = {
    'white': 0,
    'green': 1,
    'blue': 2,
    'purple': 3,
    'orange': 4
}

# Attribute Value Tables (Fixed values per rarity)
# Format: {'stat_key': {'white': val, 'green': val, ...}}
STAT_VALUES = {
    # --- Attack Stats ---
    'phys_atk': {'white': 2, 'green': 4, 'blue': 7, 'purple': 11, 'orange': 16},
    'magic_atk': {'white': 2, 'green': 4, 'blue': 7, 'purple': 11, 'orange': 16},
    'true_damage': {'white': 1, 'green': 2, 'blue': 3, 'purple': 5, 'orange': 7},
    
    # --- Penetration ---
    'phys_pen': {'white': 1, 'green': 2, 'blue': 3, 'purple': 4, 'orange': 6},
    'magic_pen': {'white': 1, 'green': 2, 'blue': 3, 'purple': 4, 'orange': 6},
    
    # --- Percentage Boosts ---
    'damage_bonus': {'white': 0.03, 'green': 0.06, 'blue': 0.10, 'purple': 0.15, 'orange': 0.22},
    
    # --- Defense ---
    'phys_def': {'white': 1, 'green': 2, 'blue': 4, 'purple': 6, 'orange': 9},
    'magic_def': {'white': 1, 'green': 2, 'blue': 4, 'purple': 6, 'orange': 9}, # Assumed symmetric
    'damage_reduction': {'white': 0.02, 'green': 0.04, 'blue': 0.06, 'purple': 0.09, 'orange': 0.12}, # Cap 60%
    'collision_damage_reduction': {'white': 0.05, 'green': 0.08, 'blue': 0.12, 'purple': 0.18, 'orange': 0.25},
    
    # --- Functional / Crit ---
    'crit_chance': {'white': 0.02, 'green': 0.04, 'blue': 0.06, 'purple': 0.09, 'orange': 0.12},
    'crit_dmg': {'white': 0.10, 'green': 0.20, 'blue': 0.35, 'purple': 0.55, 'orange': 0.80},
    'attack_speed': {'white': 0.05, 'green': 0.10, 'blue': 0.18, 'purple': 0.28, 'orange': 0.40},
    'move_speed': {'white': 5, 'green': 10, 'blue': 15, 'purple': 20, 'orange': 30},
    'attack_range': {'white': 5, 'green': 10, 'blue': 15, 'purple': 22, 'orange': 30},
    'pickup_range': {'white': 5, 'green': 10, 'blue': 15, 'purple': 22, 'orange': 30}, # Assumed similiar to ranges
    'skill_range': {'white': 5, 'green': 10, 'blue': 18, 'purple': 28, 'orange': 40},
    
    # --- Special ---
    'luck': {'white': 0, 'green': 1, 'blue': 2, 'purple': 3, 'orange': 5},
    'piercing_count': {'white': 0, 'green': 0, 'blue': 1, 'purple': 1, 'orange': 2},
    
    # --- Regen & Haste ---
    'hp_regen': {'white': 0.3, 'green': 0.6, 'blue': 1.0, 'purple': 1.6, 'orange': 2.5},
    'mp_regen': {'white': 0.4, 'green': 0.8, 'blue': 1.2, 'purple': 2.0, 'orange': 3.0},
    'skill_haste': {'white': 0.05, 'green': 0.10, 'blue': 0.18, 'purple': 0.30, 'orange': 0.45},
    
    # --- Max HP/MP (Extrapolated based on weight) ---
    # Weight: 1.0, 1.8, 3.0, 4.8, 7.0
    # Base: 10 -> 10, 18, 30, 48, 70
    'max_hp': {'white': 10, 'green': 18, 'blue': 30, 'purple': 48, 'orange': 70},
    'max_mp': {'white': 10, 'green': 18, 'blue': 30, 'purple': 48, 'orange': 70},
}

# Sub-Stat Pools (Allowed stats per slot type)
SUB_STAT_POOLS = {
    'weapon': [
        'attack_speed', 'crit_chance', 'piercing_count', 'phys_pen', 'magic_pen', 'crit_dmg', 'damage_bonus'
    ],
    'armor': [ # body, leg, head
        'max_hp', 'phys_def', 'magic_def', 'collision_damage_reduction', 'hp_regen'
    ],
    'accessory': [ # special
        'pickup_range', 'luck', 'max_mp', 'mp_regen', 'skill_haste', 'skill_range'
    ]
}

# Mapping specific slots to pool keys
SLOT_TO_POOL = {
    'hand': 'weapon',
    'hand_l': 'weapon',
    'hand_r': 'weapon',
    'head': 'armor',
    'body': 'armor',
    'leg': 'armor',
    'special': 'accessory'
}

def generate_equipment(template, rarity=None):
    """
    Generates a unique Equipment instance based on a template.
    template: dict from item_data.EQUIPMENT_TEMPLATES
    rarity: str (optional)
    """
    if not rarity:
        # Default weighted random rarity
        weights = {'white': 50, 'green': 30, 'blue': 15, 'purple': 4, 'orange': 1}
        rarity = random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]
        
    # 1. Base Info
    item_id = template['id']
    name = template['name']
    slot_type = template['slot_type']
    desc = template.get('description', '')
    
    # 2. Main Stat
    # Use lookup table directly
    base_main = template['base_main_stat'] # (key, val) - Val here is ignored or used as base multiplier?
    # Requirement says "Adjust numerical values of attribute rarity".
    # Usually templates define WHICH stat is main, but the value is determined by rarity table.
    # However, some items might be stronger base?
    # Let's assume the template defines the KEY, and we look up value from STAT_VALUES[key][rarity].
    # But some items might have 'move_speed' main stat which is not in the generic table?
    # If key is in STAT_VALUES, use it. If not, fallback to multiplier logic.
    
    main_key, base_val = base_main
    
    if main_key in STAT_VALUES:
        final_main_val = STAT_VALUES[main_key].get(rarity, base_val)
    else:
        # Fallback for stats not in table (e.g. custom ones)
        # Use weight multipliers: 1.0, 1.8, 3.0, 4.8, 7.0
        rarity_mult = {'white': 1.0, 'green': 1.8, 'blue': 3.0, 'purple': 4.8, 'orange': 7.0}
        final_main_val = base_val * rarity_mult.get(rarity, 1.0)
        
        # Rounding
        if isinstance(base_val, int) and base_val > 5:
            final_main_val = int(final_main_val)
        else:
            final_main_val = round(final_main_val, 2)
        
    main_stat = (main_key, final_main_val)
    
    # 3. Sub Stats
    num_subs = RARITY_RULES.get(rarity, 0)
    pool_key = SLOT_TO_POOL.get(slot_type, 'accessory')
    pool = SUB_STAT_POOLS.get(pool_key, [])
    
    # Filter out main stat from pool
    available_pool = [s for s in pool if s != main_key]
    
    sub_stats = []
    if num_subs > 0 and available_pool:
        # Pick N unique stats
        chosen_keys = random.sample(available_pool, k=min(num_subs, len(available_pool)))
        
        for key in chosen_keys:
            # Look up value from table
            if key in STAT_VALUES:
                val = STAT_VALUES[key].get(rarity, 0)
            else:
                val = 0 # Should not happen if pools match table
                
            # Random Variation? Usually games have fixed tiers or slight variance.
            # Requirement images show fixed values (+2, +4 etc).
            # So we use exact values.
            
            # Special case: Luck and Piercing can be 0 at low rarity
            if val == 0 and key in ['luck', 'piercing_count']:
                # If value is 0, should we skip adding it?
                # A sub-stat with +0 is useless.
                # Maybe re-roll or just accept it?
                # If luck is +0, it shouldn't consume a slot.
                # But 'chosen_keys' consumed a slot.
                # Let's just append it, or maybe filter out 0-value keys from pool beforehand?
                # Better: only add if val > 0.
                pass
            
            if val > 0:
                sub_stats.append((key, val))
            
    # 4. Negative Stats
    neg_stats = []
    if 'neg_stats' in template:
        # Template defines fixed negative stats usually
        for key, val in template['neg_stats']:
            neg_stats.append((key, val))
            
    # Create Object
    equip = Equipment(
        id=item_id,
        name=name,
        slot_type=slot_type,
        main_stat=main_stat,
        sub_stats=sub_stats,
        neg_stats=neg_stats,
        description=desc,
        rarity=rarity,
        remark=template.get('remark', '')
    )
    
    return equip
