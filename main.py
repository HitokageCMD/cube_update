import sys
import os

# Ensure the current directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.game import GameManager

if __name__ == "__main__":
    game = GameManager()
    game.run()
