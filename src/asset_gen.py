"""
BladeMotion – Asset Generator
Creates all fruit/bomb PNG assets procedurally using PIL so no external
downloads are needed. Run once at startup if assets are missing.
"""

import os
import math
from PIL import Image, ImageDraw, ImageFilter

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
FRUIT_DIR = os.path.join(ASSET_DIR, "fruits")


def _ensure(path: str):
    os.makedirs(path, exist_ok=True)


# ─── generic helper ───────────────────────────────────────────────────────────

def _circle(draw: ImageDraw.ImageDraw, cx, cy, r, fill, outline=None, width=3):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill,
                 outline=outline, width=width)


def _gradient_circle(size: int, color_inner, color_outer) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx = cy = size // 2
    for r in range(cx, 0, -1):
        t = 1 - r / cx
        c = tuple(int(color_inner[i] * t + color_outer[i] * (1 - t)) for i in range(3))
        ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r],
                                    fill=(*c, 255))
    return img


# ─── individual fruit drawers ─────────────────────────────────────────────────

def make_apple(size=96) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d    = ImageDraw.Draw(img)
    cx   = size // 2
    r    = int(size * 0.42)
    # body
    d.ellipse([cx - r, cx - r + 4, cx + r, cx + r + 4],
              fill=(200, 30, 30), outline=(140, 10, 10), width=3)
    # highlight
    hr = max(r // 4, 4)
    d.ellipse([cx - r + 8, cx - r + 12, cx - r + 8 + hr, cx - r + 12 + hr],
              fill=(255, 120, 120, 180))
    # stem
    d.line([(cx, cx - r + 4), (cx + 6, cx - r - 8)], fill=(80, 50, 20), width=3)
    # leaf
    leaf_pts = [(cx + 6, cx - r - 8), (cx + 18, cx - r - 16),
                (cx + 14, cx - r - 2)]
    d.polygon(leaf_pts, fill=(40, 160, 40))
    return img


def make_banana(size=96) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx  = size // 2
    # banana body arc using polygon
    pts = []
    for i in range(20):
        a = math.radians(-10 + i * (190 / 19))
        rx = cx + int(math.cos(a) * cx * 0.80)
        ry = cx - int(math.sin(a) * cx * 0.35)
        pts.append((rx, ry))
    # outer arc
    pts2 = []
    for i in range(20):
        a = math.radians(-10 + i * (190 / 19))
        rx = cx + int(math.cos(a) * cx * 0.55)
        ry = cx - int(math.sin(a) * cx * 0.22) + 10
        pts2.append((rx, ry))
    d.polygon(pts + pts2[::-1], fill=(240, 210, 20), outline=(180, 150, 0), width=2)
    # highlight
    d.line([(int(cx * 0.35), int(cx * 0.55)), (int(cx * 1.55), int(cx * 0.45))],
           fill=(255, 250, 130, 200), width=5)
    return img


def make_orange(size=96) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx  = size // 2
    r   = int(size * 0.42)
    d.ellipse([cx - r, cx - r, cx + r, cx + r],
              fill=(240, 130, 20), outline=(190, 90, 10), width=3)
    # texture lines
    for angle in range(0, 360, 45):
        a  = math.radians(angle)
        x1 = cx + int(math.cos(a) * r * 0.15)
        y1 = cx + int(math.sin(a) * r * 0.15)
        x2 = cx + int(math.cos(a) * r * 0.85)
        y2 = cx + int(math.sin(a) * r * 0.85)
        d.line([(x1, y1), (x2, y2)], fill=(200, 100, 10, 120), width=1)
    # highlight
    hr = max(r // 4, 4)
    d.ellipse([cx - r + 6, cx - r + 8, cx - r + 6 + hr, cx - r + 8 + hr],
              fill=(255, 200, 100, 180))
    # stem nub
    d.ellipse([cx - 4, cx - r - 4, cx + 4, cx - r + 4], fill=(60, 120, 20))
    return img


def make_watermelon(size=110) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx  = size // 2
    r   = int(size * 0.44)
    # rind
    d.ellipse([cx - r, cx - r, cx + r, cx + r],
              fill=(40, 160, 40), outline=(20, 100, 20), width=4)
    # white layer
    rw = int(r * 0.88)
    d.ellipse([cx - rw, cx - rw, cx + rw, cx + rw], fill=(230, 240, 220))
    # red flesh
    rr = int(r * 0.74)
    d.ellipse([cx - rr, cx - rr, cx + rr, cx + rr], fill=(220, 50, 50))
    # seeds
    for i in range(5):
        a   = math.radians(i * 72 + 15)
        sx  = cx + int(math.cos(a) * rr * 0.55)
        sy  = cx + int(math.sin(a) * rr * 0.55)
        d.ellipse([sx - 4, sy - 6, sx + 4, sy + 6], fill=(20, 10, 10))
    # highlight
    d.ellipse([cx - rr + 5, cx - rr + 5,
               cx - rr + 5 + rr // 4, cx - rr + 5 + rr // 4],
              fill=(255, 120, 120, 160))
    return img


def make_pineapple(size=110) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx  = size // 2
    # body (oval)
    d.ellipse([cx - 30, 28, cx + 30, size - 8],
              fill=(220, 170, 30), outline=(160, 120, 10), width=3)
    # diamond texture
    for row in range(6):
        for col in range(4):
            x = cx - 22 + col * 14 + (row % 2) * 7
            y = 40 + row * 13
            d.polygon([(x, y - 6), (x + 7, y), (x, y + 6), (x - 7, y)],
                      fill=(180, 130, 20), outline=(140, 100, 10))
    # crown
    for i in range(5):
        a  = math.radians(-80 + i * 40)
        ex = cx + int(math.cos(a) * 24)
        ey = 28 + int(math.sin(a) * 22)
        d.line([(cx, 30), (ex, ey)], fill=(30, 140, 30), width=5)
    return img


def make_cherry(size=64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx  = size // 2
    r   = int(size * 0.30)
    # left cherry
    lx = cx - 10
    d.ellipse([lx - r, cx - r + 8, lx + r, cx + r + 8],
              fill=(190, 20, 30), outline=(130, 10, 20), width=2)
    # right cherry
    rx2 = cx + 10
    d.ellipse([rx2 - r, cx - r + 8, rx2 + r, cx + r + 8],
              fill=(200, 25, 35), outline=(130, 10, 20), width=2)
    # stems
    d.line([(lx, cx - r + 8), (cx, cx - 16)], fill=(60, 120, 20), width=2)
    d.line([(rx2, cx - r + 8), (cx, cx - 16)], fill=(60, 120, 20), width=2)
    d.line([(cx, cx - 16), (cx - 4, cx - 30)], fill=(60, 120, 20), width=2)
    return img


def make_strawberry(size=72) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx  = size // 2
    # heart-ish body
    pts = []
    for i in range(40):
        a  = math.radians(270 + i * (360 / 40))
        r  = 26 + 4 * math.sin(3 * a)
        px = cx + int(r * math.cos(a))
        py = cx + 8 + int(r * math.sin(a) * 1.1)
        pts.append((px, py))
    d.polygon(pts, fill=(210, 40, 60), outline=(160, 20, 40), width=2)
    # seeds (small dots)
    for i in range(8):
        a  = math.radians(i * 45)
        sx = cx + int(math.cos(a) * 14)
        sy = cx + 10 + int(math.sin(a) * 16)
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 220, 200))
    # leaves
    for i in range(4):
        a  = math.radians(-30 + i * 25)
        lx = cx + int(math.cos(a) * 14)
        ly = cx - 14 + int(math.sin(a) * 10)
        d.polygon([(cx, cx - 14), (lx, ly),
                   (cx + int(math.cos(a + 0.3) * 8),
                    cx - 10 + int(math.sin(a + 0.3) * 8))],
                  fill=(40, 160, 40))
    return img


def make_bomb(size=80) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    cx  = size // 2
    r   = int(size * 0.38)
    # body
    d.ellipse([cx - r, cx - r + 4, cx + r, cx + r + 4],
              fill=(30, 30, 30), outline=(0, 0, 0), width=3)
    # shine
    d.ellipse([cx - r + 6, cx - r + 10,
               cx - r + 6 + r // 3, cx - r + 10 + r // 3],
              fill=(80, 80, 80, 180))
    # fuse
    fuse_pts = [(cx + r - 2, cx - r + 4),
                (cx + r + 8, cx - r - 4),
                (cx + r + 12, cx - r - 14)]
    d.line(fuse_pts, fill=(160, 120, 20), width=4)
    # spark
    sx, sy = cx + r + 12, cx - r - 14
    for a in range(0, 360, 45):
        rad = math.radians(a)
        ex  = sx + int(math.cos(rad) * 8)
        ey  = sy + int(math.sin(rad) * 8)
        d.line([(sx, sy), (ex, ey)], fill=(255, 220, 50), width=2)
    d.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=(255, 160, 0))
    return img


# ─── half-fruit maker ─────────────────────────────────────────────────────────

def make_half(img: Image.Image, left: bool) -> Image.Image:
    w, h  = img.size
    out   = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    half  = img.crop((0, 0, w // 2, h) if left else (w // 2, 0, w, h))
    if left:
        out.paste(half, (0, 0))
    else:
        out.paste(half, (w // 2, 0))
    return out


# ─── public API ───────────────────────────────────────────────────────────────

MAKERS = {
    "apple":      (make_apple,      96),
    "banana":     (make_banana,     96),
    "orange":     (make_orange,     96),
    "watermelon": (make_watermelon, 110),
    "pineapple":  (make_pineapple,  110),
    "cherry":     (make_cherry,     64),
    "strawberry": (make_strawberry, 72),
    "bomb":       (make_bomb,       80),
}


def generate_all_assets():
    """Generate all fruit + bomb images if they don't already exist."""
    _ensure(FRUIT_DIR)
    for name, (maker, size) in MAKERS.items():
        out_path = os.path.join(FRUIT_DIR, f"{name}.png")
        if not os.path.exists(out_path):
            img = maker(size)
            img.save(out_path)

        if name != "bomb":
            for side, tag in [("left", True), ("right", False)]:
                half_path = os.path.join(FRUIT_DIR, f"{name}_half_{side}.png")
                if not os.path.exists(half_path):
                    img = maker(size)
                    make_half(img, tag).save(half_path)


if __name__ == "__main__":
    generate_all_assets()
    print("Assets generated in", FRUIT_DIR)
