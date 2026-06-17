"""
BladeMotion - Settings & Constants
All global configuration for the game.
"""

import pygame
import os

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FRUIT_DIR  = os.path.join(ASSETS_DIR, "fruits")
SOUND_DIR  = os.path.join(ASSETS_DIR, "sounds")
BG_DIR     = os.path.join(ASSETS_DIR, "backgrounds")
FONT_DIR   = os.path.join(ASSETS_DIR, "fonts")
DATA_DIR   = os.path.join(BASE_DIR,   "data")
os.makedirs(DATA_DIR, exist_ok=True)

HIGH_SCORE_FILE = os.path.join(DATA_DIR, "highscore.json")

# ─── Display ──────────────────────────────────────────────────────────────────
SCREEN_W    = 1280
SCREEN_H    = 720
FPS_TARGET  = 60
TITLE       = "BladeMotion – Hand Tracking Fruit Ninja"

# ─── Physics ──────────────────────────────────────────────────────────────────
GRAVITY     = 0.25          # pixels / frame²  (applied every frame)
MIN_VY      = -18           # max upward launch speed (negative = up)
MAX_VY      = -10
MIN_VX      = -4
MAX_VX      = 4

# ─── Fruit spawn timing ───────────────────────────────────────────────────────
SPAWN_INTERVAL_BASE = 90    # frames between spawns (level 1)
SPAWN_INTERVAL_MIN  = 28

# ─── Lives & difficulty ───────────────────────────────────────────────────────
MAX_LIVES            = 3
ZEN_MODE_DURATION    = 90 * 60  # 90 seconds in frames (at 60 FPS)
POINTS_PER_LEVEL     = 100
BOMB_CHANCE_BASE     = 0.08  # 8 % chance a spawn is a bomb
BOMB_CHANCE_MAX      = 0.22

# ─── Blade trail ──────────────────────────────────────────────────────────────
TRAIL_LENGTH         = 22   # number of trail points kept
TRAIL_WIDTH_MAX      = 14
TRAIL_WIDTH_MIN      = 2
TRAIL_COLOR_INNER    = (255, 255, 255)
TRAIL_COLOR_OUTER    = (80, 180, 255)
TRAIL_GLOW_COLOR     = (30, 120, 255)

# ─── Combo ────────────────────────────────────────────────────────────────────
COMBO_WINDOW_FRAMES  = 45   # how many frames counts as "one swipe"
COMBO_MULTIPLIERS    = {1: 1, 2: 2, 3: 3, 4: 5}   # slices_in_window → mult

# ─── Scoring ──────────────────────────────────────────────────────────────────
FRUIT_SCORES = {
    "small":  10,
    "medium": 20,
    "large":  30,
}

# ─── Colours ──────────────────────────────────────────────────────────────────
COLOR_BG          = (10, 10, 20)
COLOR_HUD         = (255, 255, 255)
COLOR_SCORE       = (255, 220, 50)
COLOR_LIFE_ON     = (255, 80, 80)
COLOR_LIFE_OFF    = (60, 60, 60)
COLOR_OVERLAY     = (0, 0, 0, 180)
COLOR_ACCENT      = (80, 200, 255)
COLOR_BTN         = (30, 30, 50)
COLOR_BTN_HOVER   = (60, 60, 100)
COLOR_BTN_BORDER  = (80, 180, 255)
COLOR_DANGER      = (255, 60, 60)
COLOR_GREEN       = (60, 220, 120)

# ─── Particle & Effects ───────────────────────────────────────────────────────
PARTICLE_COUNT_SLICE   = 18
PARTICLE_COUNT_BOMB    = 40
PARTICLE_LIFESPAN      = 35   # frames
PARTICLE_SPEED_MAX     = 8

SPLATTER_COUNT_MAX     = 30   # Max splatters on screen at once
SHAKE_INTENSITY_BOMB   = 25   # Screen shake amplitude
SHAKE_INTENSITY_COMBO  = 12

# ─── Fruit definitions (name, size_class, radius) ────────────────────────────
FRUIT_DEFS = [
    {"name": "apple",      "size": "medium", "radius": 38},
    {"name": "banana",     "size": "medium", "radius": 36},
    {"name": "orange",     "size": "medium", "radius": 36},
    {"name": "watermelon", "size": "large",  "radius": 52},
    {"name": "pineapple",  "size": "large",  "radius": 48},
    {"name": "cherry",     "size": "small",  "radius": 24},
    {"name": "strawberry", "size": "small",  "radius": 26},
]

# ─── Audio volumes ────────────────────────────────────────────────────────────
VOLUME_MUSIC  = 0.35
VOLUME_SFX    = 0.70
