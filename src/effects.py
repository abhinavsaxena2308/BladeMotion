"""
BladeMotion – Visual Effects
Particle system, explosion flash, combo text, score popups.
"""

import random
import math
import pygame
from src.settings import (
    PARTICLE_COUNT_SLICE, PARTICLE_COUNT_BOMB,
    PARTICLE_LIFESPAN, PARTICLE_SPEED_MAX,
    SCREEN_W, SCREEN_H, COLOR_DANGER, COLOR_SCORE,
)


# ─── Particle ─────────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x: float, y: float,
                 color, speed_max: float = PARTICLE_SPEED_MAX,
                 lifespan: int = PARTICLE_LIFESPAN,
                 gravity: float = 0.18,
                 size_range=(2, 7)):
        self.x, self.y = x, y
        angle     = random.uniform(0, math.pi * 2)
        speed     = random.uniform(1, speed_max)
        self.vx   = math.cos(angle) * speed
        self.vy   = math.sin(angle) * speed
        self.gravity  = gravity
        self.life     = lifespan
        self.max_life = lifespan
        self.size     = random.randint(*size_range)
        # colour with slight random tint
        self.color = tuple(min(255, max(0, c + random.randint(-30, 30)))
                           for c in color[:3])
        self.alive = True

    def update(self):
        self.vy  += self.gravity
        self.x   += self.vx
        self.y   += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface):
        alpha = int(255 * self.life / self.max_life)
        r     = max(1, self.size - (self.max_life - self.life) // 6)
        color = (*self.color, alpha)
        surf  = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (r, r), r)
        surface.blit(surf, (int(self.x) - r, int(self.y) - r))


# ─── Splatter ─────────────────────────────────────────────────────────────────

class Splatter:
    """Static mark left on the background."""
    def __init__(self, x: float, y: float, color, size_range=(10, 25)):
        self.x, self.y = x, y
        self.size = random.randint(*size_range)
        self.color = color
        self.life = 300
        self.max_life = 300
        self.alive = True
        
        # Create splatter surface
        self.surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        # Main blob
        pygame.draw.circle(self.surf, self.color, (self.size, self.size), self.size // 2)
        # Little droplets
        for _ in range(4):
            dx = random.randint(-self.size//2, self.size//2)
            dy = random.randint(-self.size//2, self.size//2)
            r  = random.randint(2, max(3, self.size // 3))
            pygame.draw.circle(self.surf, self.color, (self.size + dx, self.size + dy), r)

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface):
        alpha = min(255, int(255 * self.life / 60))  # Fade out in the last 60 frames
        self.surf.set_alpha(alpha)
        surface.blit(self.surf, (int(self.x) - self.size, int(self.y) - self.size))


# ─── FloatingText ─────────────────────────────────────────────────────────────

class FloatingText:
    """Score / combo label that floats upward and fades."""

    def __init__(self, text: str, x: float, y: float,
                 color=(255, 220, 50), size: int = 32, lifespan: int = 55):
        self.text      = text
        self.x, self.y = float(x), float(y)
        self.color     = color
        self.size      = size
        self.life      = lifespan
        self.max_life  = lifespan
        self.vy        = -1.4
        self.alive     = True
        self._font: pygame.font.Font = None  # assigned on first draw

    def update(self):
        self.y    += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface):
        if self._font is None:
            self._font = pygame.font.SysFont("Arial", self.size, bold=True)
        alpha = int(255 * self.life / self.max_life)
        rendered = self._font.render(self.text, True, self.color)
        rendered.set_alpha(alpha)
        r = rendered.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rendered, r)


# ─── FlashEffect ──────────────────────────────────────────────────────────────

class FlashEffect:
    """Brief full-screen colour flash (used for bomb explosion)."""

    def __init__(self, color=(255, 80, 0), duration: int = 18):
        self.color    = color
        self.life     = duration
        self.max_life = duration
        self.alive    = True

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface):
        alpha = int(180 * self.life / self.max_life)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*self.color, alpha))
        surface.blit(overlay, (0, 0))


# ─── EffectsManager ───────────────────────────────────────────────────────────

class EffectsManager:
    """Manages all active visual effects."""

    FRUIT_COLORS = {
        "apple":      (220, 40, 40),
        "banana":     (240, 210, 30),
        "orange":     (240, 140, 20),
        "watermelon": (210, 50, 50),
        "pineapple":  (230, 180, 20),
        "cherry":     (180, 20, 40),
        "strawberry": (210, 40, 60),
    }

    def __init__(self):
        self.particles:    list[Particle]     = []
        self.texts:        list[FloatingText] = []
        self.flashes:      list[FlashEffect]  = []
        self.splatters:    list[Splatter]     = []
        self.shake_timer = 0
        self.shake_intensity = 0

    # ── spawners ─────────────────────────────────────────────────────────────

    def spawn_slice(self, x: float, y: float, fruit_name: str):
        color = self.FRUIT_COLORS.get(fruit_name, (255, 220, 80))
        for _ in range(PARTICLE_COUNT_SLICE):
            self.particles.append(
                Particle(x, y, color, speed_max=7, size_range=(3, 9))
            )
        # juice splatter (larger slower drops)
        for _ in range(8):
            self.particles.append(
                Particle(x, y, color, speed_max=3,
                         lifespan=60, gravity=0.28, size_range=(6, 14))
            )
        # Background splatter mark
        if random.random() < 0.6:
            self.splatters.append(Splatter(x, y, (*color, 140)))
            from src.settings import SPLATTER_COUNT_MAX
            if len(self.splatters) > SPLATTER_COUNT_MAX:
                self.splatters.pop(0)

    def spawn_explosion(self, x: float, y: float):
        from src.settings import SHAKE_INTENSITY_BOMB
        orange  = (255, 130, 20)
        yellow  = (255, 230, 50)
        for _ in range(PARTICLE_COUNT_BOMB):
            color = random.choice([orange, yellow, (255, 60, 20)])
            self.particles.append(
                Particle(x, y, color, speed_max=14,
                         lifespan=50, gravity=0.22, size_range=(4, 12))
            )
        self.flashes.append(FlashEffect((255, 80, 0), duration=20))
        self.shake_timer = 20
        self.shake_intensity = SHAKE_INTENSITY_BOMB

    def add_score_text(self, x: float, y: float, score: int, multiplier: int = 1):
        text = f"+{score * multiplier}"
        if multiplier > 1:
            text += f" x{multiplier}!"
        color = (255, 220, 50) if multiplier == 1 else (80, 255, 160)
        self.texts.append(FloatingText(text, x, y - 20, color=color, size=34))

    def add_combo_text(self, x: float, y: float, combo: int):
        from src.settings import SHAKE_INTENSITY_COMBO
        labels = {2: "DOUBLE!", 3: "TRIPLE!", 4: "FRENZY!"}
        text   = labels.get(combo, f"x{combo} COMBO!")
        self.texts.append(
            FloatingText(text, x, y - 60, color=(80, 230, 255), size=42, lifespan=70)
        )
        if combo >= 3:
            self.shake_timer = 10
            self.shake_intensity = SHAKE_INTENSITY_COMBO
            self.flashes.append(FlashEffect((80, 230, 255), duration=10))

    def add_missed_text(self, x: float, y: float):
        self.texts.append(
            FloatingText("MISS!", x, y, color=COLOR_DANGER, size=30, lifespan=45)
        )

    # ── update / draw ─────────────────────────────────────────────────────────

    def update(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
        for lst in (self.particles, self.texts, self.flashes, self.splatters):
            for obj in lst:
                obj.update()
            lst[:] = [o for o in lst if o.alive]

    def draw_bg_effects(self, surface: pygame.Surface):
        for s in self.splatters:
            s.draw(surface)

    def draw(self, surface: pygame.Surface):
        for p in self.particles:
            p.draw(surface)
        for t in self.texts:
            t.draw(surface)
        for f in self.flashes:
            f.draw(surface)
