import os
import sys
import json
import pygame
import copy
from enum import Enum

# 版本号
GAME_VERSION = "v0.0.4"
VERSION = GAME_VERSION

# 资源路径处理 (PyInstaller 兼容)
def resource_path(relative_path):
    """ 获取资源的绝对路径，兼容开发环境和 PyInstaller 打包环境 """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    
    # Use the directory of the current script (config/game_config.py) as the base
    # Move up one level to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)

# 资源目录定义
ASSETS_DIR = resource_path("assets")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

PLAYER_IMG_DIR = os.path.join(SPRITES_DIR, "player")
ENEMY_IMG_DIR = os.path.join(SPRITES_DIR, "enemy")
MAP_IMG_DIR = os.path.join(SPRITES_DIR, "map")
ITEMS_IMG_DIR = os.path.join(SPRITES_DIR, "items")
UI_IMG_DIR = os.path.join(SPRITES_DIR, "ui")
PROJECTILE_IMG_DIR = os.path.join(SPRITES_DIR, "projectile")
VIDEO_DIR = os.path.join(ASSETS_DIR, "videos")

# Core Assets
CORE_IMG_DIR = os.path.join(SPRITES_DIR, "cores")
CORE_ASSETS = {
    'core_fire': {'icon': os.path.join(CORE_IMG_DIR, "fire.png"), 'sfx': "fire_hit"},
    'core_water': {'icon': os.path.join(CORE_IMG_DIR, "water.png"), 'sfx': "water_hit"},
    'core_lightning': {'icon': os.path.join(CORE_IMG_DIR, "lightning.png"), 'sfx': "lightning_hit"}
}

# 游戏状态
class GameState(Enum):
    MENU = 1
    CHAR_SELECT = 2
    GAME = 3
    PAUSED = 4
    SETTINGS = 5
    CREDITS = 6
    INVENTORY = 7
    LOAD_GAME = 8
    SAVE_GAME = 9
    LEVEL_UP = 10
    GAME_OVER = 11
    LEVEL_UP_ANIM = 12
    SAVE_CONFIRM = 14
    CHANGELOG = 16
    TUTORIAL = 17
    DONATE = 18
    GUIDE = 19
    DEV_PANEL = 20
    SPLASH = 21

# 鼠标按键映射 (使用负数避免与键盘码冲突)
MOUSE_LEFT = -1
MOUSE_MIDDLE = -2
MOUSE_RIGHT = -3

# 默认配置
DEFAULT_CONFIG = {
    'resolution': (1280, 720),
    'fullscreen': False,
    'master_volume': 1.0,
    'sfx_volume': 1.0,
    'bgm_volume': 1.0,
    'ambient_volume': 1.0,
    'theme': 'light', # light, dark
    'attack_sfx_enabled': True, # 攻击音效开关
    'tutorial_completed': False, # 新手教学完成状态
    'key_bindings': {
        'basic_attack': MOUSE_LEFT, # 普通攻击
        'up': pygame.K_w,
        'down': pygame.K_s,
        'left': pygame.K_a,
        'right': pygame.K_d,
        'skill_1': pygame.K_q,     # 切换左
        'skill_2': pygame.K_e,     # 切换右
        'use_skill': pygame.K_SPACE,
        'dodge': pygame.K_LSHIFT,
        'inventory': pygame.K_b,
        'stats': pygame.K_TAB,
        'pause': pygame.K_ESCAPE
    }
}

# 全局配置变量
CONFIG_FILE = "config.json"
game_config = copy.deepcopy(DEFAULT_CONFIG)

def load_config():
    global game_config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
                # 递归更新，防止缺少新配置项
                for key, value in saved_config.items():
                    if key == 'resolution':
                        game_config[key] = tuple(value) # json list -> tuple
                    elif key == 'key_bindings':
                        # 确保所有键位都存在
                        if 'key_bindings' not in game_config: game_config['key_bindings'] = {}
                        for action, key_code in value.items():
                            game_config['key_bindings'][action] = key_code
                    else:
                        game_config[key] = value
                # 补充缺失的默认键位（例如新增的闪避）
                for action, default_code in DEFAULT_CONFIG['key_bindings'].items():
                    if action not in game_config['key_bindings']:
                        game_config['key_bindings'][action] = default_code
        except Exception as e:
            print(f"Error loading config: {e}")

def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(game_config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

# 加载配置
load_config()

# 屏幕设置初始值
SCREEN_WIDTH = game_config['resolution'][0]
SCREEN_HEIGHT = game_config['resolution'][1]

# 地图大小
MAP_WIDTH = 3000
MAP_HEIGHT = 3000

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
BLUE = (0, 0, 255)
HOVER_COLOR = (100, 100, 255)
SLIDER_BG = (220, 220, 220)
SLIDER_FILL = (100, 200, 100)
SELECTED_BORDER = (255, 215, 0) # 金色选中框

# 主题颜色配置
THEME_COLORS = {
    'light': {
        'bg': WHITE,
        'text': BLACK,
        'grid': (200, 200, 200),
        'ui_bg': (240, 240, 240, 200),
        'panel_border': BLACK,
        'button_text': BLACK
    },
    'dark': {
        'bg': (30, 30, 30),
        'text': (220, 220, 220),
        'grid': (50, 50, 50),
        'ui_bg': (50, 50, 50, 200),
        'panel_border': (100, 100, 100),
        'button_text': WHITE
    }
}

def get_theme_color(key):
    return THEME_COLORS[game_config['theme']][key]

# 角色数据
CHARACTERS = [
    {
        'id': 'square',
        'name': '坚毅方块',
        'class': '战士',
        'desc': '平衡型角色，攻守兼备',
        'color': (50, 200, 50),
        'stats': {
            'max_hp': 120,
            'max_mp': 50,
            'phys_atk': 10,
            'magic_atk': 0,
            'phys_def': 6,
            'magic_def': 4,
            'phys_pen': 0,
            'magic_pen': 0,
            'true_dmg': 0,
            'pickup_range': 100,
            'move_speed': 280,
            'attack_speed': 1.0,
            'attack_range': 250,
            'crit_chance': 5,
            'hp_regen': 2,
            'mp_regen': 1,
            'luck': 0,
            'collision_damage_reduction': 5
        },
        'growth': {
            'max_hp': 1.5,
            'phys_def': 1.5,
            'hp_regen': 1.5,
            'collision_damage_reduction': 1.5,
            'magic_def': 1.2,
            'phys_atk': 1.0,
        }
    },
    {
        'id': 'triangle',
        'name': '迅捷三角',
        'class': '刺客',
        'desc': '高机动高爆发，身板脆弱',
        'color': (200, 50, 50),
        'stats': {
            'max_hp': 80,
            'max_mp': 60,
            'phys_atk': 15,
            'magic_atk': 0,
            'phys_def': 1,
            'magic_def': 1,
            'phys_pen': 20, # 20%
            'magic_pen': 0,
            'true_dmg': 5,
            'pickup_range': 120,
            'move_speed': 340,
            'attack_speed': 1.5,
            'attack_range': 400,
            'crit_chance': 15,
            'hp_regen': 0.5,
            'mp_regen': 1,
            'luck': 5,
            'collision_damage_reduction': 0
        },
        'growth': {
            'phys_atk': 1.5,
            'crit_chance': 1.5,
            'phys_pen': 1.5,
            'attack_speed': 1.2,
            'move_speed': 1.2,
            'max_hp': 0.8,
        }
    },
    {
        'id': 'circle',
        'name': '奥术圆环',
        'class': '法师',
        'desc': '擅长范围攻击，移动较慢',
        'color': (50, 50, 200),
        'stats': {
            'max_hp': 90,
            'max_mp': 100,
            'phys_atk': 2,
            'magic_atk': 15,
            'phys_def': 1,
            'magic_def': 5,
            'phys_pen': 0,
            'magic_pen': 15, # 15%
            'true_dmg': 0,
            'pickup_range': 150,
            'move_speed': 260,
            'attack_speed': 0.8,
            'attack_range': 300,
            'crit_chance': 5,
            'hp_regen': 1.5,
            'mp_regen': 2,
            'luck': 2,
            'collision_damage_reduction': 2
        },
        'growth': {
            'magic_atk': 1.5,
            'max_mp': 1.5,
            'magic_pen': 1.5,
            'mp_regen': 1.5,
            'skill_haste': 1.2,
            'phys_atk': 0.5,
        }
    }
]

# 技能数据
SKILLS = {
    'square': [
        {
            'id': 'dash',
            'name': '冲锋',
            'cost': 15,
            'cd': 4.0,
            'desc': '向前快速冲刺一段距离'
        },
        {
            'id': 'shield',
            'name': '格挡',
            'cost': 20,
            'cd': 8.0,
            'desc': '短时间内获得高额减伤'
        }
    ],
    'triangle': [
        {
            'id': 'dash',
            'name': '闪避',
            'cost': 10,
            'cd': 2.0,
            'desc': '快速向移动方向位移'
        },
        {
            'id': 'fan_attack',
            'name': '扇形扫射',
            'cost': 25,
            'cd': 5.0,
            'desc': '向前方发射多枚子弹'
        }
    ],
    'circle': [
        {
            'id': 'fireball',
            'name': '大火球',
            'cost': 30,
            'cd': 4.0,
            'desc': '发射一颗巨大的火球，造成范围伤害'
        },
        {
            'id': 'blink',
            'name': '闪现',
            'cost': 40,
            'cd': 6.0,
            'desc': '瞬间移动到鼠标位置'
        }
    ]
}

# 字体初始化
pygame.font.init()

def get_font(size):
    # 尝试加载中文字体
    font_names = ["simhei", "microsoftyahei", "simsun", "arial"]
    
    # 优先尝试当前目录下的 simhei.ttf (使用 resource_path)
    font_path = resource_path("simhei.ttf")
    if os.path.exists(font_path):
        try:
            return pygame.font.Font(font_path, size)
        except:
            pass
            
    # 尝试系统字体
    for name in font_names:
        try:
            return pygame.font.SysFont(name, size)
        except:
            continue
            
    # 最后使用默认字体
    return pygame.font.Font(None, size)

font = None
small_font = None
medium_font = None
title_font = None

def init_fonts():
    global font, small_font, medium_font, title_font
    font = get_font(36)
    small_font = get_font(24)
    medium_font = get_font(28)
    title_font = get_font(60)

# Initialize fonts immediately
init_fonts()
