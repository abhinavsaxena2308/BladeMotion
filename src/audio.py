"""
BladeMotion – Audio Manager
Procedurally generates sounds with pygame.sndarray so no audio files are needed.
Also loads external sound files if they exist in assets/sounds/.
"""

import os
import math
import logging
import numpy as np
import pygame

from src.settings import (
    SOUND_DIR, VOLUME_MUSIC, VOLUME_SFX,
)

log = logging.getLogger(__name__)


# ─── Synth helpers ────────────────────────────────────────────────────────────

def _sine(freq: float, duration: float, sample_rate: int = 44100,
          amplitude: float = 0.5, fade_out: bool = True) -> np.ndarray:
    t    = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = amplitude * np.sin(2 * math.pi * freq * t)
    if fade_out:
        envelope = np.linspace(1, 0, len(t)) ** 2
        wave    *= envelope
    return (wave * 32767).astype(np.int16)


def _noise(duration: float, sample_rate: int = 44100,
           amplitude: float = 0.3) -> np.ndarray:
    n    = int(sample_rate * duration)
    wave = amplitude * (np.random.random(n) * 2 - 1)
    env  = np.linspace(1, 0, n) ** 1.5
    return ((wave * env) * 32767).astype(np.int16)


def _make_sound(arr: np.ndarray) -> pygame.mixer.Sound:
    stereo = np.column_stack([arr, arr])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def _synth_slice() -> pygame.mixer.Sound:
    """Whoosh + high click."""
    sr   = 44100
    dur  = 0.18
    n    = int(sr * dur)
    t    = np.linspace(0, dur, n)
    freq = np.linspace(1200, 300, n)
    wave = 0.35 * np.sin(2 * math.pi * np.cumsum(freq) / sr)
    env  = np.exp(-t * 18)
    click = 0.25 * (np.random.random(n) * 2 - 1) * np.exp(-t * 60)
    combined = ((wave * env + click) * 32767).clip(-32767, 32767).astype(np.int16)
    return _make_sound(combined)


def _synth_explosion() -> pygame.mixer.Sound:
    sr   = 44100
    dur  = 0.6
    n    = int(sr * dur)
    t    = np.linspace(0, dur, n)
    noise = (np.random.random(n) * 2 - 1)
    env   = np.exp(-t * 5)
    boom  = 0.6 * np.sin(2 * math.pi * 60 * t) * np.exp(-t * 8)
    combined = ((noise * env * 0.5 + boom) * 32767).clip(-32767, 32767).astype(np.int16)
    return _make_sound(combined)


def _synth_combo() -> pygame.mixer.Sound:
    sr   = 44100
    n    = int(sr * 0.25)
    t    = np.linspace(0, 0.25, n)
    wave = (0.3 * np.sin(2 * math.pi * 880 * t) +
            0.2 * np.sin(2 * math.pi * 1320 * t)) * np.exp(-t * 10)
    return _make_sound((wave * 32767).clip(-32767, 32767).astype(np.int16))


def _synth_gameover() -> pygame.mixer.Sound:
    sr   = 44100
    dur  = 1.0
    n    = int(sr * dur)
    t    = np.linspace(0, dur, n)
    freq = np.linspace(440, 110, n)
    wave = 0.4 * np.sin(2 * math.pi * np.cumsum(freq) / sr) * np.exp(-t * 3)
    return _make_sound((wave * 32767).clip(-32767, 32767).astype(np.int16))


def _synth_menu_music() -> pygame.mixer.Sound:
    sr   = 44100
    dur  = 4.0
    n    = int(sr * dur)
    t    = np.linspace(0, dur, n)
    notes = [261, 329, 392, 523, 392, 329]
    wave  = np.zeros(n)
    step  = n // len(notes)
    for i, freq in enumerate(notes):
        s = i * step
        e = s + step
        segment = np.sin(2 * math.pi * freq * t[s:e])
        envelope = np.ones(len(segment))
        envelope[:int(sr * 0.05)]  = np.linspace(0, 1, int(sr * 0.05))
        envelope[-int(sr * 0.05):] = np.linspace(1, 0, int(sr * 0.05))
        wave[s:e] += 0.25 * segment * envelope
    return _make_sound((wave * 32767).clip(-32767, 32767).astype(np.int16))


# ─── AudioManager ─────────────────────────────────────────────────────────────

class AudioManager:
    def __init__(self):
        self.music_volume  = VOLUME_MUSIC
        self.sfx_volume    = VOLUME_SFX
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._music_sound: pygame.mixer.Sound | None = None
        self._music_channel: pygame.mixer.Channel | None = None
        self._ok = False

    def init(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._ok = True
            self._load_or_synth()
            log.info("Audio initialised.")
        except Exception as e:
            log.warning("Audio init failed: %s", e)

    def _load_or_synth(self):
        def try_load(fname):
            path = os.path.join(SOUND_DIR, fname)
            if os.path.exists(path):
                return pygame.mixer.Sound(path)
            return None

        self._sounds["slice"]     = try_load("slice.wav")     or _synth_slice()
        self._sounds["explosion"] = try_load("explosion.wav") or _synth_explosion()
        self._sounds["combo"]     = try_load("combo.wav")     or _synth_combo()
        self._sounds["gameover"]  = try_load("gameover.wav")  or _synth_gameover()
        self._music_sound         = try_load("menu_music.wav") or _synth_menu_music()

        for snd in self._sounds.values():
            snd.set_volume(self.sfx_volume)

    def play(self, name: str):
        if not self._ok:
            return
        snd = self._sounds.get(name)
        if snd:
            snd.play()

    def start_music(self, loop: bool = True):
        if not self._ok or self._music_sound is None:
            return
        self._music_sound.set_volume(self.music_volume)
        self._music_channel = self._music_sound.play(loops=-1 if loop else 0)

    def stop_music(self):
        if self._music_channel:
            self._music_channel.stop()

    def set_music_volume(self, vol: float):
        self.music_volume = max(0.0, min(1.0, vol))
        if self._music_sound:
            self._music_sound.set_volume(self.music_volume)

    def set_sfx_volume(self, vol: float):
        self.sfx_volume = max(0.0, min(1.0, vol))
        for snd in self._sounds.values():
            snd.set_volume(self.sfx_volume)
