import pygame
import random
import math
import config.game_config as settings
import core.damage as combat
from entities.enemy import Enemy
from entities.pickup import XPOrb
from utils.sound_manager import SoundManager
from systems.drop_system import LootManager

class SpawnRule:
    def __init__(self, start_min, end_min, spawn_interval, max_enemies, types, weights, elite_chance=0.0):
        self.start_min = start_min
        self.end_min = end_min
        self.spawn_interval = spawn_interval
        self.max_enemies = max_enemies
        self.types = types
        self.weights = weights
        self.elite_chance = elite_chance

class EnemyManager:
    def __init__(self):
        self.enemies = []
        self.enemy_projectiles = []
        
        # Time-Driven Spawning State
        self.spawn_timer = 0
        self.current_rule = None
        
        # Spawn Rules Configuration
        self.rules = [
            # 0-1 min: Low pressure, mostly Squares
            SpawnRule(0, 1, 1.5, 15, ['square'], [100], 0.0),
            
            # 1-3 min: Medium pressure, Squares + Triangles
            SpawnRule(1, 3, 1.0, 30, ['square', 'triangle'], [60, 40], 0.05),
            
            # 3-5 min: High pressure, All types + Elites
            SpawnRule(3, 5, 0.5, 60, ['square', 'triangle', 'circle'], [40, 30, 30], 0.1),
            
            # 5+ min: Endless
            SpawnRule(5, 999, 0.2, 100, ['square', 'triangle', 'circle'], [33, 33, 34], 0.2)
        ]

    def spawn_elite(self, x, y, e_type, wave, mission_stats=None, elite_type=None):
        elite = Enemy(x, y, e_type, wave, is_elite=True, mission_stats=mission_stats, elite_type=elite_type)
        elite.color = (min(255, elite.color[0]+50), min(255, elite.color[1]+50), min(255, elite.color[2]+50))
        self.enemies.append(elite)

    def spawn_enemy_around_player(self, player, game_time_min, mission_stats=None):
        # 1. Determine Rule
        rule = self.current_rule
        if not rule: return
        
        # 2. Pick Type
        e_type = random.choices(rule.types, weights=rule.weights, k=1)[0]
        
        # 3. Determine Position (Outside Screen)
        # Random angle
        angle = random.uniform(0, math.pi * 2)
        
        # Distance: Half Screen Width + Buffer
        spawn_radius = (settings.SCREEN_WIDTH / 2) + random.uniform(100, 300)
        spawn_pos = player.pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * spawn_radius
        
        # 4. Elite Check
        is_elite = random.random() < rule.elite_chance
        
        if is_elite:
            self.spawn_elite(spawn_pos.x, spawn_pos.y, e_type, player.level, mission_stats)
        else:
            self.enemies.append(Enemy(spawn_pos.x, spawn_pos.y, e_type, player.level, mission_stats=mission_stats))

    def spawn_enemy(self, player, game_time_min, force_type=None, count=1):
        """Force spawn enemy near player. Used by tutorials and debug."""
        # Calculate spawn pos
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spawn_radius = (settings.SCREEN_WIDTH / 2) + random.uniform(100, 300)
            spawn_pos = player.pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * spawn_radius
            
            e_type = force_type if force_type else 'square'
            
            self.enemies.append(Enemy(spawn_pos.x, spawn_pos.y, e_type, player.level))

    def update(self, dt, player, game_manager, game_time_min, map_manager, damage_callback=None, on_destroy_callback=None, spawn_enabled=True):
        dt_sec = dt / 1000.0
        
        mission_stats = {
            'completions': game_manager.mission_manager.completions if hasattr(game_manager, 'mission_manager') else 0,
            'max_damage': getattr(player, 'max_single_damage', 0),
            'max_combo': getattr(player, 'max_combo', 0)
        }
        
        # --- Time-Driven Spawning Logic ---
        if spawn_enabled:
            # Find active rule
            active_rule = None
            for r in self.rules:
                if r.start_min <= game_time_min < r.end_min:
                    active_rule = r
                    break
            
            if active_rule:
                self.current_rule = active_rule
                
                # Check max enemies cap
                if len(self.enemies) < active_rule.max_enemies:
                    self.spawn_timer += dt_sec
                    if self.spawn_timer >= active_rule.spawn_interval:
                        self.spawn_timer = 0
                        self.spawn_enemy_around_player(player, game_time_min, mission_stats)

        # --- Update Enemies ---
        player_pos = player.pos
        
        for enemy in self.enemies[:]:
            enemy.update(dt_sec, player_pos, self.enemies, self.enemy_projectiles, map_manager, damage_callback)

            # 1. Map Collision
            if map_manager:
                map_manager.check_collision(enemy)

            # 2. Hard Collision Resolution (Enemy-Enemy)
            for other in self.enemies:
                if other != enemy:
                    dist_vec = enemy.pos - other.pos
                    dist = dist_vec.length()
                    min_dist = (enemy.size + other.size) / 2 
                    
                    if dist < min_dist:
                        if dist > 0:
                            push_vec = dist_vec.normalize() * (min_dist - dist)
                            enemy.pos += push_vec * 0.5
                        else:
                            enemy.pos += pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 1.0
            
            # Check for death
            if not enemy.alive:
                # 1. Trigger Dying Animation (if not already dying)
                if not enemy.is_dying:
                    enemy.die()
                    
                    # Mission Hook: Kill
                    if hasattr(game_manager, 'mission_manager'):
                        game_manager.mission_manager.add_kill()
                    
                    # Play sound
                    SoundManager().play_sound(f"death_{enemy.type}")
                    
                    # Drop Loot & XP (Only once)
                    game_manager.pickups.append(XPOrb(enemy.pos.x, enemy.pos.y, enemy.xp_value))
                    
                    # Ensure LootManager is called
                    LootManager.drop_enemy_loot(game_manager, enemy.pos, enemy.type, enemy.is_elite, player)
                
                # 2. Remove only when animation is finished
                if enemy.is_dying and enemy.animation_finished:
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                continue

            # --- Player vs Enemy Collision ---
            dist_vec = player.pos - enemy.pos
            dist = dist_vec.length()
            min_dist = player.size/2 + enemy.size/2 * 0.8 
            
            if dist < min_dist:
                SoundManager().play_sound("collision")
                
                push_dir = dist_vec.normalize() if dist > 0 else pygame.math.Vector2(1, 0)
                overlap = min_dist - dist
                
                # Standard separation
                push_amt = overlap * 0.5
                player.pos += push_dir * push_amt
                enemy.pos -= push_dir * push_amt
                
                # Player takes damage
                if player.invincible_timer <= 0:
                    base_dmg = player.max_hp * 0.1
                    calculated_dmg, _ = combat.calculate_damage(base_dmg, 'collision', player, attacker=enemy)
                    final_dmg = combat.apply_damage(player, calculated_dmg, source=enemy)
                    if hasattr(game_manager, 'mission_manager'):
                        game_manager.mission_manager.add_damage_taken(final_dmg)
                    if damage_callback: damage_callback(player.pos, final_dmg, 'collision', is_player_damage=True)
                    player.invincible_timer = 0.05
                    SoundManager().play_sound("damage") 
                
                # Enemy takes damage (Thorns)
                base_dmg = enemy.max_hp * 0.1
                calculated_dmg, is_crit = combat.calculate_damage(base_dmg, 'collision', enemy, attacker=player)
                
                col_bonus_pct = getattr(player, 'collision_dmg_pct', 0)
                if col_bonus_pct > 0:
                    calculated_dmg = int(calculated_dmg * (1 + col_bonus_pct / 100.0))

                final_dmg = combat.apply_damage(enemy, calculated_dmg, source=player)
                
                if damage_callback: damage_callback(enemy.pos, final_dmg, 'collision')
                if hasattr(game_manager, 'mission_manager'):
                    game_manager.mission_manager.add_damage_dealt(final_dmg)
                if final_dmg > 0:
                     SoundManager().play_sound(f"hit_{enemy.type}")

                if not enemy.alive:
                    if not enemy.is_dying:
                        enemy.die()
                        if hasattr(game_manager, 'mission_manager'):
                            game_manager.mission_manager.add_kill()
                        SoundManager().play_sound(f"death_{enemy.type}")
                        game_manager.pickups.append(XPOrb(enemy.pos.x, enemy.pos.y, enemy.xp_value))
                        LootManager.drop_enemy_loot(game_manager, enemy.pos, enemy.type, enemy.is_elite, player)
                    
                    if enemy.is_dying and enemy.animation_finished:
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                    continue 
            
            # --- Player Projectiles vs Enemy ---
            for p in player.projectiles[:]:
                if (p.pos - enemy.pos).length() < enemy.size + p.radius:
                    if p.damage_interval > 0:
                        if enemy in p.hit_timers: continue 
                        p.hit_timers[enemy] = p.damage_interval 
                    
                    crit_mult, is_crit = combat.calculate_crit_multiplier(player)
                    raw_dmg = p.damage * crit_mult
                    
                    calc_dmg, _ = combat.calculate_damage(raw_dmg, p.damage_type, enemy)
                    final_dmg = combat.apply_damage(enemy, calc_dmg, source=player)
                    if hasattr(game_manager, 'mission_manager'):
                        game_manager.mission_manager.add_damage_dealt(final_dmg)
                    
                    if damage_callback: damage_callback(enemy.pos, final_dmg, p.damage_type)
                    if final_dmg > 0:
                         SoundManager().play_sound(f"hit_{enemy.type}")
                    
                    if hasattr(p, 'effects') and p.effects:
                        for eff in p.effects:
                            if hasattr(enemy, 'apply_status_effect'):
                                enemy.apply_status_effect(eff['type'], eff['duration'], eff['intensity'])
                                
                    if hasattr(p, 'wet_stats') and p.wet_stats:
                        enemy.apply_status_effect('wet', p.wet_stats['duration'], 1.0)

                    # Elemental Reactions (Logic preserved from original)
                    skip_standard_lightning = False
                    gene_unlocked = getattr(player, 'inventory', None) and getattr(player.inventory, 'gene_unlocked', False)
                    
                    if gene_unlocked:
                        has_fire = any(eff['type'] == 'burn' for eff in p.effects) if hasattr(p, 'effects') else False
                        has_water = hasattr(p, 'wet_stats') and p.wet_stats is not None
                        has_lightning = hasattr(p, 'on_hit_effect') and p.on_hit_effect == 'lightning'
                        
                        is_target_wet = any(eff['type'] == 'wet' for eff in enemy.status_effects)
                        is_target_burning = any(eff['type'] == 'burn' for eff in enemy.status_effects)
                        
                        if (has_fire and is_target_wet) or (has_water and is_target_burning):
                            enemy.status_effects = [e for e in enemy.status_effects if e['type'] not in ('burn', 'wet')]
                            vaporize_dmg = 50 + (player.level * 10)
                            neighbors = [e for e in self.enemies if e.alive and e.pos.distance_to(enemy.pos) <= 60]
                            for n in neighbors:
                                calc_dmg, _ = combat.calculate_damage(vaporize_dmg, 'magic', n)
                                fd = combat.apply_damage(n, calc_dmg, source=player)
                                if damage_callback: damage_callback(n.pos, fd, 'magic')
                            SoundManager().play_sound("explosion") 

                        elif has_lightning and is_target_burning:
                            skip_standard_lightning = True
                            chain_range = 150
                            candidates = [e for e in self.enemies if e != enemy and e.alive]
                            if candidates:
                                candidates.sort(key=lambda e: e.pos.distance_to(enemy.pos))
                                target = candidates[0]
                                if target.pos.distance_to(enemy.pos) < chain_range:
                                    dmg = p.damage * 0.8 
                                    calc_dmg, _ = combat.calculate_damage(dmg, 'magic', target)
                                    fd = combat.apply_damage(target, calc_dmg, source=player)
                                    if damage_callback: damage_callback(target.pos, fd, 'magic')
                                    SoundManager().play_sound("lightning_hit")

                        elif has_lightning and is_target_wet:
                            skip_standard_lightning = True
                            wet_enemies = [e for e in self.enemies if e != enemy and e.alive and any(eff['type'] == 'wet' for eff in e.status_effects)]
                            curr = enemy
                            jumps = 5
                            dmg = p.damage * 0.2
                            visited = {enemy}
                            for _ in range(jumps):
                                best_next = None
                                min_d = 200
                                for we in wet_enemies:
                                    if we in visited: continue
                                    d = we.pos.distance_to(curr.pos)
                                    if d < min_d:
                                        min_d = d
                                        best_next = we
                                if best_next:
                                    calc_dmg, _ = combat.calculate_damage(dmg, 'magic', best_next)
                                    fd = combat.apply_damage(best_next, calc_dmg, source=player)
                                    if damage_callback: damage_callback(best_next.pos, fd, 'magic')
                                    visited.add(best_next)
                                    curr = best_next
                                else:
                                    break
                            SoundManager().play_sound("lightning_hit")
                                
                    if hasattr(p, 'knockback_force') and p.knockback_force > 0:
                         push_dir = (enemy.pos - p.pos).normalize() if (enemy.pos - p.pos).length() > 0 else pygame.math.Vector2(1, 0)
                         enemy.pos += push_dir * (p.knockback_force * dt_sec)
                         
                    if not skip_standard_lightning and hasattr(p, 'on_hit_effect') and p.on_hit_effect == 'lightning':
                        candidates = [e for e in self.enemies if e != enemy and e.alive]
                        if candidates:
                            candidates.sort(key=lambda e: e.pos.distance_to(enemy.pos))
                            target = candidates[0]
                            dist = target.pos.distance_to(enemy.pos)
                            if dist < 20:
                                dmg = p.damage * 0.5
                                calc_dmg, _ = combat.calculate_damage(dmg, 'magic', target)
                                final_chain_dmg = combat.apply_damage(target, calc_dmg, source=player)
                                if damage_callback: damage_callback(target.pos, final_chain_dmg, 'magic')
                                SoundManager().play_sound("lightning_hit")
                                
                    if hasattr(p, 'chain_info') and p.chain_info:
                        chain_range = p.chain_info.get('range', 100)
                        damage_pct = p.chain_info.get('pct', 0.3)
                        element = p.chain_info.get('element', None)
                        chain_targets = [e for e in self.enemies if e != enemy and e.alive and e.pos.distance_to(enemy.pos) <= chain_range]
                        for target in chain_targets:
                            chain_dmg = p.damage * damage_pct
                            calc_dmg, _ = combat.calculate_damage(chain_dmg, 'physical', target)
                            final_chain_dmg = combat.apply_damage(target, calc_dmg, source=player)
                            if damage_callback: damage_callback(target.pos, final_chain_dmg, 'physical')
                            if element == 'fire':
                                target.apply_status_effect('burn', 3.0, 0.2)
                            elif element == 'water':
                                push_dir = (target.pos - enemy.pos).normalize() if (target.pos - enemy.pos).length() > 0 else pygame.math.Vector2(1, 0)
                                target.pos += push_dir * 50
                            elif element == 'lightning':
                                calc_dmg, _ = combat.calculate_damage(chain_dmg * 0.5, 'magic', target)
                                extra_dmg = combat.apply_damage(target, calc_dmg, source=player)
                                if damage_callback: damage_callback(target.pos, extra_dmg, 'magic')
                        if chain_targets:
                             SoundManager().play_sound("lightning_hit")

                    if getattr(p, 'type', None) == 'shrink_ball':
                        enemy.apply_status_effect('compress', 3.0, 1.0)
                    
                    if not p.piercing:
                        if p.piercing_count > 0:
                            p.piercing_count -= 1
                        else:
                            if p in player.projectiles:
                                player.projectiles.remove(p)
                    
                    if not enemy.alive:
                        if not enemy.is_dying:
                            enemy.die()
                            if hasattr(game_manager, 'mission_manager'):
                                game_manager.mission_manager.add_kill()
                            SoundManager().play_sound(f"death_{enemy.type}")
                            game_manager.pickups.append(XPOrb(enemy.pos.x, enemy.pos.y, enemy.xp_value))
                            LootManager.drop_enemy_loot(game_manager, enemy.pos, enemy.type, enemy.is_elite, player)
                        if enemy.is_dying and enemy.animation_finished:
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                        break
            
            # --- Player Melee vs Enemy ---
            for m in player.melee_attacks:
                 if m.duration > 0:
                    to_enemy = enemy.pos - player.pos
                    dist = to_enemy.length()
                    if dist < m.range + enemy.size:
                        angle_diff = abs(math.atan2(to_enemy.y, to_enemy.x) - m.base_angle)
                        while angle_diff > math.pi: angle_diff -= 2*math.pi
                        while angle_diff < -math.pi: angle_diff += 2*math.pi
                        if abs(angle_diff) < 1.0: 
                            dmg_per_tick = getattr(player, 'phys_atk', 10) * dt_sec * 5
                            calc_dmg, _ = combat.calculate_damage(dmg_per_tick, 'physical', enemy)
                            final_dmg = combat.apply_damage(enemy, calc_dmg, source=player)
                            if hasattr(game_manager, 'mission_manager'):
                                game_manager.mission_manager.add_damage_dealt(final_dmg)
                            if final_dmg > 1 and damage_callback: damage_callback(enemy.pos, final_dmg, 'physical')
                            
                            if final_dmg > 0 and random.random() < 0.3:
                                SoundManager().play_sound(f"hit_{enemy.type}")
                            
                            if not enemy.alive:
                                if not enemy.is_dying:
                                    enemy.die()
                                    if hasattr(game_manager, 'mission_manager'):
                                        game_manager.mission_manager.add_kill()
                                    SoundManager().play_sound(f"death_{enemy.type}")
                                    game_manager.pickups.append(XPOrb(enemy.pos.x, enemy.pos.y, enemy.xp_value))
                                    LootManager.drop_enemy_loot(game_manager, enemy.pos, enemy.type, enemy.is_elite, player)
                                
                                if enemy.is_dying and enemy.animation_finished:
                                    if enemy in self.enemies:
                                        self.enemies.remove(enemy)
        
        # --- Update Enemy Projectiles ---
        for p in self.enemy_projectiles[:]:
            p.update(dt_sec)
            
            if (p.pos - player.pos).length() < player.size/2 + p.radius:
                if player.invincible_timer <= 0:
                    dmg_type = getattr(p, 'damage_type', 'physical')
                    calc_dmg, _ = combat.calculate_damage(p.damage, dmg_type, player)
                    final_dmg = combat.apply_damage(player, calc_dmg, source=p)
                    if hasattr(game_manager, 'mission_manager'):
                        game_manager.mission_manager.add_damage_taken(final_dmg)
                    if damage_callback: damage_callback(player.pos, final_dmg, dmg_type, is_player_damage=True)
                    player.invincible_timer = 0.05
                    SoundManager().play_sound("damage")
                    
                    if hasattr(p, 'effects') and p.effects:
                        for eff in p.effects:
                            if hasattr(player, 'apply_status_effect'):
                                player.apply_status_effect(eff['type'], eff['duration'], eff['intensity'])
                    
                if p in self.enemy_projectiles:
                    self.enemy_projectiles.remove(p)
                continue
                
            if p.duration <= 0:
                self.enemy_projectiles.remove(p)

        # --- Check Obstacle Collisions ---
        if map_manager:
            for p in player.projectiles[:]:
                if map_manager.check_projectile_collision(p, damage_callback, on_destroy_callback):
                    if not p.piercing:
                        if p in player.projectiles:
                            player.projectiles.remove(p)
                            
            for p in self.enemy_projectiles[:]:
                if map_manager.check_projectile_collision(p, damage_callback, on_destroy_callback):
                    if p in self.enemy_projectiles:
                        self.enemy_projectiles.remove(p)
                        
            for m in player.melee_attacks:
                 if m.duration > 0:
                     map_manager.check_melee_collision(player, m, dt_sec, damage_callback, on_destroy_callback)

    def draw(self, surface, camera):
        for enemy in self.enemies:
            enemy.draw(surface, camera)
            
        for p in self.enemy_projectiles:
            p.draw(surface, camera)

    def get_save_data(self):
        enemies_data = []
        for enemy in self.enemies:
            data = {
                'x': enemy.pos.x,
                'y': enemy.pos.y,
                'type': enemy.type,
                'hp': enemy.current_hp,
                'max_hp': enemy.max_hp
            }
            enemies_data.append(data)
        return enemies_data

    def load_from_data(self, data):
        self.enemies = []
        for enemy_data in data:
            enemy = Enemy(enemy_data['x'], enemy_data['y'], enemy_data['type'], 1)
            enemy.pos = pygame.math.Vector2(enemy_data['x'], enemy_data['y'])
            enemy.max_hp = enemy_data['max_hp']
            enemy.current_hp = enemy_data['hp']
            self.enemies.append(enemy)
