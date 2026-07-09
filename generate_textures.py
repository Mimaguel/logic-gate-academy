#!/usr/bin/env python3
"""Generates small, original, tileable texture images for the UI theme."""
from pathlib import Path
from PIL import Image, ImageDraw
import math

OUT = str(Path(__file__).resolve().parent / "assets" / "images")

RED = (230, 15, 45, 255)
RED_SOFT = (230, 15, 45, 40)
BLACK = (10, 10, 12, 255)
TRANSPARENT = (0, 0, 0, 0)

# --- 1. Halftone dot tile (subtle, low-opacity red dots on transparent) ---
tile = 28
img = Image.new("RGBA", (tile, tile), TRANSPARENT)
draw = ImageDraw.Draw(img)
r = 2.6
draw.ellipse([tile / 2 - r, tile / 2 - r, tile / 2 + r, tile / 2 + r], fill=RED_SOFT)
img.save(f"{OUT}/halftone_dot.png")
print("wrote halftone_dot.png")

# --- 2. Diagonal hazard stripe tile (black + red, 45 degrees) ---
tile2 = 40
img2 = Image.new("RGBA", (tile2, tile2), BLACK)
draw2 = ImageDraw.Draw(img2)
stripe_w = 10
for offset in range(-tile2, tile2 * 2, stripe_w * 2):
    draw2.polygon(
        [
            (offset, 0), (offset + stripe_w, 0),
            (offset + stripe_w - tile2, tile2), (offset - tile2, tile2),
        ],
        fill=RED,
    )
img2.save(f"{OUT}/stripes_hazard.png")
print("wrote stripes_hazard.png")

# --- 3. Thin accent divider (gradient red bar, used under headers) ---
w, h = 400, 6
img3 = Image.new("RGBA", (w, h), TRANSPARENT)
for x in range(w):
    t = x / w
    alpha = int(255 * (1 - abs(t - 0.5) * 1.7)) if abs(t - 0.5) < 0.6 else 0
    alpha = max(0, min(255, alpha))
    for y in range(h):
        img3.putpixel((x, y), (230, 15, 45, alpha))
img3.save(f"{OUT}/accent_bar.png")
print("wrote accent_bar.png")

print("done")
