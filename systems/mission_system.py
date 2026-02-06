import random
from data.item_data import get_random_equipment, get_random_skill, get_item_by_id

class MissionManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Base Targets
        self.base_targets = {
            'kill': 20,
            'damage_dealt': 1000,
            'damage_taken': 125
        }
        
        # Current Progress
        self.current_progress = {
            'kill': 0,
            'damage_dealt': 0,
            'damage_taken': 0
        }
        
        # Achievement Tracking
        self.total_kills = 0
        self.achievement_popup = None # {title, text, reward, timer, color}
        self.heart_awarded = False
        
        # Difficulty Scaling
        self.completions = 0
        self.difficulty_scale = 1.0
        self.growth_factor = 1.35
        
        # UI State
        self.just_completed = False
        self.last_reward_text = ""
        self.reward_timer = 0

    def get_current_target(self, key):
        return int(self.base_targets[key] * self.difficulty_scale)

    def add_kill(self, amount=1):
        self.current_progress['kill'] += amount
        self.total_kills += amount
        
        # Check Achievement: Kill 300
        if self.total_kills >= 300 and not self.heart_awarded:
            self.trigger_heart_drop()
            
        if self.game_manager.player:
            self.game_manager.player.add_kill()
        self.check_completion()

    def trigger_heart_drop(self):
        self.heart_awarded = True
        
        # Give Item
        item = get_item_by_id('heart')
        if item and self.game_manager.player:
            # Try add to inventory
            if self.game_manager.player.inventory.add_item(item):
                self.game_manager.spawn_floating_text(self.game_manager.player.pos, "获得 机械心脏", (255, 215, 0))
            else:
                self.game_manager.spawn_floating_text(self.game_manager.player.pos, "背包已满 (机械心脏)", (255, 0, 0))
        
        # Sound
        self.game_manager.sound_manager.play_sound("level_up")
        
        # Popup UI
        self.achievement_popup = {
            'title': "成就完成！",
            'text': "达成：秒杀300",
            'reward': "获得：机械心脏",
            'timer': 5.0,
            'color': (255, 215, 0) # Gold
        }

    def add_damage_dealt(self, amount):
        self.current_progress['damage_dealt'] += int(amount)
        if self.game_manager.player:
            self.game_manager.player.record_damage(amount)
        self.check_completion()

    def add_damage_taken(self, amount):
        self.current_progress['damage_taken'] += int(amount)
        self.check_completion()

    def check_completion(self):
        completed = False
        for key in self.base_targets:
            target = self.get_current_target(key)
            if self.current_progress[key] >= target:
                completed = True
                break
        
        if completed:
            self.complete_mission()

    def complete_mission(self):
        self.completions += 1
        self.give_reward()
        
        # Increase Difficulty
        self.difficulty_scale *= self.growth_factor
        
        # Reset Progress
        for key in self.current_progress:
            self.current_progress[key] = 0
            
        self.just_completed = True
        self.reward_timer = 3.0 # Show reward text for 3 seconds
        self.game_manager.sound_manager.play_sound("level_up") # Use level up sound for now

    def give_reward(self):
        player = self.game_manager.player
        luck = player.luck
        
        # Base Weights
        # 1. XP 150 (30%)
        # 2. XP 300 (25%)
        # 3. XP 500 (15%)
        # 4. Equip (15%)
        # 5. Skill (15%)
        
        rewards = [
            {'type': 'xp', 'val': 150, 'weight': 30, 'tier': 1},
            {'type': 'xp', 'val': 300, 'weight': 25, 'tier': 2},
            {'type': 'xp', 'val': 500, 'weight': 15, 'tier': 3},
            {'type': 'equip', 'weight': 15, 'tier': 3},
            {'type': 'skill', 'weight': 15, 'tier': 3}
        ]
        
        # Apply Luck Scaling
        # Higher tier gets more weight with luck
        # Simple formula: weight = base * (1 + luck * 0.1 * tier)
        # Lower tier weight reduced relative to others naturally
        
        adjusted_weights = []
        for r in rewards:
            w = r['weight']
            if r['tier'] > 1:
                w = w * (1.0 + luck * 0.1 * (r['tier'] - 1))
            adjusted_weights.append(w)
            
        # Select Reward
        choice = random.choices(rewards, weights=adjusted_weights, k=1)[0]
        
        self.last_reward_text = ""
        
        if choice['type'] == 'xp':
            amount = choice['val']
            if player.gain_xp(amount):
                self.game_manager.trigger_level_up()
            self.last_reward_text = f"任务奖励: {amount} 经验值"
            self.game_manager.spawn_floating_text(player.pos, f"+{amount} XP", (255, 215, 0))
            
        elif choice['type'] == 'equip':
            # Luck also affects item rarity inside get_random_equipment if we pass weights, 
            # but for now just get random.
            item = get_random_equipment()
            if item:
                if player.inventory.add_item(item):
                    self.last_reward_text = f"任务奖励: {item.name}"
                    self.game_manager.spawn_floating_text(player.pos, f"获得 {item.name}", (0, 255, 0))
                else:
                    self.last_reward_text = "任务奖励: 背包已满 (装备丢失)"
                    
        elif choice['type'] == 'skill':
            item = get_random_skill()
            if item:
                if player.inventory.add_item(item):
                    self.last_reward_text = f"任务奖励: {item.name}"
                    self.game_manager.spawn_floating_text(player.pos, f"获得 {item.name}", (0, 255, 0))
                else:
                    self.last_reward_text = "任务奖励: 背包已满 (技能丢失)"

    def update(self, dt):
        if self.just_completed:
            self.reward_timer -= dt / 1000.0
            if self.reward_timer <= 0:
                self.just_completed = False
                
        if self.achievement_popup:
            self.achievement_popup['timer'] -= dt / 1000.0
            if self.achievement_popup['timer'] <= 0:
                self.achievement_popup = None
