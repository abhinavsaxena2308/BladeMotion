<div align="center">
  <h1>🍉 BladeMotion</h1>
  <p><b>An Augmented Reality Hand-Tracking Fruit Ninja Clone</b></p>

  <p>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python Version"/></a>
    <a href="https://developers.google.com/mediapipe"><img src="https://img.shields.io/badge/MediaPipe-0.10+-orange?style=for-the-badge&logo=google" alt="MediaPipe"/></a>
    <a href="https://www.pygame.org"><img src="https://img.shields.io/badge/Pygame-2.6+-green?style=for-the-badge&logo=python" alt="Pygame"/></a>
  </p>
</div>

Slice fruits with your bare hands! BladeMotion uses **MediaPipe** and **OpenCV** to track your index finger in real-time, overlaying a glowing blade trail directly onto your webcam feed for an immersive Augmented Reality (AR) experience. Built entirely in Python using **Pygame**.

---

## ✨ Features

- **Augmented Reality (AR)**: The game uses your webcam feed as the full-screen background, allowing you to physically slice fruits falling in your room.
- **Zero-Latency Hand Tracking**: Powered by the modern MediaPipe Tasks API (`HandLandmarker`) running on a dedicated background thread.
- **Two Game Modes**:
  - **Classic**: Standard 3 lives. Bombs cause instant game-over.
  - **Zen Mode**: 90 seconds on the clock, no bombs, pure slicing for the highest score.
- **Procedural Generation**:
  - **Art**: All 7 fruit types and bomb sprites are generated mathematically via `Pillow` on first launch. No image downloads required!
  - **Audio**: Dynamic slice "swoosh" sounds and explosions are synthesised with random pitch variations using `NumPy`.
- **Advanced Visual FX**: Multi-layered glowing blade trail, dynamic screen shake, hit-flash combos, and persistent juice splatters.
- **Combo System**: 2×, 3×, and Frenzy multipliers for multi-slice swipes.
- **Auto-Setup**: The game automatically downloads the required MediaPipe model (`~7.5MB`) on first launch.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/abhinavsaxena2308/BladeMotion.git
cd BladeMotion
```

### 2. Create a virtual environment (Recommended)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run!

```bash
python main.py
```
*(The game will automatically generate all visual assets and download the tracking model on the very first run).*

---

## 🎮 Controls

| Action | How |
|---|---|
| **Slice** | Move your index fingertip across a fruit (or use your mouse) |
| **Pause / Unpause** | `Esc` |
| **Fullscreen** | `F11` |
| **Screenshot** | `F12` |

---

## ⌨️ CLI Options

```
python main.py [OPTIONS]

  --camera INT      Camera device index to use (default: 0)
  --mouse           Force mouse-only mode (disable webcam)
  --fullscreen      Launch in fullscreen
```

### Examples

```bash
# Play with a secondary webcam
python main.py --camera 1

# Play on a laptop without a webcam (uses mouse cursor)
python main.py --mouse
```

---

## 📁 Project Structure

```
BladeMotion/
│
├── main.py                  # Entry point (CLI parsing & asset generation)
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── settings.py          # Configuration (colors, gravity, difficulty)
│   ├── game.py              # Core Game Engine & State Machine
│   ├── fruit.py             # Fruit / Bomb physics & slice collision
│   ├── blade.py             # Glowing multi-layer blade renderer
│   ├── effects.py           # Particles, splatters, and screen shake
│   ├── hand_tracker.py      # Background MediaPipe LIVE_STREAM tracker
│   ├── audio.py             # NumPy synthesised procedural audio
│   ├── ui.py                # Menus, HUD, and bouncy animations
│   └── asset_gen.py         # Procedural PIL sprite generator
│
├── assets/                  
│   ├── fruits/              # Auto-generated PNG sprites
│   └── hand_landmarker.task # Auto-downloaded MediaPipe model
│
└── data/
    └── highscore.json       # Persisted high score
```

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| Camera not found | Run `python main.py --mouse` or try `--camera 1` |
| `mediapipe` import error | Ensure you are on Python `3.9`, `3.10`, or `3.11`. MediaPipe may have issues on `3.12+`. |
| Tracking is laggy | Ensure your environment is well-lit. The tracker thread runs independently to prevent game lag. |
| No sound | Check your OS audio device; the game synthesises all sounds internally. |

---

## 📝 License

MIT License – Feel free to modify and build upon this!

---
<div align="center">
  <i>Made with ✂️ + 🍉 in Python</i>
</div>
