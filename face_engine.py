"""
Terra Guide — face_engine.py  (v5 — 4K Premium Redesign)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 4K-quality render — works on any resolution, scales perfectly
• Deep-space aurora background with animated nebula layers
• Glassmorphism HUD panels with neon glow borders
• Layered neon halos, rotating radar ring, particle system
• Premium font stack: Segoe UI / Arial / fallback
• Voice state integrated: listening / speaking / idle
• Thread-safe queue, 60 FPS
"""

import pygame
import math
import random
import threading
import queue
import time
import os

# ─── Pygame init ──────────────────────────────────────────────────────────
pygame.init()
_info = pygame.display.Info()

# ─── Screen ───────────────────────────────────────────────────────────────
W         = _info.current_w
H         = _info.current_h
HUD_H     = 130          # bottom sensor bar
SUB_H     = 52           # subtitle bar above HUD
TOP_H     = 48           # top title bar
FACE_AREA = H - HUD_H - SUB_H - TOP_H

# Face — 72% of face area height, always square, centered
FACE_H    = int(FACE_AREA * 0.72)
FACE_W    = FACE_H
FACE_X    = (W - FACE_W) // 2
FACE_Y    = TOP_H + (FACE_AREA - FACE_H) // 2

# ─── Premium Palette ──────────────────────────────────────────────────────
BG_DEEP   = (  3,  4, 14)   # near-black deep space
BG_MID    = (  5,  9, 22)
COL_TEXT  = (185, 230, 200)
COL_DIM   = ( 55,  80,  60)
COL_TITLE = (220, 255, 230)
COL_GOOD  = ( 30, 230,  95)
COL_WARN  = (240, 175,  20)
COL_BAD   = (235,  45,  40)
ACCENT    = (  0, 210, 100)  # primary neon green
ACCENT2   = ( 30, 150, 255)  # electric blue
ACCENT3   = (130,  60, 255)  # deep purple (thinking)
ACCENT4   = (255, 100,  30)  # amber (warning/confused)
GLASS_BG  = (  8, 18, 12)   # glassmorphism card bg
SUB_TEXT  = (210, 248, 220)
MIC_ON    = ( 40, 225, 100)
MIC_OFF   = ( 40,  50,  45)
SKY_TOP   = BG_DEEP

BASE = os.path.dirname(os.path.abspath(__file__))

# Emrat e skedarëve PNG sipas emocionit — vendosi në assets/faces/
FACE_FILES = {
    'idle':       'face_idle.png',
    'happy':      'face_happy.png',
    'sad':        'face_sad.png',
    'angry':      'face_angry.png',
    'confused':   'face_confused.png',
    'surprised':  'face_surprised.png',
    'thinking':   'face_thinking.png',
    'laughing':   'face_laughing.png',
    'scared':     'face_scared.png',
    'sleep':      'face_sleep.png',
    'talking':    'face_talking.png',
    'listening':  'face_listening.png',
}

# ─── Helpers ───────────────────────────────────────────────────────────────
def lerp(a, b, t):    return a + (b - a) * t
def clamp(v, lo, hi): return max(lo, min(hi, v))
def smooth(t):        t = clamp(t, 0, 1); return t * t * (3 - 2 * t)


# ─── Particle ──────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, kind, x, y):
        self.kind  = kind
        self.x     = float(x)
        self.y     = float(y)
        self.life  = 1.0
        self.angle = random.uniform(0, math.tau)
        self.spin  = random.uniform(-3.5, 3.5)
        if kind == 'confetti':
            self.vx    = random.uniform(-70, 70)
            self.vy    = random.uniform(-120, -40)
            self.color = random.choice([(255,205,0),(80,215,80),(70,175,255),(255,90,145)])
        elif kind == 'spark':
            self.vx    = random.uniform(-80, 80)
            self.vy    = random.uniform(-100, -25)
            self.color = (255, 175, 35)
        elif kind == 'bubble':
            self.vx = random.uniform(-10, 10)
            self.vy = random.uniform(-38, -16)
            self.r  = random.uniform(5, 12)
        elif kind == 'zzz':
            self.vx = random.uniform(-6, 8)
            self.vy = random.uniform(-28, -12)
            self.sz = random.choice([18, 22, 27])

    def update(self, dt):
        self.life  -= dt * 1.05
        self.x     += self.vx * dt
        self.y     += self.vy * dt
        self.angle += self.spin * dt
        if self.kind not in ('bubble', 'zzz'):
            self.vy += 65 * dt

    def draw(self, surf, fn):
        if self.life <= 0:
            return
        a = int(smooth(self.life) * 230)
        if self.kind == 'confetti':
            s2 = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.rect(s2, (*self.color, a), (1, 1, 8, 8), border_radius=2)
            rot = pygame.transform.rotate(s2, math.degrees(self.angle))
            surf.blit(rot, (int(self.x) - rot.get_width()//2,
                            int(self.y) - rot.get_height()//2))
        elif self.kind == 'spark':
            s2 = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(s2, (*self.color, a), (4, 4), 4)
            surf.blit(s2, (int(self.x) - 4, int(self.y) - 4))
        elif self.kind == 'bubble':
            r  = int(self.r)
            s2 = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(s2, (130, 200, 255, a), (r+2, r+2), r, 2)
            surf.blit(s2, (int(self.x) - r, int(self.y) - r))
        elif self.kind == 'zzz':
            t2 = fn.render('z', True, (175, 198, 255))
            t2.set_alpha(a)
            surf.blit(t2, (int(self.x), int(self.y)))


# ─── FarmerFace ────────────────────────────────────────────────────────────
class FarmerFace:

    def __init__(self, screen):
        self.screen      = screen
        self.cmd_queue   = queue.Queue()
        self.state       = 'idle'
        self.t           = 0.0
        self.start_time  = time.time()
        self.fps_display = 60.0

        # Subtitle
        self.subtitle  = ''
        self.sub_alpha = 0.0
        self.sub_timer = 0.0
        self.mic_active= False

        # Blend
        self.prev_state = 'idle'
        self.blend_t    = 1.0
        self.BLEND_DUR  = 0.28

        # Voice state — ndryshon nga VoiceEngine
        self.voice_state = 'idle'   # 'idle' | 'listening' | 'speaking'

        self.particles = []

        self.sensors = dict(
            moisture_pct    = 55.0,
            moisture_status = 'OPTIMAL',
            soil_temp       = 21.0,
            air_temp        = 23.5,
            humidity        = 60.0,
            pump_active     = False,
        )

        random.seed(7)

        # Ambient particles — warm morning fireflies / golden spores
        self._ptcls = [{
            'x':      random.uniform(0, W),
            'y':      random.uniform(0, H),
            'vy':     random.uniform(-18, -4),
            'vx':     random.uniform(-2.0, 2.0),
            'sz':     random.uniform(1.0, 3.2),
            'bright': random.random() > 0.55,
            'ph':     random.uniform(0, math.tau),
            'col':    random.choice([
                (255, 200, 80),  # golden
                (255, 140, 50),  # warm orange
                (255, 225, 120), # pale gold
                (200, 255, 170), # morning green
                (240, 165, 80),  # amber
            ]),
        } for _ in range(80)]

        # Grid + star caches
        self._hex_surf  = None
        self._hex_built = False

        # Baked backgrounds (runs once at startup)
        self._star_surf   = self._bake_star_field()
        self._morning_bg  = self._bake_morning_bg()
        self._horizon_srf = self._bake_horizon()

        # Background image (optional — put assets/bg.png to override)
        self._bg_img = None
        _bgp = os.path.join(BASE, 'assets', 'bg.png')
        if os.path.exists(_bgp):
            try:
                _bgi = pygame.image.load(_bgp).convert()
                self._bg_img = pygame.transform.smoothscale(_bgi, (W, H))
                print('[Face] Loaded bg.png')
            except Exception as e:
                print(f'[Face] bg.png error: {e}')

        # ── Premium font stack ─────────────────────────────────────────
        def _font(names, size, bold=False):
            for n in names:
                try:
                    f = pygame.font.SysFont(n, size, bold=bold)
                    if f: return f
                except Exception:
                    pass
            return pygame.font.SysFont('monospace', size, bold=bold)

        UI   = ['segoeui', 'arial', 'helvetica', 'monospace']
        MONO = ['consolas', 'couriernew', 'monospace']

        self.fn_xs    = _font(MONO,  13, bold=True)  # HUD labels / badges
        self.fn_s     = _font(MONO,  15, bold=True)  # badge text
        self.fn_m     = _font(UI,    18, bold=True)  # general UI
        self.fn_l     = _font(UI,    24, bold=True)  # overlay labels
        self.fn_xl    = _font(UI,    38, bold=True)  # HUD main values
        self.fn_sub   = _font(UI,    22)             # subtitle
        self.fn_title = _font(UI,    26, bold=True)  # top bar title

        self._load_faces()

    # ── Face PNG loader ───────────────────────────────────────────────────
    def _load_faces(self):
        sz        = (FACE_W, FACE_H)
        faces_dir = os.path.join(BASE, 'assets', 'faces')
        single    = os.path.join(BASE, 'assets', 'face.png')
        fallback  = self._make_fallback(sz)

        self.faces = {}
        for state, fname in FACE_FILES.items():
            path = os.path.join(faces_dir, fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.faces[state] = pygame.transform.smoothscale(img, sz)
                    continue
                except Exception as e:
                    print(f'[Face] Could not load {fname}: {e}')
            self.faces[state] = None

        loaded = sum(1 for v in self.faces.values() if v is not None)

        if loaded == 0 and os.path.exists(single):
            try:
                img = pygame.image.load(single).convert_alpha()
                img = pygame.transform.smoothscale(img, sz)
                self.faces = {s: img for s in FACE_FILES}
                print('[Face] Using single face.png for all states')
                return
            except Exception as e:
                print(f'[Face] face.png error: {e}')

        for state in self.faces:
            if self.faces[state] is None:
                self.faces[state] = self.faces.get('idle') or fallback

        if loaded == 0:
            print('[Face] Using placeholder face')
        else:
            print(f'[Face] Loaded {loaded}/{len(FACE_FILES)} emotion faces')

    def _make_fallback(self, size):
        s  = pygame.Surface(size, pygame.SRCALPHA)
        cx = size[0] // 2
        cy = size[1] // 2
        pygame.draw.ellipse(s, (255, 200, 140), (cx-100, cy-120, 200, 230))
        pygame.draw.circle(s, (40, 20, 10), (cx-35, cy-20), 18)
        pygame.draw.circle(s, (40, 20, 10), (cx+35, cy-20), 18)
        pygame.draw.arc(s, (160, 60, 45),
                        pygame.Rect(cx-40, cy+20, 80, 45),
                        math.pi+0.3, math.tau-0.3, 4)
        return s

    # ── Hex grid (full-screen, subtle premium lines) ──────────────────────
    def _bake_hex_grid(self):
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        sz   = max(32, W // 42)   # responsive hex size
        cw   = sz * math.sqrt(3)
        rh   = sz * 1.5
        rows = int(H / rh) + 3
        cols = int(W / cw) + 3
        for row in range(-1, rows):
            for col in range(-1, cols):
                cx2 = col*cw + (cw/2 if row%2 else 0)
                cy2 = row * rh
                pts = [
                    (int(cx2 + sz*0.82*math.cos(math.pi/6 + i*math.pi/3)),
                     int(cy2 + sz*0.82*math.sin(math.pi/6 + i*math.pi/3)))
                    for i in range(6)
                ]
                pygame.draw.polygon(surf, (0, 160, 70, 11), pts, 1)
        return surf

    # ── Star field (200 stars, baked once) ───────────────────────────────
    def _bake_star_field(self):
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        rng  = random.Random(42)
        for _ in range(200):
            sx = rng.randint(0, W-1)
            sy = rng.randint(0, H-1)
            sz = rng.choice([1, 1, 1, 2, 2, 3])
            br = rng.randint(70, 210)
            tint = rng.randint(0, 2)
            if tint == 0:   col = (br, br, br)
            elif tint == 1: col = (int(br*0.55), br, int(br*0.65))
            else:           col = (int(br*0.60), int(br*0.75), br)
            pygame.draw.circle(surf, (*col, br), (sx, sy), max(1, sz-1))
            if sz == 3:
                pygame.draw.line(surf, (*col, br//4), (sx-5, sy), (sx+5, sy), 1)
                pygame.draw.line(surf, (*col, br//4), (sx, sy-5), (sx, sy+5), 1)
        return surf

    # ── Morning sky gradient (baked — runs once at startup) ──────────────
    def _bake_morning_bg(self):
        """Dawn sky: midnight blue → indigo → violet → amber → gold horizon."""
        surf  = pygame.Surface((W, H))
        stops = [
            (0.00, (  8, 10, 42)),
            (0.18, ( 20, 15, 64)),
            (0.35, ( 58, 22, 78)),
            (0.52, (145, 50, 55)),
            (0.66, (210, 90, 24)),
            (0.78, (242, 148, 18)),
            (0.89, (252, 198, 55)),
            (1.00, (195, 140, 78)),
        ]
        for y in range(H):
            tt  = y / max(1, H - 1)
            col = stops[-1][1]
            for j in range(len(stops) - 1):
                ta, ca = stops[j]; tb, cb = stops[j+1]
                if ta <= tt < tb:
                    f   = (tt - ta) / max(1e-6, tb - ta)
                    col = (int(ca[0] + (cb[0]-ca[0])*f),
                           int(ca[1] + (cb[1]-ca[1])*f),
                           int(ca[2] + (cb[2]-ca[2])*f))
                    break
            pygame.draw.line(surf, col, (0, y), (W, y))
        return surf

    # ── Rolling hills horizon silhouette (baked) ─────────────────────────
    def _bake_horizon(self):
        """Dark earth hills with a warm sunrise rim glow along the hilltop."""
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        hy   = int(H * 0.80)

        # Organic hill contour from three overlapping sine waves
        pts = [(0, H)]
        for x in range(0, W + 1, 3):
            yh = hy + int(
                26 * math.sin(x * 0.0072 + 1.0) +
                13 * math.sin(x * 0.0185 + 0.7) +
                 6 * math.sin(x * 0.0410 + 2.4)
            )
            pts.append((x, yh))
        pts.append((W, H))

        # Dark earth body
        pygame.draw.polygon(surf, (10, 20, 12, 248), pts)

        # Warm sunrise rim glow along hilltop
        for k in range(18):
            rim = pygame.Surface((W, 2), pygame.SRCALPHA)
            a   = min(255, int((18 - k) * 10))
            pygame.draw.rect(rim, (255, 190, 70, a), (0, 0, W, 2))
            surf.blit(rim, (0, hy - 9 + k))

        # Foreground darker strip at very bottom
        fh = int(H * 0.10)
        fg = pygame.Surface((W, fh), pygame.SRCALPHA)
        pygame.draw.rect(fg, (6, 14, 6, 235), (0, 0, W, fh))
        surf.blit(fg, (0, H - fh))

        return surf

    # ── API publike ───────────────────────────────────────────────────────
    def set_face(self, state, text='', mic=False):
        """Thirre nga çdo thread për të ndryshuar emocionin + subtitle."""
        self.cmd_queue.put({'state': state, 'text': text, 'mic': mic})

    def update_sensors(self, data):
        """Përditëso të dhënat e sensorëve."""
        self.sensors.update(data)

    # ── Update ────────────────────────────────────────────────────────────
    def update(self, dt, fps):
        self.fps_display = fps
        self.t += dt

        # Lexo komandat nga queue (thread-safe)
        while not self.cmd_queue.empty():
            cmd = self.cmd_queue.get_nowait()
            ns  = cmd.get('state', 'idle')
            if ns != self.state:
                self.prev_state = self.state
                self.state      = ns
                self.blend_t    = 0.0
            self.mic_active = cmd.get('mic', False)
            txt = cmd.get('text', '')
            if txt:
                self.subtitle  = txt
                self.sub_alpha = 255.0
                self.sub_timer = 0.0

        self.blend_t = min(1.0, self.blend_t + dt / self.BLEND_DUR)

        # Subtitle fade in/out
        if self.subtitle:
            self.sub_timer += dt
            hold = max(2.5, len(self.subtitle) * 0.055)
            if self.sub_timer > hold:
                self.sub_alpha = max(0, self.sub_alpha - dt * 160)
                if self.sub_alpha <= 0:
                    self.subtitle = ''
            else:
                self.sub_alpha = min(255, self.sub_alpha + dt * 350)

        # Ambient particle physics
        for p in self._ptcls:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            if p['y'] < -8:
                p['y'] = H + 6
                p['x'] = random.uniform(0, W)
            if p['x'] < -5 or p['x'] > W + 5:
                p['x'] = random.uniform(0, W)

        # Particula bazuar në gjendje
        if self.state == 'laughing' and random.random() < dt * 5:
            self.particles.append(Particle('confetti',
                FACE_X+FACE_W//2+random.uniform(-150,150), FACE_Y+40))
        if self.state == 'thinking' and random.random() < dt * 1.5:
            self.particles.append(Particle('bubble',
                FACE_X+FACE_W-60+random.uniform(-20,30), FACE_Y+80))
        if self.state == 'angry' and random.random() < dt * 2.5:
            self.particles.append(Particle('spark',
                FACE_X+FACE_W//2+random.uniform(-100,100),
                FACE_Y+random.uniform(0, FACE_H)))
        if self.state in ('idle','sleep') and random.random() < dt * 0.5:
            self.particles.append(Particle('zzz',
                FACE_X+FACE_W-50+random.uniform(0,30), FACE_Y+60))

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self):
        s = self.screen
        self._draw_bg(s)
        self._draw_face(s)
        for p in self.particles:
            p.draw(s, self.fn_l)
        self._draw_subtitle(s)
        self._draw_hud(s)
        self._draw_overlay(s)

    # ── Helper: state color ───────────────────────────────────────────────
    def _state_color(self):
        return {
            'happy':     COL_GOOD,
            'angry':     COL_BAD,
            'sad':       ACCENT2,
            'talking':   ACCENT,
            'listening': ACCENT2,
            'thinking':  ACCENT3,
            'surprised': COL_WARN,
            'laughing':  COL_WARN,
            'scared':    ACCENT2,
            'sleep':     COL_DIM,
            'confused':  ACCENT4,
        }.get(self.state, ACCENT)

    # ── Background — morning sky + crepuscular rays + mist + hills ───────
    def _draw_bg(self, s):
        if not self._hex_built:
            self._hex_surf  = self._bake_hex_grid()
            self._hex_built = True

        sc = self._state_color()
        cx0 = FACE_X + FACE_W // 2
        cy0 = FACE_Y + FACE_H // 2

        # 1. Morning sky gradient (or custom bg.png override)
        if self._bg_img:
            s.blit(self._bg_img, (0, 0))
        else:
            s.blit(self._morning_bg, (0, 0))

        # 2. Stars (visible in upper portion of pre-dawn sky)
        if self._star_surf:
            st = self._star_surf.copy()
            # Fade stars out in lower half — sunrise washes them away
            mask = pygame.Surface((W, H), pygame.SRCALPHA)
            for y in range(H):
                fade = clamp((y / H - 0.25) / 0.40, 0, 1)
                alpha = int(255 * fade)
                pygame.draw.line(mask, (0, 0, 0, alpha), (0, y), (W, y))
            st.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            s.blit(st, (0, 0))

        # 3. Sunrise solar disk (warm golden orb at horizon)
        sun_x = cx0
        sun_y = int(H * 0.80)
        sun_r = max(38, W // 30)
        pulse_sun = 0.90 + 0.10 * math.sin(self.t * 0.55)
        for sr in range(sun_r + int(sun_r*1.8), sun_r - 2, -8):
            fade = clamp(1.0 - (sr - sun_r) / (sun_r * 1.8), 0, 1)
            a_sun = max(0, min(255, int(fade * fade * 90 * pulse_sun)))
            gs = pygame.Surface((sr*2, sr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (255, 200, 60, a_sun), (sr, sr), sr)
            s.blit(gs, (sun_x - sr, sun_y - sr), special_flags=pygame.BLEND_RGBA_ADD)
        # hard disk
        pygame.draw.circle(s, (255, 230, 140), (sun_x, sun_y), sun_r)
        pygame.draw.circle(s, (255, 248, 200), (sun_x, sun_y), max(1, sun_r - 6))

        # 4. Crepuscular rays from sun
        NUM_RAYS = 14
        for ri in range(NUM_RAYS):
            angle = -math.pi / 2 + (ri - NUM_RAYS//2) * (math.pi / (NUM_RAYS * 1.1))
            ray_len = int(H * 1.2)
            spread = sun_r // 2
            ox1 = sun_x + int(math.cos(angle - 0.06) * spread)
            oy1 = sun_y + int(math.sin(angle - 0.06) * spread)
            ox2 = sun_x + int(math.cos(angle + 0.06) * spread)
            oy2 = sun_y + int(math.sin(angle + 0.06) * spread)
            ex1 = sun_x + int(math.cos(angle - 0.06) * ray_len)
            ey1 = sun_y + int(math.sin(angle - 0.06) * ray_len)
            ex2 = sun_x + int(math.cos(angle + 0.06) * ray_len)
            ey2 = sun_y + int(math.sin(angle + 0.06) * ray_len)
            ray_pts = [
                (ox1, oy1), (ox2, oy2), (ex2, ey2), (ex1, ey1)
            ]
            # Pulsing brightness
            pulse_r = 0.65 + 0.35 * math.sin(self.t * 0.28 + ri * 0.7)
            a_ray = max(0, min(255, int(22 * pulse_r)))
            ray_s = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.polygon(ray_s, (255, 215, 100, a_ray), ray_pts)
            s.blit(ray_s, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # 5. Morning mist layers near horizon
        mist_y = int(H * 0.74)
        for mk in range(6):
            mh = max(1, int(H * 0.06) - mk * 8)
            my = mist_y + mk * 9
            ma = max(0, min(255, 55 - mk * 8))
            mist = pygame.Surface((W, mh), pygame.SRCALPHA)
            pygame.draw.rect(mist, (220, 200, 170, ma), (0, 0, W, mh))
            s.blit(mist, (0, my))

        # 6. Rolling hills silhouette
        if self._horizon_srf:
            s.blit(self._horizon_srf, (0, 0))

        # 7. Hex grid overlay (subtle — gives tech feel over natural bg)
        if self._hex_surf:
            s.blit(self._hex_surf, (0, 0))

        # 8. Outer glow behind face (warm gold tinted)
        p0 = 0.38 + 0.14 * math.sin(self.t * 0.95)
        warm_col = (
            min(255, sc[0] + 40),
            min(255, sc[1] + 20),
            min(255, sc[2]),
        )
        for i, rr in enumerate([int(FACE_W*0.72), int(FACE_W*0.60),
                                  int(FACE_W*0.48), int(FACE_W*0.36)]):
            a = max(0, int(p0 * (22 - i*5)))
            gs = pygame.Surface((rr*2, rr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*warm_col, a), (rr, rr), rr, max(1, 3-i))
            s.blit(gs, (cx0-rr, cy0-rr))

        # 9. Ambient golden fireflies
        for p in self._ptcls:
            base_a = 220 if p['bright'] else 80
            a2 = int(clamp((0.5+0.5*math.sin(self.t*0.85+p['ph'])) * base_a, 0, 255))
            r2 = max(1, int(p['sz']))
            if p['bright']:
                gs2 = pygame.Surface((r2*6+2, r2*6+2), pygame.SRCALPHA)
                pygame.draw.circle(gs2, (*p['col'], max(0, a2//4)), (r2*3+1, r2*3+1), r2*3)
                s.blit(gs2, (int(p['x'])-r2*3, int(p['y'])-r2*3))
            ps2 = pygame.Surface((r2*2+2, r2*2+2), pygame.SRCALPHA)
            pygame.draw.circle(ps2, (*p['col'], a2), (r2+1, r2+1), r2)
            s.blit(ps2, (int(p['x'])-r2, int(p['y'])-r2))

        # 10. Soft side vignette
        vw = max(80, W // 10)
        vstep = max(1, vw // 6)
        vig_col = (8, 4, 2)
        for ew in range(vw, 0, -vstep):
            a3 = min(255, int((vw - ew) * 2.0))
            vs = pygame.Surface((ew, H), pygame.SRCALPHA)
            pygame.draw.rect(vs, (*vig_col, a3), (0, 0, ew, H))
            s.blit(vs, (0, 0))
            s.blit(vs, (W - ew, 0))

        # 11. Corner brackets — warm gold
        bsz = max(28, W // 50); bth = 2
        GOLD = (230, 180, 60)
        for bx, by, dx, dy in [
            (8, 8, 1, 1), (W-8, 8, -1, 1),
            (8, H-8, 1, -1), (W-8, H-8, -1, -1),
        ]:
            pygame.draw.line(s, GOLD, (bx, by), (bx + dx*bsz, by), bth)
            pygame.draw.line(s, GOLD, (bx, by), (bx, by + dy*bsz), bth)
            pygame.draw.circle(s, GOLD, (bx, by), 3)

    # ── Face Image — premium rings, glow, cross-fade ─────────────────────
    def _draw_face(self, s):
        fx = FACE_X; fy = FACE_Y
        cx = fx + FACE_W // 2
        cy = fy + FACE_H // 2
        sc = self._state_color()
        pulse = 0.72 + 0.28 * math.sin(self.t * 2.1)

        # Outer diffuse glow halo
        halo_r = FACE_W // 2 + int(FACE_W * 0.22)
        for gw in range(halo_r, halo_r - 55, -11):
            a4 = max(0, int(pulse * (55 - (halo_r - gw)) * 0.7))
            gsurf = pygame.Surface((gw*2, gw*2), pygame.SRCALPHA)
            pygame.draw.circle(gsurf, (*sc, a4), (gw, gw), gw)
            s.blit(gsurf, (cx - gw, cy - gw), special_flags=pygame.BLEND_RGBA_ADD)

        # Radar / tick ring
        tick_r    = FACE_W // 2 + int(FACE_W * 0.06)
        tick_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        num_ticks = 60
        for i in range(num_ticks):
            angle = -self.t * 0.18 + i * math.tau / num_ticks
            major = (i % 15 == 0); mid = (i % 5 == 0)
            r1 = tick_r + (0 if major else (2 if mid else 4))
            r2 = tick_r + (18 if major else (10 if mid else 5))
            brightness = 230 if major else (110 if mid else 45)
            lw = 2 if major else 1
            x1,y1 = int(cx+r1*math.cos(angle)), int(cy+r1*math.sin(angle))
            x2,y2 = int(cx+r2*math.cos(angle)), int(cy+r2*math.sin(angle))
            pygame.draw.line(tick_surf, (*sc, brightness), (x1,y1),(x2,y2), lw)

        # Arc progress fill
        arc_fill = {'talking':0.88,'listening':0.65,'thinking':0.50,
                    'happy':1.0,'angry':0.92,'idle':0.28,
                    'sad':0.40,'confused':0.55}.get(self.state, 0.50)
        arc_r2   = tick_r + 24
        arc_rect = pygame.Rect(cx-arc_r2, cy-arc_r2, arc_r2*2, arc_r2*2)
        end_a    = -math.pi/2
        start_a  = end_a - arc_fill * math.tau
        pygame.draw.arc(tick_surf, (*sc, 180), arc_rect, start_a, end_a, 4)
        pygame.draw.arc(tick_surf, (*sc, 55),  arc_rect.inflate(8,8), start_a, end_a, 9)

        # Secondary inner counter-rotating tick ring
        tick_r2 = FACE_W // 2 - int(FACE_W * 0.04)
        for ii in range(32):
            ang2 = self.t * 0.32 + ii * math.tau / 32
            r2a  = tick_r2 - 3
            r2b  = tick_r2 + (11 if ii % 8 == 0 else 5)
            br2  = 180 if ii % 8 == 0 else 50
            lw2  = 2 if ii % 8 == 0 else 1
            x2a,y2a = int(cx+r2a*math.cos(-ang2)), int(cy+r2a*math.sin(-ang2))
            x2b,y2b = int(cx+r2b*math.cos(-ang2)), int(cy+r2b*math.sin(-ang2))
            pygame.draw.line(tick_surf, (*sc, br2), (x2a,y2a),(x2b,y2b), lw2)

        # Decorative rotating dashed orbit rings
        for orb_r, orb_sp, orb_a, orb_dash in [
            (tick_r + int(FACE_W*0.12),  0.038, 40, 9),
            (tick_r + int(FACE_W*0.24), -0.022, 24, 6),
        ]:
            steps = 200
            for j in range(steps):
                ao = self.t * orb_sp + j * math.tau / steps
                if j % orb_dash < (orb_dash * 2 // 3):
                    ox = int(cx + orb_r * math.cos(ao))
                    oy = int(cy + orb_r * math.sin(ao))
                    pygame.draw.circle(tick_surf, (*sc, orb_a), (ox, oy), 1)

        s.blit(tick_surf, (0, 0))

        # Inner neon ring
        ring_r = FACE_W // 2 + 3
        for gw in range(22, 0, -5):
            a4b = max(0, int(pulse * (22 - gw) * 1.4))
            rs2 = pygame.Surface((ring_r*2+gw*2, ring_r*2+gw*2), pygame.SRCALPHA)
            pygame.draw.circle(rs2, (*sc, a4b), (ring_r+gw, ring_r+gw), ring_r+gw, 2)
            s.blit(rs2, (cx-ring_r-gw, cy-ring_r-gw))
        rs_hard = pygame.Surface(((ring_r+2)*2, (ring_r+2)*2), pygame.SRCALPHA)
        pygame.draw.circle(rs_hard, (*sc, 200), (ring_r+2, ring_r+2), ring_r, 2)
        s.blit(rs_hard, (cx-ring_r-2, cy-ring_r-2))

        # Face PNG cross-fade
        cur  = self.faces.get(self.state) or self.faces.get('idle')
        prev = self.faces.get(self.prev_state) or self.faces.get('idle')
        if cur is None:
            return
        if self.blend_t < 1.0 and prev is not None and prev is not cur:
            t2 = smooth(self.blend_t)
            ps = prev.copy(); ps.set_alpha(int(255*(1.0-t2))); s.blit(ps,(fx,fy))
            cs = cur.copy();  cs.set_alpha(int(255*t2));       s.blit(cs,(fx,fy))
        else:
            s.blit(cur, (fx, fy))

        # MIC indicator — top-right of face
        mic_x = fx + FACE_W - 30
        mic_y = fy + 30
        mc = MIC_ON if self.mic_active else MIC_OFF
        if self.mic_active:
            mp2 = 0.5 + 0.5*math.sin(self.t * 7)
            mgs = pygame.Surface((38,38), pygame.SRCALPHA)
            pygame.draw.circle(mgs, (*MIC_ON, int(60*mp2)), (19,19), 18)
            s.blit(mgs, (mic_x-6, mic_y-6))
        pygame.draw.circle(s, mc, (mic_x, mic_y), 10)
        pygame.draw.circle(s, (0,0,0), (mic_x, mic_y), 10, 2)
        lt = self.fn_xs.render('MIC', True, (210,235,215) if self.mic_active else (60,75,65))
        s.blit(lt, (mic_x - lt.get_width()//2, mic_y + 14))

        # State badge below face
        bt  = self.fn_s.render(self.state.upper(), True, COL_TITLE)
        bw  = bt.get_width() + 32
        bh2 = bt.get_height() + 14
        bx3 = cx - bw//2
        by3 = fy + FACE_H + 10
        badge = pygame.Surface((bw, bh2), pygame.SRCALPHA)
        pygame.draw.rect(badge, (*BG_DEEP, 210), (0,0,bw,bh2), border_radius=12)
        pygame.draw.rect(badge, (*sc, 160), (0,0,bw,bh2), width=1, border_radius=12)
        gbadge = pygame.Surface((bw+10, bh2+10), pygame.SRCALPHA)
        pygame.draw.rect(gbadge, (*sc, 25), (0,0,bw+10,bh2+10), border_radius=14)
        s.blit(gbadge, (bx3-5, by3-5))
        s.blit(badge, (bx3, by3))
        s.blit(bt, (bx3 + 16, by3 + 7))

    # ── Subtitle bar — glassmorphism ──────────────────────────────────────
    def _draw_subtitle(self, s):
        sy = TOP_H + FACE_AREA
        sc = self._state_color()

        # Glass panel
        sub_bg = pygame.Surface((W, SUB_H), pygame.SRCALPHA)
        pygame.draw.rect(sub_bg, (*BG_DEEP, 220), (0,0,W,SUB_H))
        pygame.draw.line(sub_bg, (*sc, 60),  (0,0),(W,0), 1)
        pygame.draw.line(sub_bg, (*sc, 20),  (0,1),(W,1), 1)
        pygame.draw.line(sub_bg, (*sc, 25),  (0,SUB_H-1),(W,SUB_H-1), 1)
        s.blit(sub_bg, (0, sy))

        if self.subtitle and self.sub_alpha > 2:
            words = self.subtitle.split()
            line  = ''; lines = []
            for w in words:
                test = line + (' ' if line else '') + w
                if self.fn_sub.size(test)[0] < W - 80:
                    line = test
                else:
                    lines.append(line); line = w
            if line:
                lines.append(line)
            lh      = self.fn_sub.get_height() + 2
            total_h = len(lines) * lh
            start_y = sy + (SUB_H - total_h) // 2
            for i, ln in enumerate(lines):
                surf = self.fn_sub.render(ln, True, SUB_TEXT)
                surf.set_alpha(int(self.sub_alpha))
                s.blit(surf, (W//2 - surf.get_width()//2, start_y + i*lh))

        if self.mic_active:
            pulse = 0.5 + 0.5 * math.sin(self.t * 6)
            a2    = int(pulse * 220)
            ds = pygame.Surface((24,24), pygame.SRCALPHA)
            pygame.draw.circle(ds, (*MIC_ON, a2), (12,12), 12)
            s.blit(ds, (18, sy + SUB_H//2 - 12))
            lt = self.fn_s.render('LISTENING...', True, MIC_ON)
            lt.set_alpha(int(pulse * 240))
            s.blit(lt, (50, sy + SUB_H//2 - lt.get_height()//2))

    # ── HUD — premium glassmorphism panels ───────────────────────────────
    def _draw_hud(self, s):
        hy = H - HUD_H
        d  = self.sensors
        sc = self._state_color()

        # Glass background
        hb = pygame.Surface((W, HUD_H), pygame.SRCALPHA)
        pygame.draw.rect(hb, (*BG_DEEP, 240), (0, 0, W, HUD_H))
        pygame.draw.line(hb, (*sc, 100), (0,0),(W,0), 2)
        pygame.draw.line(hb, (*sc, 30),  (0,2),(W,2), 1)
        s.blit(hb, (0, hy))

        # Sensor values
        mp  = float(d.get('moisture_pct',   50))
        ms  = str(d.get('moisture_status',  'OPTIMAL'))
        hu  = float(d.get('humidity',        60))
        mc  = {'WET':COL_WARN,'OPTIMAL':COL_GOOD,
               'DRY':COL_WARN,'CRITICAL':COL_BAD}.get(ms, COL_TEXT)

        vs_now = getattr(self, 'voice_state', 'idle')
        vc     = ACCENT2 if vs_now == 'listening' else \
                 ACCENT  if vs_now == 'speaking'  else COL_DIM
        vl     = 'LISTENING' if vs_now == 'listening' else \
                 'SPEAKING'  if vs_now == 'speaking'  else 'STANDBY'

        panels = [
            ('SOIL MOISTURE', f'{mp:.0f}%',  ms,              mc,       mp/100),
            ('HUMIDITY',      f'{hu:.0f}%',  'REL. HUM',      COL_TEXT, hu/100),
            ('VOICE AI',      vl,            vs_now.upper(),  vc,       None),
        ]

        PAD = 14
        PW  = W // len(panels)
        BR  = 12

        for i, (hdr, val, sub, col, bar) in enumerate(panels):
            px  = i * PW
            cpx = px + PAD
            cpw = PW - PAD*2

            # Card glass background
            card = pygame.Surface((cpw, HUD_H - PAD), pygame.SRCALPHA)
            pygame.draw.rect(card, (*GLASS_BG, 200), (0,0,cpw,HUD_H-PAD), border_radius=BR)
            pygame.draw.rect(card, (*col, 18),        (0,0,cpw,HUD_H-PAD), border_radius=BR)
            hi = pygame.Surface((cpw-2, 14), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255,255,255,14), (0,0,cpw-2,14), border_radius=BR)
            card.blit(hi, (1, 1))
            pygame.draw.rect(card, (*col, 90),  (0,0,cpw,HUD_H-PAD),   width=1, border_radius=BR)
            pygame.draw.rect(card, (*col, 28),  (-1,-1,cpw+2,HUD_H-PAD+2), width=2, border_radius=BR+1)
            s.blit(card, (cpx, hy + PAD//2))

            mid_x = cpx + cpw // 2

            # Header label
            ht = self.fn_xs.render(hdr, True, COL_DIM)
            s.blit(ht, (mid_x - ht.get_width()//2, hy + PAD + 4))

            # Main value (pulse for voice)
            va = 255
            if i == 2:
                if vs_now == 'listening':
                    va = int(160 + 95*(0.5+0.5*math.sin(self.t*6)))
                elif vs_now == 'speaking':
                    va = int(185 + 70*(0.5+0.5*math.sin(self.t*4)))

            fn_val = self.fn_xl if i < 2 else self.fn_l
            vt = fn_val.render(val, True, col)
            vt.set_alpha(va)
            s.blit(vt, (mid_x - vt.get_width()//2, hy + PAD + 22))

            # Sub label
            ss2 = self.fn_xs.render(sub, True, COL_DIM)
            s.blit(ss2, (mid_x - ss2.get_width()//2, hy + HUD_H - 22))

            # Progress bar with gradient + animated sweep
            if bar is not None:
                bx2 = cpx + 8; bw2 = cpw - 16; bh2 = 6
                by2 = hy + HUD_H - 14
                # Track: dark base + very dim color tint
                pygame.draw.rect(s, (12,20,14), (bx2, by2, bw2, bh2), border_radius=3)
                dim = (col[0]//4, col[1]//4, col[2]//4)
                pygame.draw.rect(s, dim, (bx2, by2, bw2, bh2), border_radius=3)
                # Color fill
                fill = max(6, int(bw2 * bar))
                pygame.draw.rect(s, col, (bx2, by2, fill, bh2), border_radius=3)
                # Top highlight stripe
                hl = pygame.Surface((fill, 2), pygame.SRCALPHA)
                pygame.draw.rect(hl, (255,255,255,55), (0,0,fill,2), border_radius=1)
                s.blit(hl, (bx2, by2))
                # Animated sweep glint
                sw_x = int((self.t * 55 + i * 80) % (fill + 38)) - 19
                if 0 < sw_x < fill:
                    sw = pygame.Surface((38, bh2), pygame.SRCALPHA)
                    pygame.draw.ellipse(sw, (255,255,255,50), (0,0,38,bh2))
                    s.blit(sw, (bx2 + sw_x - 19, by2))
                # Outer bar glow
                gl = pygame.Surface((fill+4, bh2+6), pygame.SRCALPHA)
                pygame.draw.rect(gl, (*col, 30), (0,0,fill+4,bh2+6), border_radius=4)
                s.blit(gl, (bx2-2, by2-3))
                # End cap glow dot
                gt = pygame.Surface((16,16), pygame.SRCALPHA)
                pygame.draw.circle(gt, (*col, 220), (8,8), 7)
                pygame.draw.circle(gt, (255,255,255,90), (8,8), 4)
                pygame.draw.circle(gt, (255,255,255,190), (8,8), 2)
                s.blit(gt, (bx2+fill-8, by2-5))

            # Right divider
            if i < len(panels)-1:
                pygame.draw.line(s, (*sc, 18),
                                 (px+PW, hy+PAD+2), (px+PW, hy+HUD_H-PAD-2), 1)

    # ── Top overlay bar — premium ─────────────────────────────────────────
    def _draw_overlay(self, s):
        el      = int(time.time() - self.start_time)
        mm, ss2 = el//60, el%60
        sc      = self._state_color()

        # Glass top bar
        tb = pygame.Surface((W, TOP_H), pygame.SRCALPHA)
        pygame.draw.rect(tb, (*BG_DEEP, 230), (0,0,W,TOP_H))
        pygame.draw.line(tb, (*sc, 65),  (0,TOP_H-1),(W,TOP_H-1), 2)
        pygame.draw.line(tb, (*sc, 20),  (0,TOP_H-3),(W,TOP_H-3), 1)
        s.blit(tb, (0,0))

        # Animated shimmer under title
        tlen  = 260; tx0 = W//2 - tlen//2
        shimx = int((self.t * 90) % (tlen + 70)) - 35
        pygame.draw.line(s, (*sc, 30), (tx0, TOP_H-1), (tx0+tlen, TOP_H-1), 1)
        shim = pygame.Surface((55, 2), pygame.SRCALPHA)
        pygame.draw.rect(shim, (*sc, 210), (0,0,55,2))
        s.blit(shim, (tx0 + shimx, TOP_H-1))

        # Title — centered with decorative markers
        title = self.fn_title.render('TERRA  GUIDE', True, COL_TITLE)
        tglow = self.fn_title.render('TERRA  GUIDE', True, sc)
        tglow.set_alpha(45)
        ty = TOP_H//2 - title.get_height()//2
        s.blit(tglow, (W//2 - title.get_width()//2 + 1, ty + 1))
        s.blit(title, (W//2 - title.get_width()//2, ty))
        # Decorative diamond markers flanking title
        mkr = self.fn_s.render('◆', True, sc)
        mkr.set_alpha(185)
        gap = 10
        s.blit(mkr, (W//2 - title.get_width()//2 - mkr.get_width() - gap,
                     TOP_H//2 - mkr.get_height()//2))
        s.blit(mkr, (W//2 + title.get_width()//2 + gap,
                     TOP_H//2 - mkr.get_height()//2))

        # Right: FPS · uptime
        info = self.fn_xs.render(f'{self.fps_display:.0f} FPS   {mm:02d}:{ss2:02d}', True, COL_DIM)
        s.blit(info, (W - info.get_width() - 16, TOP_H//2 - info.get_height()//2))

        # Left: status dot + label
        pulse4 = 0.5 + 0.5*math.sin(self.t * 3.5)
        dot    = pygame.Surface((14,14), pygame.SRCALPHA)
        pygame.draw.circle(dot, (*sc, int(170+85*pulse4)), (7,7), 6)
        pygame.draw.circle(dot, (*sc, 250), (7,7), 3)
        s.blit(dot, (14, TOP_H//2 - 7))
        st_lbl = self.fn_xs.render(self.state.upper(), True, sc)
        s.blit(st_lbl, (32, TOP_H//2 - st_lbl.get_height()//2))


# ─── run_face — entry point ────────────────────────────────────────────────
def run_face(cmd_queue=None, sensor_data=None):
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
    pygame.display.set_caption('Terra Guide 🌱')
    pygame.mouse.set_visible(False)

    clock = pygame.time.Clock()
    face  = FarmerFace(screen)

    if cmd_queue:
        face.cmd_queue = cmd_queue

    # ── Voice Engine (aktivizohet automatikisht nëse ka voice_engine.py) ─
    voice = None

    # Tastiera: 1-0 për teste të shpejta
    KEY_MAP = {
        pygame.K_1: 'idle',      pygame.K_2: 'happy',
        pygame.K_3: 'sad',       pygame.K_4: 'angry',
        pygame.K_5: 'talking',   pygame.K_6: 'thinking',
        pygame.K_7: 'surprised', pygame.K_8: 'confused',
        pygame.K_9: 'listening', pygame.K_0: 'laughing',
    }

    # Demo sequence (auto-cycle when no external queue)
    DEMO = [
        ('idle',      '',                                              4.5),
        ('happy',     'Good morning! Your farm is doing well.',        3.5),
        ('talking',   'Soil moisture at 54%. Optimal conditions.',     4.0),
        ('thinking',  'Analyzing field conditions...',                 3.0),
        ('listening', '',                                              3.0),
        ('sad',       'Moisture dropping. Consider irrigation.',       3.5),
        ('surprised', 'Obstacle detected at 15 cm!',                  2.5),
        ('laughing',  'Excellent harvest season ahead!',              3.5),
    ]
    demo_i = 0; demo_t = 0.0

    demo_sensors = [
        dict(moisture_pct=72, moisture_status='WET',      soil_temp=17.5, air_temp=21.0, humidity=72, pump_active=False),
        dict(moisture_pct=54, moisture_status='OPTIMAL',  soil_temp=21.0, air_temp=24.0, humidity=62, pump_active=False),
        dict(moisture_pct=31, moisture_status='DRY',      soil_temp=26.5, air_temp=29.0, humidity=46, pump_active=True),
        dict(moisture_pct=11, moisture_status='CRITICAL', soil_temp=30.5, air_temp=32.0, humidity=38, pump_active=True),
    ]
    si = 0; st2 = 0.0

    prev_t  = time.time()
    running = True

    while running:
        now    = time.time()
        dt     = clamp(now - prev_t, 0, 0.05)
        prev_t = now

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in KEY_MAP:
                    face.set_face(KEY_MAP[ev.key])

        # Demo loop kur nuk ka komanda nga jashtë
        if not cmd_queue:
            demo_t += dt
            if demo_t > DEMO[demo_i][2]:
                demo_t = 0.0
                demo_i = (demo_i+1) % len(DEMO)
                st, txt, _ = DEMO[demo_i]
                face.set_face(st, txt)

        # Rrotullim sensorësh demo
        st2 += dt
        if st2 > 4.0:
            st2 = 0.0
            si  = (si+1) % len(demo_sensors)
        face.update_sensors(demo_sensors[si])
        if sensor_data:
            face.update_sensors(sensor_data)

        face.update(dt, clock.get_fps())
        screen.fill(SKY_TOP)
        face.draw()
        pygame.display.flip()
        clock.tick(60)

    if voice:
        voice.stop()
    pygame.quit()


if __name__ == '__main__':
    cmd_queue = queue.Queue()
    sensor_data = {}
    try:
        from chatbot import ChatBot
        bot = ChatBot(
            face_queue  = cmd_queue,
            sensor_data = sensor_data
        )
        voice_thread = threading.Thread(
            target = bot.run_voice_loop,
            daemon = True
        )
        voice_thread.start()
        print('[Main] Chatbot me zë startoi!')
    except ImportError:
        print('[Main] chatbot.py nuk u gjet')
    except Exception as e:
        print(f'[Main] Chatbot error: {e}')
    run_face(cmd_queue=cmd_queue, sensor_data=sensor_data)