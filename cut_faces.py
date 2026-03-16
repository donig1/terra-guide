"""
cut_faces.py — Pret sprite sheet 4x3 ne 12 foto emocioni
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vendos sprite sheet-in si:  assets/spritesheet.png
Rezultati ruhet ne:         assets/faces/face_idle.png  etj.

Grid:  4 kolona  x  3 rreshta  =  12 fytyra
Row 1: idle, happy, sad, angry
Row 2: thinking, surprised, confused, laughing
Row 3: scared, sleep, talking, listening
"""

from PIL import Image
import os

# ── Konfigurim ────────────────────────────────────────────────────────────
INPUT  = os.path.join('assets', 'spritesheet.png')
OUTDIR = os.path.join('assets', 'faces')

COLS = 4
ROWS = 3

# Rendi i emocioneve ne grid (rresht pas rreshti, majtas-djathtas)
NAMES = [
    'idle',      'happy',     'sad',      'angry',
    'thinking',  'surprised', 'confused', 'laughing',
    'scared',    'sleep',     'talking',  'listening',
]

# Koordinatat e sakta te seciles qelize (x0, y0, x1, y1)
# Zbuluar automatikisht nga analiza e pikseleve (alpha detection)
CELLS = [
    # Row 1
    (108, 63, 425, 312),   # idle
    (444, 63, 762, 312),   # happy
    (779, 63, 1086, 312),  # sad
    (1121, 63, 1449, 312), # angry
    # Row 2
    (108, 356, 425, 601),   # thinking
    (444, 356, 762, 601),   # surprised
    (779, 356, 1086, 601),  # confused
    (1121, 356, 1449, 601), # laughing
    # Row 3 (pa etiketat)
    (108, 649, 425, 893),   # scared
    (444, 649, 762, 893),   # sleep
    (779, 649, 1086, 893),  # talking
    (1121, 649, 1449, 893), # listening
]

# ─────────────────────────────────────────────────────────────────────────

def crop_uniform(img, names, cells, outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, (x0, y0, x1, y1) in zip(names, cells):
        cell = img.crop((x0, y0, x1, y1))
        # Bej katrore duke shtuar padding transparent
        w, h = cell.size
        side = max(w, h)
        square = Image.new('RGBA', (side, side), (0, 0, 0, 0))
        square.paste(cell, ((side - w) // 2, (side - h) // 2))
        out_path = os.path.join(outdir, f'face_{name}.png')
        square.save(out_path)
        print(f"  ✓  face_{name}.png   ({x0},{y0}) → ({x1},{y1})  [{w}x{h} → {side}x{side}]")
    print(f"\n✅  Ruajtura {len(names)} foto ne:  {outdir}/")


if __name__ == '__main__':
    if not os.path.exists(INPUT):
        print(f"❌  Nuk u gjet:  {INPUT}")
        exit(1)

    img = Image.open(INPUT).convert('RGBA')
    print(f"Image: {img.size[0]}x{img.size[1]}")
    crop_uniform(img, NAMES, CELLS, OUTDIR)
    print("\nTani rinis:  py -3.11 face_engine.py")
