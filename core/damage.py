import random

def calculate_crit_multiplier(attacker):
    """
    计算暴击倍率和是否暴击
    """
    crit_chance = getattr(attacker, 'crit_chance', 0)
    crit_dmg_base = getattr(attacker, 'crit_dmg', 150)
    
    # 溢出处理
    if crit_chance > 100:
        excess = crit_chance - 100
        crit_dmg_base += excess * 10
        crit_chance = 100
        
    is_crit = False
    crit_multiplier = 1.0
    
    if random.uniform(0, 100) <= crit_chance:
        is_crit = True
        crit_multiplier = crit_dmg_base / 100.0
        
    return crit_multiplier, is_crit

def calculate_damage(base_amount, damage_type, target, attacker=None):
    """
    伤害结算核心逻辑 (Balance Anchor Implementation)
    
    ⚠️ 以下顺序必须写入代码注释 ⚠️ 禁止任何系统跳过或重排（真实伤害除外）
    
    Step 1: 基础伤害确定
    Step 2: 穿透计算 (Effective Def = max(0, Def - Pen))
    Step 3: 数值防御结算 (Actual = max(1, Base - Eff_Def))
    Step 4: 百分比减免 (Reduced = Actual * (1 - Red%), Max 60%)
    Step 5: 暴击计算 (Crit Dmg = Reduced * CritMult)
    Step 6: 伤害加成 (Final = Crit * (1 + Bonus%))
    """
    
    # 获取必要的属性
    # Attacker stats
    attacker_stats = {}
    if attacker:
        attacker_stats['phys_pen'] = getattr(attacker, 'phys_pen', 0)
        attacker_stats['magic_pen'] = getattr(attacker, 'magic_pen', 0)
        attacker_stats['crit_chance'] = getattr(attacker, 'crit_chance', 0)
        attacker_stats['crit_dmg'] = getattr(attacker, 'crit_dmg', 150)
        attacker_stats['damage_bonus'] = getattr(attacker, 'damage_bonus', 0)
    
    # Target stats
    target_stats = {}
    if target:
        target_stats['phys_def'] = getattr(target, 'phys_def', 0)
        target_stats['magic_def'] = getattr(target, 'magic_def', 0)
        target_stats['final_damage_reduction'] = getattr(target, 'final_damage_reduction', 0)
        target_stats['collision_damage_reduction'] = getattr(target, 'collision_damage_reduction', 0)

    # 特殊规则：真实伤害
    # 不参与第 2 / 3 / 4 / 5 步
    # 直接进入第 6 步
    if damage_type == 'true':
        # Step 6: 伤害加成
        bonus = attacker_stats.get('damage_bonus', 0)
        final_damage = base_amount * (1 + bonus / 100.0)
        return int(final_damage), False

    # Step 1: 基础伤害确定 (已通过参数 base_amount 传入)
    # 类型处理
    is_collision = (damage_type == 'collision')
    calc_type = 'physical' if is_collision else damage_type # Collision 视为物理计算防御

    # Step 2: 穿透计算（只影响防御）
    # 有效防御 = max(0, 防御值 - 穿透值)
    defense = 0
    penetration = 0
    
    if calc_type == 'physical':
        defense = target_stats.get('phys_def', 0)
        penetration = attacker_stats.get('phys_pen', 0)
    elif calc_type == 'magic':
        defense = target_stats.get('magic_def', 0)
        penetration = attacker_stats.get('magic_pen', 0)
        
    effective_defense = max(0, defense - penetration)

    # Step 3: 数值防御结算
    # 实际伤害 = max(1, 基础伤害 - 有效防御)
    actual_damage = max(1, base_amount - effective_defense)

    # Step 4: 百分比减免
    # 减免后伤害 = 实际伤害 × (1 - 减免%)
    # 百分比减免上限：60%
    reduction_pct = target_stats.get('final_damage_reduction', 0)
    
    if is_collision:
        reduction_pct += target_stats.get('collision_damage_reduction', 0)
        
    # Cap at 60%
    reduction_pct = min(60, reduction_pct)
    
    reduced_damage = actual_damage * (1 - reduction_pct / 100.0)

    # Step 5: 暴击计算（若触发）
    # 暴击伤害 = 减免后伤害 × 暴击倍率
    # 基础暴击倍率：150%
    
    is_crit = False
    crit_multiplier = 1.0
    
    if attacker:
        crit_multiplier, is_crit = calculate_crit_multiplier(attacker)
        
    crit_damage_val = reduced_damage * crit_multiplier

    # Step 6: 伤害加成（最终乘区）
    # 最终伤害 = 暴击伤害 × (1 + 伤害加成%)
    bonus = attacker_stats.get('damage_bonus', 0)
    final_damage = crit_damage_val * (1 + bonus / 100.0)

    return int(final_damage), is_crit

def apply_damage(target, amount, source=None):
    """
    应用最终伤害到目标
    """
    if hasattr(target, 'god_mode') and target.god_mode:
        return 0

    if hasattr(target, 'current_hp'):
        target.current_hp -= amount
        if target.current_hp <= 0:
            target.current_hp = 0
            target.alive = False
            if hasattr(target, 'on_death'):
                target.on_death(source)
    return amount

def attack(attacker, defender):
    """
    发起攻击
    """
    total_dmg = 0
    
    # 1. 物理攻击
    phys_atk = getattr(attacker, 'phys_atk', 0)
    if phys_atk > 0:
        dmg, is_crit = calculate_damage(phys_atk, 'physical', defender, attacker)
        apply_damage(defender, dmg, source=attacker)
        total_dmg += dmg
        
    # 2. 魔法攻击
    magic_atk = getattr(attacker, 'magic_atk', 0)
    if magic_atk > 0:
        dmg, is_crit = calculate_damage(magic_atk, 'magic', defender, attacker)
        apply_damage(defender, dmg, source=attacker)
        total_dmg += dmg
        
    # 3. 真实伤害
    true_dmg = getattr(attacker, 'true_dmg', 0)
    if true_dmg > 0:
        dmg, is_crit = calculate_damage(true_dmg, 'true', defender, attacker)
        apply_damage(defender, dmg, source=attacker)
        total_dmg += dmg
        
    return total_dmg
