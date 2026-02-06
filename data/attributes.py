
STATS = {
    # Layer 1: Basic
    "max_hp": {
        "name": "最大生命",
        "layer": 1,
        "base": 100,
        "min_rarity": "white",
        "upgrade_value": 10,
    },
    "max_mp": {
        "name": "最大魔力",
        "layer": 1,
        "base": 100,
        "min_rarity": "white",
        "upgrade_value": 10,
    },
    "phys_atk": {
        "name": "物理攻击",
        "layer": 1,
        "base": 10,
        "min_rarity": "white",
        "upgrade_value": 2,
    },
    "magic_atk": {
        "name": "魔法攻击",
        "layer": 1,
        "base": 8,
        "min_rarity": "white",
        "upgrade_value": 2,
    },
    "phys_def": {
        "name": "物理防御",
        "layer": 1,
        "base": 3,
        "min_rarity": "white",
        "upgrade_value": 1,
    },
    "magic_def": {
        "name": "魔法防御",
        "layer": 1,
        "base": 2,
        "min_rarity": "white",
        "upgrade_value": 1,
    },
    "attack_speed": {
        "name": "攻击速度",
        "layer": 1,
        "base": 1.0,
        "min_rarity": "white",
        "upgrade_value": 0.05,
    },
    "move_speed": {
        "name": "移动速度",
        "layer": 1,
        "base": 280,
        "min_rarity": "white",
        "upgrade_value": 10,
    },
    "pickup_range": {
        "name": "拾取范围",
        "layer": 1,
        "base": 100,
        "min_rarity": "white",
        "upgrade_value": 20,
    },
    "attack_range": {
        "name": "攻击范围",
        "layer": 1,
        "base": 0,
        "min_rarity": "white",
        "upgrade_value": 10,
    },
    "skill_range": {
        "name": "技能范围",
        "layer": 1,
        "base": 0,
        "min_rarity": "white",
        "upgrade_value": 50,
    },

    # Layer 2: Enhanced
    "crit_chance": {
        "name": "暴击率",
        "layer": 2,
        "base": 5, # 5%
        "min_rarity": "green",
        "upgrade_value": 2,
        "max": 100,
    },
    "phys_pen": {
        "name": "物理穿透",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 5,
    },
    "magic_pen": {
        "name": "魔法穿透",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 5,
    },
    "damage_bonus": {
        "name": "伤害加成",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 5, # 5%
    },
    "hp_regen": {
        "name": "生命恢复",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 1,
    },
    "mp_regen": {
        "name": "魔力恢复",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 1,
    },
    "skill_haste": {
        "name": "技能急速",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 5,
    },
    "luck": {
        "name": "幸运",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 1,
    },
    "collision_damage_reduction": {
        "name": "碰撞减免",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 2,
        "max": 60,
    },
    "final_damage_reduction": {
        "name": "百分比减免",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 2,
        "max": 60,
    },
    "collision_dmg_pct": {
        "name": "碰撞伤害",
        "layer": 2,
        "base": 0,
        "min_rarity": "green",
        "upgrade_value": 20,
    },

    # Layer 3: Rule
    "skill_haste_cap": {
        "name": "技能急速上限",
        "layer": 3,
        "base": 80,
        "min_rarity": "purple",
        "upgrade_value": 5,
        "max": 100,
    },
    "crit_dmg": {
        "name": "暴击伤害",
        "layer": 3,
        "base": 150, # 150%
        "min_rarity": "purple",
        "upgrade_value": 10,
    },
    "piercing_count": {
        "name": "穿透数量",
        "layer": 3,
        "base": 0,
        "min_rarity": "purple",
        "upgrade_value": 1,
    },
    "true_dmg": {
        "name": "真实伤害",
        "layer": 3,
        "base": 0,
        "min_rarity": "purple",
        "upgrade_value": 1,
    }
}

def validate_stats_config():
    for stat_id, config in STATS.items():
        assert "base" in config, f"{stat_id} 缺少 base"
        assert "upgrade_value" in config, f"{stat_id} 缺少 upgrade_value"
        assert "layer" in config, f"{stat_id} 缺少 layer"
