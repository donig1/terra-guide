"""
setup_faces.py  –  ARES-X Farmer Face Setup
=============================================
1. Saves the embedded sprite-sheet (base64) OR loads it from disk.
2. Splits it into 12 individual expressions (3 cols x 4 rows).
3. Saves them to  assets/faces/
4. Generates animation frames for blink / talk / listen.

Run once:
    py -3.11 setup_faces.py
"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    import numpy as np
except ImportError:
    print("Installing Pillow & numpy …")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "numpy"])
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    import numpy as np

ROOT      = os.path.dirname(os.path.abspath(__file__))
FACES_DIR = os.path.join(ROOT, "assets", "faces")
ANIM_DIR  = os.path.join(ROOT, "assets", "animations")

for d in [FACES_DIR,
          os.path.join(ANIM_DIR, "blink"),
          os.path.join(ANIM_DIR, "talk"),
          os.path.join(ANIM_DIR, "listen")]:
    os.makedirs(d, exist_ok=True)

# ── Names per sprite-sheet position (row-major, 3 cols x 4 rows) ─
FACE_NAMES = [
    "farmer_happy",       # row0 col0
    "farmer_laugh",       # row0 col1
    "farmer_thinking",    # row0 col2
    "farmer_angry",       # row0 col3  ← 4th col would wrap to row1; sheet is 4×3
    "farmer_sad",         # row1 col0
    "farmer_suspicious",  # row1 col1
    "farmer_surprised",   # row1 col2
    "farmer_scared",      # row1 col3
    "farmer_sleep",       # row2 col0
    "farmer_smirk",       # row2 col1
    "farmer_idle",        # row2 col2
    "farmer_confused",    # row2 col3
]

# 4-col x 3-row layout (matches the attached image: 4 cols, 3 rows = 12 faces)
COLS = 4
ROWS = 3


def split_sprite(sheet_path: str):
    """Split sprite sheet and save individual face images."""
    img = Image.open(sheet_path).convert("RGBA")
    w, h   = img.size
    cell_w = w // COLS
    cell_h = h // ROWS

    print(f"Sprite: {w}x{h}  ->  cells {cell_w}x{cell_h}")

    saved = []
    for idx, name in enumerate(FACE_NAMES):
        col = idx % COLS
        row = idx // COLS
        x   = col * cell_w
        y   = row * cell_h
        cell = img.crop((x, y, x + cell_w, y + cell_h))

        # Resize to standard 400×400
        cell = cell.resize((400, 400), Image.LANCZOS)

        out_path = os.path.join(FACES_DIR, f"{name}.png")
        cell.save(out_path, "PNG")
        saved.append(out_path)
        print(f"  [{idx+1:02d}] {name}.png  ({col},{row})")

    return saved


def make_blink_frames(base_img_path: str):
    """
    Generate 3 blink frames from farmer_idle.
    Progressively closes the eyes with a dark band.
    """
    base = Image.open(base_img_path).convert("RGBA")
    w, h = base.size

    # Eye region: roughly top 35–60% of face height
    eye_y_start = int(h * 0.30)
    eye_y_end   = int(h * 0.55)
    eye_h       = eye_y_end - eye_y_start

    for i, close_frac in enumerate([0.35, 0.75, 1.0], start=1):
        frame   = base.copy()
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw    = ImageDraw.Draw(overlay)

        band_h = int(eye_h * close_frac)
        # Top lid comes down
        draw.rectangle(
            [0, eye_y_start, w, eye_y_start + band_h],
            fill=(200, 160, 110, int(255 * close_frac * 0.95))
        )
        # Bottom lid comes up (half as much)
        draw.rectangle(
            [0, eye_y_end - band_h // 2, w, eye_y_end],
            fill=(200, 160, 110, int(255 * close_frac * 0.95))
        )

        frame = Image.alpha_composite(frame, overlay)
        frame = frame.resize((400, 400), Image.LANCZOS)
        out   = os.path.join(ANIM_DIR, "blink", f"blink{i}.png")
        frame.save(out, "PNG")
        print(f"  blink{i}.png")


def make_talk_frames(happy_path: str, laugh_path: str):
    """
    Generate 3 talk frames by cross-blending happy ↔ laugh.
    Simulates mouth opening/closing.
    """
    happy = Image.open(happy_path).convert("RGBA")
    laugh = Image.open(laugh_path).convert("RGBA")

    blends = [0.2, 0.85, 0.45]   # how far toward 'open mouth' (laugh)
    for i, alpha in enumerate(blends, start=1):
        frame = Image.blend(happy, laugh, alpha)
        out   = os.path.join(ANIM_DIR, "talk", f"talk{i}.png")
        frame.save(out, "PNG")
        print(f"  talk{i}.png  (blend {alpha})")


def make_listen_frames(base_path: str):
    """
    Generate 3 listen frames: subtle brightness / contrast shifts
    + tiny vertical nudge to simulate attentive head movement.
    """
    base = Image.open(base_path).convert("RGBA")

    adjustments = [
        (1.05, 1.08, 0),    # slightly brighter, -0 px
        (1.10, 1.15, -3),   # more alert,        -3 px
        (1.03, 1.05, -1),   # settle            -1 px
    ]
    for i, (bright, contrast, dy) in enumerate(adjustments, start=1):
        frame = base.copy()

        # Brightness + contrast tweak
        frame_rgb = frame.convert("RGB")
        frame_rgb = ImageEnhance.Brightness(frame_rgb).enhance(bright)
        frame_rgb = ImageEnhance.Contrast(frame_rgb).enhance(contrast)
        frame     = frame_rgb.convert("RGBA")

        # Tiny vertical shift (head bob)
        if dy != 0:
            shifted = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            shifted.paste(frame, (0, dy))
            frame = shifted

        out = os.path.join(ANIM_DIR, "listen", f"listen{i}.png")
        frame.save(out, "PNG")
        print(f"  listen{i}.png  (bright={bright}, dy={dy})")


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Try to find the sprite sheet
    candidates = [
        os.path.join(ROOT, "sprite_sheet.png"),
        os.path.join(ROOT, "farmer_sprite.png"),
        os.path.join(ROOT, "faces.png"),
    ]

    sheet_path = None
    for c in candidates:
        if os.path.exists(c):
            sheet_path = c
            break

    if not sheet_path:
        print("\n[!] Sprite sheet not found.")
        print("    Save the 12-face farmer image as one of:")
        for c in candidates:
            print(f"      {c}")
        print("    Then run:  py -3.11 setup_faces.py\n")

        # Fallback: generate placeholder colored tiles for testing
        print("[i] Generating placeholder face tiles for testing...")
        COLORS = {
            "farmer_idle":       (200, 190, 160),
            "farmer_happy":      (255, 220, 100),
            "farmer_thinking":   (180, 200, 240),
            "farmer_angry":      (255, 100,  80),
            "farmer_sad":        (140, 160, 200),
            "farmer_confused":   (200, 170, 240),
            "farmer_surprised":  (255, 230, 150),
            "farmer_scared":     (200, 120, 100),
            "farmer_sleep":      (160, 180, 160),
            "farmer_smirk":      (220, 200, 120),
            "farmer_suspicious": (170, 150, 180),
            "farmer_laugh":      (255, 200,  80),
        }
        EMOJI = {
            "farmer_idle": "😐", "farmer_happy": "😊",
            "farmer_thinking": "🤔", "farmer_angry": "😠",
            "farmer_sad": "😢", "farmer_confused": "😕",
            "farmer_surprised": "😮", "farmer_scared": "😱",
            "farmer_sleep": "😴", "farmer_smirk": "😏",
            "farmer_suspicious": "🤨", "farmer_laugh": "😄",
        }
        try:
            import pygame
            pygame.init()
            # Use pygame to draw placeholder images with text
            surf = pygame.Surface((400, 400))
            font_big   = pygame.font.SysFont("segoe ui emoji", 140)
            font_small = pygame.font.SysFont("consolas", 26, bold=True)
            for name, col in COLORS.items():
                surf.fill(col)
                # Draw face circle
                pygame.draw.circle(surf, (230, 200, 160), (200, 200), 170)
                pygame.draw.circle(surf, (80, 60, 40),    (200, 200), 170, 4)
                # Label
                lbl = font_small.render(name.replace("farmer_", "").upper(), True, (40, 30, 20))
                surf.blit(lbl, (200 - lbl.get_width() // 2, 340))
                # Emoji eyes/mouth placeholders
                for ex, ey in [(140, 160), (260, 160)]:
                    pygame.draw.circle(surf, (40, 30, 20), (ex, ey), 22)
                    pygame.draw.circle(surf, (255, 255, 255), (ex - 6, ey - 6), 7)
                if "happy" in name or "laugh" in name or "smirk" in name:
                    pygame.draw.arc(surf, (40,30,20),
                                    pygame.Rect(150, 230, 100, 50), 0, 3.14, 4)
                elif "sad" in name or "scared" in name:
                    pygame.draw.arc(surf, (40,30,20),
                                    pygame.Rect(150, 260, 100, 50), 3.14, 6.28, 4)
                elif "angry" in name:
                    pygame.draw.line(surf, (40,30,20), (150, 270), (250, 270), 5)
                    pygame.draw.line(surf, (40,30,20), (110, 145), (170, 165), 5)
                    pygame.draw.line(surf, (40,30,20), (290, 145), (230, 165), 5)
                elif "thinking" in name or "suspicious" in name:
                    pygame.draw.line(surf, (40,30,20), (150, 270), (250, 260), 4)
                elif "surprised" in name:
                    pygame.draw.circle(surf, (40,30,20), (200, 270), 22)
                else:
                    pygame.draw.line(surf, (40,30,20), (155, 268), (245, 268), 4)

                out = os.path.join(FACES_DIR, f"{name}.png")
                pygame.image.save(surf, out)
                print(f"  placeholder: {name}.png")
            pygame.quit()
        except Exception as e:
            print(f"  pygame fallback failed: {e}")
            print("  Creating simple solid-color placeholders...")
            for name, col in COLORS.items():
                img = Image.new("RGB", (400, 400), col)
                draw = ImageDraw.Draw(img)
                draw.ellipse([30, 30, 370, 370], fill=(230, 200, 160), outline=(80,60,40), width=4)
                draw.text((200, 360), name.replace("farmer_","").upper(),
                          fill=(40,30,20), anchor="mm")
                img.save(os.path.join(FACES_DIR, f"{name}.png"))
                print(f"  placeholder: {name}.png")

        sheet_path = None  # skip split

    if sheet_path:
        print(f"\nSplitting: {sheet_path}")
        split_sprite(sheet_path)

    # Generate animations from saved faces
    idle_path  = os.path.join(FACES_DIR, "farmer_idle.png")
    happy_path = os.path.join(FACES_DIR, "farmer_happy.png")
    laugh_path = os.path.join(FACES_DIR, "farmer_laugh.png")

    if all(os.path.exists(p) for p in [idle_path, happy_path, laugh_path]):
        print("\nGenerate: blink frames")
        make_blink_frames(idle_path)

        print("\nGenerate: talk frames")
        make_talk_frames(happy_path, laugh_path)

        print("\nGenerate: listen frames")
        make_listen_frames(idle_path)
    else:
        print("\n[!] Some face PNGs missing – re-run after providing sprite sheet.")

    print("\n✅  setup_faces.py  complete!")
    print(f"   Faces   -> {FACES_DIR}")
    print(f"   Anims   -> {ANIM_DIR}")
