import copy
from core.item import SkillItem, Equipment, ItemType, Item
from utils.item_generator import generate_equipment
import random

# Skill Definitions
SKILL_ITEMS = {
    # Original Skills
    'skill_dash': SkillItem(
        id='skill_dash',
        name='冲刺',
        description='朝向箭头方向冲刺，冲刺时+碰撞减免10\n消耗: 20 MP\n冷却: 5秒',
        mp_cost=20,
        cooldown=5,
        effect_func_name='dash_effect',
        rarity='green',
        exclusive_id='square',
        damage=0,
        remark='位移技能'
    ),
    'skill_fan_shot': SkillItem(
        id='skill_fan_shot',
        name='扇形扫射',
        description='朝向箭头方向发射扇形扫射，共5颗子弹，连续射击3次\n消耗: 20 MP\n冷却: 8秒',
        mp_cost=20,
        cooldown=8,
        effect_func_name='fan_shot_effect',
        rarity='blue',
        exclusive_id='triangle',
        damage=10,
        remark='群体伤害'
    ),
    'skill_shrink_ball': SkillItem(
        id='skill_shrink_ball',
        name='收缩球',
        description='释放高密度力场，向目标方向发射穿透球体，造成无视防御的真实伤害\n伤害: 40%魔攻 + 10%物攻\n消耗: 20 MP\n冷却: 6秒',
        mp_cost=20,
        cooldown=6,
        effect_func_name='compression_state_effect',
        rarity='purple',
        exclusive_id='circle',
        damage='40%魔攻+10%物攻',
        remark='真实伤害'
    ),
    
    # Square Exclusives
    'skill_area_slash': SkillItem(
        id='skill_area_slash',
        name='范围斩杀',
        description='蓄力1.5秒后对周围造成150%物理伤害，蓄力期间无敌\n消耗: 40 MP\n冷却: 15秒',
        mp_cost=40,
        cooldown=15,
        effect_func_name='area_slash_effect',
        rarity='orange',
        exclusive_id='square',
        damage='150%物理伤害',
        remark='无敌+爆发'
    ),
    'skill_ground_slam': SkillItem(
        id='skill_ground_slam',
        name='大地震击',
        description='向鼠标方向跳跃，落地造成75%物理伤害并击退\n消耗: 30 MP\n冷却: 10秒',
        mp_cost=30,
        cooldown=10,
        effect_func_name='ground_slam_effect',
        rarity='purple',
        exclusive_id='square',
        damage='75%物理伤害',
        remark='位移+控制'
    ),
    
    # Triangle Exclusives
    'skill_overload': SkillItem(
        id='skill_overload',
        name='过载射击',
        description='5秒内射速大幅提升，但单发伤害降低\n消耗: 30 MP\n冷却: 20秒',
        mp_cost=30,
        cooldown=20,
        effect_func_name='overload_effect',
        rarity='orange',
        exclusive_id='triangle',
        damage=0,
        remark='爆发状态'
    ),
    'skill_storm': SkillItem(
        id='skill_storm',
        name='风暴',
        description='向四周16个方向发射子弹，造成70%物理伤害\n消耗: 35 MP\n冷却: 12秒',
        mp_cost=35,
        cooldown=12,
        effect_func_name='storm_effect',
        rarity='purple',
        exclusive_id='triangle',
        damage='70%物理伤害',
        remark='全方位打击'
    ),
    
    # Circle Exclusives
    'skill_black_hole': SkillItem(
        id='skill_black_hole',
        name='黑洞余烬',
        description='吟唱1秒后在鼠标位置生成黑洞，缓慢吸附敌人\n消耗: 50 MP\n冷却: 25秒',
        mp_cost=50,
        cooldown=25,
        effect_func_name='black_hole_effect',
        rarity='orange',
        exclusive_id='circle',
        damage=5,
        remark='强力控制'
    ),
    'skill_fire_ring': SkillItem(
        id='skill_fire_ring',
        name='炎环护身',
        description='召唤跟随自身的火焰环，持续伤害\n消耗: 30 MP\n冷却: 15秒',
        mp_cost=30,
        cooldown=15,
        effect_func_name='fire_ring_effect',
        rarity='purple',
        exclusive_id='circle',
        damage=8,
        remark='近身防护'
    ),
    # Special / Key Items
    'heart': Item(
        id='heart',
        name='机械心脏',
        item_type='heart',
        description='神秘的机械心脏，蕴含着强大的能量。\n放入心脏槽位可激活下层核心。\n吞噬其他物品可升级，解锁更多细胞槽位。',
        rarity='orange',
        remark='核心激活'
    ),
}

# New Equipment Templates
EQUIPMENT_TEMPLATES = {
    'equip_rusty_sword': {
        'id': 'equip_rusty_sword',
        'name': '生锈的铁剑',
        'slot_type': 'hand',
        'base_main_stat': ('phys_atk', 5), # Base Value (White)
        'description': '一刀破伤风',
        'remark': '新手神器'
    },
    'equip_crutch': {
        'id': 'equip_crutch',
        'name': '拐杖',
        'slot_type': 'hand',
        'base_main_stat': ('magic_atk', 10),
        'neg_stats': [('attack_speed', -0.15)],
        'description': '移速+5 (左右手)',
        'remark': '法师入门'
    },
    'equip_damaged_armor': {
        'id': 'equip_damaged_armor',
        'name': '战损盔甲',
        'slot_type': 'body',
        'base_main_stat': ('phys_def', 2),
        'neg_stats': [('move_speed', -5)],
        'description': '虽然破损，但还能用',
        'remark': '保持风格'
    },
    'equip_overload_armor': {
        'id': 'equip_overload_armor',
        'name': '过载护甲',
        'slot_type': 'body',
        'base_main_stat': ('phys_def', 5),
        'neg_stats': [('skill_haste', -0.10)], # Increase cooldown = negative haste
        'description': '强力防护，但影响灵活性',
        'remark': '非常健康'
    },
    'equip_running_shoes': {
        'id': 'equip_running_shoes',
        'name': '跑鞋',
        'slot_type': 'leg',
        'base_main_stat': ('move_speed', 15),
        'description': '跑得快才是硬道理',
        'remark': '简单的快乐'
    },
    'equip_clover': {
        'id': 'equip_clover',
        'name': '四叶草',
        'slot_type': 'special',
        'base_main_stat': ('luck', 1.0),
        'description': '希望能带来好运',
        'remark': '玄学'
    }
}

# Compatibility Export for legacy systems
EQUIPMENT_ITEMS = {}
for t_id, template in EQUIPMENT_TEMPLATES.items():
    EQUIPMENT_ITEMS[t_id] = generate_equipment(template, rarity='white')

# Placeholder for other items
OTHER_ITEMS = {
    # 'hp_potion': Item('hp_potion', 'HP药水', 'consumable', '恢复生命值', 'white'), # Deleted
    'gene_potion': Item(
        id='gene_potion',
        name='基因药水',
        item_type='key',
        description='用于解锁基因锁的神奇药水。\n拖拽到基因锁位置即可解锁下层核心。',
        rarity='purple',
        remark='解锁道具'
    ),
}

# --- Virtual Data for Guide ---
CELL_ITEMS = {
    'mech_split': Item('mech_split', '分裂', 'cell', '将普攻攻击投射物+2\n增加散射角度\n单发伤害降低', 'green'),
    'mech_giant': Item('mech_giant', '巨型', 'cell', '体积 x1.5\n伤害 x1.5\n飞行速度降低\n增加穿透数量3', 'blue'),
    
    # Elemental Cores
    'core_fire': Item('core_fire', '火焰核心', 'cell', '普攻附带燃烧效果\n造成每秒20%攻击力的持续伤害', 'orange'),
    'core_water': Item('core_water', '潮汐核心', 'cell', '普攻附带强力击退\n击退距离大幅增加', 'blue'),
    'core_lightning': Item('core_lightning', '雷霆核心', 'cell', '普攻命中触发连锁闪电\n对周围敌人造成50%攻击力的弹射伤害', 'purple'),
    
    # Mechanism Cells
    'cell_tracking': Item('cell_tracking', '跟踪细胞', 'cell', '子弹自动追踪前方30度敌人\n移动速度调整为75', 'purple'),
    'cell_chain': Item('cell_chain', '连锁细胞', 'cell', '命中后触发范围100的连锁打击\n造成30%伤害并触发核心效果', 'purple'),
    'cell_exhaust': Item('cell_exhaust', '尾气细胞', 'cell', '移动路径留下核心效果尾气\n持续触发核心伤害', 'purple'),
}

ENEMY_INFO = {
    'square': Item('square', '正方形战士', 'enemy', '定位: 近战坦克\n特点: 血量高，速度慢\n行为: 持续追踪玩家', 'white'),
    'triangle': Item('triangle', '三角形射手', 'enemy', '定位: 远程输出\n特点: 射速快，身板脆\n行为: 保持距离射击', 'yellow'), # Yellow rarity as proxy for color
    'circle': Item('circle', '圆形法师', 'enemy', '定位: 魔法控制\n特点: 带有减速效果\n行为: 发射魔法球', 'purple'),
}

REACTION_INFO = {
    'vaporize': Item('reaction_vaporize', '蒸发', 'reaction', '清除状态并造成范围魔法伤害', 'orange', remark='AOE清场'),
    'overload': Item('reaction_overload', '超载', 'reaction', '造成连锁爆炸伤害，范围大幅增加', 'orange', remark='超远连锁'),
    'electro_charged': Item('reaction_electro_charged', '感电', 'reaction', '在潮湿敌人间弹射电流伤害', 'orange', remark='持续弹射'),
}
# Manually attach recipe for Guide display
REACTION_INFO['vaporize'].recipe = "火 + 水"
REACTION_INFO['overload'].recipe = "雷 + 火"
REACTION_INFO['electro_charged'].recipe = "雷 + 水"

def get_item_by_id(item_id):
    item = None
    if item_id in SKILL_ITEMS:
        item = SKILL_ITEMS[item_id]
    elif item_id in EQUIPMENT_TEMPLATES:
        # Generate a default version (White)
        item = generate_equipment(EQUIPMENT_TEMPLATES[item_id], rarity='white')
    elif item_id in OTHER_ITEMS:
        item = OTHER_ITEMS[item_id]
    elif item_id in CELL_ITEMS:
        item = CELL_ITEMS[item_id]
    
    if item:
        return copy.deepcopy(item)
    
    if isinstance(item_id, str):
         return Item(item_id, item_id, 'generic')
         
    return None

def get_random_equipment(rarity_weights=None):
    # rarity_weights: dict {'white': int, ...}
    if not rarity_weights:
        rarity_weights = {'white': 50, 'green': 30, 'blue': 15, 'purple': 4, 'orange': 1}
        
    # Filter items by rarity based on weighted choice
    rarity = random.choices(list(rarity_weights.keys()), weights=list(rarity_weights.values()), k=1)[0]
    
    # Pick a random template
    template = random.choice(list(EQUIPMENT_TEMPLATES.values()))
    
    return generate_equipment(template, rarity)

def get_random_cell(rarity_weights=None):
    if not rarity_weights:
        rarity_weights = {'white': 50, 'green': 30, 'blue': 15, 'purple': 4, 'orange': 1}
    
    rarity = random.choices(list(rarity_weights.keys()), weights=list(rarity_weights.values()), k=1)[0]
    
    # Filter for Cells (not starting with 'core_')
    candidates = [item for id, item in CELL_ITEMS.items() if not id.startswith('core_') and item.rarity == rarity]
    if not candidates:
        # Fallback to any cell
        candidates = [item for id, item in CELL_ITEMS.items() if not id.startswith('core_')]
        
    if candidates:
        return copy.deepcopy(random.choice(candidates))
    return None

def get_random_core(rarity_weights=None):
    if not rarity_weights:
        rarity_weights = {'white': 50, 'green': 30, 'blue': 15, 'purple': 4, 'orange': 1}
        
    rarity = random.choices(list(rarity_weights.keys()), weights=list(rarity_weights.values()), k=1)[0]
    
    # Filter for Cores (starting with 'core_')
    candidates = [item for id, item in CELL_ITEMS.items() if id.startswith('core_') and item.rarity == rarity]
    if not candidates:
        # Fallback to any core
        candidates = [item for id, item in CELL_ITEMS.items() if id.startswith('core_')]
        
    if candidates:
        return copy.deepcopy(random.choice(candidates))
    return None

def get_random_skill(rarity_weights=None):
    if not rarity_weights:
        rarity_weights = {'white': 50, 'green': 30, 'blue': 15, 'purple': 4, 'orange': 1}
        
    rarity = random.choices(list(rarity_weights.keys()), weights=list(rarity_weights.values()), k=1)[0]
    
    # Filter by rarity manually since SKILL_ITEMS has objects with fixed rarity
    candidates = [item for item in SKILL_ITEMS.values() if item.rarity == rarity]
    if not candidates:
        candidates = list(SKILL_ITEMS.values())
        
    if candidates:
        return copy.deepcopy(random.choice(candidates))
    return None
