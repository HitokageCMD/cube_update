import pygame
import sys
import os
import math
import random
import json
import datetime

# Ensure project root is on sys.path when running this file directly.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Ensure project root is on sys.path when running this file directly.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import config.game_config as settings
from config.game_config import GameState, CHARACTERS, game_config, save_config, DEFAULT_CONFIG, MOUSE_LEFT, MOUSE_RIGHT, MOUSE_MIDDLE
from entities.player import Player
from entities.pickup import Pickup, XPOrb
from core.map import MapManager
from entities.interactables import Chest
from systems.combat_system import EnemyManager
from ui.renderer import GameRenderer
from ui.widgets import Camera, Button, CharacterCard, Slider, SaveSlotButton, ThemeButton, KeybindButton
from data.item_data import SKILL_ITEMS, EQUIPMENT_ITEMS, OTHER_ITEMS, CELL_ITEMS, ENEMY_INFO, REACTION_INFO, get_item_by_id
from core.item import SkillItem
from systems.upgrade_system import upgrade_system
from systems.mission_system import MissionManager
from utils.debug import DevManager
from utils.sound_manager import SoundManager
from utils.resource_manager import resource_manager
from data.attributes import STATS
from data.changelog import CHANGELOG_DATA

class FloatingText:
    def __init__(self, x, y, text, color):
        self.pos = pygame.math.Vector2(x, y)
        self.text = text
        self.color = color
        self.timer = 0
        self.duration = 1.0
        self.vel = pygame.math.Vector2(random.uniform(-50, 50), -100)
    
    def update(self, dt):
        self.timer += dt
        self.pos += self.vel * dt
        
    def is_alive(self):
        return self.timer < self.duration

class GameManager:
    def __init__(self):
        self.running = True
        self.state = GameState.SPLASH # Start with Splash
        self.settings_sub_state = "main"
        
        self.splash_timer = 0
        self.splash_duration_fade = 2.0 # Fade in time (s)
        self.splash_duration_hold = 1.0 # Hold time (s)
        self.splash_alpha = 0
        
        pygame.init()
        flags = pygame.FULLSCREEN if game_config['fullscreen'] else 0
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), flags)
        pygame.display.set_caption("方块的升级")
        
        # Initialize Resource Manager
        print("Initializing ResourceManager...")
        resource_manager.initialize()
        
        self.clock = pygame.time.Clock()
        self.sound_manager = SoundManager()
        self.renderer = GameRenderer(self.screen)
        self.mission_manager = MissionManager(self)
        
        self.floating_texts = []
        
        self.save_dir = os.path.join(os.getcwd(), "saves")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.save_slots = [None] * 3 
        self.load_saves() 

        self.rebinding_action = None 

        self.selected_character = None
        self.player = None
        # Shared camera instance from renderer
        self.camera = self.renderer.camera
        self.map_manager = MapManager()
        self.enemy_manager = EnemyManager()
        self.pickups = []
        
        self.game_time = 0
        self.tutorial_step = 0
        self.tutorial_move_dist = 0
        self.tutorial_start_pos = pygame.math.Vector2(0, 0)
        self.tutorial_transition_timer = 0
        self.tutorial_enemy = None
        
        self.game_over_timer = 0
        self.game_speed = 1.0
        
        self.show_stats_panel = False # 统计面板开关
        self.destruction_count = 0 # Track destroyed objects for Heart drop
        self.dev_mode = False # 开发者模式
        self.dev_manager = DevManager(self)
        
        # Guide
        self.guide_tabs = ['skills', 'equipment', 'cores', 'reactions', 'enemies', 'drops']
        self.guide_items = []
        self.guide_tab_index = 0
        self.guide_selected_item = None
        self.guide_scroll_y = 0
        self.guide_from_menu = False
        
        self.available_resolutions = [(800, 600), (1024, 768), (1280, 720), (1920, 1080), (1080, 1060)]
        self.current_res_index = 0
        try:
            self.current_res_index = self.available_resolutions.index(game_config['resolution'])
        except ValueError:
            self.current_res_index = 0

        self.init_ui()

    def spawn_damage_text(self, pos, amount, damage_type='physical', is_player_damage=False):
        color = (200, 200, 200) 
        
        if is_player_damage:
            color = (255, 50, 50) 
        else:
            if damage_type == 'magic': color = (50, 150, 255) 
            elif damage_type == 'true': color = (255, 215, 0) 
            elif damage_type == 'physical': color = (230, 230, 230) 
        
        amount_int = int(amount)
        if amount_int > 0:
            self.floating_texts.append(FloatingText(pos.x, pos.y, str(amount_int), color))

    def spawn_floating_text(self, pos, text, color):
        self.floating_texts.append(FloatingText(pos.x, pos.y, text, color))

    def show_error_message(self, text):
        # Center of screen or above player
        if self.player:
            pos = self.player.pos - pygame.math.Vector2(0, 50)
            self.spawn_floating_text(pos, text, (255, 100, 100))
            self.sound_manager.play_sound("error")

    def on_object_destroyed(self, obj):
        if obj.type in ['tree', 'house']:
            self.destruction_count += 1
            print(f"Destruction Count: {self.destruction_count}")
            
            if self.destruction_count % 5 == 0:
                # Drop Gene Potion Logic
                should_drop = True
                
                # 1. Check if unlocked
                if self.player and hasattr(self.player, 'inventory') and self.player.inventory.gene_unlocked:
                    should_drop = False
                
                # 2. Check if in backpack
                if should_drop and self.player and hasattr(self.player, 'inventory'):
                    for i in self.player.inventory.items:
                        if i and getattr(i, 'id', '') == 'gene_potion':
                            should_drop = False
                            break
                            
                if should_drop:
                    # Drop Gene Potion
                    from data.item_data import get_item_by_id
                    item = get_item_by_id('gene_potion')
                    if item:
                        # Spawn pickup
                        from entities.pickup import Pickup
                        # Use generic Pickup for Item
                        p = Pickup(obj.pos.x, obj.pos.y, 'item', item=item)
                        self.pickups.append(p)
                        self.spawn_floating_text(obj.pos, "掉落: 基因药水", (255, 215, 0))
                        self.sound_manager.play_sound("ui_upgrade") # Use upgrade sound for special drop

    def load_saves(self):
        for i in range(3):
            path = os.path.join(self.save_dir, f"save_{i}.json")
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.save_slots[i] = json.load(f)
                except Exception as e:
                    print(f"Error loading save {i}: {e}")
                    self.save_slots[i] = None
            else:
                self.save_slots[i] = None

    def _serialize_item(self, item):
        if item is None:
            return None
        if hasattr(item, 'to_dict'):
            return item.to_dict()
        return None

    def _deserialize_item(self, data):
        if data is None:
            return None
        if isinstance(data, str): # Legacy support for simple ID strings
            return get_item_by_id(data)
        if isinstance(data, dict):
            item_id = data.get('id')
            return get_item_by_id(item_id)
        return None

    def save_game_to_slot(self, slot_index):
        if not self.player: return
        
        data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "game_time": self.game_time,
            "char_id": self.player.data['id'],
            "char_name": self.player.data['name'],
            "level": self.player.level,
            "current_xp": self.player.current_xp,
            "xp_to_next_level": self.player.xp_to_next_level,
            "stats": self.player.stats,
            "current_hp": self.player.current_hp,
            "current_mp": self.player.current_mp,
            "pos": (self.player.pos.x, self.player.pos.y),
            "inventory": [self._serialize_item(i) for i in self.player.inventory.items],
            "equipment": {k: self._serialize_item(v) for k, v in self.player.inventory.equipment.items()},
            "cells": [self._serialize_item(i) for i in self.player.inventory.cells],
            "skill_slots": [self._serialize_item(i) for i in self.player.inventory.skill_slots],
            "inventory_state": {
                "gene_unlocked": self.player.inventory.gene_unlocked,
                "heart_slot": self._serialize_item(self.player.inventory.heart_slot)
            },
            "destruction_count": self.destruction_count,
            "camera_pos": (self.camera.pos.x, self.camera.pos.y),
            "enemies": self.enemy_manager.get_save_data()
        }
        
        path = os.path.join(self.save_dir, f"save_{slot_index}.json")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Game saved to slot {slot_index}")
            self.save_slots[slot_index] = data 
        except Exception as e:
            print(f"Error saving game: {e}")

    def load_game_from_slot(self, slot_index):
        data = self.save_slots[slot_index]
        if not data: return
        
        char_id = data['char_id']
        char_data = next((c for c in CHARACTERS if c['id'] == char_id), None)
        if not char_data:
            print("Error: Character data not found")
            return
            
        self.player = Player(char_data)
        self.player.level = data.get('level', 1)
        self.player.current_xp = data.get('current_xp', 0)
        self.player.xp_to_next_level = data.get('xp_to_next_level', 100)
        
        self.player.stats = data['stats']
        self.player.current_hp = data['current_hp']
        self.player.current_mp = data['current_mp']
        self.player.pos = pygame.math.Vector2(data['pos'][0], data['pos'][1])
        
        if 'inventory' in data:
             self.player.inventory.items = [self._deserialize_item(i) for i in data['inventory']]
        
        if 'equipment' in data:
            self.player.inventory.equipment = {k: self._deserialize_item(v) for k, v in data['equipment'].items()}
            # Apply equipment effects
            self.player.check_equipment_effects()

        if 'cells' in data:
            self.player.inventory.cells = [self._deserialize_item(i) for i in data['cells']]
            
        if 'skill_slots' in data:
            self.player.inventory.skill_slots = [self._deserialize_item(i) for i in data['skill_slots']]
        
        if 'inventory_state' in data:
            inv_state = data['inventory_state']
            self.player.inventory.gene_unlocked = inv_state.get('gene_unlocked', False)
            if 'heart_slot' in inv_state:
                self.player.inventory.heart_slot = self._deserialize_item(inv_state['heart_slot'])

        self.destruction_count = data.get('destruction_count', 0)

        self.camera.pos = pygame.math.Vector2(data['camera_pos'][0], data['camera_pos'][1])
        
        self.enemy_manager = EnemyManager()
        if 'enemies' in data:
            self.enemy_manager.load_from_data(data['enemies'])
            
        self.pickups = []
        self.game_time = data.get('game_time', 0)
        
        self.state = GameState.GAME
        self.sound_manager.play_game_bgm()
        print(f"Game loaded from slot {slot_index}")

    def layout_buttons_centered(self, buttons, start_y, gap):
        for i, btn in enumerate(buttons):
            btn.center_horizontal(settings.SCREEN_WIDTH)
            btn.rect.y = start_y + i * gap

    def init_ui(self):
        start_y = 250 # Moved down from 150 to avoid title overlap
        gap = 60 # Reduced gap slightly

        self.menu_buttons = [
            Button("开始游戏", 0, 0, 0, 0, "goto_char_select"),
            Button("继续游戏", 0, 0, 0, 0, "goto_load_game"),
            Button("游戏图鉴", 0, 0, 0, 0, "guide_from_menu"),
            Button("设置", 0, 0, 0, 0, "settings"),
            Button("版本日志", 0, 0, 0, 0, "changelog"),
            Button("创作者", 0, 0, 0, 0, "credits"),
            Button("退出游戏", 0, 0, 0, 0, "quit")
        ]
        self.layout_buttons_centered(self.menu_buttons, start_y, gap)
        
        self.back_button = Button("返回", 50, 50, 0, 0, "back")
        
        self.save_load_buttons = []
        
        self.char_card_size = 150
        char_gap = 50
        total_width = 3 * self.char_card_size + 2 * char_gap
        char_start_x = (settings.SCREEN_WIDTH - total_width) // 2
        self.char_y = int(settings.SCREEN_HEIGHT * 0.25)
        
        self.char_cards = []
        for i, char_data in enumerate(CHARACTERS):
            x = char_start_x + i * (self.char_card_size + char_gap)
            self.char_cards.append(CharacterCard(char_data, x, self.char_y, self.char_card_size))
            
        self.start_game_button = Button("开始冒险", 0, 0, 0, 0, "start_game")
        self.start_game_button.center_horizontal(settings.SCREEN_WIDTH)
        self.start_game_button.rect.y = settings.SCREEN_HEIGHT - 100
        self.start_game_button.visible = False
        
        self.settings_buttons = [
            Button("界面设置", 0, 0, 0, 0, "settings_display"),
            Button("声音设置", 0, 0, 0, 0, "settings_audio"),
            Button("控制设置", 0, 0, 0, 0, "settings_controls")
        ]
        self.layout_buttons_centered(self.settings_buttons, start_y, gap)

        self.display_buttons = [
            Button(f"分辨率: {game_config['resolution'][0]}x{game_config['resolution'][1]}", 0, 0, 0, 0, "toggle_resolution"),
            Button(f"全屏: {'开' if game_config['fullscreen'] else '关'}", 0, 0, 0, 0, "toggle_fullscreen"),
            Button(f"显示FPS: {'开' if game_config.get('show_fps', True) else '关'}", 0, 0, 0, 0, "toggle_fps"),
        ]
        self.layout_buttons_centered(self.display_buttons, start_y, gap)
        
        self.theme_button = ThemeButton(settings.SCREEN_WIDTH - 80, 50, 50, "toggle_theme")
        
        self.audio_sliders = [
            Slider(settings.SCREEN_WIDTH // 2 - 150, 200, 300, 20, 0.0, 1.0, game_config['master_volume'], "主音量"),
            Slider(settings.SCREEN_WIDTH // 2 - 150, 280, 300, 20, 0.0, 1.0, game_config['sfx_volume'], "音效"),
            Slider(settings.SCREEN_WIDTH // 2 - 150, 360, 300, 20, 0.0, 1.0, game_config['bgm_volume'], "音乐"),
            Slider(settings.SCREEN_WIDTH // 2 - 150, 440, 300, 20, 0.0, 1.0, game_config.get('ambient_volume', 1.0), "环境")
        ]
        
        self.audio_buttons = [
            Button(f"攻击音效: {'开' if game_config.get('attack_sfx_enabled', True) else '关'}", 
                   0, 0, 200, 40, "toggle_attack_sfx")
        ]
        self.layout_buttons_centered(self.audio_buttons, 520, 60)
        
        self.control_buttons = []
        kb_start_y = 130
        kb_gap = 50
        
        # 定义两列
        col1_x = settings.SCREEN_WIDTH // 2 - 220 # 左列中心
        col2_x = settings.SCREEN_WIDTH // 2 + 220 # 右列中心
        
        # 左列动作 (移动 + 攻击)
        col1_actions = ['basic_attack', 'up', 'down', 'left', 'right']
        # 右列动作 (技能 + 功能)
        col2_actions = ['dodge', 'skill_1', 'skill_2', 'use_skill', 'inventory', 'pause']
        
        labels = {
            'basic_attack': '普通攻击',
            'up': '向上', 'down': '向下', 'left': '向左', 'right': '向右',
            'dodge': '闪避',
            'skill_1': '切换技能(左)', 'skill_2': '切换技能(右)', 'use_skill': '使用技能',
            'inventory': '物品栏', 'pause': '暂停'
        }
        
        # 生成左列
        for i, action in enumerate(col1_actions):
            btn = KeybindButton(0, 0, 350, 40, action, labels[action], f"rebind:{action}")
            btn.rect.centerx = col1_x
            btn.rect.y = kb_start_y + i * kb_gap
            self.control_buttons.append(btn)
            
        # 生成右列
        for i, action in enumerate(col2_actions):
            btn = KeybindButton(0, 0, 350, 40, action, labels[action], f"rebind:{action}")
            btn.rect.centerx = col2_x
            btn.rect.y = kb_start_y + i * kb_gap
            self.control_buttons.append(btn)

        # 重置按钮
        reset_btn = Button("重置默认", 0, 0, 200, 40, "reset_controls")
        reset_btn.center_horizontal(settings.SCREEN_WIDTH)
        max_rows = max(len(col1_actions), len(col2_actions))
        reset_btn.rect.y = kb_start_y + max_rows * kb_gap + 30
        self.control_buttons.append(reset_btn)

        self.pause_buttons = [
            Button("继续游戏", 0, 0, 0, 0, "resume_game"),
            Button("保存游戏", 0, 0, 0, 0, "goto_save_game"),
            Button("设置", 0, 0, 0, 0, "settings_ingame"),
            Button("返回主菜单", 0, 0, 0, 0, "back_to_menu"),
            Button("退出桌面", 0, 0, 0, 0, "quit")
        ]
        self.pause_buttons.append(Button("游戏图鉴", 0, 0, 0, 0, "guide_ingame"))
        self.layout_buttons_centered(self.pause_buttons, 200, 60)

        self.confirm_save_buttons = [
            Button("覆盖", 0, 0, 0, 0, "confirm_save"),
            Button("取消", 0, 0, 0, 0, "cancel_save")
        ]
        dialog_y = (settings.SCREEN_HEIGHT - 250) // 2
        btn_y = dialog_y + 160
        self.confirm_save_buttons[0].rect.center = (settings.SCREEN_WIDTH // 2 - 80, btn_y)
        self.confirm_save_buttons[1].rect.center = (settings.SCREEN_WIDTH // 2 + 80, btn_y)
        
        self.confirm_slot_index = -1

    def update_guide_items(self):
        tab = self.guide_tabs[self.guide_tab_index]
        self.guide_items = []
        
        if tab == 'reactions':
             # Reactions are hardcoded for now or we iterate REACTION_INFO
             self.guide_items = list(REACTION_INFO.values())
        elif tab == 'skills':
             self.guide_items = list(SKILL_ITEMS.values())
        elif tab == 'equipment':
             self.guide_items = list(EQUIPMENT_ITEMS.values())
        elif tab == 'cores':
             self.guide_items = list(CELL_ITEMS.values())
        elif tab == 'enemies':
             self.guide_items = list(ENEMY_INFO.values())
        elif tab == 'drops':
             self.guide_items = [1, 1, 1, 1, 1, 1]

    def start_new_game(self, char_data):
        self.player = Player(char_data)
        self.camera.pos = pygame.math.Vector2(self.player.pos)
        self.game_time = 0
        self.map_manager = MapManager() # Reset map
        self.enemy_manager = EnemyManager() 
        self.pickups = []
        
        # Reset Mission Manager
        self.mission_manager = MissionManager(self)
        
        # Check Tutorial
        if not game_config.get('tutorial_completed', False):
            self.state = GameState.TUTORIAL
            self.tutorial_step = 0
            self.tutorial_move_dist = 0
            self.tutorial_start_pos = pygame.math.Vector2(self.player.pos)
            
            # Give a skill for tutorial purposes
            skill = get_item_by_id('skill_fan_shot')
            if skill:
                # Find first empty skill slot
                added_to_slot = False
                for i in range(len(self.player.inventory.skill_slots)):
                    if self.player.inventory.skill_slots[i] is None:
                        self.player.inventory.skill_slots[i] = skill
                        added_to_slot = True
                        break
                
                # If no slot available (unlikely), add to backpack
                if not added_to_slot:
                    self.player.inventory.add_item(skill)
        else:
            self.state = GameState.GAME
            
        self.sound_manager.play_game_bgm()

    def trigger_level_up(self, skip_anim=False):
        if skip_anim:
            self.state = GameState.LEVEL_UP
            self.generate_upgrades()
            self.sound_manager.play_sound("level_up")
        else:
            self.state = GameState.LEVEL_UP_ANIM
            self.level_up_timer = 0
            self.level_up_duration = 1500 
            self.generate_upgrades()
            self.sound_manager.play_sound("level_up")

    def generate_upgrades(self):
        self.upgrade_choices = upgrade_system.generate_upgrade_options(self.player)

    def apply_upgrade(self, upgrade):
        upgrade_system.apply_upgrade(self.player, upgrade['attr'], upgrade['value'])
        self.state = GameState.GAME
        self.player.level_up()
        self.sound_manager.play_sound("ui_upgrade")
        
        # Check for overflow XP (Directly upgrade if still enough XP)
        if self.player.current_xp >= self.player.xp_to_next_level:
            self.trigger_level_up(skip_anim=True)

    def handle_input(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            
            if self.rebinding_action:
                # 鼠标绑定处理
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_code = 0
                    if event.button == 1: mouse_code = MOUSE_LEFT
                    elif event.button == 2: mouse_code = MOUSE_MIDDLE
                    elif event.button == 3: mouse_code = MOUSE_RIGHT
                    
                    if mouse_code != 0:
                        print(f"DEBUG: Binding {self.rebinding_action} to Mouse {mouse_code}")
                        # 冲突清除
                        for action, key in game_config['key_bindings'].items():
                            if key == mouse_code and action != self.rebinding_action:
                                print(f"DEBUG: Clearing conflict for {action}")
                                game_config['key_bindings'][action] = 0
                                
                        game_config['key_bindings'][self.rebinding_action] = mouse_code
                        settings.save_config()
                        
                        self.rebinding_action = None
                        for btn in self.control_buttons:
                            btn.waiting_for_input = False
                        return # 阻止后续 UI 点击

                # 键盘绑定处理
                if event.type == pygame.KEYDOWN:
                    print(f"DEBUG: Key pressed: {event.key}, Name: {pygame.key.name(event.key)}")
                    if event.key != pygame.K_ESCAPE:
                        # 忽略未知按键
                        if event.key == 0:
                            print("DEBUG: Ignored key 0")
                            return

                        # 冲突清除
                        for action, key in game_config['key_bindings'].items():
                            if key == event.key and action != self.rebinding_action:
                                print(f"DEBUG: Clearing conflict for {action}")
                                game_config['key_bindings'][action] = 0 
                                
                        print(f"DEBUG: Binding {self.rebinding_action} to {event.key}")
                        game_config['key_bindings'][self.rebinding_action] = event.key
                        settings.save_config()
                    else:
                        print("DEBUG: Rebind cancelled (ESCAPE)")
                        
                    self.rebinding_action = None
                    
                    for btn in self.control_buttons:
                        btn.waiting_for_input = False
                    return 
            
            if self.state == GameState.SPLASH:
                # Ignore all inputs except Quit (already handled above)
                pass

            elif self.state == GameState.MENU:
                for btn in self.menu_buttons:
                    action = btn.check_click(event)
                    if action:
                        if action == "start_game": self.state = GameState.CHAR_SELECT
                        elif action == "goto_char_select": self.state = GameState.CHAR_SELECT
                        elif action == "goto_load_game":
                            self.state = GameState.LOAD_GAME
                            self.save_load_buttons = []
                            start_y = 150
                            for i, save_data in enumerate(self.save_slots):
                                btn = SaveSlotButton(0, 0, 400, 100, i, save_data, f"load_slot_{i}")
                                btn.center_horizontal(settings.SCREEN_WIDTH)
                                btn.rect.y = start_y + i * 120
                                self.save_load_buttons.append(btn)
                        elif action == "guide_from_menu":
                            self.state = GameState.GUIDE
                            self.guide_from_menu = True
                            self.guide_tab_index = 0
                            self.guide_selected_item = None
                            self.guide_scroll_y = 0
                            self.update_guide_items()
                        elif action == "settings": self.state = GameState.SETTINGS; self.settings_sub_state = "main"
                        elif action == "changelog": self.state = GameState.CHANGELOG
                        elif action == "donate": self.state = GameState.DONATE
                        elif action == "quit": self.running = False
                        elif action == "credits": self.state = GameState.CREDITS
            
            elif self.state == GameState.CHAR_SELECT:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                
                action = self.back_button.check_click(event)
                if action == "back": self.state = GameState.MENU
                
                for card in self.char_cards:
                    if card.check_click(event):
                        for c in self.char_cards: c.selected = False
                        card.selected = True
                        self.selected_character = card.data
                        self.start_game_button.visible = True
                        
                action = self.start_game_button.check_click(event)
                if action == "start_game":
                    if self.selected_character:
                        self.start_new_game(self.selected_character)

            elif self.state == GameState.GAME:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check stats toggle click
                    # Access HUD renderer via self.renderer.hud
                    if self.renderer.hud.stats_toggle_rect and self.renderer.hud.stats_toggle_rect.collidepoint(event.pos):
                        self.renderer.hud.show_stats = not self.renderer.hud.show_stats

                kb = game_config['key_bindings']
                if event.type == pygame.KEYDOWN:
                    if event.key == kb['pause']:
                        self.state = GameState.PAUSED
                    elif event.key == kb['inventory']:
                        self.state = GameState.INVENTORY
                    elif event.key == kb.get('stats', pygame.K_TAB):
                        self.show_stats_panel = not self.show_stats_panel
                    
                    # Developer Mode Keys
                    elif event.key == pygame.K_F4:
                        self.state = GameState.DEV_PANEL
                        self.dev_manager.update_ui()

                    # Interact (F)
                    elif event.key == pygame.K_f:
                        obstacles = self.map_manager.get_obstacles()
                        for obs in obstacles:
                            if isinstance(obs, Chest):
                                dist = (obs.pos - self.player.pos).length()
                                if dist < obs.interact_radius:
                                    obs.interact(self.player, self)
                                    break
                                    
                if self.player:
                    self.player.handle_event(event, self.show_error_message, self.camera)

            elif self.state == GameState.DEV_PANEL:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                    self.state = GameState.GAME
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.GAME
                else:
                    self.dev_manager.handle_input(event)

            elif self.state == GameState.TUTORIAL:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.PAUSED
                
                # Tutorial Step 3: Finish
                if self.tutorial_step == 3:
                     if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                         game_config['tutorial_completed'] = True
                         settings.save_config()
                         self.state = GameState.GAME
                
                # Pass input to player for movement/attack
                if self.player:
                    self.player.handle_event(event, self.show_error_message)

            elif self.state == GameState.PAUSED:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.GAME
                
                for btn in self.pause_buttons:
                    action = btn.check_click(event)
                    if action == "resume_game": self.state = GameState.GAME
                    elif action == "guide_ingame":
                        self.state = GameState.GUIDE
                        self.guide_from_menu = False
                        self.guide_tab_index = 0
                        self.guide_selected_item = None
                        self.guide_scroll_y = 0
                        self.update_guide_items()
                    elif action == "goto_save_game":
                        self.state = GameState.SAVE_GAME
                        self.save_load_buttons = []
                        start_y = 150
                        for i, save_data in enumerate(self.save_slots):
                            btn = SaveSlotButton(0, 0, 400, 100, i, save_data, f"save_slot_{i}")
                            btn.center_horizontal(settings.SCREEN_WIDTH)
                            btn.rect.y = start_y + i * 120
                            self.save_load_buttons.append(btn)
                    elif action == "settings_ingame": self.state = GameState.SETTINGS; self.settings_sub_state = "main"
                    elif action == "back_to_menu": 
                        self.state = GameState.MENU
                        self.sound_manager.play_menu_bgm()
                    elif action == "quit": self.running = False

            elif self.state == GameState.SAVE_GAME:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.PAUSED
                
                action = self.back_button.check_click(event)
                if action == "back": self.state = GameState.PAUSED
                
                for btn in self.save_load_buttons:
                    action = btn.check_click(event)
                    if action and action.startswith("save_slot_"):
                        slot_index = int(action.split("_")[-1])
                        
                        if self.save_slots[slot_index]:
                            self.state = GameState.SAVE_CONFIRM
                            self.confirm_slot_index = slot_index
                        else:
                            self.save_game_to_slot(slot_index)
                            btn.save_data = self.save_slots[slot_index]
                            btn.set_text("", resize=False) 

            elif self.state == GameState.SAVE_CONFIRM:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.SAVE_GAME
                
                for btn in self.confirm_save_buttons:
                    action = btn.check_click(event)
                    if action == "confirm_save":
                        self.save_game_to_slot(self.confirm_slot_index)
                        for b in self.save_load_buttons:
                             if b.slot_index == self.confirm_slot_index:
                                 b.save_data = self.save_slots[self.confirm_slot_index]
                                 b.set_text("", resize=False)
                        self.state = GameState.SAVE_GAME
                    elif action == "cancel_save":
                        self.state = GameState.SAVE_GAME

            elif self.state == GameState.LOAD_GAME:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                
                action = self.back_button.check_click(event)
                if action == "back": self.state = GameState.MENU
                
                for btn in self.save_load_buttons:
                    action = btn.check_click(event)
                    if action and action.startswith("load_slot_"):
                        slot_index = int(action.split("_")[-1])
                        if self.save_slots[slot_index]: 
                            self.load_game_from_slot(slot_index)

            elif self.state == GameState.SETTINGS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.settings_sub_state == "main":
                        if self.player: self.state = GameState.PAUSED
                        else: self.state = GameState.MENU
                    else:
                        self.settings_sub_state = "main"

                action = self.back_button.check_click(event)
                if action == "back": 
                    if self.player: self.state = GameState.PAUSED
                    else: self.state = GameState.MENU
                
                if self.settings_sub_state == "main":
                    for btn in self.settings_buttons:
                        action = btn.check_click(event)
                        if action == "settings_display": self.settings_sub_state = "display"
                        elif action == "settings_audio": self.settings_sub_state = "audio"
                        elif action == "settings_controls": self.settings_sub_state = "controls"
                
                elif self.settings_sub_state == "display":
                    for btn in self.display_buttons:
                        action = btn.check_click(event)
                        if action == "toggle_resolution":
                            self.current_res_index = (self.current_res_index + 1) % len(self.available_resolutions)
                            res = self.available_resolutions[self.current_res_index]
                            game_config['resolution'] = res
                            btn.set_text(f"分辨率: {res[0]}x{res[1]}")
                            settings.SCREEN_WIDTH = res[0]
                            settings.SCREEN_HEIGHT = res[1]
                            # Respect fullscreen flag when changing resolution
                            flags = pygame.FULLSCREEN if game_config['fullscreen'] else 0
                            self.screen = pygame.display.set_mode(res, flags)
                            self.init_ui()
                            settings.save_config()
                            
                        elif action == "toggle_fullscreen":
                            game_config['fullscreen'] = not game_config['fullscreen']
                            btn.set_text(f"全屏: {'开' if game_config['fullscreen'] else '关'}")
                            flags = pygame.FULLSCREEN if game_config['fullscreen'] else 0
                            self.screen = pygame.display.set_mode(game_config['resolution'], flags)
                            settings.save_config()

                        elif action == "toggle_fps":
                            game_config['show_fps'] = not game_config.get('show_fps', True)
                            btn.set_text(f"显示FPS: {'开' if game_config['show_fps'] else '关'}")
                            settings.save_config()
                    
                    action = self.theme_button.check_click(event)
                    if action == "toggle_theme":
                        game_config['theme'] = 'dark' if game_config['theme'] == 'light' else 'light'
                        settings.save_config()

                elif self.settings_sub_state == "audio":
                    for slider in self.audio_sliders:
                        if slider.handle_event(event):
                            if slider.label_text == "主音量": game_config['master_volume'] = slider.value
                            elif slider.label_text == "音效": game_config['sfx_volume'] = slider.value
                            elif slider.label_text == "音乐": game_config['bgm_volume'] = slider.value
                            elif slider.label_text == "环境": game_config['ambient_volume'] = slider.value
                            settings.save_config()
                            self.sound_manager.update_volumes()

                    for btn in self.audio_buttons:
                        action = btn.check_click(event)
                        if action == "toggle_attack_sfx":
                            game_config['attack_sfx_enabled'] = not game_config.get('attack_sfx_enabled', True)
                            btn.set_text(f"攻击音效: {'开' if game_config['attack_sfx_enabled'] else '关'}")
                            settings.save_config()
                
                elif self.settings_sub_state == "controls":
                    for btn in self.control_buttons:
                        action = btn.check_click(event)
                        
                        if action == "reset_controls":
                            game_config['key_bindings'] = DEFAULT_CONFIG['key_bindings'].copy()
                            settings.save_config()
                            continue

                        if action and action.startswith("rebind:"): 
                            self.rebinding_action = action.split(":")[1]
                            if hasattr(btn, 'waiting_for_input'):
                                btn.waiting_for_input = True
                            for other in self.control_buttons:
                                if other != btn and hasattr(other, 'waiting_for_input'): 
                                    other.waiting_for_input = False

            elif self.state == GameState.INVENTORY:
                kb = game_config['key_bindings']
                if event.type == pygame.KEYDOWN:
                    if event.key == kb['inventory'] or event.key == pygame.K_ESCAPE:
                        self.state = GameState.GAME
                
                if self.player:
                    self.player.inventory.handle_event(event, self.screen)

            elif self.state == GameState.LEVEL_UP:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    card_w = 250
                    card_h = 350
                    gap = 50
                    total_w = 3 * card_w + 2 * gap
                    start_x = (settings.SCREEN_WIDTH - total_w) // 2
                    start_y = (settings.SCREEN_HEIGHT - card_h) // 2
                    
                    mouse_pos = pygame.mouse.get_pos()
                    
                    for i, upgrade in enumerate(self.upgrade_choices):
                        x = start_x + i * (card_w + gap)
                        rect = pygame.Rect(x, start_y, card_w, card_h)
                        
                        if rect.collidepoint(mouse_pos):
                            self.apply_upgrade(upgrade)
                            break

            elif self.state == GameState.CHANGELOG:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                
                action = self.back_button.check_click(event)
                if action == "back": self.state = GameState.MENU

            elif self.state == GameState.DONATE:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                
                action = self.back_button.check_click(event)
                if action == "back": self.state = GameState.MENU

            elif self.state == GameState.CREDITS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                
                action = self.back_button.check_click(event)
                if action == "back": self.state = GameState.MENU

            elif self.state == GameState.GUIDE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.guide_from_menu:
                            self.state = GameState.MENU
                        else:
                            self.state = GameState.PAUSED
                    
                    # Tab Switch
                    elif event.key == pygame.K_q:
                        self.guide_tab_index = (self.guide_tab_index - 1) % len(self.guide_tabs)
                        self.update_guide_items()
                        self.guide_selected_item = None
                        self.guide_scroll_y = 0
                    elif event.key == pygame.K_e:
                        self.guide_tab_index = (self.guide_tab_index + 1) % len(self.guide_tabs)
                        self.update_guide_items()
                        self.guide_selected_item = None
                        self.guide_scroll_y = 0

                action = self.back_button.check_click(event)
                if action == "back": 
                    if self.guide_from_menu:
                        self.state = GameState.MENU
                    else:
                        self.state = GameState.PAUSED
                
                # Handle Tab Clicks
                tab_w = 120
                tab_h = 40
                total_tabs_width = len(self.guide_tabs) * tab_w + (len(self.guide_tabs) - 1) * 10
                start_x = (settings.SCREEN_WIDTH - total_tabs_width) // 2
                start_y = 80
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left Click
                        # Tabs
                        for i in range(len(self.guide_tabs)):
                            x = start_x + i * (tab_w + 10)
                            rect = pygame.Rect(x, start_y, tab_w, tab_h)
                            if rect.collidepoint(event.pos):
                                self.guide_tab_index = i
                                self.update_guide_items()
                                self.guide_selected_item = None
                                self.guide_scroll_y = 0
                                self.sound_manager.play_sound("ui_click")
                                break
                        
                        # Grid Items (if not reactions or drops)
                        if self.guide_tabs[self.guide_tab_index] not in ['reactions', 'drops']:
                            content_y = start_y + tab_h + 20
                            slot_size = 60
                            gap = 15
                            cols = 6
                            offset_y = -self.guide_scroll_y
                            
                            for i, item in enumerate(self.guide_items):
                                col = i % cols
                                row = i // cols
                                x = 50 + 20 + col * (slot_size + gap)
                                y = content_y + 20 + row * (slot_size + gap) + offset_y
                                
                                rect = pygame.Rect(x, y, slot_size, slot_size)
                                # Clip check roughly
                                if y + slot_size > content_y: 
                                    if rect.collidepoint(event.pos):
                                        self.guide_selected_item = item
                                        self.sound_manager.play_sound("ui_click")
                                        break

                    elif event.button == 4: # Scroll Up
                        self.guide_scroll_y = max(0, self.guide_scroll_y - 30)
                    elif event.button == 5: # Scroll Down
                        # Calculate max scroll
                        if self.guide_tabs[self.guide_tab_index] in ['reactions', 'drops']:
                             total_h = len(self.guide_items) * 80 + 40
                             view_h = settings.SCREEN_HEIGHT - 150
                             max_scroll = max(0, total_h - view_h)
                             self.guide_scroll_y = min(max_scroll, self.guide_scroll_y + 30)
                        else:
                            cols = 6
                            total_rows = (len(self.guide_items) + cols - 1) // cols
                            total_height = total_rows * (60 + 15)
                            view_h = settings.SCREEN_HEIGHT - (start_y + tab_h + 20) - 50
                            max_scroll = max(0, total_height - view_h + 40)
                            self.guide_scroll_y = min(max_scroll, self.guide_scroll_y + 30)

            elif self.state == GameState.GAME_OVER:
                if self.game_over_timer > 1.0:
                    if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                        self.state = GameState.MENU

    def update(self, dt):
        # Apply Game Speed
        dt = dt * self.game_speed
        dt_sec = dt / 1000.0
        
        if self.state == GameState.SPLASH:
            # Update splash animation
            self.renderer.update_splash(dt_sec)
            
            if self.renderer.is_splash_finished():
                self.state = GameState.MENU
                self.sound_manager.play_menu_bgm()

        if self.state == GameState.GAME:
            if self.player:
                self.player.update(dt)
                
                # Check collision BEFORE camera update to prevent jitter
                self.map_manager.update(self.player.pos)
                self.map_manager.check_collision(self.player)
                
                # Update Camera AFTER player position is finalized
                target_zoom = 1.0
                self.camera.target_zoom = target_zoom
                self.camera.update(self.player.pos, dt)
                
                # Update Ambience based on biome
                biome = self.map_manager.get_biome_at(self.player.pos)
                self.sound_manager.set_ambience(biome)
                
                # Pass map_manager to player update for accurate footsteps? 
                # Or just update footsteps here?
                # Player update is already called. Let's patch footstep logic in player update or here.
                # Actually, SoundManager.play_footstep needs biome/tile type.
                # Player.update plays "grass" default. We can improve this if we pass map_manager to player.update
                # But changing signature is risky.
                # Let's override the footstep logic in Player by monkey patching or just accept default for now.
                # To do it properly, we should update Player.update signature.
                # For now, let's just rely on the default added in previous step.
                
                self.game_time += dt / 1000.0
                game_time_min = self.game_time / 60.0
                
                self.mission_manager.update(dt)

                self.enemy_manager.update(dt, self.player, self, game_time_min, self.map_manager, self.spawn_damage_text, on_destroy_callback=self.on_object_destroyed)
                
                if self.player.current_hp <= 0:
                    self.state = GameState.GAME_OVER
                    self.game_over_timer = 0
                    self.sound_manager.play_sound("death")
                    print("Game Over")

                pickup_range = self.player.pickup_range
                for p in self.pickups[:]:
                    if p.update(dt_sec, self.player.pos, pickup_range):
                        if p.type == 'xp':
                            self.sound_manager.play_sound("xp_pickup")
                            if self.player.gain_xp(p.amount):
                                self.trigger_level_up()
                            self.pickups.remove(p)
                        elif p.type == 'item':
                            if self.player.inventory.add_item(p.item):
                                self.floating_texts.append(FloatingText(self.player.pos.x, self.player.pos.y - 50, f"获得 {p.item.name}", (255, 255, 0)))
                                self.pickups.remove(p)
                            else:
                                self.floating_texts.append(FloatingText(self.player.pos.x, self.player.pos.y - 50, "背包已满", (255, 0, 0)))
                                # Don't remove, let player handle it (maybe move away)

                for ft in self.floating_texts[:]:
                    ft.update(dt_sec)
                    if not ft.is_alive():
                        self.floating_texts.remove(ft)

        elif self.state == GameState.TUTORIAL:
            # Define dt_sec for tutorial state
            
            if self.player:
                self.player.update(dt)
                
                target_zoom = 1.0
                self.camera.target_zoom = target_zoom
                self.camera.update(self.player.pos, dt) # Ensure camera updates with player pos
                self.map_manager.update(self.player.pos)
                self.map_manager.check_collision(self.player)
                
                # Update enemies (but disable auto-spawning)
                # Use current game time (0 in tutorial) for scaling
                self.enemy_manager.update(dt, self.player, self, 0, self.map_manager, self.spawn_damage_text, spawn_enabled=False)
                
                # Step Logic
                if self.tutorial_step == 0: # Move
                    dist = self.player.pos.distance_to(self.tutorial_start_pos)
                    if dist > 50: # Moved enough (Reduced from 300)
                         if self.tutorial_transition_timer == 0:
                             self.tutorial_transition_timer = 0.5
                         
                         self.tutorial_transition_timer -= dt_sec
                         if self.tutorial_transition_timer <= 0:
                             self.tutorial_step = 1
                             self.tutorial_transition_timer = 0
                             # Spawn Enemy
                             self.enemy_manager.spawn_enemy(self.player, 0, force_type='square')
                             if self.enemy_manager.enemies:
                                 self.tutorial_enemy = self.enemy_manager.enemies[-1]
                                 # Set 5% HP (Base HP for square is approx 20 at level 1, but let's use max_hp from obj)
                                 self.tutorial_enemy.current_hp = max(1, self.tutorial_enemy.max_hp * 0.05)
                                 # Move closer (fixed offset)
                                 self.tutorial_enemy.pos = self.player.pos + pygame.math.Vector2(250, 0)
                             
                elif self.tutorial_step == 1: # Attack
                    # Check if enemy is dead
                    if self.tutorial_enemy:
                        if self.tutorial_enemy not in self.enemy_manager.enemies or self.tutorial_enemy.current_hp <= 0:
                            if self.tutorial_transition_timer == 0:
                                self.tutorial_transition_timer = 0.5
                    
                    if self.tutorial_transition_timer > 0:
                        self.tutorial_transition_timer -= dt_sec
                        if self.tutorial_transition_timer <= 0:
                            self.tutorial_step = 2
                            self.tutorial_transition_timer = 0
                            
                elif self.tutorial_step == 2: # Skill
                     # Check for skill key (F usually)
                     # Check cooldowns to detect usage
                     skill_used = False
                     for skill in self.player.inventory.skill_slots:
                         if skill and self.player.skill_cooldowns.get(skill.id, 0) > skill.cooldown - 0.5:
                             skill_used = True
                             break
                     
                     if skill_used:
                         if self.tutorial_transition_timer == 0:
                             self.tutorial_transition_timer = 0.5
                             
                     if self.tutorial_transition_timer > 0:
                        self.tutorial_transition_timer -= dt_sec
                        if self.tutorial_transition_timer <= 0:
                             self.tutorial_step = 3
                             self.tutorial_transition_timer = 0
            
            # Update floating texts if any (e.g. from attack)
            dt_sec = dt / 1000.0
            for ft in self.floating_texts[:]:
                ft.update(dt_sec)
                if not ft.is_alive():
                    self.floating_texts.remove(ft)

        elif self.state == GameState.LEVEL_UP_ANIM:
            self.level_up_timer += dt
            if self.level_up_timer >= self.level_up_duration:
                self.state = GameState.LEVEL_UP

        elif self.state == GameState.GAME_OVER:
            self.game_over_timer += dt / 1000.0

    def draw(self):
        # 1. Fill background with base grass color to prevent black lines
        base_grass_color = (106, 190, 48) # Match the grass tile color
        self.screen.fill(base_grass_color)
        
        draw_world_states = [
            GameState.GAME, GameState.PAUSED, GameState.LEVEL_UP_ANIM, 
            GameState.LEVEL_UP, GameState.GAME_OVER, GameState.INVENTORY,
            GameState.TUTORIAL, GameState.DEV_PANEL
        ]
        
        if self.state in draw_world_states:
            self.map_manager.draw(self.screen, self.camera)
            
            if self.player:
                self.renderer.draw_entity(self.player)
                for p in self.player.projectiles:
                    self.renderer.draw_projectile(p)
                for m in self.player.melee_attacks:
                    self.renderer.draw_melee_swing(self.player, m['angle'], m['progress'])
            
            for enemy in self.enemy_manager.enemies:
                self.renderer.draw_entity(enemy)
            for p in self.enemy_manager.enemy_projectiles:
                self.renderer.draw_projectile(p)
            
            for p in self.pickups:
                self.renderer.draw_pickup(p)

            self.renderer.draw_floating_texts(self.floating_texts)

            if self.state in [GameState.GAME, GameState.PAUSED, GameState.LEVEL_UP_ANIM, GameState.INVENTORY, GameState.TUTORIAL]:
                 if self.player:
                    self.renderer.draw_player_ui(self.player)
                    
                    # Draw Game Time
                    game_time_min = self.game_time / 60.0
                    self.renderer.draw_game_time(game_time_min)
                    
                    # Draw FPS
                    self.renderer.hud.draw_fps(self.clock)
                    
                    # Draw Mission UI
                    self.renderer.draw_mission_ui(self.mission_manager)
                    
                    # Draw Achievement Popup
                    self.renderer.draw_achievement_popup(self.mission_manager)
                    
                    if self.show_stats_panel:
                        self.renderer.draw_statistics_panel(self)

        if self.state == GameState.MENU:
            self.renderer.draw_menu(self.menu_buttons)
            
        elif self.state == GameState.SPLASH:
            self.renderer.draw_splash()
            
        elif self.state == GameState.CHAR_SELECT:
            self.renderer.draw_char_select(
                self.char_cards, self.start_game_button, self.back_button
            )
            
        elif self.state == GameState.LEVEL_UP_ANIM:
             self.renderer.draw_level_up_anim(self.level_up_timer / self.level_up_duration)
             
        elif self.state == GameState.LEVEL_UP:
             self.renderer.draw_level_up_choices(self.upgrade_choices)
             
        elif self.state == GameState.PAUSED:
             self.renderer.draw_pause(self.pause_buttons)
             
        if self.state in [GameState.SAVE_GAME, GameState.LOAD_GAME]:
             self.renderer.draw_save_load(self.state.name, self.save_load_buttons, self.back_button)
        
        elif self.state == GameState.SAVE_CONFIRM:
             self.renderer.draw_save_load("SAVE_GAME", self.save_load_buttons, self.back_button)
             self.renderer.draw_save_confirm("save", self.confirm_slot_index, self.confirm_save_buttons[0], self.confirm_save_buttons[1])
             
        elif self.state == GameState.INVENTORY:
             if self.player:
                 self.renderer.draw_inventory(self.player.inventory)

        elif self.state == GameState.SETTINGS:
             self.renderer.draw_settings(
                self.settings_sub_state, 
                self.back_button,
                main_buttons=self.settings_buttons,
                display_buttons=self.display_buttons,
                theme_btn=self.theme_button,
                audio_sliders=self.audio_sliders,
                audio_buttons=self.audio_buttons,
                control_buttons=self.control_buttons
             )
             
        elif self.state == GameState.GAME_OVER:
            self.renderer.draw_game_over(self.game_time, [])

        elif self.state == GameState.CHANGELOG:
            self.renderer.draw_changelog(0, self.back_button)

        elif self.state == GameState.DONATE:
            self.renderer.draw_donate(self.back_button)

        elif self.state == GameState.GUIDE:
            self.renderer.draw_guide(
                self.guide_tabs, 
                self.guide_tab_index,
                self.guide_items,
                self.guide_selected_item,
                self.guide_scroll_y,
                self.back_button
            )

        elif self.state == GameState.CREDITS:
            self.renderer.draw_credits(self.back_button)

        elif self.state == GameState.DEV_PANEL:
            self.renderer.draw_dev_panel(self.dev_manager)

    def run(self):
        while self.running:
            dt = self.clock.tick(60) 
            self.handle_input()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
