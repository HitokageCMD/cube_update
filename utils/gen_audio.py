import wave
import math
import struct
import random
import os

def generate_sine_wave(frequency, duration, volume=0.5, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    data = []
    for i in range(n_samples):
        t = float(i) / sample_rate
        value = math.sin(2.0 * math.pi * frequency * t) * volume
        packed_value = struct.pack('h', int(value * 32767.0))
        data.append(packed_value)
    return b''.join(data)

def generate_square_wave(frequency, duration, volume=0.3, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    data = []
    for i in range(n_samples):
        t = float(i) / sample_rate
        # Simple square
        val = 1.0 if math.sin(2.0 * math.pi * frequency * t) > 0 else -1.0
        value = val * volume
        packed_value = struct.pack('h', int(value * 32767.0))
        data.append(packed_value)
    return b''.join(data)

def generate_noise(duration, volume=0.2, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    data = []
    for i in range(n_samples):
        value = random.uniform(-1, 1) * volume
        packed_value = struct.pack('h', int(value * 32767.0))
        data.append(packed_value)
    return b''.join(data)

def save_wav(filename, data, sample_rate=44100):
    with wave.open(filename, 'w') as f:
        f.setnchannels(1) # Mono
        f.setsampwidth(2) # 16-bit
        f.setframerate(sample_rate)
        f.writeframes(data)

def create_audio_assets():
    base_dir = os.path.join("assets", "sounds")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # 1. BGM (Simple Arpeggio)
    # C Major: C4, E4, G4, B4
    notes = [261.63, 329.63, 392.00, 493.88, 523.25, 493.88, 392.00, 329.63]
    bgm_data = b''
    # 4 bars of arpeggio
    for _ in range(8): 
        for freq in notes:
            # Add slight decay envelope effect? No, keep simple 8-bit feel
            bgm_data += generate_square_wave(freq, 0.2, 0.1)
    
    save_wav(os.path.join(base_dir, "bgm_game.wav"), bgm_data)
    print("Generated bgm_game.wav")

    # 2. Footsteps (Short noise bursts)
    # Grass: Softer, lower pitch noise
    step_grass = generate_noise(0.1, 0.1)
    save_wav(os.path.join(base_dir, "step_grass.wav"), step_grass)
    
    # Dirt: Slightly crunchier
    step_dirt = generate_noise(0.1, 0.15)
    save_wav(os.path.join(base_dir, "step_dirt.wav"), step_dirt)
    
    # Stone: Sharp click (High pitch sine + noise?)
    step_stone = generate_square_wave(800, 0.05, 0.1) + generate_noise(0.05, 0.1)
    save_wav(os.path.join(base_dir, "step_stone.wav"), step_stone)

    # 3. Ambience
    # Forest: Wind (Low filtered noise - approximated by low volume noise)
    amb_forest = generate_noise(2.0, 0.05) # 2 seconds loop
    save_wav(os.path.join(base_dir, "ambience_forest.wav"), amb_forest)
    
    # Village: Quiet (Just silence or very low hum?)
    amb_village = generate_sine_wave(100, 2.0, 0.02)
    save_wav(os.path.join(base_dir, "ambience_village.wav"), amb_village)
    
    # Rain
    amb_rain = generate_noise(2.0, 0.3)
    save_wav(os.path.join(base_dir, "ambience_rain.wav"), amb_rain)

if __name__ == "__main__":
    create_audio_assets()
