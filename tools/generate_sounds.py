import wave
import math
import random
import struct
import os

def generate_wav(filename, duration, func, volume=0.5, sample_rate=44100):
    if os.path.exists(filename):
        print(f"Skipping {filename} (already exists)")
        return

    n_frames = int(duration * sample_rate)
    data = []
    
    for i in range(n_frames):
        t = i / sample_rate
        # func should return value between -1 and 1
        value = func(t, duration)
        # Scale to 16-bit integer range
        sample = int(value * volume * 32767)
        data.append(struct.pack('<h', sample))
        
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, 'w') as f:
        f.setnchannels(1) # Mono
        f.setsampwidth(2) # 16-bit
        f.setframerate(sample_rate)
        f.writeframes(b''.join(data))
    print(f"Generated {filename}")

# --- Sound Functions ---

def sound_click(t, d):
    # Short high pitch sine wave
    freq = 800
    decay = math.exp(-t * 20)
    return math.sin(2 * math.pi * freq * t) * decay

def sound_attack(t, d):
    # White noise with fast decay
    noise = random.uniform(-1, 1)
    decay = math.exp(-t * 15)
    return noise * decay

def sound_dash(t, d):
    # Slide down frequency (Whoosh)
    start_freq = 800
    end_freq = 200
    curr_freq = start_freq + (end_freq - start_freq) * (t / d)
    return math.sin(2 * math.pi * curr_freq * t) * 0.8

def sound_fan_shot(t, d):
    # Laser-like pew pew
    freq = 600 - (t / d) * 400 # 600 -> 200
    return math.sin(2 * math.pi * freq * t) * (1 - t/d)

def sound_shrink_ball(t, d):
    # Tremolo / Magic hum
    base_freq = 300
    mod_freq = 20
    modulation = math.sin(2 * math.pi * mod_freq * t)
    return math.sin(2 * math.pi * (base_freq + modulation * 50) * t) * 0.8

def sound_collision(t, d):
    # Low thud
    freq = 100 * math.exp(-t * 10)
    return math.sin(2 * math.pi * freq * t) * math.exp(-t * 5)

def sound_damage(t, d):
    # Sharp noise + decay
    noise = random.uniform(-1, 1)
    return noise * math.exp(-t * 20)

def sound_death(t, d):
    # Descending 8-bit slide
    freq = 400 - (t / d) * 350
    # Square waveish
    val = 1 if math.sin(2 * math.pi * freq * t) > 0 else -1
    return val * (1 - t/d)

# --- New Sounds (Material & Game) ---

def sound_hit_metal(t, d):
    # Clang: metallic partials
    f1 = 400
    f2 = 1200 # Overtone
    decay = math.exp(-t * 10)
    v1 = math.sin(2 * math.pi * f1 * t)
    v2 = math.sin(2 * math.pi * f2 * t) * 0.5
    return (v1 + v2) * decay * 0.8

def sound_hit_wood(t, d):
    # Thud: short, mid freq
    freq = 200
    decay = math.exp(-t * 30) # Fast decay
    return math.sin(2 * math.pi * freq * t) * decay

def sound_hit_glass(t, d):
    # Ping: high freq, ring
    freq = 1500
    decay = math.exp(-t * 5) # Slow decay (ringing)
    return math.sin(2 * math.pi * freq * t) * decay * 0.5

def sound_death_metal(t, d):
    # Heavy crash: Noise + Low Sine
    noise = random.uniform(-1, 1)
    sine = math.sin(2 * math.pi * 50 * t)
    decay = math.exp(-t * 3)
    return (noise * 0.7 + sine * 0.3) * decay

def sound_death_wood(t, d):
    # Splintering: Noise bursts with modulation
    noise = random.uniform(-1, 1)
    mod = abs(math.sin(2 * math.pi * 20 * t)) # Amplitude modulation
    decay = math.exp(-t * 5)
    return noise * mod * decay

def sound_death_glass(t, d):
    # Shatter: High noise + high sine
    noise = random.uniform(-1, 1)
    freq = 2000
    sine = math.sin(2 * math.pi * freq * t)
    decay = math.exp(-t * 10)
    return (noise * 0.6 + sine * 0.4) * decay

def sound_xp(t, d):
    # High Ding
    freq = 1200
    decay = math.exp(-t * 8)
    return math.sin(2 * math.pi * freq * t) * decay

def sound_level_up(t, d):
    # Arpeggio C-E-G-C
    # t is 0 to d (1.0s)
    notes = [523.25, 659.25, 783.99, 1046.50] # C5, E5, G5, C6
    idx = int(t / (d/4))
    if idx > 3: idx = 3
    freq = notes[idx]
    local_t = t % (d/4)
    decay = math.exp(-local_t * 5)
    return math.sin(2 * math.pi * freq * local_t) * decay * 0.8

def sound_ui_upgrade(t, d):
    # Chord C-E-G played together
    decay = math.exp(-t * 5)
    c = math.sin(2 * math.pi * 523.25 * t)
    e = math.sin(2 * math.pi * 659.25 * t)
    g = math.sin(2 * math.pi * 783.99 * t)
    return (c + e + g) / 3 * decay

def sound_error(t, d):
    # Buzzer
    return math.sin(2 * math.pi * 150 * t) * (1 if int(t*20)%2==0 else 0) * 0.5

def sound_attack_square(t, d):
    # Heavy swoosh/swing
    freq = 200 - (t/d) * 100
    noise = random.uniform(-0.5, 0.5)
    return (math.sin(2 * math.pi * freq * t) + noise) * (1 - t/d)

def sound_attack_triangle(t, d):
    # Sharp laser/shoot
    freq = 800 - (t/d) * 600
    return math.sin(2 * math.pi * freq * t) * (1 - t/d)

def sound_attack_circle(t, d):
    # Magic cast / chime
    freq = 600
    mod = math.sin(2 * math.pi * 50 * t)
    return math.sin(2 * math.pi * (freq + mod * 100) * t) * (1 - t/d)

# --- Main Generation ---

if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), 'sounds')
    
    sounds = [
        ('ui_click.wav', 0.1, sound_click),
        ('attack.wav', 0.15, sound_attack),
        ('skill_dash.wav', 0.3, sound_dash),
        ('skill_fan_shot.wav', 0.2, sound_fan_shot),
        ('skill_shrink_ball.wav', 0.5, sound_shrink_ball),
        ('collision.wav', 0.1, sound_collision),
        ('damage.wav', 0.2, sound_damage),
        ('death.wav', 0.8, sound_death),
        
        # New Sounds
        ('hit_square.wav', 0.1, sound_hit_metal),
        ('hit_triangle.wav', 0.1, sound_hit_wood),
        ('hit_circle.wav', 0.2, sound_hit_glass),
        
        ('death_square.wav', 0.5, sound_death_metal),
        ('death_triangle.wav', 0.4, sound_death_wood),
        ('death_circle.wav', 0.4, sound_death_glass),
        
        ('xp_pickup.wav', 0.1, sound_xp),
        ('level_up.wav', 1.0, sound_level_up),
        ('ui_upgrade.wav', 0.5, sound_ui_upgrade),
        ('error.wav', 0.2, sound_error),

        # Character Attacks
        ('attack_square.wav', 0.2, sound_attack_square),
        ('attack_triangle.wav', 0.15, sound_attack_triangle),
        ('attack_circle.wav', 0.3, sound_attack_circle)
    ]
    
    for name, duration, func in sounds:
        generate_wav(os.path.join(base_dir, name), duration, func)
