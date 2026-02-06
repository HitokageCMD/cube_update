import pygame
import os
import config.game_config as settings
import time
import random

class SoundManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        self.sounds = {}
        self.last_played = {} # {name: timestamp} for throttling
        self.initialized = True
        
        # Ambience State
        self.current_ambience = None
        self.ambience_channel = None
        self.ambience_fade_start = 0
        self.ambience_fade_duration = 2.0
        self.target_ambience = None
        self.next_ambience_channel = None # For cross-fading
        
        # BGM State
        self.bgm_channel = None
        
        # Initialize mixer if not already done
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"Error initializing mixer: {e}")
                return
        
        # Increase channels to handle busy scenes (e.g. many XP orbs + attacks)
        try:
            pygame.mixer.set_num_channels(32)
            print("Mixer channels set to 32")
            
            # Reserve channels for ambience and music
            pygame.mixer.set_reserved(4) # 0, 1 for music/ambience
            self.bgm_channel = pygame.mixer.Channel(0)
            self.ambience_channel = pygame.mixer.Channel(1)
            self.next_ambience_channel = pygame.mixer.Channel(2)
            
        except Exception as e:
            print(f"Error setting channels: {e}")

        self.load_sounds()
        self.update_volumes()
        
        # BGM is now controlled manually by GameManager

    def load_sounds(self):
        # 使用 settings.SOUNDS_DIR 获取正确的音频目录
        sound_dir = settings.SOUNDS_DIR
        
        if not os.path.exists(sound_dir):
            # Fallback: try relative path for development if resource_path fails or returns CWD incorrectly
            dev_sound_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'sounds')
            if os.path.exists(dev_sound_dir):
                sound_dir = dev_sound_dir
            else:
                print(f"Sound directory not found: {sound_dir}")
                return

        print(f"Loading sounds from {sound_dir}...")
        for root, dirs, files in os.walk(sound_dir):
            for filename in files:
                if filename.endswith(('.wav', '.ogg', '.mp3')):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(root, filename)
                    try:
                        sound = pygame.mixer.Sound(path)
                        self.sounds[name] = sound
                        print(f"Loaded sound: {name}")
                    except Exception as e:
                        print(f"Failed to load sound {filename}: {e}")

    def play_game_bgm(self):
        if self.bgm_channel and 'bgm_game' in self.sounds:
            bgm_vol = settings.game_config.get('bgm_volume', 1.0) * settings.game_config.get('master_volume', 1.0)
            self.bgm_channel.set_volume(bgm_vol * 0.5)
            self.bgm_channel.play(self.sounds['bgm_game'], loops=-1)

    def play_menu_bgm(self):
        # Placeholder for menu BGM
        if self.bgm_channel and 'bgm_menu' in self.sounds:
            bgm_vol = settings.game_config.get('bgm_volume', 1.0) * settings.game_config.get('master_volume', 1.0)
            self.bgm_channel.set_volume(bgm_vol * 0.5)
            self.bgm_channel.play(self.sounds['bgm_menu'], loops=-1)
        else:
            # If no menu bgm, maybe stop game bgm?
            if self.bgm_channel:
                self.bgm_channel.stop()

    def play_sound(self, name):
        """
        Play a sound by name.
        """
        if name in self.sounds:
            try:
                # 1. Throttling for high-frequency sounds
                current_time = time.time()
                last_time = self.last_played.get(name, 0)
                
                # Default throttle threshold
                threshold = 0.05 
                
                # Stricter throttle for XP pickup and hits
                if name == 'xp_pickup': threshold = 0.08
                elif name.startswith('hit_'): threshold = 0.08
                
                if current_time - last_time < threshold:
                    return # Skip playing to prevent spam/starvation
                
                self.last_played[name] = current_time

                # 2. Volume Calculation
                vol = settings.game_config.get('sfx_volume', 1.0)
                master = settings.game_config.get('master_volume', 1.0)
                final_vol = vol * master
                
                self.sounds[name].set_volume(final_vol)
                
                # 3. Priority Playback
                # Force play for critical sounds
                force_play = False
                if name in ['level_up', 'ui_upgrade', 'death_square', 'death_triangle', 'death_circle']:
                    force_play = True
                
                if force_play:
                    # Try to find an available channel, or force grab one
                    channel = pygame.mixer.find_channel(force=True)
                    if channel:
                        channel.play(self.sounds[name])
                    else:
                        # Fallback (should rarely happen with 32 channels and force=True)
                        self.sounds[name].play()
                else:
                    # Normal play (finds empty channel automatically)
                    self.sounds[name].play()
                    
            except Exception as e:
                print(f"Error playing sound {name}: {e}")
        else:
            # Silent fail for missing sounds to avoid spamming console
            pass

    def update_volumes(self):
        """
        Update volume for currently playing sounds (Music mainly, but here we handle global mixer too if needed)
        Sound objects volume is set on play.
        """
        # Update volume for all loaded sound objects immediately
        sfx_vol = settings.game_config.get('sfx_volume', 1.0)
        master = settings.game_config.get('master_volume', 1.0)
        bgm_vol = settings.game_config.get('bgm_volume', 1.0)
        amb_vol = settings.game_config.get('ambient_volume', 1.0)
        
        final_sfx = sfx_vol * master
        final_bgm = bgm_vol * master
        final_amb = amb_vol * master
        
        # Update SFX sounds
        for name, sound in self.sounds.items():
            if not name.startswith('bgm_') and not name.startswith('ambience_'):
                sound.set_volume(final_sfx)
        
        # Update BGM Channel
        if self.bgm_channel:
            self.bgm_channel.set_volume(final_bgm * 0.5)
            
        # Update Ambience Channels
        if self.ambience_channel:
            self.ambience_channel.set_volume(final_amb)
        if self.next_ambience_channel:
            self.next_ambience_channel.set_volume(final_amb)

    def set_ambience(self, biome_type):
        target_name = None
        if biome_type == 1: # Forest
            target_name = 'ambience_forest'
        elif biome_type == 2: # Village
            target_name = 'ambience_village'
        # Plains might just be wind/silence or reuse forest at low volume
        
        if target_name == self.current_ambience:
            return
            
        self.current_ambience = target_name
        
        # Simple switch for now (Cross-fade logic is complex without per-frame update)
        # We'll just stop current and play new if exists
        
        amb_vol = settings.game_config.get('ambient_volume', 1.0) * settings.game_config.get('master_volume', 1.0)
        
        # Crossfade:
        # 1. Fade out current channel
        if self.ambience_channel:
            self.ambience_channel.fadeout(1000)
        
        # 2. Start new channel (if we have a sound)
        if target_name and target_name in self.sounds:
            # Swap channels for simple crossfade simulation
            # We use next_ambience_channel as the "incoming" channel
            
            # Ensure next channel is free or stop it
            # Actually, we should swap the references so self.ambience_channel ALWAYS points to the active one
            
            # Swap references
            self.ambience_channel, self.next_ambience_channel = self.next_ambience_channel, self.ambience_channel
            
            # Stop whatever was on the new 'active' channel (it was the old 'next', possibly playing fading out sound?)
            # No, if we swap, the 'old active' (now next) is fading out.
            # The 'new active' (was next) might be free or busy.
            
            # Force stop new active channel to be sure
            self.ambience_channel.stop()
            
            sound = self.sounds[target_name]
            sound.set_volume(amb_vol)
            self.ambience_channel.play(sound, loops=-1, fade_ms=1000)
        else:
            # If no target sound (e.g. silence), just fade out current and set current to None logic
            pass

    def play_footstep(self, biome_type):
        sound_name = "step_grass"
        if biome_type == 1: # Forest (Dirt?) - Actually Forest is mostly grass/dirt mix.
            # We need terrain type check, not just biome.
            # But biome is a good proxy if we don't have tile info here.
            pass
        
        # If we can get tile type, better. But for now use biome proxy or passed string
        # If input is int (biome), map to sound
        if isinstance(biome_type, int):
            if biome_type == 2: sound_name = "step_stone" # Village has stone roads
        elif isinstance(biome_type, str):
            sound_name = f"step_{biome_type}"
            
        # Randomize pitch slightly? Pygame mixer doesn't support pitch shift easily.
        # Just play.
        self.play_sound(sound_name)
