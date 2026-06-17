"""
BladeMotion – Fruit & Bomb objects
Handles projectile physics, slicing, and half-piece animation.
"""

import math
import random
import pygame
from typing import Optional, Tuple
from src.settings import (
    GRAVITY, FRUIT_DEFS, FRUIT_SCORES,
    SCREEN_W, SCREEN_H, FRUIT_DIR,
)


# ─── Image cache ─────────────────────────────────────────────────────────────

_img_cache: dict = {}


def _load(name: str) -> pygame.Surface:
    if name not in _img_cache:
        import os
        path = os.path.join(FRUIT_DIR, f"{name}.png")
        try:
            surf = pygame.image.load(path).convert_alpha()
        except Exception:
            # fallback coloured circle
            surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 60, 60, 220), (40, 40), 38)
        _img_cache[name] = surf
    return _img_cache[name]


# ─── FruitHalf ────────────────────────────────────────────────────────────────

class FruitHalf:
    """A sliced half that flies off with extra velocity."""

    def __init__(self, name: str, x: float, y: float,
                 vx: float, vy: float, side: str):
        self.x, self.y  = x, y
        self.vx, self.vy = vx, vy
        self.angle      = random.uniform(-3, 3)
        self.rotation   = 0.0
        self.alive      = True
        self.alpha      = 255

        raw = _load(f"{name}_half_{side}")
        self.image = pygame.transform.scale(raw, (raw.get_width() // 2 * 2,
                                                  raw.get_height()))
        self._orig = self.image.copy()

    def update(self):
        self.vy += GRAVITY * 1.5
        self.x  += self.vx
        self.y  += self.vy
        self.rotation += self.angle
        self.alpha = max(0, self.alpha - 4)
        if self.y > SCREEN_H + 100 or self.alpha <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface):
        img = pygame.transform.rotate(self._orig, self.rotation)
        img.set_alpha(self.alpha)
        r   = img.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(img, r)


# ─── Fruit ────────────────────────────────────────────────────────────────────

class Fruit:
    """Projectile fruit with arc motion."""

    def __init__(self, definition: dict, speed_mult: float = 1.0):
        self.name   = definition["name"]
        self.size   = definition["size"]
        self.radius = definition["radius"]
        self.score  = FRUIT_SCORES[self.size]
        self.sliced = False
        self.missed = False
        self.alive  = True

        margin = 120
        self.x  = float(random.randint(margin, SCREEN_W - margin))
        self.y  = float(SCREEN_H + self.radius + 10)

        vy_base    = random.uniform(-20, -12) * speed_mult
        self.vx    = random.uniform(-3.5, 3.5)
        self.vy    = vy_base
        self.angle = random.uniform(-180, 180)
        self.spin  = random.uniform(-2.5, 2.5)

        raw        = _load(self.name)
        diameter   = self.radius * 2
        self.image = pygame.transform.scale(raw, (diameter, diameter))
        self._orig = self.image.copy()

    # ── physics ──────────────────────────────────────────────────────────────

    def update(self):
        if not self.alive:
            return
        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy
        self.angle += self.spin

        # fell below screen without being sliced → missed
        if self.y > SCREEN_H + self.radius + 60:
            if not self.sliced:
                self.missed = True
            self.alive = False

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return
        rotated = pygame.transform.rotate(self._orig, self.angle)
        r       = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, r)

    # ── collision ─────────────────────────────────────────────────────────────

    def check_slice(self, blade_pts: list) -> bool:
        """Return True if any blade segment intersects this fruit's circle."""
        if len(blade_pts) < 2:
            return False
        for i in range(len(blade_pts) - 1):
            if self._segment_hits_circle(blade_pts[i], blade_pts[i + 1]):
                return True
        return False

    def _segment_hits_circle(self, p1: Tuple, p2: Tuple) -> bool:
        cx, cy = self.x, self.y
        ax, ay = p1
        bx, by = p2
        dx, dy = bx - ax, by - ay
        fx, fy = ax - cx, ay - cy
        a  = dx * dx + dy * dy
        if a == 0:
            return False
        b  = 2 * (fx * dx + fy * dy)
        c  = fx * fx + fy * fy - self.radius * self.radius
        disc = b * b - 4 * a * c
        if disc < 0:
            return False
        disc  = math.sqrt(disc)
        t1    = (-b - disc) / (2 * a)
        t2    = (-b + disc) / (2 * a)
        return (0 <= t1 <= 1) or (0 <= t2 <= 1)

    def spawn_halves(self):
        """Return two FruitHalf objects flying apart."""
        halves = []
        for side, dx in [("left", -3), ("right", 3)]:
            h = FruitHalf(
                self.name, self.x, self.y,
                self.vx + dx,
                self.vy - random.uniform(1, 3),
                side,
            )
            halves.append(h)
        return halves


# ─── Bomb ─────────────────────────────────────────────────────────────────────

class Bomb:
    """Spawns like a fruit but causes instant game-over on slice."""

    RADIUS = 36

    def __init__(self, speed_mult: float = 1.0):
        self.radius = self.RADIUS
        self.sliced = False
        self.missed = False
        self.alive  = True

        margin  = 120
        self.x  = float(random.randint(margin, SCREEN_W - margin))
        self.y  = float(SCREEN_H + self.radius + 10)
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-18, -11) * speed_mult
        self.angle = 0.0
        self.spin  = random.uniform(-1.5, 1.5)

        raw        = _load("bomb")
        diameter   = self.radius * 2
        self.image = pygame.transform.scale(raw, (diameter, diameter))
        self._orig = self.image.copy()

    def update(self):
        if not self.alive:
            return
        self.vy += GRAVITY
        self.x  += self.vx
        self.y  += self.vy
        self.angle += self.spin
        if self.y > SCREEN_H + self.radius + 60:
            self.missed = True
            self.alive  = False

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return
        rotated = pygame.transform.rotate(self._orig, self.angle)
        r       = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, r)

    def check_slice(self, blade_pts: list) -> bool:
        """Segment-circle test identical to Fruit."""
        if len(blade_pts) < 2:
            return False
        for i in range(len(blade_pts) - 1):
            if self._segment_hits_circle(blade_pts[i], blade_pts[i + 1]):
                return True
        return False

    def _segment_hits_circle(self, p1, p2):
        cx, cy = self.x, self.y
        ax, ay = p1
        bx, by = p2
        dx, dy = bx - ax, by - ay
        fx, fy = ax - cx, ay - cy
        a  = dx * dx + dy * dy
        if a == 0:
            return False
        b  = 2 * (fx * dx + fy * dy)
        c  = fx * fx + fy * fy - self.radius * self.radius
        disc = b * b - 4 * a * c
        if disc < 0:
            return False
        disc = math.sqrt(disc)
        t1   = (-b - disc) / (2 * a)
        t2   = (-b + disc) / (2 * a)
        return (0 <= t1 <= 1) or (0 <= t2 <= 1)
