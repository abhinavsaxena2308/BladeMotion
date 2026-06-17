"""
BladeMotion – Blade Trail Renderer
Draws a glowing multi-layer blade trail.
"""

import math
import pygame
from collections import deque
from src.settings import (
    TRAIL_LENGTH, TRAIL_WIDTH_MAX, TRAIL_WIDTH_MIN,
    TRAIL_COLOR_INNER, TRAIL_COLOR_OUTER, TRAIL_GLOW_COLOR,
)


class BladeTrail:
    def __init__(self):
        self._pts: deque[tuple[int, int]] = deque(maxlen=TRAIL_LENGTH)
        self._sparks = []

    def add(self, pt: tuple[int, int]):
        if pt:
            self._pts.append(pt)
            # Emit sparks occasionally
            import random
            if random.random() < 0.3:
                self._sparks.append({
                    "x": pt[0] + random.uniform(-10, 10),
                    "y": pt[1] + random.uniform(-10, 10),
                    "vx": random.uniform(-1, 1),
                    "vy": random.uniform(-1, 2),
                    "life": 25
                })

    def clear(self):
        self._pts.clear()
        self._sparks.clear()

    def get_points(self) -> list[tuple[int, int]]:
        return list(self._pts)

    def draw(self, surface: pygame.Surface):
        # Update and draw sparks
        for s in self._sparks:
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["life"] -= 1
            if s["life"] > 0:
                alpha = int(255 * (s["life"] / 25))
                # draw tiny spark
                pygame.draw.circle(surface, (*TRAIL_GLOW_COLOR, alpha), (int(s["x"]), int(s["y"])), 2)
        
        self._sparks = [s for s in self._sparks if s["life"] > 0]

        pts = list(self._pts)
        n   = len(pts)
        if n < 2:
            return

        # Draw from oldest to newest so newest is on top
        for i in range(1, n):
            t      = i / n          # 0 (tail) → 1 (head)
            width  = max(TRAIL_WIDTH_MIN, int(TRAIL_WIDTH_MAX * t))
            alpha  = int(220 * t)

            # Blend outer → inner colour along trail
            r = int(TRAIL_COLOR_OUTER[0] * (1 - t) + TRAIL_COLOR_INNER[0] * t)
            g = int(TRAIL_COLOR_OUTER[1] * (1 - t) + TRAIL_COLOR_INNER[1] * t)
            b = int(TRAIL_COLOR_OUTER[2] * (1 - t) + TRAIL_COLOR_INNER[2] * t)

            p1, p2 = pts[i - 1], pts[i]
            length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            if length < 1:
                continue

            # Glow layer (wider, transparent)
            glow_w = width + 8
            seg    = pygame.Surface((int(length) + glow_w + 2,
                                     glow_w * 2 + 2), pygame.SRCALPHA)
            pygame.draw.line(seg, (*TRAIL_GLOW_COLOR, max(0, alpha - 100)),
                             (0, glow_w + 1), (int(length), glow_w + 1), glow_w)

            angle  = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            rotated = pygame.transform.rotate(seg, -math.degrees(angle))
            off_x  = p1[0] - rotated.get_width() // 2
            off_y  = p1[1] - rotated.get_height() // 2
            surface.blit(rotated, (off_x, off_y))

            # Core line
            pygame.draw.line(surface, (r, g, b, alpha),
                             p1, p2, max(1, width - 2))
            # White core
            if width > 4:
                pygame.draw.line(surface, (*TRAIL_COLOR_INNER, alpha),
                                 p1, p2, max(1, width - 6))

        # Bright tip circle at head
        if pts:
            hx, hy = pts[-1]
            tip_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(tip_surf, (*TRAIL_COLOR_INNER, 220), (15, 15), 8)
            pygame.draw.circle(tip_surf, (*TRAIL_GLOW_COLOR, 80),   (15, 15), 14)
            surface.blit(tip_surf, (hx - 15, hy - 15))
