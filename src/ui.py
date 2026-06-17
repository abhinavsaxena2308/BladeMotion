"""
BladeMotion – UI Renderer
All screens: Main Menu, Instructions, Pause, Game Over, HUD.
"""

import pygame
import math
import os
from src.settings import (
    SCREEN_W, SCREEN_H,
    COLOR_BG, COLOR_HUD, COLOR_SCORE, COLOR_LIFE_ON, COLOR_LIFE_OFF,
    COLOR_ACCENT, COLOR_BTN, COLOR_BTN_HOVER, COLOR_BTN_BORDER,
    COLOR_DANGER, COLOR_GREEN, MAX_LIVES, FONT_DIR,
)

# ─── Font helpers ─────────────────────────────────────────────────────────────

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    """Try to load a nice system font, fall back to default."""
    candidates = ["Segoe UI", "Arial", "Helvetica", "DejaVu Sans"]
    for name in candidates:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        except Exception:
            pass
    return pygame.font.Font(None, size)


# ─── Button ───────────────────────────────────────────────────────────────────

class Button:
    def __init__(self, x: int, y: int, w: int, h: int, text: str,
                 font_size: int = 28, color=COLOR_BTN,
                 hover_color=COLOR_BTN_HOVER, border=COLOR_BTN_BORDER,
                 text_color=COLOR_HUD, corner_radius: int = 14):
        self.rect         = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.text         = text
        self.color        = color
        self.hover_color  = hover_color
        self.border       = border
        self.text_color   = text_color
        self.corner_radius = corner_radius
        self._font        = _font(font_size, bold=True)
        self._hovered     = False
        self._scale       = 1.0

    def update(self, mouse_pos):
        self._hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface: pygame.Surface, alpha_mult: float = 1.0):
        color = self.hover_color if self._hovered else self.color
        # glow on hover
        if self._hovered:
            glow = pygame.Surface((self.rect.w + 20, self.rect.h + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.border, 60),
                             glow.get_rect(), border_radius=self.corner_radius + 8)
            surface.blit(glow, (self.rect.x - 10, self.rect.y - 10))

        pygame.draw.rect(surface, color, self.rect, border_radius=self.corner_radius)
        pygame.draw.rect(surface, self.border, self.rect,
                         width=2, border_radius=self.corner_radius)

        rendered = self._font.render(self.text, True, self.text_color)
        r        = rendered.get_rect(center=self.rect.center)
        surface.blit(rendered, r)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and self.rect.collidepoint(event.pos))


# ─── UIRenderer ───────────────────────────────────────────────────────────────

class UIRenderer:
    def __init__(self, screen: pygame.Surface):
        self.screen  = screen
        self.w, self.h = screen.get_size()
        self._tick   = 0

        # Fonts
        self._title_font  = _font(90, bold=True)
        self._sub_font    = _font(32)
        self._hud_font    = _font(28, bold=True)
        self._small_font  = _font(20)

        # Pre-bake background gradient surface
        self._bg = self._make_bg()

        # Buttons – built once
        cx = self.w // 2
        self._menu_buttons = {
            "start":   Button(cx, self.h // 2 + 20,  320, 60, "▶  START GAME"),
            "instruct":Button(cx, self.h // 2 + 100, 320, 60, "ℹ  HOW TO PLAY"),
            "camera":  Button(cx, self.h // 2 + 180, 320, 60, "📷  SELECT CAMERA"),
            "exit":    Button(cx, self.h // 2 + 260, 320, 60, "✕  EXIT",
                              color=(60, 20, 20), hover_color=(100, 30, 30),
                              border=COLOR_DANGER),
        }
        self._pause_buttons = {
            "resume":  Button(cx, self.h // 2,       300, 55, "▶  RESUME"),
            "restart": Button(cx, self.h // 2 + 80,  300, 55, "↺  RESTART"),
            "menu":    Button(cx, self.h // 2 + 160, 300, 55, "⌂  MAIN MENU"),
        }
        self._over_buttons = {
            "restart": Button(cx, self.h // 2 + 60,  300, 55, "↺  PLAY AGAIN"),
            "menu":    Button(cx, self.h // 2 + 140, 300, 55, "⌂  MAIN MENU"),
        }
        self._instruct_buttons = {
            "back": Button(cx, self.h - 80, 250, 50, "← BACK"),
        }

    def _make_bg(self) -> pygame.Surface:
        surf = pygame.Surface((self.w, self.h))
        for y in range(self.h):
            t   = y / self.h
            r   = int(8 + t * 18)
            g   = int(8 + t * 12)
            b   = int(20 + t * 30)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.w, y))
        return surf

    def _overlay(self, alpha: int = 160):
        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, alpha))
        self.screen.blit(ov, (0, 0))

    def _glow_text(self, text: str, font, x: int, y: int,
                   color, glow_color=None, anchor="center"):
        if glow_color is None:
            glow_color = COLOR_ACCENT
        # glow pass
        for offset in range(6, 0, -2):
            gs = font.render(text, True, (*glow_color, 60))
            gs.set_alpha(40)
            r  = gs.get_rect(**{anchor: (x, y)})
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                self.screen.blit(gs, r.move(dx, dy))
        rendered = font.render(text, True, color)
        r        = rendered.get_rect(**{anchor: (x, y)})
        self.screen.blit(rendered, r)

    # ── HUD ──────────────────────────────────────────────────────────────────

    def draw_hud(self, score: int, high_score: int, lives: int,
                 level: int, fps: float, combo: int = 1,
                 camera_ok: bool = True):
        # Score
        self._glow_text(f"{score:06d}", self._hud_font,
                        self.w // 2, 30, COLOR_SCORE, anchor="midtop")
        # High score
        hs_txt = self._small_font.render(f"BEST  {high_score:06d}", True,
                                         (180, 180, 180))
        self.screen.blit(hs_txt, (self.w // 2 - hs_txt.get_width() // 2, 60))

        # Level
        lv_txt = self._hud_font.render(f"LVL {level}", True, COLOR_ACCENT)
        self.screen.blit(lv_txt, (20, 16))

        # Lives (hearts)
        for i in range(MAX_LIVES):
            color = COLOR_LIFE_ON if i < lives else COLOR_LIFE_OFF
            hx    = self.w - 40 - (MAX_LIVES - 1 - i) * 38
            self._draw_heart(hx, 28, 14, color)

        # FPS
        fps_txt = self._small_font.render(f"FPS {int(fps)}", True, (80, 80, 80))
        self.screen.blit(fps_txt, (20, self.h - 28))

        # Camera status
        if not camera_ok:
            cam_txt = self._small_font.render("MOUSE MODE", True, (200, 140, 40))
            self.screen.blit(cam_txt, (20, self.h - 52))

        # Combo indicator
        if combo >= 2:
            labels = {2: "DOUBLE!", 3: "TRIPLE!", 4: "FRENZY!"}
            label  = labels.get(combo, f"x{combo}!")
            pulse  = abs(math.sin(self._tick * 0.12)) * 0.3 + 0.85
            sz     = int(36 * pulse)
            cf     = _font(sz, bold=True)
            self._glow_text(label, cf, self.w // 2, 100,
                            (80, 255, 160), glow_color=(0, 200, 100), anchor="midtop")

        self._tick += 1

    def _draw_heart(self, cx: int, cy: int, r: int, color):
        # simple heart using two circles + triangle
        pygame.draw.circle(self.screen, color, (cx - r // 2, cy - r // 4), r // 2)
        pygame.draw.circle(self.screen, color, (cx + r // 2, cy - r // 4), r // 2)
        pts = [(cx - r, cy), (cx + r, cy), (cx, cy + r + 4)]
        pygame.draw.polygon(self.screen, color, pts)

    # ── Main Menu ────────────────────────────────────────────────────────────

    def draw_main_menu(self, events, high_score: int) -> str | None:
        self.screen.blit(self._bg, (0, 0))
        self._animated_particles()

        # Title
        pulse = abs(math.sin(self._tick * 0.04)) * 0.06 + 0.97
        sz    = int(90 * pulse)
        tf    = _font(sz, bold=True)
        self._glow_text("BLADE", tf, self.w // 2, self.h // 4 - 40,
                        (255, 255, 255), glow_color=COLOR_ACCENT, anchor="center")
        self._glow_text("MOTION", tf, self.w // 2, self.h // 4 + 60,
                        COLOR_ACCENT, glow_color=(255, 255, 255), anchor="center")

        sub = self._sub_font.render("Hand Tracking Fruit Ninja", True, (160, 160, 200))
        self.screen.blit(sub, (self.w // 2 - sub.get_width() // 2,
                               self.h // 4 + 130))

        hs = self._hud_font.render(f"HIGH SCORE  {high_score:06d}", True, COLOR_SCORE)
        self.screen.blit(hs, (self.w // 2 - hs.get_width() // 2,
                               self.h // 4 + 170))

        mouse = pygame.mouse.get_pos()
        for name, btn in self._menu_buttons.items():
            btn.update(mouse)
            btn.draw(self.screen)

        self._tick += 1

        for event in events:
            for name, btn in self._menu_buttons.items():
                if btn.is_clicked(event):
                    return name
        return None

    # ── Instructions ─────────────────────────────────────────────────────────

    def draw_instructions(self, events) -> str | None:
        self.screen.blit(self._bg, (0, 0))
        self._overlay(140)

        lines = [
            ("HOW TO PLAY", (255, 255, 255), 46),
            ("", None, 0),
            ("✋  Hold your hand in front of the webcam", (200, 230, 255), 26),
            ("☝  Your index fingertip is the blade", (200, 230, 255), 26),
            ("🍎  Swipe across fruits to slice them!", (200, 230, 255), 26),
            ("💣  Avoid bombs — they end the game instantly", (255, 180, 180), 26),
            ("", None, 0),
            ("SCORING", (255, 220, 50), 36),
            ("  Small fruit  →  +10 pts", (200, 200, 200), 24),
            ("  Medium fruit →  +20 pts", (200, 200, 200), 24),
            ("  Large fruit  →  +30 pts", (200, 200, 200), 24),
            ("  Slice 2 in one swipe    →  ×2", (80, 255, 160), 24),
            ("  Slice 3 in one swipe    →  ×3", (80, 255, 160), 24),
            ("  Slice 4+ in one swipe   →  ×5 FRENZY", (80, 255, 160), 24),
            ("", None, 0),
            ("  Lose a life for each missed fruit", (255, 180, 180), 24),
            ("  3 missed fruits → Game Over", (255, 180, 180), 24),
        ]
        y = 60
        for text, color, size in lines:
            if text and color and size:
                f   = _font(size, bold=(size >= 36))
                sur = f.render(text, True, color)
                self.screen.blit(sur, (self.w // 2 - sur.get_width() // 2, y))
            y += max(size + 8, 18)

        mouse = pygame.mouse.get_pos()
        for name, btn in self._instruct_buttons.items():
            btn.update(mouse)
            btn.draw(self.screen)

        self._tick += 1
        for event in events:
            for name, btn in self._instruct_buttons.items():
                if btn.is_clicked(event):
                    return name
        return None

    # ── Pause ─────────────────────────────────────────────────────────────────

    def draw_pause(self, events) -> str | None:
        self._overlay(160)
        self._glow_text("PAUSED", _font(72, bold=True),
                        self.w // 2, self.h // 3, (255, 255, 255))
        mouse = pygame.mouse.get_pos()
        for name, btn in self._pause_buttons.items():
            btn.update(mouse)
            btn.draw(self.screen)
        self._tick += 1
        for event in events:
            for name, btn in self._pause_buttons.items():
                if btn.is_clicked(event):
                    return name
        return None

    # ── Game Over ────────────────────────────────────────────────────────────

    def draw_game_over(self, events, score: int, high_score: int,
                       is_bomb: bool = False) -> str | None:
        self._overlay(175)

        title_color = COLOR_DANGER if is_bomb else (255, 255, 255)
        title_text  = "💥  BOMB HIT!" if is_bomb else "GAME OVER"
        self._glow_text(title_text, _font(72, bold=True),
                        self.w // 2, self.h // 3 - 40, title_color)

        sc = _font(40, bold=True).render(f"Score:  {score:06d}", True, COLOR_SCORE)
        self.screen.blit(sc, (self.w // 2 - sc.get_width() // 2, self.h // 3 + 50))

        if score >= high_score and score > 0:
            nb = _font(30).render("✨  NEW HIGH SCORE!", True, (80, 255, 160))
            self.screen.blit(nb, (self.w // 2 - nb.get_width() // 2,
                                  self.h // 3 + 100))
        else:
            hs = _font(28).render(f"Best:   {high_score:06d}", True, (160, 160, 160))
            self.screen.blit(hs, (self.w // 2 - hs.get_width() // 2,
                                  self.h // 3 + 100))

        mouse = pygame.mouse.get_pos()
        for name, btn in self._over_buttons.items():
            btn.update(mouse)
            btn.draw(self.screen)

        self._tick += 1
        for event in events:
            for name, btn in self._over_buttons.items():
                if btn.is_clicked(event):
                    return name
        return None

    # ── Camera selection ─────────────────────────────────────────────────────

    def draw_camera_select(self, events, cameras: list[int]) -> int | None:
        self.screen.blit(self._bg, (0, 0))
        self._overlay(140)
        self._glow_text("SELECT CAMERA", _font(56, bold=True),
                        self.w // 2, 120, (255, 255, 255))

        buttons = {}
        for i, cam_idx in enumerate(cameras):
            btn = Button(self.w // 2, 220 + i * 80, 340, 60,
                         f"Camera {cam_idx}")
            buttons[cam_idx] = btn

        none_btn = Button(self.w // 2, 220 + len(cameras) * 80, 340, 60,
                          "▷  Mouse Mode (no camera)", color=(40, 40, 60))
        buttons[-1] = none_btn

        mouse = pygame.mouse.get_pos()
        for btn in buttons.values():
            btn.update(mouse)
            btn.draw(self.screen)

        for event in events:
            for cam_idx, btn in buttons.items():
                if btn.is_clicked(event):
                    return cam_idx
        return None

    # ── Animated background decoration ───────────────────────────────────────

    _anim_particles: list = []

    def _animated_particles(self):
        import random
        if len(self._anim_particles) < 40:
            self._anim_particles.append({
                "x": random.randint(0, self.w),
                "y": random.randint(0, self.h),
                "vy": random.uniform(-0.5, -0.15),
                "r":  random.randint(1, 3),
                "alpha": random.randint(40, 120),
            })
        for p in self._anim_particles:
            p["y"] += p["vy"]
            if p["y"] < -10:
                p["y"] = self.h + 10
            surf = pygame.Surface((p["r"] * 2, p["r"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (100, 180, 255, p["alpha"]),
                               (p["r"], p["r"]), p["r"])
            self.screen.blit(surf, (p["x"], int(p["y"])))

    # ── Volume sliders (drawn in pause / settings) ────────────────────────────

    def draw_volume_sliders(self, music_vol: float, sfx_vol: float,
                            events) -> tuple[float | None, float | None]:
        """Returns (new_music_vol, new_sfx_vol) if changed, else (None, None)."""
        bar_w, bar_h = 200, 8
        my   = self.h // 2 + 250
        sy   = self.h // 2 + 300
        cx   = self.w // 2

        def draw_slider(y, vol, label):
            lbl = self._small_font.render(label, True, (180, 180, 180))
            self.screen.blit(lbl, (cx - bar_w // 2 - lbl.get_width() - 8,
                                   y - lbl.get_height() // 2))
            track = pygame.Rect(cx - bar_w // 2, y - bar_h // 2, bar_w, bar_h)
            pygame.draw.rect(self.screen, (50, 50, 70), track, border_radius=4)
            fill  = pygame.Rect(track.x, track.y, int(bar_w * vol), bar_h)
            pygame.draw.rect(self.screen, COLOR_ACCENT, fill, border_radius=4)
            knob_x = track.x + int(bar_w * vol)
            pygame.draw.circle(self.screen, (255, 255, 255), (knob_x, y), 8)
            return track

        mt = draw_slider(my, music_vol, "♪ Music")
        st = draw_slider(sy, sfx_vol,  "🔊 SFX")

        new_mv, new_sv = None, None
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mt.collidepoint(event.pos):
                    new_mv = (event.pos[0] - mt.x) / bar_w
                elif st.collidepoint(event.pos):
                    new_sv = (event.pos[0] - st.x) / bar_w

        return new_mv, new_sv
