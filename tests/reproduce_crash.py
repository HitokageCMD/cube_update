import sys
import os
import pygame
import random

# Add project root to path
sys.path.append(os.getcwd())

try:
    from core.game import GameManager
    from config.game_config import CHARACTERS, GameState
    import config.game_config as settings
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_game_flow():
    pygame.init()
    # Create window
    pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    
    print("Initializing GameManager...")
    gm = GameManager()
    
    # Test all characters
    for char_data in CHARACTERS:
        char_id = char_data['id']
        print(f"\n=== Testing Character: {char_id} ===")
        
        try:
            gm.start_new_game(char_data)
            
            # Force spawn an enemy immediately
            print("Spawning Enemy...")
            gm.enemy_manager.spawn_enemy(gm.player, 0, force_type='square')
            
            print(f"Testing Game Loop for {char_id} (60 frames)...")
            for i in range(60):
                gm.update(16)
                gm.draw()
                
        except Exception as e:
            print(f"CRASH during loop for {char_id}: {e}")
            import traceback
            traceback.print_exc()
            return

    print("\nTest Completed Successfully for ALL characters!")
    pygame.quit()

if __name__ == "__main__":
    test_game_flow()
