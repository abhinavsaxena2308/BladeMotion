"""Quick headless import test."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from src.settings import FRUIT_DEFS, SCREEN_W, SCREEN_H
from src.fruit import Fruit, Bomb
from src.effects import EffectsManager
from src.blade import BladeTrail
from src.audio import AudioManager

print("All modules imported successfully")
print(f"Screen: {SCREEN_W}x{SCREEN_H}")
print(f"Fruit types: {[d['name'] for d in FRUIT_DEFS]}")

# Quick functional test
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
blade  = BladeTrail()
blade.add((100, 100))
blade.add((200, 200))
pts = blade.get_points()
assert len(pts) == 2, "Blade trail failed"

fx = EffectsManager()
fx.spawn_slice(400, 300, "apple")
fx.update()
print(f"Particles after slice: {len(fx.particles)}")

f = Fruit(FRUIT_DEFS[0])
f.update()
assert f.alive
print(f"Fruit '{f.name}' alive after 1 update: OK")

b = Bomb()
b.update()
assert b.alive
print("Bomb alive after 1 update: OK")

print("\nAll tests PASSED!")
pygame.quit()
