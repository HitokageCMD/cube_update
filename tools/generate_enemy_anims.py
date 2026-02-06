import pygame
import os
import math

# Initialize Pygame (for drawing)
pygame.init()

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "images")
ENEMY_DIR = os.path.join(ASSETS_DIR, "enemy")

# Colors
COLORS = {
    'square': (200, 50, 50),     # Red
    'triangle': (200, 200, 50),  # Yellow
    'circle': (50, 50, 200),     # Blue
}

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_animation_frames(enemy_type, action, color, size=64):
    frames = []
    
    # Create directory
    anim_dir = os.path.join(ENEMY_DIR, enemy_type, action)
    ensure_dir(anim_dir)
    
    print(f"Generating {enemy_type} - {action}...")
    
    for i in range(5):
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        base_size = size // 2
        
        progress = i / 4.0 # 0.0 to 1.0
        
        draw_color = color
        
        if action == 'idle':
            # Breathing effect
            scale = 1.0 + math.sin(progress * math.pi * 2) * 0.05
            current_size = base_size * scale
            
        elif action == 'attack':
            # Lunge / Flash
            if i < 2: # Wind up
                scale = 0.8
                draw_color = tuple(min(255, c + 20) for c in color)
            elif i == 2: # Strike
                scale = 1.3
                draw_color = (255, 255, 255) # Flash white
            else: # Recover
                scale = 1.0
            current_size = base_size * scale
            
        elif action == 'hurt':
            # Shake and White Flash
            offset_x = math.sin(progress * math.pi * 8) * 5
            center = (size // 2 + offset_x, size // 2)
            
            # Flash white-ish
            white_factor = 1.0 - abs(progress - 0.5) * 2 # Peak at 0.5
            draw_color = tuple(min(255, int(c + (255-c)*white_factor)) for c in color)
            current_size = base_size
            
        elif action == 'die':
            # Shrink and Fade
            current_size = base_size * (1.0 - progress)
            alpha = int(255 * (1.0 - progress))
            surface.set_alpha(alpha)
            
        else:
            current_size = base_size

        # Draw shape based on type
        if enemy_type == 'square':
            rect = pygame.Rect(0, 0, current_size, current_size)
            rect.center = center
            pygame.draw.rect(surface, draw_color, rect)
            pygame.draw.rect(surface, (0,0,0), rect, 2)
            
        elif enemy_type == 'triangle':
            h = current_size * math.sqrt(3) / 2
            points = [
                (center[0], center[1] - h/2),
                (center[0] - current_size/2, center[1] + h/2),
                (center[0] + current_size/2, center[1] + h/2)
            ]
            pygame.draw.polygon(surface, draw_color, points)
            pygame.draw.polygon(surface, (0,0,0), points, 2)
            
        elif enemy_type == 'circle':
            # Draw as Diamond for circle enemy (as per renderer logic)
            # Actually renderer draws circle as Diamond, but let's stick to name 'circle' for folder
            # Wait, renderer draws 'circle' type as Diamond.
            # Let's draw a Circle here to match the name, OR a Diamond to match the game?
            # The user asked for "Circle" enemy.
            # Let's draw a Diamond shape to match the renderer's unique style for this enemy.
            
            half_w = current_size / 2
            points = [
                (center[0], center[1] - half_w),
                (center[0] + half_w, center[1]),
                (center[0], center[1] + half_w),
                (center[0] - half_w, center[1])
            ]
            pygame.draw.polygon(surface, (150, 0, 200), points) # Purple
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)

        # Save
        filename = f"{i}.png"
        pygame.image.save(surface, os.path.join(anim_dir, filename))

# Generate for all types
TYPES = ['square', 'triangle', 'circle']
ACTIONS = ['attack', 'hurt', 'die', 'idle'] # Added idle just in case

for t in TYPES:
    for a in ACTIONS:
        create_animation_frames(t, a, COLORS[t])

print("Enemy animations generated!")
