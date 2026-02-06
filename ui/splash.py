import pygame
import os
import time
import numpy as np
import config.game_config as settings

# Use moviepy for video + audio
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    try:
        from moviepy import VideoFileClip
    except ImportError:
        print("Could not import VideoFileClip from moviepy. Make sure moviepy is installed correctly.")
        VideoFileClip = None

class SplashRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.finished = False
        self.mode = 'video'
        
        self.clip = None
        self.timer = 0
        self.fade_duration = 1.5 # Fade in time (s)
        self.hold_duration = 1.0 # Hold time after fade
        self.total_duration = 0
        
        # Try to load logo image first as fallback or for static mode
        self.logo_surf = None
        self.logo_rect = None
        logo_path = os.path.join(settings.ASSETS_DIR, "sprites", "ui", "logo.png")
        if os.path.exists(logo_path):
             try:
                 img = pygame.image.load(logo_path).convert_alpha()
                 # Scale logo if too big
                 max_w = settings.SCREEN_WIDTH * 0.6
                 if img.get_width() > max_w:
                     scale = max_w / img.get_width()
                     new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                     img = pygame.transform.scale(img, new_size)
                 self.logo_surf = img
             except Exception as e:
                 print(f"Error loading logo image: {e}")

        if not self.logo_surf:
            self.logo_text = "TPAI GAMES"
            self.logo_surf = settings.title_font.render(self.logo_text, True, settings.WHITE)
            
        self.logo_rect = self.logo_surf.get_rect(center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2))

        video_candidates = ["logo_intro.mp4", "logo.mp4"]
        video_path = None
        for name in video_candidates:
            p = os.path.join(settings.VIDEO_DIR, name)
            if os.path.exists(p):
                video_path = p
                break
        
        if video_path and os.path.exists(video_path):
            try:
                self.clip = VideoFileClip(video_path)
                if self.clip.duration > 0:
                    # Extract and play audio immediately
                    if self.clip.audio:
                        temp_audio = "temp_splash_audio.mp3"
                        self.clip.audio.write_audiofile(temp_audio, logger=None, fps=44100)
                        pygame.mixer.music.load(temp_audio)
                        pygame.mixer.music.play()
                else:
                    self.clip = None
            except Exception as e:
                print(f"Error loading video: {e}")
                self.clip = None
        
        if not self.clip:
            self.mode = 'static'
            self.total_duration = self.fade_duration + self.hold_duration
        else:
            self.mode = 'video'
            # Video dictates duration, but at least fade_duration + hold_duration
            self.total_duration = max(self.fade_duration + self.hold_duration, self.clip.duration)

    def update(self, dt):
        """
        Update animation state using dt (seconds)
        """
        self.timer += dt
        
        if self.timer >= self.total_duration:
            self.finished = True
            self.cleanup()

    def get_alpha(self):
        """
        Calculate alpha based on timer for Fade In effect (0 -> 255)
        """
        if self.timer < self.fade_duration:
            return int((self.timer / self.fade_duration) * 255)
        else:
            return 255

    def draw(self):
        self.screen.fill(settings.BLACK)
        
        alpha = self.get_alpha()
        
        if self.mode == 'video' and self.clip:
            # Video Frame Logic
            # We sync video frame to self.timer
            if self.timer < self.clip.duration:
                try:
                    frame_time = min(self.timer, self.clip.duration - 0.05)
                    frame = self.clip.get_frame(frame_time)
                    frame = frame.swapaxes(0, 1)
                    surf = pygame.surfarray.make_surface(frame)
                    
                    if surf.get_width() != settings.SCREEN_WIDTH or surf.get_height() != settings.SCREEN_HEIGHT:
                        surf = pygame.transform.scale(surf, (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
                    
                    # Apply Alpha to Video Surface
                    surf.set_alpha(alpha)
                    self.screen.blit(surf, (0, 0))
                except Exception as e:
                    print(f"Error drawing video frame: {e}")
            else:
                # Video finished but still holding? Show last frame or black?
                # Usually just black or last frame. Let's show last frame static if needed, 
                # but usually video covers the whole duration.
                pass
                
        else:
            # Static Logic
            self.logo_surf.set_alpha(alpha)
            self.screen.blit(self.logo_surf, self.logo_rect)

    def cleanup(self):
        if self.mode == 'video' and self.clip:
            # Check if mixer is initialized before using it
            if pygame.mixer.get_init():
                try:
                    pygame.mixer.music.stop()
                except: pass
            
            try:
                self.clip.close()
            except: pass
            self.clip = None
            
        if os.path.exists("temp_splash_audio.mp3"):
            try:
                os.remove("temp_splash_audio.mp3")
            except: pass

    def __del__(self):
        self.cleanup()
