import pygame
import random
import math
import os
import config.game_config as settings
from entities.interactables import Chest
from utils.resource_manager import resource_manager

# Biome Types
BIOME_PLAINS = 0
BIOME_FOREST = 1
BIOME_VILLAGE = 2

class Chunk:
    def __init__(self, cx, cy, chunk_size, grid_size=64, map_manager=None):
        self.cx = cx
        self.cy = cy
        self.chunk_size = chunk_size
        self.grid_size = grid_size
        self.obstacles = []
        self.grid = None # Logical grid for obstacles placement
        self.surface = None # Base generated surface (High Res)
        self.cached_surface = None # Scaled surface for current zoom
        self.cached_zoom = -1
        self.start_x = cx * chunk_size
        self.start_y = cy * chunk_size
        self.map_manager = map_manager
        
        # Determine Biome (Use MapManager's logic if available)
        if map_manager:
            self.biome = map_manager.get_biome_at_chunk(cx, cy)
        else:
            # Fallback
            rng = random.Random(f"{cx},{cy}")
            val = rng.random()
            if val < 0.4: self.biome = BIOME_FOREST
            elif val < 0.6: self.biome = BIOME_VILLAGE
            else: self.biome = BIOME_PLAINS

    def generate_ground(self):
        """Generates the ground texture for this chunk using auto-tiling."""
        self.surface = pygame.Surface((self.chunk_size, self.chunk_size))
        cols = self.chunk_size // self.grid_size
        rows = self.chunk_size // self.grid_size
        
        rng = random.Random(f"{self.cx},{self.cy}_ground")
        
        # Load tiles
        tile_dir = os.path.join(settings.ASSETS_DIR, "sprites", "map", "tiles")
        tiles = {}
        
        def load_tile(name):
            key = name
            if key not in tiles:
                try:
                    img = pygame.image.load(os.path.join(tile_dir, f"{name}.png")).convert()
                    tiles[key] = pygame.transform.scale(img, (self.grid_size, self.grid_size))
                except:
                    # Fallback
                    s = pygame.Surface((self.grid_size, self.grid_size))
                    if "dirt" in name: s.fill((153, 100, 41))
                    elif "stone" in name: s.fill((120, 120, 120))
                    else: s.fill((106, 190, 48))
                    tiles[key] = s
            return tiles[key]

        # 1. Generate Logical Map (0=Grass, 1=Dirt/Stone)
        # Use Perlin-like noise or Cellular Automata for natural shapes
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        
        if self.biome == BIOME_VILLAGE:
            # Generate Roads
            # Simple grid road system
            road_spacing = 6
            for r in range(rows):
                for c in range(cols):
                    if r % road_spacing == road_spacing // 2 or c % road_spacing == road_spacing // 2:
                         grid[r][c] = 2 # Stone Road
            
            # Add random connections
            for _ in range(20):
                r = rng.randint(0, rows-1)
                c = rng.randint(0, cols-1)
                grid[r][c] = 2
                
        else:
            # Natural Dirt Patches
            dirt_blobs = []
            num_blobs = rng.randint(5, 15)
            for _ in range(num_blobs):
                bx = rng.randint(0, cols-1)
                by = rng.randint(0, rows-1)
                radius = rng.randint(2, 6)
                dirt_blobs.append((bx, by, radius))

            for r in range(rows):
                for c in range(cols):
                    for bx, by, radius in dirt_blobs:
                        dist = math.sqrt((c - bx)**2 + (r - by)**2)
                        if dist < radius:
                            if dist > radius - 1.5 and rng.random() < 0.5: continue
                            grid[r][c] = 1 # Dirt
                            break
        
        self.grid = grid # Save for obstacle generation

        # 2. Draw Tiles with Auto-Tiling
        for r in range(rows):
            for c in range(cols):
                x = c * self.grid_size
                y = r * self.grid_size
                
                tile_type = grid[r][c]
                
                if tile_type == 0: # Grass
                    if rng.random() < 0.05:
                        tile_name = f"grass_flower_{rng.randint(0,2)}"
                    else:
                        tile_name = "grass_center"
                    self.surface.blit(load_tile(tile_name), (x, y))
                    
                elif tile_type == 1: # Dirt
                    self.draw_autotile(r, c, grid, rows, cols, x, y, "dirt", "grass", rng, load_tile)

                elif tile_type == 2: # Stone Road
                    self.draw_autotile(r, c, grid, rows, cols, x, y, "stone", "grass", rng, load_tile)

    def draw_autotile(self, r, c, grid, rows, cols, x, y, base_type, overlay_type, rng, load_tile):
        # Base Tile
        if rng.random() < 0.05:
            base_name = f"{base_type}_center" # Simplified, could add variants
        else:
            base_name = f"{base_type}_center"
        self.surface.blit(load_tile(base_name), (x, y))
        
        # Check neighbors for overlay (transitions)
        # If neighbor is 'overlay_type' (e.g. Grass), we need a transition.
        # Logic: If N is Grass, we need "Top Grass, Bottom Dirt".
        # Generator name: "grass_to_dirt_S" (Top Grass, Bottom Dirt).
        
        # Wait, generator Naming was:
        # N: Top Dirt, Bottom Grass. -> Transition from Grass(Bottom) to Dirt(Top).
        # S: Top Grass, Bottom Dirt. -> Transition from Dirt(Bottom) to Grass(Top).
        
        # Let's verify generator logic from previous step:
        # make_mask_tile("S", [pygame.Rect(0, 0, w, h//2)]) # Top half grass, Bottom half dirt.
        # So "S" tile has Grass on Top.
        # If my North neighbor is Grass, I want Grass on my Top edge.
        # So I need "S" tile.
        
        # Mapping:
        # Neighbor N is Overlay -> Use "S" tile (Grass Top)
        # Neighbor S is Overlay -> Use "N" tile (Grass Bottom)
        # Neighbor W is Overlay -> Use "E" tile (Grass Left)
        # Neighbor E is Overlay -> Use "W" tile (Grass Right)
        
        # 0 is Overlay (Grass)
        # 1/2 is Base (Dirt/Stone)
        
        n = grid[r-1][c] if r > 0 else 0 
        s = grid[r+1][c] if r < rows-1 else 0
        w = grid[r][c-1] if c > 0 else 0
        e = grid[r][c+1] if c < cols-1 else 0
        
        # Helper to check if neighbor is overlay type
        def is_overlay(val): return val == 0
        
        prefix = f"{overlay_type}_to_{base_type}"
        
        if is_overlay(n): self.surface.blit(load_tile(f"{prefix}_S"), (x, y))
        if is_overlay(s): self.surface.blit(load_tile(f"{prefix}_N"), (x, y))
        if is_overlay(w): self.surface.blit(load_tile(f"{prefix}_E"), (x, y))
        if is_overlay(e): self.surface.blit(load_tile(f"{prefix}_W"), (x, y))
        
        # Corners
        if is_overlay(n) and is_overlay(w): self.surface.blit(load_tile(f"{prefix}_SE"), (x, y))
        if is_overlay(n) and is_overlay(e): self.surface.blit(load_tile(f"{prefix}_SW"), (x, y))
        if is_overlay(s) and is_overlay(w): self.surface.blit(load_tile(f"{prefix}_NE"), (x, y))
        if is_overlay(s) and is_overlay(e): self.surface.blit(load_tile(f"{prefix}_NW"), (x, y))

    def get_draw_surface(self, zoom):
        """Returns a cached surface scaled to the current zoom level."""
        if self.cached_surface is None or abs(self.cached_zoom - zoom) > 0.001:
            self.cached_zoom = zoom
            target_size = int(self.chunk_size * zoom) + 2 # +2 overlap baked in
            self.cached_surface = pygame.transform.scale(self.surface, (target_size, target_size))
        return self.cached_surface

class Obstacle:
    def __init__(self, x, y, size, hp, obs_type):
        self.pos = pygame.math.Vector2(x, y)
        self.size = size
        self.max_hp = hp
        self.current_hp = hp
        self.type = obs_type # 'tree' or 'house'
        self.color = (255, 255, 255)
        self.rect = pygame.Rect(x - size/2, y - size/2, size, size)
        
        if self.type == 'tree':
            self.color = (34, 139, 34) # Forest Green
        elif self.type == 'house':
            self.color = (139, 69, 19) # Saddle Brown

    def take_damage(self, amount):
        self.current_hp -= amount
        return self.current_hp <= 0

    def draw(self, surface, camera):
        screen_pos = camera.apply(self.pos)
        draw_size = int(self.size * camera.zoom)
        
        # 尝试使用图片
        image_key = f"map_{self.type}"
        image = resource_manager.get_image(image_key)
        
        if image:
            scaled_image = pygame.transform.scale(image, (draw_size, draw_size))
            rect = scaled_image.get_rect(center=(int(screen_pos.x), int(screen_pos.y)))
            surface.blit(scaled_image, rect)
            
            # HP Bar if damaged
            if self.current_hp < self.max_hp * 0.1:
                hp_ratio = self.current_hp / self.max_hp
                bar_w = draw_size
                bar_h = 4
                bar_pos = (screen_pos.x - bar_w//2, screen_pos.y - draw_size//2 - 8)
                pygame.draw.rect(surface, (50, 0, 0), (*bar_pos, bar_w, bar_h))
                pygame.draw.rect(surface, (0, 200, 0), (*bar_pos, bar_w * hp_ratio, bar_h))
            return
        
        if self.type == 'tree':
            # Draw Trunk
            trunk_w = max(4, draw_size // 4)
            trunk_h = draw_size // 2
            trunk_color = (139, 69, 19) # Saddle Brown
            
            trunk_rect = pygame.Rect(0, 0, trunk_w, trunk_h)
            half_w = draw_size // 2
            trunk_rect.midtop = (int(screen_pos.x), int(screen_pos.y + half_w - trunk_h * 0.5))
            
            pygame.draw.rect(surface, trunk_color, trunk_rect)
            pygame.draw.rect(surface, (0, 0, 0), trunk_rect, 1)

            # Draw Triangle (Leaves)
            points = [
                (screen_pos.x, screen_pos.y - half_w),
                (screen_pos.x - half_w, screen_pos.y + half_w),
                (screen_pos.x + half_w, screen_pos.y + half_w)
            ]
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, (0, 0, 0), points, 1)
            
        elif self.type == 'house':
            # Draw House with details
            half_w = draw_size // 2
            
            # 1. Wall (Rectangle body)
            wall_w = int(draw_size * 0.8)
            wall_h = int(draw_size * 0.6)
            wall_color = (222, 184, 135) # Burlywood (Light Wood)
            
            wall_rect = pygame.Rect(0, 0, wall_w, wall_h)
            wall_rect.midbottom = (int(screen_pos.x), int(screen_pos.y + half_w))
            
            pygame.draw.rect(surface, wall_color, wall_rect)
            pygame.draw.rect(surface, (0, 0, 0), wall_rect, 1)
            
            # 2. Door (Dark Rectangle)
            door_w = int(wall_w * 0.3)
            door_h = int(wall_h * 0.6)
            door_color = (70, 40, 20) # Dark Brown
            
            door_rect = pygame.Rect(0, 0, door_w, door_h)
            door_rect.midbottom = wall_rect.midbottom
            pygame.draw.rect(surface, door_color, door_rect)
            pygame.draw.rect(surface, (0, 0, 0), door_rect, 1)
            
            # 3. Roof (Triangle overhang)
            roof_h = int(draw_size * 0.5)
            roof_w = draw_size # Wider than wall
            
            roof_bottom_y = wall_rect.top
            roof_top_y = roof_bottom_y - roof_h
            
            points = [
                (screen_pos.x, roof_top_y), # Top Peak
                (screen_pos.x - roof_w//2, roof_bottom_y), # Bottom Left
                (screen_pos.x + roof_w//2, roof_bottom_y)  # Bottom Right
            ]
            
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, (0, 0, 0), points, 1)
            
            # 4. Window (Small circle/square)
            win_size = int(wall_w * 0.25)
            win_color = (135, 206, 250) # Light Sky Blue
            win_x = wall_rect.centerx
            win_y = wall_rect.top + int(wall_h * 0.2)
            pygame.draw.circle(surface, win_color, (win_x, win_y), win_size // 2)
            pygame.draw.circle(surface, (0, 0, 0), (win_x, win_y), win_size // 2, 1)

        # HP Bar if damaged
        if self.current_hp < self.max_hp * 0.1:
            hp_ratio = self.current_hp / self.max_hp
            bar_w = draw_size
            bar_h = 4
            bar_pos = (screen_pos.x - bar_w//2, screen_pos.y - draw_size//2 - 8)
            pygame.draw.rect(surface, (50, 0, 0), (*bar_pos, bar_w, bar_h))
            pygame.draw.rect(surface, (0, 200, 0), (*bar_pos, bar_w * hp_ratio, bar_h))

class MapManager:
    def __init__(self):
        self.chunk_size = 2000
        self.active_chunks = {} # (cx, cy) -> Chunk
        self.grid_size = 100 
        self.seed = random.randint(0, 999999)

    def get_biome_at_chunk(self, cx, cy):
        # Macro Biome Logic using Perlin-like noise
        # We simulate noise by combining sine waves
        # Scale 1: Large continents
        val1 = math.sin(cx * 0.1 + self.seed) * math.cos(cy * 0.1 + self.seed)
        # Scale 2: Detail
        val2 = math.sin(cx * 0.5) * math.cos(cy * 0.5) * 0.5
        
        noise = val1 + val2
        
        # Thresholds
        if noise > 0.3: return BIOME_FOREST
        elif noise < -0.7: return BIOME_VILLAGE # Make villages rarer and smaller
        else: return BIOME_PLAINS

    def get_chunk(self, cx, cy):
        if (cx, cy) in self.active_chunks:
            return self.active_chunks[(cx, cy)]
        
        chunk = Chunk(cx, cy, self.chunk_size, map_manager=self)
        chunk.generate_ground()
        self.generate_obstacles(chunk)
        return chunk

    def get_biome_at(self, pos):
        cx = int(pos.x // self.chunk_size)
        cy = int(pos.y // self.chunk_size)
        return self.get_biome_at_chunk(cx, cy)

    def generate_obstacles(self, chunk):
        obstacles = []
        cx, cy = chunk.cx, chunk.cy
        start_x = chunk.start_x
        start_y = chunk.start_y
        rng = random.Random(f"{cx},{cy}_obs_{self.seed}")
        
        # 1. Forest: Dense trees, Maze-like
        if chunk.biome == BIOME_FOREST:
            rows = self.chunk_size // self.grid_size
            cols = self.chunk_size // self.grid_size
            
            # Generate Maze Grid using Prim's or Recursive Backtracker? 
            # Too complex for quick gen. Use Noise density.
            
            for r in range(rows):
                for c in range(cols):
                    # Higher density noise
                    nx = cx * cols + c
                    ny = cy * rows + r
                    noise = math.sin(nx * 0.2) * math.cos(ny * 0.2)
                    
                    if noise > -0.2: # 60% dense
                        x = start_x + c * self.grid_size + self.grid_size/2
                        y = start_y + r * self.grid_size + self.grid_size/2
                        # Leave some random clearings for chests
                        if rng.random() > 0.05:
                            obstacles.append(Obstacle(x, y, 60, 500, 'tree'))
            
            # Chests in clearings
            if rng.random() < 0.4:
                 chest_x = start_x + rng.uniform(200, self.chunk_size - 200)
                 chest_y = start_y + rng.uniform(200, self.chunk_size - 200)
                 # Check overlap
                 valid = True
                 for obs in obstacles:
                     if (pygame.math.Vector2(chest_x, chest_y) - obs.pos).length() < 100:
                         valid = False; break
                 if valid:
                     chest = Chest(chest_x, chest_y, 'gold' if rng.random() < 0.3 else 'blue')
                     obstacles.append(chest)

        # 2. Village: Houses along roads
        elif chunk.biome == BIOME_VILLAGE:
             # Use stored grid to place houses near roads
             if chunk.grid:
                 rows = len(chunk.grid)
                 cols = len(chunk.grid[0])
                 candidates = []
                 
                 for r in range(1, rows-1):
                     for c in range(1, cols-1):
                         if chunk.grid[r][c] == 0: # Grass
                             # Check neighbors for Road (2)
                             has_road = False
                             for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                                 if chunk.grid[r+dr][c+dc] == 2:
                                     has_road = True
                                     break
                             if has_road:
                                 candidates.append((r, c))
                 
                 # Shuffle and pick
                 rng.shuffle(candidates)
                 
                 # Limit density
                 count = min(len(candidates), rng.randint(6, 12)) # Fewer houses for smaller feel?
                 
                 for i in range(count):
                     r, c = candidates[i]
                     # Convert to world coords (center of tile)
                     gx = start_x + c * self.grid_size + self.grid_size/2
                     gy = start_y + r * self.grid_size + self.grid_size/2
                     
                     # Check overlap with existing obstacles (though unlikely with grid logic)
                     # But we should ensure we don't pick the same spot? 
                     # candidates are unique (r,c), so no overlap on grid.
                     
                     obstacles.append(Obstacle(gx, gy, 80, 700, 'house'))
             else:
                 # Fallback if grid missing
                 count = rng.randint(8, 15)
                 for _ in range(count):
                    x = start_x + rng.uniform(100, self.chunk_size - 100)
                    y = start_y + rng.uniform(100, self.chunk_size - 100)
                    gx = int((x - start_x) // self.grid_size) * self.grid_size + self.grid_size/2 + start_x
                    gy = int((y - start_y) // self.grid_size) * self.grid_size + self.grid_size/2 + start_y
                    obstacles.append(Obstacle(gx, gy, 80, 700, 'house'))
                
        # 3. Plains: Sparse trees, flowers
        else:
            count = rng.randint(5, 20)
            for _ in range(count):
                x = start_x + rng.uniform(50, self.chunk_size - 50)
                y = start_y + rng.uniform(50, self.chunk_size - 50)
                obstacles.append(Obstacle(x, y, 50, 300, 'tree'))
            
            if rng.random() < 0.3:
                 chest_x = start_x + rng.uniform(200, self.chunk_size - 200)
                 chest_y = start_y + rng.uniform(200, self.chunk_size - 200)
                 obstacles.append(Chest(chest_x, chest_y, 'white'))

        chunk.obstacles = obstacles

    def update(self, player_pos):
        cx = int(player_pos.x // self.chunk_size)
        cy = int(player_pos.y // self.chunk_size)
        
        needed_chunks = set()
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                needed_chunks.add((cx + dx, cy + dy))
                
        # Load new chunks
        for coords in needed_chunks:
            if coords not in self.active_chunks:
                self.active_chunks[coords] = self.get_chunk(coords[0], coords[1])
                
        # Unload old chunks
        for coords in list(self.active_chunks.keys()):
            if coords not in needed_chunks:
                del self.active_chunks[coords]

    def draw(self, surface, camera):
        # Draw Ground First
        for chunk in self.active_chunks.values():
            screen_x = math.floor(chunk.start_x * camera.zoom - camera.pos.x * camera.zoom + settings.SCREEN_WIDTH/2)
            screen_y = math.floor(chunk.start_y * camera.zoom - camera.pos.y * camera.zoom + settings.SCREEN_HEIGHT/2)
            
            next_screen_x = math.floor((chunk.start_x + chunk.chunk_size) * camera.zoom - camera.pos.x * camera.zoom + settings.SCREEN_WIDTH/2)
            next_screen_y = math.floor((chunk.start_y + chunk.chunk_size) * camera.zoom - camera.pos.y * camera.zoom + settings.SCREEN_HEIGHT/2)
            
            screen_w = next_screen_x - screen_x
            screen_h = next_screen_y - screen_y
            
            if (screen_x + screen_w > 0 and screen_x < settings.SCREEN_WIDTH and
                screen_y + screen_h > 0 and screen_y < settings.SCREEN_HEIGHT):
                
                cached_surf = chunk.get_draw_surface(camera.zoom)
                surface.blit(cached_surf, (screen_x, screen_y))

        # Draw Obstacles
        for chunk in self.active_chunks.values():
            for obs in chunk.obstacles:
                obs.draw(surface, camera)

    def get_obstacles(self):
        all_obs = []
        for chunk in self.active_chunks.values():
            all_obs.extend(chunk.obstacles)
        return all_obs

    def check_collision(self, entity):
        for chunk in self.active_chunks.values():
            for obs in chunk.obstacles:
                dist_vec = entity.pos - obs.pos
                dist = dist_vec.length()
                
                if obs.type == 'house': obs_radius = obs.size * 0.4
                else: obs_radius = obs.size / 2

                min_dist = (entity.size / 2) + obs_radius
                
                if dist < min_dist:
                    if dist > 0:
                        push_vec = dist_vec.normalize() * (min_dist - dist)
                        entity.pos += push_vec
                    else:
                        entity.pos += pygame.math.Vector2(1, 0)

    def check_projectile_collision(self, projectile, damage_callback=None, on_destroy=None):
        cx = int(projectile.pos.x // self.chunk_size)
        cy = int(projectile.pos.y // self.chunk_size)
        
        chunks_to_check = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                chunks_to_check.append((cx + dx, cy + dy))
        
        for coords in chunks_to_check:
            if coords in self.active_chunks:
                chunk = self.active_chunks[coords]
                for obs in chunk.obstacles[:]:
                    dist = (projectile.pos - obs.pos).length()
                    if dist < obs.size/2 + projectile.radius:
                        destroyed = obs.take_damage(projectile.damage)
                        
                        if obs.current_hp < obs.max_hp * 0.1 and damage_callback:
                            damage_callback(obs.pos, projectile.damage, getattr(projectile, 'damage_type', 'physical'))

                        if destroyed:
                            if on_destroy: on_destroy(obs)
                            chunk.obstacles.remove(obs)
                        return True
        return False

    def check_melee_collision(self, player, melee_attack, dt_sec, damage_callback=None, on_destroy=None):
        cx = int(player.pos.x // self.chunk_size)
        cy = int(player.pos.y // self.chunk_size)
        
        chunks_to_check = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                chunks_to_check.append((cx + dx, cy + dy))
                
        for coords in chunks_to_check:
            if coords in self.active_chunks:
                chunk = self.active_chunks[coords]
                for obs in chunk.obstacles[:]:
                    dist = (obs.pos - player.pos).length()
                    if dist < melee_attack.range + obs.size:
                        to_obs = obs.pos - player.pos
                        angle_diff = abs(math.atan2(to_obs.y, to_obs.x) - melee_attack.base_angle)
                        while angle_diff > math.pi: angle_diff -= 2*math.pi
                        while angle_diff < -math.pi: angle_diff += 2*math.pi
                        
                        if abs(angle_diff) < 1.0:
                             dmg = getattr(player, 'phys_atk', 10) * dt_sec * 5
                             destroyed = obs.take_damage(dmg)
                             
                             if obs.current_hp < obs.max_hp * 0.1 and damage_callback and dmg > 1:
                                 damage_callback(obs.pos, dmg, 'physical')

                             if destroyed:
                                 if on_destroy: on_destroy(obs)
                                 chunk.obstacles.remove(obs)
