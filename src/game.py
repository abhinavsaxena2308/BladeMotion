"""
BladeMotion – Core Game Engine
Manages game states, spawn logic, collision, scoring, and the main loop.
"""

import random
import json
import os
import logging
import math
import pygame
import numpy as np
from typing import Optional

from src.settings import (
    SCREEN_W, SCREEN_H, FPS_TARGET, MAX_LIVES, TITLE,
    FRUIT_DEFS, SPAWN_INTERVAL_BASE, SPAWN_INTERVAL_MIN,
    POINTS_PER_LEVEL, BOMB_CHANCE_BASE, BOMB_CHANCE_MAX,
    COMBO_WINDOW_FRAMES, COMBO_MULTIPLIERS,
    HIGH_SCORE_FILE, COLOR_BG,
)
from src.fruit     import Fruit, FruitHalf, Bomb
from src.effects   import EffectsManager
from src.blade     import BladeTrail
from src.audio     import AudioManager
from src.ui        import UIRenderer
from src.hand_tracker import HandTracker

log = logging.getLogger(__name__)

# ─── State constants ──────────────────────────────────────────────────────────
ST_MENU       = "menu"
ST_INSTRUCT   = "instructions"
ST_CAMERA_SEL = "camera_select"
ST_PLAYING    = "playing"
ST_PAUSED     = "paused"
ST_GAME_OVER  = "game_over"


class Game:
    def __init__(self, camera_index: int = 0, debug: bool = False,
                 mouse_mode: bool = False, fullscreen: bool = False):
        self.debug       = debug
        self.mouse_mode  = mouse_mode
        self.camera_index = camera_index

        # ── pygame init ──────────────────────────────────────────────────────
        pygame.init()
        flags = pygame.FULLSCREEN | pygame.SCALED if fullscreen else pygame.RESIZABLE
        self.screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
        pygame.display.set_caption(TITLE)
        self.clock   = pygame.time.Clock()

        # ── subsystems ──────────────────────────────────────────────────────
        self.audio   = AudioManager()
        self.audio.init()
        self.ui      = UIRenderer(self.screen)
        self.tracker = HandTracker(camera_index=camera_index, debug=debug)
        # Blade & effects must be created BEFORE _reset_game_vars()
        self.blade   = BladeTrail()
        self.fx      = EffectsManager()

        # ── state ────────────────────────────────────────────────────────────
        self.state   = ST_MENU
        self._bomb_game_over = False  # flagged when bomb was hit
        self._reset_game_vars()
        self._high_score = self._load_high_score()

        # ── camera ───────────────────────────────────────────────────────────
        self.camera_ok = False
        if not mouse_mode:
            self.camera_ok = self.tracker.start()
        if not self.camera_ok:
            log.info("Running in mouse mode.")

        self._prev_mouse = (SCREEN_W // 2, SCREEN_H // 2)

        # Background gradient surface
        self._bg = self._build_bg()

        # Camera preview surface (small)
        self._cam_surf: Optional[pygame.Surface] = None

        log.info("Game initialised. Camera OK: %s", self.camera_ok)

    # ─── Game variable reset ─────────────────────────────────────────────────

    def _reset_game_vars(self):
        self.score          = 0
        self.lives          = MAX_LIVES
        self.level          = 1
        self.frame          = 0
        self.spawn_timer    = 0
        self.fruits: list[Fruit | Bomb] = []
        self.halves: list[FruitHalf]    = []
        self.blade.clear()
        self.fx             = EffectsManager()
        self._combo_count   = 0
        self._combo_timer   = 0
        self._last_blade_pts: list = []
        self._bomb_game_over = False

    # ─── High score I/O ──────────────────────────────────────────────────────

    def _load_high_score(self) -> int:
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE) as f:
                    return json.load(f).get("high_score", 0)
        except Exception:
            pass
        return 0

    def _save_high_score(self):
        try:
            os.makedirs(os.path.dirname(HIGH_SCORE_FILE), exist_ok=True)
            with open(HIGH_SCORE_FILE, "w") as f:
                json.dump({"high_score": self._high_score}, f)
        except Exception as e:
            log.warning("Could not save high score: %s", e)

    # ─── Background ──────────────────────────────────────────────────────────

    def _build_bg(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            r = int(8  + t * 10)
            g = int(8  + t * 8)
            b = int(20 + t * 25)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_W, y))
        return surf

    # ─── Blade input ─────────────────────────────────────────────────────────

    def _get_blade_pos(self) -> Optional[tuple[int, int]]:
        if self.camera_ok:
            tip = self.tracker.get_tip()
            if tip:
                # MediaPipe gives (0-1) from camera perspective (already mirrored)
                x = int(tip[0] * SCREEN_W)
                y = int(tip[1] * SCREEN_H)
                return (x, y)
            return None
        else:
            # Mouse fallback
            mx, my = pygame.mouse.get_pos()
            return (mx, my)

    # ─── Spawning ─────────────────────────────────────────────────────────────

    def _speed_mult(self) -> float:
        return 1.0 + (self.level - 1) * 0.12

    def _spawn_interval(self) -> int:
        base = SPAWN_INTERVAL_BASE - (self.level - 1) * 8
        return max(SPAWN_INTERVAL_MIN, base)

    def _bomb_chance(self) -> float:
        return min(BOMB_CHANCE_MAX,
                   BOMB_CHANCE_BASE + (self.level - 1) * 0.025)

    def _try_spawn(self):
        self.spawn_timer += 1
        if self.spawn_timer < self._spawn_interval():
            return
        self.spawn_timer = 0

        # Level 4+: chance to spawn a wave
        count = 1
        if self.level >= 4 and random.random() < 0.25:
            count = random.randint(2, 3)

        for _ in range(count):
            if random.random() < self._bomb_chance():
                self.fruits.append(Bomb(self._speed_mult()))
            else:
                defn = random.choice(FRUIT_DEFS)
                self.fruits.append(Fruit(defn, self._speed_mult()))

    # ─── Collision & scoring ─────────────────────────────────────────────────

    def _check_collisions(self):
        blade_pts = self.blade.get_points()
        if len(blade_pts) < 2:
            return

        sliced_this_frame = 0

        for obj in list(self.fruits):
            if not obj.alive or getattr(obj, "sliced", False):
                continue

            if obj.check_slice(blade_pts):
                if isinstance(obj, Bomb):
                    obj.sliced = True
                    obj.alive  = False
                    self.fx.spawn_explosion(obj.x, obj.y)
                    self.audio.play("explosion")
                    self._bomb_game_over = True
                    self.lives = 0
                    return

                # Fruit sliced
                obj.sliced = True
                obj.alive  = False
                sliced_this_frame += 1

                # Combo logic
                self._combo_timer  = COMBO_WINDOW_FRAMES
                self._combo_count += 1
                mult_key  = min(self._combo_count, max(COMBO_MULTIPLIERS.keys()))
                mult      = COMBO_MULTIPLIERS.get(mult_key, 5)

                pts_gained = obj.score * mult
                self.score += pts_gained
                self.fx.spawn_slice(obj.x, obj.y, obj.name)
                self.fx.add_score_text(obj.x, obj.y, obj.score, mult)
                self.audio.play("slice")

                if self._combo_count >= 2:
                    self.fx.add_combo_text(obj.x, obj.y, self._combo_count)
                    self.audio.play("combo")

                for half in obj.spawn_halves():
                    self.halves.append(half)

        # Combo timer decay
        if self._combo_timer > 0:
            self._combo_timer -= 1
        else:
            self._combo_count = 0

    # ─── Level progression ───────────────────────────────────────────────────

    def _update_level(self):
        new_level = self.score // POINTS_PER_LEVEL + 1
        if new_level != self.level:
            self.level = new_level
            log.info("Level up → %d", self.level)

    # ─── Update (playing state) ───────────────────────────────────────────────

    def _update_playing(self):
        self.frame += 1

        # Blade
        pos = self._get_blade_pos()
        self.blade.add(pos)

        # Camera debug overlay
        if self.camera_ok and self.debug:
            frame = self.tracker.get_frame()
            if frame is not None:
                small = pygame.transform.scale(
                    pygame.surfarray.make_surface(
                        np.transpose(frame, (1, 0, 2))
                    ), (320, 180)
                )
                self._cam_surf = small

        # Spawn
        self._try_spawn()

        # Update objects
        for f in self.fruits:
            f.update()
        for h in self.halves:
            h.update()

        # Missed fruits → lose life
        for f in list(self.fruits):
            if isinstance(f, Fruit) and f.missed:
                self.lives -= 1
                self.fx.add_missed_text(f.x, SCREEN_H - 40)
                self.fruits.remove(f)
            elif f.missed:
                self.fruits.remove(f)

        # Clean dead
        self.fruits[:] = [f for f in self.fruits if f.alive]
        self.halves[:] = [h for h in self.halves if h.alive]

        # Collisions
        self._check_collisions()

        # Effects
        self.fx.update()

        # Level
        self._update_level()

        # High score
        if self.score > self._high_score:
            self._high_score = self.score

        # Check game over
        if self.lives <= 0:
            self.audio.play("gameover")
            self._save_high_score()
            self.state = ST_GAME_OVER

    # ─── Draw (playing state) ─────────────────────────────────────────────────

    def _draw_playing(self):
        self.screen.blit(self._bg, (0, 0))

        # Halves (behind whole fruits)
        for h in self.halves:
            h.draw(self.screen)

        # Fruits
        for f in self.fruits:
            f.draw(self.screen)

        # Effects
        self.fx.draw(self.screen)

        # Blade
        self.blade.draw(self.screen)

        # Debug cam
        if self._cam_surf and self.debug:
            self.screen.blit(self._cam_surf, (SCREEN_W - 324, SCREEN_H - 184))
            pygame.draw.rect(self.screen, (80, 180, 255),
                             (SCREEN_W - 326, SCREEN_H - 186, 324, 184), 2)

        # HUD
        combo = min(self._combo_count, max(COMBO_MULTIPLIERS.keys()))
        self.ui.draw_hud(
            self.score, self._high_score, self.lives,
            self.level, self.clock.get_fps(),
            combo=combo, camera_ok=self.camera_ok,
        )

    # ─── Main loop ───────────────────────────────────────────────────────────

    def run(self):
        self.audio.start_music(loop=True)
        running = True

        while running:
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    running = False
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        if self.state == ST_PLAYING:
                            self.state = ST_PAUSED
                        elif self.state == ST_PAUSED:
                            self.state = ST_PLAYING
                    if ev.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    if ev.key == pygame.K_F12 and self.state == ST_PLAYING:
                        self._take_screenshot()
                    if ev.key == pygame.K_d:
                        self.debug = not self.debug

            # ── State machine ───────────────────────────────────────────────
            if self.state == ST_MENU:
                action = self.ui.draw_main_menu(events, self._high_score)
                if action == "start":
                    self._start_game()
                elif action == "instruct":
                    self.state = ST_INSTRUCT
                elif action == "camera":
                    self.state = ST_CAMERA_SEL
                elif action == "exit":
                    running = False

            elif self.state == ST_INSTRUCT:
                action = self.ui.draw_instructions(events)
                if action == "back":
                    self.state = ST_MENU

            elif self.state == ST_CAMERA_SEL:
                cameras = HandTracker.list_cameras()
                sel = self.ui.draw_camera_select(events, cameras)
                if sel is not None:
                    if sel == -1:
                        self.mouse_mode = True
                        self.camera_ok  = False
                    else:
                        self.camera_index = sel
                        if self.tracker.camera_ok:
                            self.tracker.stop()
                        self.tracker = HandTracker(sel, self.debug)
                        self.camera_ok = self.tracker.start()
                    self.state = ST_MENU

            elif self.state == ST_PLAYING:
                self._update_playing()
                self._draw_playing()

            elif self.state == ST_PAUSED:
                self._draw_playing()  # freeze frame
                action = self.ui.draw_pause(events)
                # Volume sliders
                mv, sv = self.ui.draw_volume_sliders(
                    self.audio.music_volume, self.audio.sfx_volume, events
                )
                if mv is not None:
                    self.audio.set_music_volume(mv)
                if sv is not None:
                    self.audio.set_sfx_volume(sv)

                if action == "resume":
                    self.state = ST_PLAYING
                elif action == "restart":
                    self._start_game()
                elif action == "menu":
                    self.state = ST_MENU

            elif self.state == ST_GAME_OVER:
                self._draw_playing()
                action = self.ui.draw_game_over(
                    events, self.score, self._high_score, self._bomb_game_over
                )
                if action == "restart":
                    self._start_game()
                elif action == "menu":
                    self.state = ST_MENU

            pygame.display.flip()
            self.clock.tick(FPS_TARGET)

        self._shutdown()

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _start_game(self):
        self._reset_game_vars()
        self.state = ST_PLAYING

    def _take_screenshot(self):
        import datetime
        ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"screenshot_{ts}.png"
        pygame.image.save(self.screen, fname)
        log.info("Screenshot saved: %s", fname)

    def _shutdown(self):
        self._save_high_score()
        if self.tracker:
            self.tracker.stop()
        pygame.quit()
        log.info("Game shut down.")
