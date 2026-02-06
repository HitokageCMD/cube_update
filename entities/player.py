import pygame
import math
import config.game_config as settings
from systems.equipment_system import Inventory
from systems.skill_system import SkillSystem
from data.item_data import get_item_by_id
from entities.base_entity import Entity
from entities.projectile import Projectile, MeleeSwing
from ui.trail import Trail
from data.attributes import STATS
from utils.sound_manager import SoundManager

class Player(Entity):
    def __init__(self, character_data):
        self.data = character_data
        
        # Initialize stats container for property setters called in super().__init__
        self.stats = {}
            
        # Call parent init (Note: This will write legacy defaults to self.stats via properties)
        super().__init__()
        
        # Re-initialize stats from Data Layer (Overwriting legacy defaults)
        print(f"[Player Init] Initializing player {self.data.get('id', 'unknown')}")
        for key, config in STATS.items():
            self.stats[key] = config.get('base', 0)
            
        # Apply Character specific overrides
        # character_data['stats'] might contain keys that are in STATS
        if 'stats' in character_data:
            print(f"[Player Init] Found overrides: {list(character_data['stats'].keys())}")
            for key, val in character_data['stats'].items():
                if key in self.stats:
                    print(f"[Player Init] Overriding {key}: {self.stats[key]} -> {val}")
                    self.stats[key] = val
                else:
                    print(f"[Player Init] Warning: Key {key} not in STATS")
        else:
            print("[Player Init] No 'stats' overrides found in character_data")
        
        # Re-initialize core attributes based on stats
        self.current_hp = self.max_hp
        self.current_mp = self.stats['max_mp']
        
        # Backpack
        self.inventory = Inventory(self)
        
        # Skill System
        self.skill_system = SkillSystem(self)
        
        # Default Skills
        char_id = character_data['id']
        skill_id = None
        if char_id == 'square': skill_id = 'skill_dash'
        elif char_id == 'triangle': skill_id = 'skill_fan_shot'
        elif char_id == 'circle': skill_id = 'skill_shrink_ball'
        
        if skill_id:
            skill_item = get_item_by_id(skill_id)
            if skill_item:
                self.inventory.skill_slots[0] = skill_item

        self.selected_skill_slot = 0
        self.skill_cooldowns = {}
        
        self.pos = pygame.math.Vector2(0, 0)
        self.size = 50
        self.width = self.size
        self.height = self.size
        
        # Ensure compatibility
        if 'move_speed' not in self.stats: self.stats['move_speed'] = 280
        
        self.hp_regen_timer = 0
        self.mp_regen_timer = 0
        
        self.projectiles = []
        self.melee_attacks = []
        
        self.level = 1
        self.current_xp = 0
        self.xp_to_next_level = 100
        
        # Timers
        self.attack_cooldown_timer = 0
        self.invincible_timer = 0
        self.dodge_cooldown_timer = 0
        self.dodge_last_cd = 0
        
        # Status Effects
        self.status_effects = []
        
        # Dash
        self.dash_timer = 0
        self.dash_velocity = pygame.math.Vector2(0, 0)
        self.is_dashing = False
        self.scheduled_actions = []
        
        # Dev Mode
        self.god_mode = False
        
        # New Mechanics
        self.overlord_rage = False # 霸王血恺
        self.slippery = False # 滑轮鞋
        self.nearby_interactables = []
        
        # Exhaust Mechanic
        self.exhaust_timer = 0
        
        # Animation State
        self.animation_state = 'idle'
        self.animation_frame = 0.0
        self.animation_speed = 10.0 # Frames per second

        # Tracking Stats
        self.max_single_damage = 0
        self.current_combo = 0
        self.max_combo = 0
        self.combo_timer = 0
        
        # DPS Tracking
        self.dps = 0
        self.damage_history = [] # List of (timestamp_ms, damage_amount)

    def take_damage(self, amount, damage_type='physical', penetration=0, source=None):
        if self.god_mode:
            return 0
        return super().take_damage(amount, damage_type, penetration, source)

    # Properties for Stats
    @property
    def max_hp(self): 
        val = self.stats.get('max_hp', 100)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('max_hp')
        return val
    @max_hp.setter
    def max_hp(self, value): self.stats['max_hp'] = value
        
    @property
    def max_mp(self): 
        val = self.stats.get('max_mp', 100)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('max_mp')
        return val
    @max_mp.setter
    def max_mp(self, value): self.stats['max_mp'] = value

    @property
    def phys_atk(self): 
        val = self.stats.get('phys_atk', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('phys_atk')
            
        # Overlord Rage
        if self.overlord_rage:
            hp_pct = self.current_hp / self.max_hp
            if hp_pct < 0.9:
                # <90%: 5%, <80%: 7%, ... <30%: max
                bonus_pct = 5 + 2 * int((0.9 - max(0.3, hp_pct)) * 10)
                val *= (1.0 + bonus_pct / 100.0)
                
        # Status Effects: Overload
        for effect in self.status_effects:
            if effect['type'] == 'overload':
                val *= 0.5 # Reduce Damage by 50%
                
        return val
    @phys_atk.setter
    def phys_atk(self, value): self.stats['phys_atk'] = value
    
    @property
    def magic_atk(self): 
        val = self.stats.get('magic_atk', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('magic_atk')
        return val
    @magic_atk.setter
    def magic_atk(self, value): self.stats['magic_atk'] = value

    @property
    def phys_def(self): 
        val = self.stats.get('phys_def', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('phys_def')
        return val
    @phys_def.setter
    def phys_def(self, value): self.stats['phys_def'] = value

    @property
    def magic_def(self): 
        val = self.stats.get('magic_def', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('magic_def')
        return val
    @magic_def.setter
    def magic_def(self, value): self.stats['magic_def'] = value
    
    @property
    def phys_pen(self): 
        val = self.stats.get('phys_pen', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('phys_pen')
        return val
    @phys_pen.setter
    def phys_pen(self, value): self.stats['phys_pen'] = value

    @property
    def magic_pen(self): 
        val = self.stats.get('magic_pen', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('magic_pen')
        return val
    @magic_pen.setter
    def magic_pen(self, value): self.stats['magic_pen'] = value

    @property
    def true_dmg(self): 
        val = self.stats.get('true_dmg', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('true_dmg')
        return val
    @true_dmg.setter
    def true_dmg(self, value): self.stats['true_dmg'] = value

    @property
    def attack_range(self): 
        val = self.stats.get('attack_range', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('attack_range')
        return val
    @attack_range.setter
    def attack_range(self, value): self.stats['attack_range'] = value

    @property
    def skill_range(self): 
        val = self.stats.get('skill_range', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('skill_range')
        return val
    @skill_range.setter
    def skill_range(self, value): self.stats['skill_range'] = value

    @property
    def pickup_range(self): 
        val = self.stats.get('pickup_range', 100)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('pickup_range')
        return val
    @pickup_range.setter
    def pickup_range(self, value): self.stats['pickup_range'] = value

    @property
    def piercing_count(self): 
        val = self.stats.get('piercing_count', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('piercing_count')
        return val
    @piercing_count.setter
    def piercing_count(self, value): self.stats['piercing_count'] = value

    @property
    def collision_damage_reduction(self):
        base = self.stats.get('collision_damage_reduction', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            base += self.inventory.get_stat_bonus('collision_damage_reduction')
        if hasattr(self, 'is_dashing') and self.is_dashing:
            return base + 10
        return base
    @collision_damage_reduction.setter
    def collision_damage_reduction(self, value): self.stats['collision_damage_reduction'] = value

    @property
    def collision_dmg_pct(self): 
        val = self.stats.get('collision_dmg_pct', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('collision_dmg_pct')
        return val
    @collision_dmg_pct.setter
    def collision_dmg_pct(self, value): self.stats['collision_dmg_pct'] = value

    @property
    def skill_haste(self): 
        val = self.stats.get('skill_haste', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('skill_haste')
        return val
    @skill_haste.setter
    def skill_haste(self, value): self.stats['skill_haste'] = value

    @property
    def skill_haste_cap(self): 
        val = self.stats.get('skill_haste_cap', 80)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('skill_haste_cap')
        return val
    @skill_haste_cap.setter
    def skill_haste_cap(self, value): self.stats['skill_haste_cap'] = value

    @property
    def cooldown_reduction(self):
        sh = self.skill_haste
        if sh < 0: return 0
        raw_cdr = sh / (sh + 100.0)
        max_cdr = self.skill_haste_cap / 100.0
        return min(raw_cdr, max_cdr)

    # New Props
    @property
    def crit_chance(self): 
        val = self.stats.get('crit_chance', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('crit_chance')
        return val
    @crit_chance.setter
    def crit_chance(self, value): self.stats['crit_chance'] = value

    @property
    def damage_bonus(self): 
        val = self.stats.get('damage_bonus', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('damage_bonus')
        return val
    @damage_bonus.setter
    def damage_bonus(self, value): self.stats['damage_bonus'] = value

    @property
    def crit_dmg(self): 
        val = self.stats.get('crit_dmg', 200)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('crit_dmg')
        return val
    @crit_dmg.setter
    def crit_dmg(self, value): self.stats['crit_dmg'] = value

    @property
    def hp_regen(self): 
        val = self.stats.get('hp_regen', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('hp_regen')
        return val
    @hp_regen.setter
    def hp_regen(self, value): self.stats['hp_regen'] = value

    @property
    def luck(self): 
        val = self.stats.get('luck', 0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('luck')
        return val
    @luck.setter
    def luck(self, value): self.stats['luck'] = value

    @property
    def attack_speed(self):
        val = self.stats.get('attack_speed', 1.0)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('attack_speed')
        return max(0.1, val)
    @attack_speed.setter
    def attack_speed(self, value): self.stats['attack_speed'] = value

    @property
    def move_speed(self):
        val = self.stats.get('move_speed', 300)
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'get_stat_bonus'):
            val += self.inventory.get_stat_bonus('move_speed')
            
        # Apply Status Effects
        modifier = 1.0
        for effect in self.status_effects:
            if effect['type'] == 'slow':
                modifier *= (1.0 - effect['intensity'])
        
        return max(0, val * modifier)
    @move_speed.setter
    def move_speed(self, value): self.stats['move_speed'] = value

    # Legacy Aliases
    @property
    def atk(self): return self.phys_atk
    @atk.setter
    def atk(self, value): self.phys_atk = value

    @property
    def defense(self): return self.phys_def
    @defense.setter
    def defense(self, value): self.phys_def = value

    def apply_status_effect(self, effect_type, duration, intensity=1.0):
        # Check if effect already exists
        for effect in self.status_effects:
            if effect['type'] == effect_type:
                # Refresh duration and max intensity
                effect['duration'] = max(effect['duration'], duration)
                effect['intensity'] = max(effect['intensity'], intensity)
                return
        
        self.status_effects.append({
            'type': effect_type,
            'duration': duration,
            'intensity': intensity,
            'timer': 0
        })

    def update_status_effects(self, dt_sec):
        # speed_modifier = 1.0 # Moved to property
        
        for effect in self.status_effects[:]:
            effect['timer'] += dt_sec
            if effect['timer'] >= effect['duration']:
                self.status_effects.remove(effect)
                continue
            
            # if effect['type'] == 'slow':
            #     speed_modifier *= (1.0 - effect['intensity'])
                
        # return speed_modifier
        return 1.0

    # Helper methods for input
    def is_action_pressed(self, action):
        kb = settings.game_config['key_bindings']
        code = kb.get(action, 0)
        if code == 0: return False
        
        if code < 0: # Mouse
            mouse_pressed = pygame.mouse.get_pressed()
            if code == settings.MOUSE_LEFT: return mouse_pressed[0]
            if code == settings.MOUSE_MIDDLE: return mouse_pressed[1]
            if code == settings.MOUSE_RIGHT: return mouse_pressed[2]
            return False
        else: # Keyboard
            keys = pygame.key.get_pressed()
            if code < len(keys): return keys[code]
            return False

    def is_action_triggered(self, event, action):
        kb = settings.game_config['key_bindings']
        code = kb.get(action, 0)
        if code == 0: return False
        
        if code < 0: # Mouse
            if event.type == pygame.MOUSEBUTTONDOWN:
                if code == settings.MOUSE_LEFT and event.button == 1: return True
                if code == settings.MOUSE_MIDDLE and event.button == 2: return True
                if code == settings.MOUSE_RIGHT and event.button == 3: return True
        else: # Keyboard
            if event.type == pygame.KEYDOWN:
                if event.key == code: return True
        return False

    def update(self, dt):
        dt_sec = dt / 1000.0
        
        # Combo Timer
        if self.combo_timer > 0:
            self.combo_timer -= dt_sec
            if self.combo_timer <= 0:
                self.current_combo = 0
        
        # Update Animation
        self.animation_frame += self.animation_speed * dt_sec
        # Determine animation state based on movement
        if hasattr(self, 'is_dashing') and self.is_dashing:
            # Could add 'dash' state later, for now 'run' is fine or 'idle'
            self.animation_state = 'run'
        else:
            move_vec = pygame.math.Vector2(0, 0)
            if self.is_action_pressed('up'): move_vec.y -= 1
            if self.is_action_pressed('down'): move_vec.y += 1
            if self.is_action_pressed('left'): move_vec.x -= 1
            if self.is_action_pressed('right'): move_vec.x += 1
            
            if move_vec.length() > 0:
                self.animation_state = 'run'
            else:
                self.animation_state = 'idle'
        
        # Update Status Effects
        speed_modifier = self.update_status_effects(dt_sec)
        
        # Scheduled actions
        if hasattr(self, 'scheduled_actions') and self.scheduled_actions:
            for action in self.scheduled_actions[:]:
                action['timer'] -= dt_sec
                if action['timer'] <= 0:
                    action['func']()
                    self.scheduled_actions.remove(action)

        # Dash
        if hasattr(self, 'is_dashing') and self.is_dashing:
            self.dash_timer -= dt_sec
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.dash_velocity = pygame.math.Vector2(0, 0)
            else:
                self.pos += self.dash_velocity * dt_sec
        else:
            # Timers
            if self.attack_cooldown_timer > 0: self.attack_cooldown_timer -= dt_sec
            if self.invincible_timer > 0: self.invincible_timer -= dt_sec
            if self.dodge_cooldown_timer > 0: self.dodge_cooldown_timer -= dt_sec
                
            # Movement
            # keys = pygame.key.get_pressed() # No longer needed directly
            move_vec = pygame.math.Vector2(0, 0)
            
            # kb = settings.game_config['key_bindings'] # Used via helper
            if self.is_action_pressed('up'): move_vec.y -= 1
            if self.is_action_pressed('down'): move_vec.y += 1
            if self.is_action_pressed('left'): move_vec.x -= 1
            if self.is_action_pressed('right'): move_vec.x += 1
            
            if move_vec.length() > 0:
                move_vec = move_vec.normalize()
                current_speed = self.move_speed # Use property
                    
                self.pos += move_vec * current_speed * dt_sec
                
                # Play footstep sound
                if settings.game_config.get('sfx_volume', 1.0) > 0:
                    # We need access to map_manager. 
                    # Player doesn't have reference to map_manager usually.
                    # But we can try to access it via singleton or pass it in update?
                    # Passing in update is better but requires changing signature across many files.
                    # For now, let's use a global access or similar if possible, or just play generic step.
                    
                    # Better: Play step based on timer
                    if not hasattr(self, 'step_timer'): self.step_timer = 0
                    self.step_timer -= dt_sec
                    if self.step_timer <= 0:
                        self.step_timer = 0.35 # Step interval
                        # Ideally we get tile type. For now, just play generic step or random
                        # We can't easily get tile type here without map reference.
                        # Let's assume generic "step" sound handled by SoundManager with randomization
                        SoundManager().play_footstep("grass") # Default to grass for now
                        
            elif self.slippery:
                # Slippery logic (Roller skates)
                mouse_pos = pygame.mouse.get_pos()
                screen_center = pygame.math.Vector2(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
                aim_vec = pygame.math.Vector2(mouse_pos) - screen_center
                if aim_vec.length() > 0:
                    self.pos += aim_vec.normalize() * 30 * dt_sec
            
            # Exhaust Logic
            mechanisms = self.inventory.get_active_mechanisms()
            exhaust_mech = next((m for m in mechanisms if m['type'] == 'exhaust'), None)
            
            if exhaust_mech:
                self.exhaust_timer -= dt_sec
                if self.exhaust_timer <= 0:
                    self.exhaust_timer = 0.2 # Spawn trail every 0.2s
                    
                    element = exhaust_mech['element']
                    dmg = self.magic_atk * 0.5 # 50% Magic Damage
                    
                    # Spawn Trail
                    trail = Trail(self.pos.x, self.pos.y, 3.0, element, dmg, self)
                    self.projectiles.append(trail)

            # Attack
            if self.is_action_pressed('basic_attack'):
                self.attack()
            
        # Projectiles
        for p in self.projectiles[:]:
            p.update(dt_sec)
            if p.duration <= 0:
                self.projectiles.remove(p)
                
        for m in self.melee_attacks[:]:
            m.update(dt_sec)
            if m.duration <= 0:
                self.melee_attacks.remove(m)
            
        # Skill Cooldowns
        for skill_id in list(self.skill_cooldowns.keys()):
            if self.skill_cooldowns[skill_id] > 0:
                self.skill_cooldowns[skill_id] = max(0, self.skill_cooldowns[skill_id] - dt_sec)

        # HP Regen
        self.hp_regen_timer += dt
        if self.hp_regen_timer >= 1000: 
            self.hp_regen_timer = 0
            self.heal(self.stats.get('hp_regen', 0))
            
        # MP Regen
        self.mp_regen_timer += dt
        if self.mp_regen_timer >= 1000: 
            self.mp_regen_timer = 0
            self.restore_mp(self.stats.get('mp_regen', 0))
            
        # Update DPS
        current_time = pygame.time.get_ticks()
        cutoff = current_time - 1000 # 1 second window
        # Keep only recent
        if self.damage_history:
             # Optimization: only filter if we have history
             self.damage_history = [x for x in self.damage_history if x[0] > cutoff]
             self.dps = sum(x[1] for x in self.damage_history)
        else:
             self.dps = 0
            
    def record_damage(self, amount):
        if amount > self.max_single_damage:
            self.max_single_damage = amount
        
        # Add to history
        current_time = pygame.time.get_ticks()
        self.damage_history.append((current_time, amount))
            
    def add_kill(self):
        self.current_combo += 1
        self.combo_timer = 5.0 # 5 seconds window
        if self.current_combo > self.max_combo:
            self.max_combo = self.current_combo

    def gain_xp(self, amount):
        self.current_xp += amount
        if self.current_xp >= self.xp_to_next_level:
            return True 
        return False
        
    def level_up(self):
        self.level += 1
        self.current_xp -= self.xp_to_next_level
        self.xp_to_next_level = int(self.xp_to_next_level * 1.2)
        heal_amount = self.stats.get('max_hp', 100) * 0.15
        self.heal(heal_amount)
        self.current_mp = self.stats.get('max_mp', 100)
    
    def handle_event(self, event, error_callback=None, camera=None):
        if self.is_action_triggered(event, 'skill_1'):
            self.selected_skill_slot = (self.selected_skill_slot - 1) % 4
        elif self.is_action_triggered(event, 'skill_2'):
            self.selected_skill_slot = (self.selected_skill_slot + 1) % 4
        elif self.is_action_triggered(event, 'dodge'):
            self.try_dodge()
        elif self.is_action_triggered(event, 'use_skill'):
            self.use_skill(error_callback)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                # Basic Attack
                self.attack(camera)
            
    def get_active_cores(self):
        """Retrieve active core effects from inventory cells."""
        cores = {
            'fire': 0,
            'water': 0,
            'lightning': 0
        }
        if hasattr(self, 'inventory') and hasattr(self.inventory, 'cells'):
            for item in self.inventory.cells:
                if item:
                    if item.id == 'core_fire': cores['fire'] += 1 + getattr(item, 'awakened_level', 0)
                    elif item.id == 'core_water': cores['water'] += 1 + getattr(item, 'awakened_level', 0)
                    elif item.id == 'core_lightning': cores['lightning'] += 1 + getattr(item, 'awakened_level', 0)
        return cores

    def attack(self, camera=None):
        if self.attack_cooldown_timer > 0: return

        mouse_pos = pygame.mouse.get_pos()
        if camera:
            target_pos = camera.unapply(pygame.math.Vector2(mouse_pos))
            aim_vec = target_pos - self.pos
        else:
            screen_center = pygame.math.Vector2(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
            aim_vec = pygame.math.Vector2(mouse_pos) - screen_center
        angle = math.atan2(aim_vec.y, aim_vec.x)
        
        color = self.data['color']
        atk_speed = self.attack_speed # Use property
        
        # Apply Status Effects to Attack Speed
        for effect in self.status_effects:
            if effect['type'] == 'overload':
                atk_speed *= 3.0 # Increase Attack Speed by 200%
            elif effect['type'] == 'haste':
                atk_speed *= 1.5
                
        self.attack_cooldown_timer = 1.0 / atk_speed
        
        # Play Sound
        if settings.game_config.get('attack_sfx_enabled', True):
            char_id = self.data['id']
            sound_name = f"attack_{char_id}"
            SoundManager().play_sound(sound_name)
        
        # Get Active Cores (Legacy for direct stats)
        cores = self.get_active_cores()
        
        # Get Active Mechanisms (New System)
        mechanisms = self.inventory.get_active_mechanisms()
        tracking_mech = next((m for m in mechanisms if m['type'] == 'tracking'), None)
        chain_mech = next((m for m in mechanisms if m['type'] == 'chain'), None)
        
        # Prepare Projectile Effects
        proj_effects = []
        knockback_bonus = 0
        on_hit_effect = None
        wet_stats = None
        
        # Apply Core Effects (Legacy)
        if cores['fire'] > 0:
            # Burn Effect
            # Enemy.update_status_effects deals 10 * intensity damage every 0.5s
            # Target: 20% ATK per second => 10% ATK per tick
            # 10 * intensity = 0.1 * ATK => intensity = 0.01 * ATK
            proj_effects.append({
                'type': 'burn',
                'duration': 3.0,
                'intensity': self.phys_atk * 0.01 * cores['fire'] # 20% ATK per level (DPS)
            })
            color = (255, 100, 50) # Tinge red
            
        if cores['water'] > 0:
            knockback_bonus = 600 * cores['water'] # Enhanced from 300 to 600
            color = (50, 100, 255) # Tinge blue
            wet_stats = {'duration': 5.0}
            
        if cores['lightning'] > 0:
            on_hit_effect = 'lightning'
            color = (255, 255, 0) # Tinge yellow
        
        # Determine tracking
        is_tracking = False
        if tracking_mech:
            is_tracking = True
            
        # Determine chain
        chain_info = None
        if chain_mech:
            chain_info = {
                'range': 100,
                'pct': 0.3,
                'element': chain_mech['element']
            }

        if self.data['id'] == 'square':
            speed = 450
            # 细胞跟踪速度减少10% (原本75 -> 减少10%即 0.9倍?) 
            # 或者是 "按照原本射的速度减少10%"? 
            # 用户描述: "加强细胞跟踪，按照原本射的速度减少10%"
            # 理解为：如果是跟踪子弹，速度为原速度的 90%。
            if is_tracking: speed = speed * 0.9 
            rng = self.stats.get('attack_range', 0)
            duration = rng / speed if speed > 0 else 0
            proj = Projectile(self.pos.x, self.pos.y, angle, speed, self.phys_atk, duration, color, "sword_wave", "physical", 
                              effects=proj_effects, knockback_force=100 + knockback_bonus,
                              is_tracking=is_tracking, chain_info=chain_info, wet_stats=wet_stats)
            proj.radius = 15 
            proj.piercing = False 
            proj.piercing_count = self.stats.get('piercing_count', 0)
            proj.damage_interval = 0.2
            if on_hit_effect: proj.on_hit_effect = on_hit_effect
            if cores['lightning'] > 0: proj.lightning_level = cores['lightning']
            self.projectiles.append(proj)
            
        elif self.data['id'] == 'triangle':
            speed = 800
            if is_tracking: speed = speed * 0.9
            split_mech = next((m for m in mechanisms if m.get('type') == 'split'), None)
            giant_mech = next((m for m in mechanisms if m.get('type') == 'giant'), None)
            
            base_damage = self.phys_atk
            duration = 2.0
            radius_mult = 2.0 if giant_mech else 1.0
            pierce_add = 3 if giant_mech else 0
            
            if split_mech:
                count = 3
                spread = math.radians(30)
                start_angle = angle - spread / 2
                step = spread / (count - 1)
                for i in range(count):
                    a = start_angle + i * step
                    dmg = base_damage * 0.6
                    if giant_mech:
                        dmg *= 1.5
                    proj = Projectile(self.pos.x, self.pos.y, a, speed, dmg, duration, color, "bullet", "physical",
                                      effects=proj_effects, knockback_force=0 + knockback_bonus,
                                      is_tracking=is_tracking, chain_info=chain_info, wet_stats=wet_stats)
                    proj.piercing_count = self.stats.get('piercing_count', 0) + pierce_add
                    proj.radius = proj.radius * radius_mult
                    if on_hit_effect: proj.on_hit_effect = on_hit_effect
                    if cores['lightning'] > 0: proj.lightning_level = cores['lightning']
                    self.projectiles.append(proj)
            else:
                dmg = base_damage * (1.5 if giant_mech else 1.0)
                proj = Projectile(self.pos.x, self.pos.y, angle, speed, dmg, duration, color, "bullet", "physical",
                                  effects=proj_effects, knockback_force=0 + knockback_bonus,
                                  is_tracking=is_tracking, chain_info=chain_info, wet_stats=wet_stats)
                proj.piercing_count = self.stats.get('piercing_count', 0) + pierce_add
                proj.radius = proj.radius * radius_mult
                if on_hit_effect: proj.on_hit_effect = on_hit_effect
                if cores['lightning'] > 0: proj.lightning_level = cores['lightning']
                self.projectiles.append(proj)
            
        elif self.data['id'] == 'circle':
            speed = 500
            if is_tracking: speed = speed * 0.9
            giant_mech = next((m for m in mechanisms if m.get('type') == 'giant'), None)
            dmg = self.magic_atk * (1.5 if giant_mech else 1.0)
            duration = 1.5
            proj = Projectile(self.pos.x, self.pos.y, angle, speed, dmg, duration, color, "magic", "magic",
                              effects=proj_effects, knockback_force=0 + knockback_bonus,
                              is_tracking=is_tracking, chain_info=chain_info, wet_stats=wet_stats)
            base_pierce = self.stats.get('piercing_count', 0)
            proj.piercing_count = base_pierce + (3 if giant_mech else 0)
            if giant_mech:
                proj.radius = proj.radius * 2.0
            if on_hit_effect: proj.on_hit_effect = on_hit_effect
            if cores['lightning'] > 0: proj.lightning_level = cores['lightning']
            self.projectiles.append(proj)

    def use_skill(self, error_callback=None):
        skill_item = self.inventory.skill_slots[self.selected_skill_slot]
        if not skill_item: return
        if self.skill_cooldowns.get(skill_item.id, 0) > 0:
            if error_callback: error_callback("冷却中!")
            print("Skill Cooldown!")
            return
        if self.current_mp < skill_item.mp_cost:
            if error_callback: error_callback("魔力不足!")
            print("Not enough MP!")
            return
        if self.skill_system.execute_skill(skill_item):
            self.current_mp -= skill_item.mp_cost
            final_cd = skill_item.cooldown * (1.0 - self.cooldown_reduction)
            self.skill_cooldowns[skill_item.id] = final_cd
            print(f"Used skill: {skill_item.name}, CD: {final_cd:.2f}s")

    def try_dodge(self):
        if self.dodge_cooldown_timer > 0 or self.is_dashing:
            return
        base_cd = 4.0
        final_cd = base_cd * (1.0 - self.cooldown_reduction)
        self.dodge_cooldown_timer = final_cd
        self.dodge_last_cd = final_cd
        
        base_distance = 90.0
        speed = 900.0
        duration = base_distance / speed
        
        move_vec = pygame.math.Vector2(0, 0)
        if self.is_action_pressed('up'): move_vec.y -= 1
        if self.is_action_pressed('down'): move_vec.y += 1
        if self.is_action_pressed('left'): move_vec.x -= 1
        if self.is_action_pressed('right'): move_vec.x += 1
        
        if move_vec.length() == 0:
            mouse_pos = pygame.mouse.get_pos()
            screen_center = pygame.math.Vector2(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
            move_vec = pygame.math.Vector2(mouse_pos) - screen_center
        if move_vec.length() == 0:
            move_vec = pygame.math.Vector2(1, 0)
        
        dir_vec = move_vec.normalize()
        self.is_dashing = True
        self.dash_timer = duration
        self.dash_velocity = dir_vec * speed
        
        self.invincible_timer = max(self.invincible_timer, 0.15)

    def heal(self, amount):
        self.current_hp = min(self.stats.get('max_hp', 100), self.current_hp + amount)
        
    def restore_mp(self, amount):
        self.current_mp = min(self.stats.get('max_mp', 100), self.current_mp + amount)

    def check_equipment_effects(self):
        # Reset flags
        self.overlord_rage = False
        self.slippery = False
        
        if not hasattr(self, 'inventory'): return
        
        for item in self.inventory.equipment.values():
            if not item: continue
            
            # 霸王血恺: 生命越低攻击越高
            if getattr(item, 'id', '') == 'equip_overlord_armor':
                self.overlord_rage = True
            
            # 滑轮鞋: 惯性滑行
            elif getattr(item, 'id', '') == 'equip_roller_skates':
                self.slippery = True
        
    def draw(self, surface, camera):
        for p in self.projectiles: p.draw(surface, camera)
        for m in self.melee_attacks: m.draw(surface, camera)
        
        # NOTE: Player entity drawing is now handled by GameRenderer.draw_entity in ui/renderer.py
        # This method might be legacy or redundant if GameRenderer calls draw_entity separately.
        # But if it is called, we should respect the new shape logic or remove it if unused.
        # Checking core/game.py, renderer.draw_entity(self.player) is called.
        # So this method might not be used for the main player body, OR it might be double drawing.
        # However, checking ui/renderer.py, it uses resource_manager to get sprites.
        # The user issue is that the shape is always square.
        # Let's check ui/renderer.py again. It checks for sprite_key = f"player_{entity.char_id}".
        # If resource_manager doesn't find the image, it falls back to shape drawing.
        # We need to ensure that:
        # 1. char_id is correct. (Player init sets it from character_data['id'])
        # 2. Resource manager has the images loaded.
        # 3. If no images, renderer.py should use entity.shape or similar.
        # Player init doesn't explicitly set self.shape based on ID, so renderer.py fallback might default to rect.
        pass
