import pygame
import os
import random

def generate_tile_assets():
    base_dir = os.path.join("assets", "sprites", "map", "tiles")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    tile_size = 64
    
    # Colors (Pixel Art Palette)
    # Grass: Bright, vibrant
    grass_base = (106, 190, 48)
    grass_dark = (75, 144, 40)
    grass_light = (138, 224, 60)
    
    # Dirt: Reddish brown
    dirt_base = (153, 100, 41)
    dirt_dark = (110, 65, 20)
    dirt_light = (180, 120, 50)

    # 1. Generate Grass Variants
    for i in range(4):
        surf = pygame.Surface((tile_size, tile_size))
        surf.fill(grass_base)
        
        # Add noise/texture
        for _ in range(20):
            x = random.randint(0, tile_size-1)
            y = random.randint(0, tile_size-1)
            color = grass_light if random.random() > 0.5 else grass_dark
            # Draw small pixel clusters
            pygame.draw.rect(surf, color, (x, y, 4, 4))
            
        pygame.image.save(surf, os.path.join(base_dir, f"grass_{i}.png"))
        print(f"Generated grass_{i}.png")

    # 2. Generate Dirt Variants
    for i in range(4):
        surf = pygame.Surface((tile_size, tile_size))
        surf.fill(dirt_base)
        
        # Add noise/texture
        for _ in range(30):
            x = random.randint(0, tile_size-1)
            y = random.randint(0, tile_size-1)
            color = dirt_light if random.random() > 0.5 else dirt_dark
            pygame.draw.rect(surf, color, (x, y, 4, 4))
            
        pygame.image.save(surf, os.path.join(base_dir, f"dirt_{i}.png"))
        print(f"Generated dirt_{i}.png")

if __name__ == "__main__":
    pygame.init()
    # Dummy display for image saving
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    generate_tile_assets()
    pygame.quit()
