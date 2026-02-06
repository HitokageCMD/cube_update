import pygame
import config.game_config as settings
from utils.sound_manager import SoundManager
from utils.resource_manager import resource_manager

# 引用 Settings 中的全局变量
game_config = settings.game_config
get_theme_color = settings.get_theme_color

class Camera:
    def __init__(self):
        self.pos = pygame.math.Vector2(0, 0) # 摄像机中心在世界坐标的位置
        self.zoom = 1.0
        self.target_zoom = 1.0
        
    def update(self, target_pos, dt):
        # 平滑跟随目标
        self.pos.x += (target_pos.x - self.pos.x) * 0.1
        self.pos.y += (target_pos.y - self.pos.y) * 0.1
        
        # 平滑缩放
        self.zoom += (self.target_zoom - self.zoom) * 0.1

    def apply(self, world_pos):
        # 将世界坐标转换为屏幕坐标
        # 屏幕中心 + (世界坐标 - 摄像机坐标) * 缩放
        screen_center = pygame.math.Vector2(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
        # Fix: Ensure self.pos is the center of the camera view
        # Correct formula: Screen = ScreenCenter + (World - CameraPos) * Zoom
        return screen_center + (world_pos - self.pos) * self.zoom

    def unapply(self, screen_pos):
        # 将屏幕坐标转换为世界坐标
        # World = CameraPos + (Screen - ScreenCenter) / Zoom
        screen_center = pygame.math.Vector2(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
        return self.pos + (screen_pos - screen_center) / self.zoom

    def draw_grid(self, surface):
        # 绘制无限网格背景
        grid_size = int(100 * self.zoom)
        if grid_size <= 0: return # 避免除零
        
        offset_x = (settings.SCREEN_WIDTH / 2 - self.pos.x * self.zoom) % grid_size
        offset_y = (settings.SCREEN_HEIGHT / 2 - self.pos.y * self.zoom) % grid_size
        
        grid_color = get_theme_color('grid')
        
        for x in range(int(offset_x) - grid_size, settings.SCREEN_WIDTH + grid_size, grid_size):
            pygame.draw.line(surface, grid_color, (x, 0), (x, settings.SCREEN_HEIGHT), 2)
            
        for y in range(int(offset_y) - grid_size, settings.SCREEN_HEIGHT + grid_size, grid_size):
            pygame.draw.line(surface, grid_color, (0, y), (settings.SCREEN_WIDTH, y), 2)
            
        # 绘制原点标记
        origin_screen = self.apply(pygame.math.Vector2(0, 0))
        pygame.draw.circle(surface, get_theme_color('text'), (int(origin_screen.x), int(origin_screen.y)), int(5 * self.zoom))

class Button:
    def __init__(self, text, x, y, width=None, height=None, action=None, font_obj=None, padding=(40, 20)):
        self.text = text
        self.font = font_obj if font_obj else settings.font
        self.padding = padding
        
        # Calculate size from text if width/height are missing
        text_surface = self.font.render(text, True, settings.BLACK)
        text_w, text_h = text_surface.get_size()
        
        required_w = text_w + padding[0]
        required_h = text_h + padding[1]
        
        if width is None or width <= 0:
            width = required_w
        elif width < required_w:
            width = required_w
            
        if height is None or height <= 0:
            height = required_h
            
        self.rect = pygame.Rect(x, y, width, height)
        self.action = action
        self.color = settings.GRAY
        self.hover_color = settings.HOVER_COLOR
        self.text_color = settings.BLACK
        self.visible = True
        
    def center_horizontal(self, screen_width):
        self.rect.centerx = screen_width // 2

    def set_text(self, text, resize=True):
        self.text = text
        if resize:
            text_surface = self.font.render(text, True, settings.BLACK)
            text_w, text_h = text_surface.get_size()
            old_center = self.rect.center
            
            new_w = text_w + self.padding[0]
            new_h = text_h + self.padding[1]
            
            if new_w > self.rect.width:
                self.rect.width = new_w
            
            # Also update height if needed
            if new_h > self.rect.height:
                self.rect.height = new_h
                
            self.rect.center = old_center

    def draw(self, surface, offset=(0, 0)):
        if not self.visible:
            return
            
        # Apply offset to rect for drawing
        draw_rect = self.rect.move(offset[0], offset[1])
            
        # 尝试使用 UI 图片
        img_normal = resource_manager.get_image("ui_button_normal")
        img_hover = resource_manager.get_image("ui_button_hover")
        
        mouse_pos = pygame.mouse.get_pos()
        is_hover = draw_rect.collidepoint(mouse_pos)
        
        if img_normal and img_hover:
            # 使用图片绘制
            target_img = img_hover if is_hover else img_normal
            # 缩放至按钮大小
            scaled_img = pygame.transform.scale(target_img, (draw_rect.width, draw_rect.height))
            surface.blit(scaled_img, draw_rect)
        else:
            # 代码绘制 (Fallback)
            if is_hover:
                current_color = self.hover_color
            else:
                current_color = self.color
            
            pygame.draw.rect(surface, current_color, draw_rect)
            pygame.draw.rect(surface, settings.BLACK, draw_rect, 2)  # 边框

        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=draw_rect.center)
        surface.blit(text_surface, text_rect)

    def check_click(self, event, offset=(0, 0)):
        if not self.visible:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # 左键
                # Check collision with offset rect
                draw_rect = self.rect.move(offset[0], offset[1])
                if draw_rect.collidepoint(event.pos):
                    SoundManager().play_sound("ui_click")
                    return self.action
        return None

class InputBox:
    def __init__(self, x, y, w, h, text='', font=None, text_color=settings.BLACK):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = settings.GRAY
        self.color_active = settings.HOVER_COLOR
        self.color = self.color_inactive
        self.text = str(text)
        self.font = font if font else settings.small_font
        self.text_color = text_color
        self.txt_surface = self.font.render(self.text, True, self.text_color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
            return self.active # Return True if clicked
            
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return "submit"
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    # Filter for numbers only if needed, but generic is fine
                    self.text += event.unicode
                self.txt_surface = self.font.render(self.text, True, self.text_color)
                return "typed"
        return None

    def draw(self, screen):
        # Draw bg
        pygame.draw.rect(screen, settings.WHITE, self.rect)
        # Draw text
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Draw border
        pygame.draw.rect(screen, self.color, self.rect, 2)

class CharacterCard:
    def __init__(self, character_data, x, y, size):
        self.data = character_data
        self.rect = pygame.Rect(x, y, size, size)
        self.selected = False
        
    def draw(self, surface):
        # 绘制背景
        color = self.data['color']
        # 如果选中，绘制高亮边框
        if self.selected:
            pygame.draw.rect(surface, settings.SELECTED_BORDER, self.rect.inflate(10, 10), 5)
            
        # 绘制角色形状
        center = self.rect.center
        size = self.rect.width // 2
        
        if self.data['id'] == 'square':
            pygame.draw.rect(surface, color, pygame.Rect(center[0]-size//2, center[1]-size//2, size, size))
        elif self.data['id'] == 'triangle':
            points = [
                (center[0], center[1] - size//2),
                (center[0] - size//2, center[1] + size//2),
                (center[0] + size//2, center[1] + size//2)
            ]
            pygame.draw.polygon(surface, color, points)
        elif self.data['id'] == 'circle':
            pygame.draw.circle(surface, color, center, size//2)
            
        # 绘制名称
        text = settings.medium_font.render(self.data['name'], True, settings.BLACK)
        text_rect = text.get_rect(center=(center[0], self.rect.bottom + 20))
        surface.blit(text, text_rect)
        
        # 绘制职业
        class_text = settings.small_font.render(f"[{self.data['class']}]", True, settings.DARK_GRAY)
        class_rect = class_text.get_rect(center=(center[0], self.rect.bottom + 50))
        surface.blit(class_text, class_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    SoundManager().play_sound("ui_click")
                    return True
        return False

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label_text):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label_text = label_text
        self.dragging = False
        self.handle_width = 20

    def draw(self, surface):
        # 绘制标签
        label = settings.small_font.render(f"{self.label_text}: {int(self.value * 100)}%", True, settings.BLACK)
        surface.blit(label, (self.rect.x, self.rect.y - 25))

        # 绘制背景条
        pygame.draw.rect(surface, settings.SLIDER_BG, self.rect)
        
        # 绘制填充条
        fill_width = (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, settings.SLIDER_FILL, fill_rect)
        
        # 绘制滑块手柄
        handle_x = self.rect.x + fill_width - self.handle_width // 2
        handle_rect = pygame.Rect(handle_x, self.rect.y - 5, self.handle_width, self.rect.height + 10)
        pygame.draw.rect(surface, settings.HOVER_COLOR if self.dragging else settings.GRAY, handle_rect)
        pygame.draw.rect(surface, settings.BLACK, handle_rect, 1)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.inflate(0, 20).collidepoint(event.pos):
                self.dragging = True
                self.update_value(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_value(event.pos[0])
                return True
        return False

    def update_value(self, mouse_x):
        ratio = (mouse_x - self.rect.x) / self.rect.width
        ratio = max(0, min(1, ratio))
        self.value = self.min_val + ratio * (self.max_val - self.min_val)

class SaveSlotButton(Button):
    def __init__(self, x, y, width, height, slot_index, save_data, action):
        super().__init__("", x, y, width, height, action)
        self.slot_index = slot_index
        self.save_data = save_data
        
    def draw(self, surface):
        super().draw(surface)
        
        # 绘制存档信息
        title = f"存档 {self.slot_index + 1}"
        if self.save_data:
            info = f"Lv.{self.save_data.get('level', 1)} {self.save_data['char_name']}"
            
            # Format game time
            game_time = self.save_data.get('game_time', 0)
            minutes = int(game_time / 60)
            seconds = int(game_time % 60)
            play_time_str = f"时长: {minutes:02d}:{seconds:02d}"
            
            time_str = f"{self.save_data['timestamp']}  {play_time_str}"
        else:
            info = "空存档"
            time_str = ""
            
        title_surf = settings.medium_font.render(title, True, settings.BLACK)
        info_surf = settings.small_font.render(info, True, settings.DARK_GRAY)
        
        # Use bold/darker color for time
        time_surf = settings.small_font.render(time_str, True, settings.BLACK) 
        
        surface.blit(title_surf, (self.rect.x + 20, self.rect.y + 10))
        surface.blit(info_surf, (self.rect.x + 20, self.rect.y + 40))
        surface.blit(time_surf, (self.rect.x + 20, self.rect.y + 70))

class ThemeButton(Button):
    def __init__(self, x, y, size, action):
        super().__init__("", x, y, size, size, action)
        
    def draw(self, surface):
        super().draw(surface)
        # 绘制一个月亮/太阳图标
        center = self.rect.center
        radius = self.rect.width // 4
        
        if game_config['theme'] == 'light':
            # Draw Moon (Dark)
            pygame.draw.circle(surface, (50, 50, 50), center, radius) 
            pygame.draw.circle(surface, self.color, (center[0]-5, center[1]-2), radius) 
        else:
            # Draw Sun (Bright)
            pygame.draw.circle(surface, (255, 215, 0), center, radius)

class KeybindButton(Button):
    def __init__(self, x, y, width, height, config_key, label_text, action):
        self.config_key = config_key
        self.label_text = label_text
        
        # Get current key code from config
        key_code = game_config['key_bindings'][config_key]
        key_name = pygame.key.name(key_code).upper() if key_code != 0 else "未绑定"
        if not key_name: key_name = "未知"
        text = f"{label_text}: {key_name}"
        
        super().__init__(text, x, y, width, height, action)
        self.waiting_for_input = False
        
    def draw(self, surface):
        if self.waiting_for_input:
            self.text = f"{self.label_text}: <按任意键>"
            self.color = (255, 200, 200)
        else:
            key_code = game_config['key_bindings'][self.config_key]
            if key_code == 0:
                key_name = "未绑定"
            elif key_code == settings.MOUSE_LEFT:
                key_name = "鼠标左键"
            elif key_code == settings.MOUSE_RIGHT:
                key_name = "鼠标右键"
            elif key_code == settings.MOUSE_MIDDLE:
                key_name = "鼠标中键"
            else:
                try:
                    key_name = pygame.key.name(key_code).upper()
                    if not key_name: key_name = f"未知({key_code})"
                except:
                    key_name = f"ERR({key_code})"
            
            self.text = f"{self.label_text}: {key_name}"
            self.color = settings.GRAY
            
        super().draw(surface)
