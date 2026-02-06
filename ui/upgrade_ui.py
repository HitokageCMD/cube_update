import pygame
import config.game_config as settings
from utils.resource_manager import resource_manager
from utils.sound_manager import SoundManager

get_theme_color = settings.get_theme_color

class UpgradeRenderer:
    def __init__(self, screen):
        self.screen = screen

    def draw_level_up_anim(self, anim_progress):
        if anim_progress <= 0: return
        
        # Flash effect
        alpha = int(anim_progress * 150)
        if alpha > 0:
            s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
            s.fill((255, 255, 200))
            s.set_alpha(alpha)
            self.screen.blit(s, (0, 0))
            
        # Text "LEVEL UP!"
        scale = 1.0 + (1.0 - anim_progress) * 2.0 
        font_size = int(80 * scale)
        try:
            font = pygame.font.Font(None, font_size)
        except:
            font = settings.font
            
        text = font.render("LEVEL UP!", True, (255, 215, 0))
        rect = text.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 100))
        
        # Shadow
        shadow = font.render("LEVEL UP!", True, (50, 50, 0))
        shadow_rect = rect.move(5, 5)
        
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(text, rect)

    def draw_level_up_choices(self, choices, hovered_idx=None):
        if not choices: return

        # Draw dark background
        s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 200))
        self.screen.blit(s, (0, 0))
        
        title = settings.title_font.render("选择升级奖励", True, (255, 215, 0))
        title_rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Layout
        num_choices = len(choices)
        card_width = 220
        card_height = 320
        spacing = 40
        total_width = num_choices * card_width + (num_choices - 1) * spacing
        start_x = (settings.SCREEN_WIDTH - total_width) // 2
        start_y = (settings.SCREEN_HEIGHT - card_height) // 2
        
        for i, choice in enumerate(choices):
            x = start_x + i * (card_width + spacing)
            y = start_y
            
            rect = pygame.Rect(x, y, card_width, card_height)
            is_hover = (i == hovered_idx)
            
            # Draw Card Background
            bg_color = (40, 40, 50)
            if is_hover:
                bg_color = (60, 60, 80)
                # Scale up slightly
                rect = rect.inflate(20, 20)
                
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=15)
            
            # Border
            border_color = (200, 200, 200)
            rarity = choice.get('rarity', 'white') # Default to white if not specified
            
            # Color Mapping matching other systems
            if rarity == 'white': border_color = (200, 200, 200)
            elif rarity == 'green': border_color = (100, 255, 100)
            elif rarity == 'blue': border_color = (100, 100, 255)
            elif rarity == 'purple': border_color = (255, 100, 255)
            elif rarity == 'orange': border_color = (255, 215, 0)
            elif rarity == 'red': border_color = (255, 50, 50)
            
            # Legacy fallback (rare/epic/legendary)
            if rarity == 'rare': border_color = (100, 100, 255)
            elif rarity == 'epic': border_color = (200, 50, 200)
            elif rarity == 'legendary': border_color = (255, 215, 0)
            
            width = 5 if is_hover else 3
            pygame.draw.rect(self.screen, border_color, rect, width, border_radius=15)
            
            # Content
            center_x = rect.centerx
            curr_y = rect.top + 30
            
            # Name
            name = choice.get('name', 'Unknown')
            name_surf = settings.medium_font.render(name, True, border_color)
            name_rect = name_surf.get_rect(center=(center_x, curr_y))
            self.screen.blit(name_surf, name_rect)
            
            curr_y += 50
            
            # Icon (Placeholder or real)
            icon_key = choice.get('icon')
            icon = resource_manager.get_image(icon_key) if icon_key else None
            
            if icon:
                scaled = pygame.transform.scale(icon, (64, 64))
                icon_rect = scaled.get_rect(center=(center_x, curr_y))
                self.screen.blit(scaled, icon_rect)
            else:
                # Shape placeholder
                pygame.draw.circle(self.screen, border_color, (center_x, curr_y), 30)
                
            curr_y += 60
            
            # Description
            desc = choice.get('desc', '')
            words = desc.split()
            lines = []
            curr_line = []
            for word in words:
                curr_line.append(word)
                test_line = " ".join(curr_line)
                if settings.small_font.size(test_line)[0] > card_width - 30:
                    curr_line.pop()
                    lines.append(" ".join(curr_line))
                    curr_line = [word]
            if curr_line: lines.append(" ".join(curr_line))
            
            for line in lines:
                line_surf = settings.small_font.render(line, True, (200, 200, 200))
                line_rect = line_surf.get_rect(center=(center_x, curr_y))
                self.screen.blit(line_surf, line_rect)
                curr_y += 25
                
            # Type / Tag
            tag = choice.get('type', 'upgrade')
            if tag == 'weapon': tag = "新武器"
            elif tag == 'passive': tag = "被动"
            elif tag == 'heal': tag = "回复"
            
            tag_surf = settings.small_font.render(f"[{tag}]", True, (150, 150, 150))
            tag_rect = tag_surf.get_rect(center=(center_x, rect.bottom - 30))
            self.screen.blit(tag_surf, tag_rect)

    def get_choice_rects(self, num_choices):
        # Helper to get rects for collision detection, matching drawing logic
        card_width = 220
        card_height = 320
        spacing = 40
        total_width = num_choices * card_width + (num_choices - 1) * spacing
        start_x = (settings.SCREEN_WIDTH - total_width) // 2
        start_y = (settings.SCREEN_HEIGHT - card_height) // 2
        
        rects = []
        for i in range(num_choices):
            x = start_x + i * (card_width + spacing)
            y = start_y
            rects.append(pygame.Rect(x, y, card_width, card_height))
        return rects
