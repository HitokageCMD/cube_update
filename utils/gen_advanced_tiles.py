import pygame
import os
import random

def generate_advanced_tiles():
    base_dir = os.path.join("assets", "sprites", "map", "tiles")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    tile_size = 64
    
    # Palette
    c_grass = (106, 190, 48)
    c_grass_dark = (75, 144, 40)
    c_grass_light = (138, 224, 60)
    
    c_dirt = (153, 100, 41)
    c_dirt_dark = (110, 65, 20)
    c_dirt_light = (180, 120, 50)
    
    c_stone = (120, 120, 120)
    c_stone_dark = (80, 80, 80)
    c_stone_light = (160, 160, 160)

    def create_base_tile(color, dark, light, noise_count=20):
        surf = pygame.Surface((tile_size, tile_size))
        surf.fill(color)
        for _ in range(noise_count):
            x = random.randint(0, tile_size-1)
            y = random.randint(0, tile_size-1)
            c = light if random.random() > 0.5 else dark
            pygame.draw.rect(surf, c, (x, y, 4, 4))
        return surf

    # 1. Base Tiles
    # Grass
    grass_base = create_base_tile(c_grass, c_grass_dark, c_grass_light)
    pygame.image.save(grass_base, os.path.join(base_dir, "grass_center.png"))
    
    # Dirt
    dirt_base = create_base_tile(c_dirt, c_dirt_dark, c_dirt_light, 30)
    pygame.image.save(dirt_base, os.path.join(base_dir, "dirt_center.png"))
    
    # Stone
    stone_base = create_base_tile(c_stone, c_stone_dark, c_stone_light, 40)
    pygame.image.save(stone_base, os.path.join(base_dir, "stone_center.png"))

    # 2. Decorations
    # Flowers on Grass
    for i in range(3):
        surf = grass_base.copy()
        for _ in range(random.randint(3, 6)):
            x = random.randint(10, tile_size-10)
            y = random.randint(10, tile_size-10)
            flower_col = random.choice([(255, 100, 100), (255, 255, 100), (100, 100, 255)])
            pygame.draw.circle(surf, flower_col, (x, y), 3)
            pygame.draw.circle(surf, (255, 255, 255), (x, y), 1)
        pygame.image.save(surf, os.path.join(base_dir, f"grass_flower_{i}.png"))

    # Stones on Dirt
    for i in range(3):
        surf = dirt_base.copy()
        for _ in range(random.randint(2, 5)):
            x = random.randint(5, tile_size-10)
            y = random.randint(5, tile_size-10)
            s_size = random.randint(4, 8)
            pygame.draw.rect(surf, c_stone, (x, y, s_size, s_size))
        pygame.image.save(surf, os.path.join(base_dir, f"dirt_stone_{i}.png"))

    # 3. Transitions (Masking)
    # We need transitions from Grass -> Dirt (Dirt is "lower" or "path")
    # Actually usually Dirt is the path, so Grass overlays Dirt? Or Dirt overlays Grass?
    # Let's say we have Grass and Dirt. 
    # We want "Grass Edge" over "Dirt Background".
    
    def create_transition(base_surf, overlay_surf, mask_type):
        """
        mask_type: 'top', 'bottom', 'left', 'right', 'top_left', etc.
        """
        res = base_surf.copy() # Bottom layer (e.g. Dirt)
        top = overlay_surf.copy() # Top layer (e.g. Grass)
        
        mask = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        mask.fill((0,0,0,0)) # Transparent
        
        # Draw opaque white on mask where we want the top layer to be KEPT
        # Actually standard way: Draw clear where we want to ERASE top layer
        
        # Simpler: Create a mask for the 'Top Layer Shape'
        # e.g. 'top' transition means Dirt is on Top? No, usually 'grass_to_dirt_top' means
        # the tile is physically located at the top edge of a dirt patch.
        # So it should look like Grass on top, Dirt on bottom.
        
        # Let's define: We are drawing a DIRT PATCH.
        # So the center is Dirt.
        # The top edge of the Dirt patch meets Grass.
        # So this tile is mostly Dirt, but top part fades to Grass? 
        # OR: This tile is Grass, but bottom part fades to Dirt?
        
        # Standard Autotile Logic:
        # We determine what the tile IS. 
        # If tile is DIRT, and neighbor UP is GRASS -> We need 'dirt_top_edge'.
        
        # Let's make Dirt the "overlay" for paths.
        # So Grass is background. Dirt is drawn on top.
        # Transitions will be Dirt with transparency.
        
        # Wait, usually Grass overlays Dirt visually (grass grows on dirt).
        # Let's stick to: Background = Dirt. Foreground = Grass.
        # If we have a patch of Grass, the edges of that Grass patch need to transition to Dirt.
        
        # Let's assume the map is mostly Grass. Dirt are "holes" or "paths".
        # So we need "Grass Edges".
        
        pass

    # Simplified approach:
    # Generate specific transition tiles for "Grass to Dirt"
    # We assume 'base' is Dirt, 'top' is Grass.
    
    # 1. Top Edge (Grass on bottom, Dirt on top? No, Top Edge of a Grass Block)
    # Let's name them by direction of the 'Other' terrain.
    # grass_to_dirt_N: North is Dirt. So top of tile is Dirt, bottom is Grass.
    
    def make_mask_tile(name, keep_rects):
        # Base: Dirt
        surf = dirt_base.copy()
        # Overlay: Grass
        grass = grass_base.copy()
        
        mask = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        mask.fill((0,0,0,0))
        
        for r in keep_rects:
            pygame.draw.rect(mask, (255,255,255), r)
            
        # Add some noise to mask edges?
        # Skip for now, keep pixel perfect
        
        # Blit grass onto dirt using mask
        # Actually: We want to blit Grass where mask is White.
        # Pygame doesn't have easy mask blit.
        # Manual pixel array or stencil.
        
        # Workaround:
        # 1. Create Surface with Alpha
        final_grass = grass.convert_alpha()
        # 2. Iterate pixels? Too slow for python.
        # 3. Use special flags.
        
        final_grass.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(final_grass, (0,0))
        
        pygame.image.save(surf, os.path.join(base_dir, f"grass_to_dirt_{name}.png"))

    def make_stone_mask_tile(name, keep_rects):
        # Base: Stone
        surf = stone_base.copy()
        # Overlay: Grass
        grass = grass_base.copy()
        
        mask = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        mask.fill((0,0,0,0))
        
        for r in keep_rects:
            pygame.draw.rect(mask, (255,255,255), r)
            
        final_grass = grass.convert_alpha()
        final_grass.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(final_grass, (0,0))
        
        pygame.image.save(surf, os.path.join(base_dir, f"grass_to_stone_{name}.png"))

    h = tile_size
    w = tile_size
    
    # N = North is Dirt -> Top part is Dirt -> Bottom part is Grass
    # S = South is Dirt -> Bottom part is Dirt -> Top part is Grass
    
    # Simple straight edges
    make_mask_tile("N", [pygame.Rect(0, h//2, w, h//2)]) # Top half dirt, Bottom half grass
    make_mask_tile("S", [pygame.Rect(0, 0, w, h//2)]) # Top half grass, Bottom half dirt
    make_mask_tile("W", [pygame.Rect(w//2, 0, w//2, h)]) # Left half dirt, Right half grass
    make_mask_tile("E", [pygame.Rect(0, 0, w//2, h)]) # Left half grass, Right half dirt
    
    # Corners (Inner)
    make_mask_tile("NW", [pygame.Rect(w//2, h//2, w//2, h//2)])
    make_mask_tile("NE", [pygame.Rect(0, h//2, w//2, h//2)])
    make_mask_tile("SW", [pygame.Rect(w//2, 0, w//2, h//2)])
    make_mask_tile("SE", [pygame.Rect(0, 0, w//2, h//2)])

    # Stone Transitions (Overlay Grass on Stone)
    # Same logic: Mask defines where GRASS is kept (Overlay)
    make_stone_mask_tile("N", [pygame.Rect(0, h//2, w, h//2)])
    make_stone_mask_tile("S", [pygame.Rect(0, 0, w, h//2)])
    make_stone_mask_tile("W", [pygame.Rect(w//2, 0, w//2, h)])
    make_stone_mask_tile("E", [pygame.Rect(0, 0, w//2, h)])
    make_stone_mask_tile("NW", [pygame.Rect(w//2, h//2, w//2, h//2)])
    make_stone_mask_tile("NE", [pygame.Rect(0, h//2, w//2, h//2)])
    make_stone_mask_tile("SW", [pygame.Rect(w//2, 0, w//2, h//2)])
    make_stone_mask_tile("SE", [pygame.Rect(0, 0, w//2, h//2)])

    # 4. Obstacle Placeholders
    # Tree
    tree_surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    # Trunk
    pygame.draw.rect(tree_surf, (139, 69, 19), (56, 80, 16, 48))
    # Leaves (3 circles)
    pygame.draw.circle(tree_surf, (34, 139, 34), (64, 50), 40)
    pygame.draw.circle(tree_surf, (40, 160, 40), (40, 60), 30)
    pygame.draw.circle(tree_surf, (40, 160, 40), (88, 60), 30)
    pygame.image.save(tree_surf, os.path.join(base_dir, "..", "map_tree.png"))

    # House
    house_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
    # Wall
    pygame.draw.rect(house_surf, (222, 184, 135), (20, 60, 120, 80))
    pygame.draw.rect(house_surf, (100, 50, 20), (20, 60, 120, 80), 2)
    # Roof
    pygame.draw.polygon(house_surf, (139, 69, 19), [(10, 60), (80, 10), (150, 60)])
    pygame.draw.polygon(house_surf, (50, 20, 0), [(10, 60), (80, 10), (150, 60)], 2)
    # Door
    pygame.draw.rect(house_surf, (70, 40, 20), (65, 90, 30, 50))
    # Window
    pygame.draw.rect(house_surf, (135, 206, 250), (35, 80, 20, 20))
    pygame.draw.rect(house_surf, (0, 0, 0), (35, 80, 20, 20), 1)
    
    pygame.image.save(house_surf, os.path.join(base_dir, "..", "map_house.png"))

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    generate_advanced_tiles()
    pygame.quit()
