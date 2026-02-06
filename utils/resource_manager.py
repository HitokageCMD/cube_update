import pygame
import os
from config.game_config import *

class ResourceManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance.images = {}
            cls._instance.initialized = False
        return cls._instance

    def initialize(self):
        if not self.initialized:
            self.load_all_images()
            self.load_animations()
            self.initialized = True

    def load_all_images(self):
        # 加载各类图片
        self.load_dir(PLAYER_IMG_DIR, "player")
        self.load_dir(ENEMY_IMG_DIR, "enemy")
        self.load_dir(MAP_IMG_DIR, "map")
        self.load_dir(ITEMS_IMG_DIR, "items")
        self.load_dir(UI_IMG_DIR, "ui")
        self.load_dir(PROJECTILE_IMG_DIR, "projectile")
        
    def load_dir(self, directory, prefix):
        if not os.path.exists(directory):
            print(f"Warning: Directory not found: {directory}")
            return
            
        for root, dirs, files in os.walk(directory):
             # Skip if it's an animation folder (handled by load_animations)
             # Simple heuristic: if it has subdirs, we might process files in subdirs later or now.
             # Current load_dir logic was flat. os.listdir only checks top level.
             # We should keep flat loading for basic assets, but allow recursive if needed?
             # For now, keep original flat loading for compatibility, but maybe extend it?
             # Let's keep load_dir as is (os.listdir) for flat folders.
             pass

        for filename in os.listdir(directory):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                name = os.path.splitext(filename)[0]
                # 键名格式: player_warrior, enemy_square, etc.
                key = f"{prefix}_{name}"
                try:
                    img = pygame.image.load(os.path.join(directory, filename)).convert_alpha()
                    self.images[key] = img
                    print(f"Loaded image: {key}")
                except Exception as e:
                    print(f"Failed to load image {filename}: {e}")

    def load_animations(self):
        # 1. Load Player Animations
        # Structure: assets/images/player/{char_id}/{action}/{frame}.png
        if os.path.exists(PLAYER_IMG_DIR):
            self._load_anim_from_dir(PLAYER_IMG_DIR, "anim_player")
            
        # 2. Load Enemy Animations
        # Structure: assets/images/enemy/{type}/{action}/{frame}.png
        if os.path.exists(ENEMY_IMG_DIR):
             self._load_anim_from_dir(ENEMY_IMG_DIR, "anim_enemy")

    def _load_anim_from_dir(self, base_dir, prefix_key):
        self.animations = getattr(self, 'animations', {})
        
        for entity_id in os.listdir(base_dir):
            entity_path = os.path.join(base_dir, entity_id)
            if os.path.isdir(entity_path):
                for action in os.listdir(entity_path):
                    action_path = os.path.join(entity_path, action)
                    if os.path.isdir(action_path):
                        frames = []
                        try:
                            filenames = sorted(
                                [f for f in os.listdir(action_path) if f.lower().endswith('.png')],
                                key=lambda x: int(os.path.splitext(x)[0])
                            )
                            
                            for fname in filenames:
                                img_path = os.path.join(action_path, fname)
                                img = pygame.image.load(img_path).convert_alpha()
                                frames.append(img)
                                
                            if frames:
                                key = f"{prefix_key}_{entity_id}_{action}"
                                self.animations[key] = frames
                                print(f"Loaded animation: {key} ({len(frames)} frames)")
                        except Exception as e:
                            print(f"Error loading animation {entity_id}/{action}: {e}")

    def get_image(self, key):
        return self.images.get(key)
    
    def get_animation(self, key):
        return self.animations.get(key)


    def get_scaled_image(self, key, size):
        """ 获取缩放后的图片，如果不匹配则缩放并缓存（简单的实时缩放，不做缓存优化暂可） """
        img = self.get_image(key)
        if img:
            return pygame.transform.scale(img, size)
        return None

# 全局实例
resource_manager = ResourceManager()
