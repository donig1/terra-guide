"""
Terra Guide — face_engine.py  (v3 — PNG + Chatbot integrated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Loads real PNG farmer faces from  assets/faces/
• Uses animation frames:  assets/animations/talk/  blink/  listen/
• Beautiful farm background (parallax sky, fields, stars, moon)
• HUD bar at bottom: moisture, soil temp, air temp, humidity, pump
• Subtitle bar: shows what Terra Guide is saying / heard
• Thread-safe queue: chatbot calls set_face() from any thread
• 60 FPS pygame loop
"""

import pygame
import math
import random
import threading
import queue
import time
import os

# ─── Screen ────────────────────────────────────────────────────────────────
W, H      = 1024, 720
HUD_H     = 90           # bottom sensor bar
SUB_H     = 48           # subtitle strip just above HUD
FACE_AREA = H - HUD_H - SUB_H

FACE_W, FACE_H = 420, 420
FACE_X = (W - FACE_W) // 2
FACE_Y = (FACE_AREA - FACE_H) // 2 - 10

# ─── Palette ───────────────────────────────────────────────────────────────
SKY_TOP  = (  6,  10,  20)
SKY_BOT  = (  8,  18,  14)
COL_TEXT = (160, 215, 130)
COL_DIM  = ( 70, 100,  70)
COL_GOOD = ( 50, 220,  90)
COL_WARN = (220, 175,  30)
COL_BAD  = (220,  50,  40)
HUD_EDGE = (  0, 160,  70)
SUB_TEXT = (200, 240, 175)
MIC_ON   = ( 50, 220,  90)
MIC_OFF  = ( 55,  55,  55)
ACCENT   = (  0, 200,  90)   # green accent for borders/glow
ACCENT2  = (  0, 140, 220)   # blue accent

BASE = os.path.dirname(os.path.abspath(__file__))

# One PNG per emotion — place files in assets/faces/
# Filenames must match exactly these keys:
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

def lerp(a,b,t): return a+(b-a)*t
def clamp(v,lo,hi): return max(lo,min(hi,v))
def smooth(t): t=clamp(t,0,1); return t*t*(3-2*t)


class Particle:
    def __init__(self, kind, x, y):
        self.kind=kind; self.x=float(x); self.y=float(y)
        self.life=1.0; self.angle=random.uniform(0,math.tau); self.spin=random.uniform(-3.5,3.5)
        if kind=='confetti':
            self.vx=random.uniform(-70,70); self.vy=random.uniform(-120,-40)
            self.color=random.choice([(255,205,0),(80,215,80),(70,175,255),(255,90,145)])
        elif kind=='spark':
            self.vx=random.uniform(-80,80); self.vy=random.uniform(-100,-25); self.color=(255,175,35)
        elif kind=='bubble':
            self.vx=random.uniform(-10,10); self.vy=random.uniform(-38,-16); self.r=random.uniform(5,12)
        elif kind=='zzz':
            self.vx=random.uniform(-6,8); self.vy=random.uniform(-28,-12); self.sz=random.choice([18,22,27])

    def update(self, dt):
        self.life-=dt*1.05; self.x+=self.vx*dt; self.y+=self.vy*dt; self.angle+=self.spin*dt
        if self.kind not in ('bubble','zzz'): self.vy+=65*dt

    def draw(self, surf, fn):
        if self.life<=0: return
        a=int(smooth(self.life)*230)
        if self.kind=='confetti':
            s2=pygame.Surface((10,10),pygame.SRCALPHA)
            pygame.draw.rect(s2,(*self.color,a),(1,1,8,8),border_radius=2)
            rot=pygame.transform.rotate(s2,math.degrees(self.angle))
            surf.blit(rot,(int(self.x)-rot.get_width()//2,int(self.y)-rot.get_height()//2))
        elif self.kind=='spark':
            s2=pygame.Surface((8,8),pygame.SRCALPHA); pygame.draw.circle(s2,(*self.color,a),(4,4),4)
            surf.blit(s2,(int(self.x)-4,int(self.y)-4))
        elif self.kind=='bubble':
            r=int(self.r); s2=pygame.Surface((r*2+4,r*2+4),pygame.SRCALPHA)
            pygame.draw.circle(s2,(130,200,255,a),(r+2,r+2),r,2)
            surf.blit(s2,(int(self.x)-r,int(self.y)-r))
        elif self.kind=='zzz':
            t2=fn.render('z',True,(175,198,255)); t2.set_alpha(a); surf.blit(t2,(int(self.x),int(self.y)))


class FarmerFace:

    def __init__(self, screen):
        self.screen=screen; self.cmd_queue=queue.Queue()
        self.state='idle'; self.t=0.0; self.start_time=time.time(); self.fps_display=60.0

        self.subtitle=''; self.sub_alpha=0.0; self.sub_timer=0.0
        self.mic_active=False

        self.prev_state='idle'; self.blend_t=1.0; self.BLEND_DUR=0.25

        self.particles=[]
        self.sensors=dict(moisture_pct=55.0,moisture_status='OPTIMAL',soil_temp=21.0,
                          air_temp=23.5,humidity=60.0,pump_active=False)

        random.seed(7)
        # Ambient floating particles (spores / fireflies)
        self._ptcls = [{
            'x': random.uniform(0, W),
            'y': random.uniform(0, FACE_AREA),
            'vy': random.uniform(-22, -5),
            'vx': random.uniform(-2.5, 2.5),
            'sz': random.uniform(1.0, 2.8),
            'bright': random.random() > 0.62,
            'ph': random.uniform(0, math.tau)
        } for _ in range(60)]
        # Pre-baked hexagonal grid (background texture)
        self._hex_surf = None   # built after pygame.display ready
        self._hex_built = False
        # bg image (optional)
        self._bg_img = None
        _bgp = os.path.join(BASE,'assets','bg.png')
        if os.path.exists(_bgp):
            try:
                _bgi = pygame.image.load(_bgp).convert()
                self._bg_img = pygame.transform.smoothscale(_bgi,(W,FACE_AREA))
                print('[Face] Loaded bg.png')
            except: pass

        self.fn_xs=pygame.font.SysFont('monospace',12,bold=True)
        self.fn_s =pygame.font.SysFont('monospace',14,bold=True)
        self.fn_m =pygame.font.SysFont('monospace',18,bold=True)
        self.fn_l =pygame.font.SysFont('monospace',24,bold=True)
        self.fn_xl=pygame.font.SysFont('monospace',32,bold=True)
        try:    self.fn_sub=pygame.font.SysFont('segoeui',20)
        except: self.fn_sub=pygame.font.SysFont('monospace',17)

        self._load_face()

    def _load_face(self):
        """Load one PNG per emotion from assets/faces/. Falls back to face.png or drawn placeholder."""
        sz = (FACE_W, FACE_H)
        faces_dir = os.path.join(BASE, 'assets', 'faces')
        single    = os.path.join(BASE, 'assets', 'face.png')
        fallback  = self._make_fallback(sz)

        # Try to load per-emotion faces
        self.faces = {}
        for state, fname in FACE_FILES.items():
            path = os.path.join(faces_dir, fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.faces[state] = pygame.transform.smoothscale(img, sz)
                    continue
                except Exception as e:
                    print(f"[Face] Could not load {fname}: {e}")
            self.faces[state] = None   # will fall back below

        loaded = sum(1 for v in self.faces.values() if v is not None)

        # If no per-emotion faces found, try single face.png for all states
        if loaded == 0 and os.path.exists(single):
            try:
                img = pygame.image.load(single).convert_alpha()
                img = pygame.transform.smoothscale(img, sz)
                self.faces = {s: img for s in FACE_FILES}
                print("[Face] Using single face.png for all states")
                return
            except Exception as e:
                print(f"[Face] Could not load face.png: {e}")

        # Fill missing states with fallback
        for state in self.faces:
            if self.faces[state] is None:
                # try idle as base, else placeholder
                self.faces[state] = self.faces.get('idle') or fallback

        if loaded == 0:
            print("[Face] Using placeholder face")
        else:
            print(f"[Face] Loaded {loaded}/{len(FACE_FILES)} emotion faces")

    def _make_fallback(self, size):
        s=pygame.Surface(size,pygame.SRCALPHA)
        cx,cy=size[0]//2,size[1]//2
        pygame.draw.ellipse(s,(255,200,140),(cx-100,cy-120,200,230))
        pygame.draw.circle(s,(40,20,10),(cx-35,cy-20),18)
        pygame.draw.circle(s,(40,20,10),(cx+35,cy-20),18)
        pygame.draw.arc(s,(160,60,45),pygame.Rect(cx-40,cy+20,80,45),math.pi+0.3,math.tau-0.3,4)
        return s

    def _bake_hex_grid(self):
        """Pre-render subtle hexagonal grid texture — called once after display init."""
        surf = pygame.Surface((W, FACE_AREA), pygame.SRCALPHA)
        sz   = 36
        cw   = sz * math.sqrt(3)
        rh   = sz * 1.5
        rows = int(FACE_AREA / rh) + 3
        cols = int(W / cw) + 3
        for row in range(-1, rows):
            for col in range(-1, cols):
                cx = col*cw + (cw/2 if row%2 else 0)
                cy = row*rh
                pts = [(int(cx + sz*0.80*math.cos(math.pi/6 + i*math.pi/3)),
                        int(cy + sz*0.80*math.sin(math.pi/6 + i*math.pi/3))) for i in range(6)]
                pygame.draw.polygon(surf, (0, 175, 65, 16), pts, 1)
        return surf

    def _draw_left_panel(self, s):
        """Left panel: circular arc moisture gauge."""
        px, py = 14, FACE_Y + 30
        pw     = FACE_X - 28
        ph     = FACE_H - 60
        # Glass panel background
        pan = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(pan, (0, 220, 80, 11), (0,0,pw,ph), border_radius=14)
        pygame.draw.rect(pan, (0, 220, 80, 45), (0,0,pw,ph), width=1, border_radius=14)
        s.blit(pan, (px, py))
        # Header
        ht = self.fn_xs.render('SOIL MOISTURE', True, COL_DIM)
        s.blit(ht, (px+pw//2-ht.get_width()//2, py+9))
        # Circular arc gauge
        cx2  = px + pw//2
        cy2  = py + ph//2 + 8
        rad  = min(pw//2 - 18, 66)
        moist = float(self.sensors.get('moisture_pct', 50))
        ms    = str(self.sensors.get('moisture_status', 'OPTIMAL'))
        gcol  = {'WET':COL_WARN,'OPTIMAL':COL_GOOD,'DRY':COL_WARN,'CRITICAL':COL_BAD}.get(ms, COL_GOOD)
        # Track arc (270° sweep, start at 135°)
        arc_rect = pygame.Rect(cx2-rad, cy2-rad, rad*2, rad*2)
        pygame.draw.arc(s, (18,38,26), arc_rect, math.radians(135), math.radians(405), 9)
        # Value arc
        fill_deg = moist / 100.0 * 270.0
        if fill_deg > 1:
            end_r   = math.radians(405)
            start_r = math.radians(405 - fill_deg)
            pygame.draw.arc(s, gcol, arc_rect, start_r, end_r, 9)
            # Glow tip
            tip_angle = start_r
            tx = int(cx2 + rad * math.cos(tip_angle))
            ty = int(cy2 - rad * math.sin(tip_angle))
            gs2 = pygame.Surface((22, 22), pygame.SRCALPHA)
            pygame.draw.circle(gs2, (*gcol, 180), (11,11), 8)
            s.blit(gs2, (tx-11, ty-11))
        # Center value text
        vt = self.fn_l.render(f'{moist:.0f}%', True, gcol)
        s.blit(vt, (cx2-vt.get_width()//2, cy2-vt.get_height()//2))
        # Status badge
        st_t = self.fn_xs.render(ms, True, gcol)
        s.blit(st_t, (cx2-st_t.get_width()//2, cy2+rad+7))
        # Pump indicator
        pump  = self.sensors.get('pump_active', False)
        pcol  = COL_GOOD if pump else COL_DIM
        plbl  = self.fn_xs.render('PUMP  ' + ('● ACTIVE' if pump else '○  OFF'), True, pcol)
        if pump:
            pulse3 = 0.5+0.5*math.sin(self.t*4.5)
            plbl.set_alpha(int(180+75*pulse3))
        s.blit(plbl, (px+pw//2-plbl.get_width()//2, py+ph-20))

    def _draw_right_panel(self, s):
        """Right panel: temperature + humidity compact cards."""
        rx = FACE_X + FACE_W + 14
        ry = FACE_Y + 30
        rw = W - rx - 14
        rh = FACE_H - 60
        # Glass panel
        pan = pygame.Surface((rw, rh), pygame.SRCALPHA)
        pygame.draw.rect(pan, (0,140,220,11), (0,0,rw,rh), border_radius=14)
        pygame.draw.rect(pan, (0,140,220,45), (0,0,rw,rh), width=1, border_radius=14)
        s.blit(pan, (rx, ry))
        d   = self.sensors
        st  = float(d.get('soil_temp', 20))
        at  = float(d.get('air_temp',  22))
        hu  = float(d.get('humidity',  60))
        stc = COL_BAD if st<10 or st>35 else (COL_WARN if st<15 or st>30 else COL_GOOD)
        atc = COL_BAD if at<5  or at>40 else (COL_WARN if at<10 or at>35 else COL_TEXT)
        cards = [
            ('SOIL TEMP', f'{st:.1f}°C', stc),
            ('AIR TEMP',  f'{at:.1f}°C', atc),
        ]
        card_h = (rh - 14) // 3
        for i,(lbl,val,col) in enumerate(cards):
            iy = ry + 7 + i*(card_h+4)
            card = pygame.Surface((rw-10, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card, (*col, 14), (0,0,rw-10,card_h), border_radius=9)
            pygame.draw.rect(card, (*col, 50), (0,0,rw-10,card_h), width=1, border_radius=9)
            s.blit(card, (rx+5, iy))
            lt = self.fn_xs.render(lbl, True, COL_DIM)
            s.blit(lt, (rx+13, iy+5))
            vt = self.fn_m.render(val, True, col)
            s.blit(vt, (rx+rw-vt.get_width()-13, iy+card_h//2-vt.get_height()//2))
        # Humidity bar card
        iy3 = ry + 7 + 2*(card_h+4)
        card = pygame.Surface((rw-10, card_h), pygame.SRCALPHA)
        pygame.draw.rect(card, (*COL_TEXT, 11), (0,0,rw-10,card_h), border_radius=9)
        pygame.draw.rect(card, (*COL_TEXT, 40), (0,0,rw-10,card_h), width=1, border_radius=9)
        s.blit(card, (rx+5, iy3))
        lt3 = self.fn_xs.render('HUMIDITY', True, COL_DIM)
        s.blit(lt3, (rx+13, iy3+5))
        hu_t = self.fn_m.render(f'{hu:.0f}%', True, COL_TEXT)
        s.blit(hu_t, (rx+rw-hu_t.get_width()-13, iy3+5))
        # Bar
        bx,bw2,bh2 = rx+10, rw-20, 6; by2 = iy3+card_h-13
        pygame.draw.rect(s, (14,22,18), (bx,by2,bw2,bh2), border_radius=3)
        fill = max(4, int(bw2*hu/100))
        pygame.draw.rect(s, COL_TEXT, (bx,by2,fill,bh2), border_radius=3)
        gts = pygame.Surface((10,10), pygame.SRCALPHA)
        pygame.draw.circle(gts, (*COL_TEXT, 120), (5,5), 4)
        s.blit(gts, (bx+fill-5, by2-2))

    # ── API ──────────────────────────────────────────────────────────────
    def set_face(self, state, text='', mic=False):
        self.cmd_queue.put({'state':state,'text':text,'mic':mic})

    def update_sensors(self, data):
        self.sensors.update(data)

    # ── update ───────────────────────────────────────────────────────────
    def update(self, dt, fps):
        self.fps_display=fps; self.t+=dt

        while not self.cmd_queue.empty():
            cmd=self.cmd_queue.get_nowait()
            ns=cmd.get('state','idle')
            if ns!=self.state:
                self.prev_state=self.state; self.state=ns; self.blend_t=0.0
            self.mic_active=cmd.get('mic',False)
            txt=cmd.get('text','')
            if txt: self.subtitle=txt; self.sub_alpha=255.0; self.sub_timer=0.0

        self.blend_t=min(1.0,self.blend_t+dt/self.BLEND_DUR)

        # subtitle fade
        if self.subtitle:
            self.sub_timer+=dt
            hold=max(2.5, len(self.subtitle)*0.055)
            if self.sub_timer>hold:
                self.sub_alpha=max(0,self.sub_alpha-dt*160)
                if self.sub_alpha<=0: self.subtitle=''
            else:
                self.sub_alpha=min(255,self.sub_alpha+dt*350)

        # Ambient particle physics
        for p in self._ptcls:
            p['x'] += p['vx']*dt; p['y'] += p['vy']*dt
            if p['y'] < -8: p['y'] = FACE_AREA+6; p['x'] = random.uniform(0,W)
            if p['x'] < -5 or p['x'] > W+5: p['x'] = random.uniform(0,W)

        # State-based particles    and random.random()<dt*3:   self.particles.append(Particle('confetti',FACE_X+FACE_W//2+random.uniform(-130,130),FACE_Y+20))
        if self.state=='laughing' and random.random()<dt*5:   self.particles.append(Particle('confetti',FACE_X+FACE_W//2+random.uniform(-150,150),FACE_Y+40))
        if self.state=='thinking' and random.random()<dt*1.5: self.particles.append(Particle('bubble',  FACE_X+FACE_W-60+random.uniform(-20,30),  FACE_Y+80))
        if self.state=='angry'    and random.random()<dt*2.5: self.particles.append(Particle('spark',   FACE_X+FACE_W//2+random.uniform(-100,100), FACE_Y+random.uniform(0,FACE_H)))
        if self.state in ('idle','sleep') and random.random()<dt*0.5: self.particles.append(Particle('zzz',FACE_X+FACE_W-50+random.uniform(0,30),FACE_Y+60))

        for p in self.particles: p.update(dt)
        self.particles=[p for p in self.particles if p.life>0]

    # ── draw ─────────────────────────────────────────────────────────────
    def draw(self):
        s=self.screen
        self._draw_bg(s); self._draw_face(s)
        for p in self.particles: p.draw(s,self.fn_l)
        self._draw_subtitle(s); self._draw_hud(s); self._draw_overlay(s)

    def _draw_bg(self, s):
        # Build hex grid once (needs display surface to exist)
        if not self._hex_built:
            self._hex_surf = self._bake_hex_grid()
            self._hex_built = True

        # ── 1. Background ─────────────────────────────────────────────────
        if self._bg_img:
            s.blit(self._bg_img, (0, 0))
        else:
            for y in range(FACE_AREA):
                tt = y / max(1, FACE_AREA)
                pygame.draw.line(s,
                    (int(lerp(3,5,tt)), int(lerp(7,11,tt)), int(lerp(15,9,tt))),
                    (0,y),(W,y))

        # ── 2. Hex grid texture ───────────────────────────────────────────
        if self._hex_surf:
            s.blit(self._hex_surf, (0, 0))

        # ── 3. Large radial glow rings behind face ────────────────────────
        cx0 = FACE_X + FACE_W//2;  cy0 = FACE_Y + FACE_H//2
        p0  = 0.38 + 0.12*math.sin(self.t*1.05)
        state_col = {'happy':COL_GOOD,'angry':COL_BAD,'sad':ACCENT2,'talking':ACCENT,
                     'listening':ACCENT2,'thinking':(170,90,220),'surprised':COL_WARN,
                     'laughing':COL_WARN,'scared':ACCENT2}.get(self.state, ACCENT)
        for i,rr in enumerate([260,205,155,112]):
            a = max(0, int(p0*(20-i*4)))
            gs = pygame.Surface((rr*2,rr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*state_col, a), (rr,rr), rr, 3-min(i,2))
            s.blit(gs, (cx0-rr, cy0-rr))

        # ── 4. Ambient firefly particles ──────────────────────────────────
        for p in self._ptcls:
            a2 = int(clamp((0.5+0.5*math.sin(self.t*0.9+p['ph']))*(220 if p['bright'] else 75),0,255))
            col2 = (155,255,195) if p['bright'] else (40,115,65)
            r2   = max(1, int(p['sz']))
            ps2  = pygame.Surface((r2*2+2,r2*2+2), pygame.SRCALPHA)
            pygame.draw.circle(ps2, (*col2, a2), (r2+1,r2+1), r2)
            s.blit(ps2, (int(p['x'])-r2, int(p['y'])-r2))

        # ── 5. Moving scan line ───────────────────────────────────────────
        sy2 = int((self.t*55) % (FACE_AREA+60))-30
        sc  = pygame.Surface((W,2), pygame.SRCALPHA)
        pygame.draw.rect(sc, (*state_col, 12), (0,0,W,2))
        s.blit(sc, (0, sy2))

        # ── 6. Edge vignette ─────────────────────────────────────────────
        for ew in range(80,0,-16):
            a3 = int((80-ew)*3.0)
            vs = pygame.Surface((ew, FACE_AREA), pygame.SRCALPHA)
            pygame.draw.rect(vs, (3,7,14,a3),(0,0,ew,FACE_AREA))
            s.blit(vs,(0,0)); s.blit(vs,(W-ew,0))
        # bottom fade into HUD
        bf = pygame.Surface((W,60), pygame.SRCALPHA)
        for i in range(60):
            pygame.draw.line(bf,(3,7,14,int(i*3.5)),(0,i),(W,i))
        s.blit(bf,(0,FACE_AREA-60))

        # ── 7. Corner brackets ───────────────────────────────────────────
        bsz=28; bth=2
        for bx,by,dx,dy in [(0,0,1,1),(W,0,-1,1),(0,FACE_AREA,1,-1),(W,FACE_AREA,-1,-1)]:
            pygame.draw.line(s,ACCENT,(bx,by),(bx+dx*bsz,by),bth)
            pygame.draw.line(s,ACCENT,(bx,by),(bx,by+dy*bsz),bth)

        # ── 8. Side data panels ───────────────────────────────────────────
        self._draw_left_panel(s)
        self._draw_right_panel(s)

    def _draw_face(self, s):
        fx=FACE_X; fy=FACE_Y
        cx=fx+FACE_W//2; cy=fy+FACE_H//2

        # State color
        state_col = {'happy':COL_GOOD,'angry':COL_BAD,'sad':ACCENT2,'talking':ACCENT,
                     'listening':ACCENT2,'thinking':(170,90,220),'surprised':COL_WARN,
                     'laughing':COL_WARN,'scared':ACCENT2,'sleep':COL_DIM}.get(self.state, ACCENT)

        # ── Outer rotating tick ring ──────────────────────────────────────
        tick_r = FACE_W//2 + 22
        tick_surf = pygame.Surface((W, FACE_AREA+SUB_H), pygame.SRCALPHA)
        for i in range(40):
            angle = -self.t*0.22 + i*math.tau/40
            major = (i % 10 == 0)
            r1    = tick_r + (0 if major else 2)
            r2    = tick_r + (14 if major else 6)
            x1,y1 = int(cx+r1*math.cos(angle)), int(cy+r1*math.sin(angle))
            x2,y2 = int(cx+r2*math.cos(angle)), int(cy+r2*math.sin(angle))
            pygame.draw.line(tick_surf, (*state_col, 190 if major else 70),
                             (x1,y1),(x2,y2), 2 if major else 1)
        # Arc progress indicator (state-dependent fill)
        arc_fill = {'talking':0.85,'listening':0.60,'thinking':0.45,
                    'happy':1.0,'angry':0.9,'idle':0.30}.get(self.state,0.5)
        arc_r2   = tick_r + 18
        arc_rect = pygame.Rect(cx-arc_r2+1, cy-arc_r2+1, arc_r2*2-2, arc_r2*2-2)
        end_a    = -math.pi/2
        start_a  = end_a - arc_fill*math.tau
        pygame.draw.arc(tick_surf, (*state_col, 130), arc_rect, start_a, end_a, 3)
        s.blit(tick_surf, (0,0))

        # ── Inner glow ring (tight, behind face) ─────────────────────────
        ring_r = FACE_W//2 + 5
        pulse  = 0.75 + 0.25*math.sin(self.t*2.2)
        for gw in range(20,0,-5):
            a4 = max(0,int(pulse*(22-gw)))
            gs3= pygame.Surface((ring_r*2+gw*2,ring_r*2+gw*2), pygame.SRCALPHA)
            pygame.draw.circle(gs3,(*state_col,a4),(ring_r+gw,ring_r+gw),ring_r+gw,1)
            s.blit(gs3,(cx-ring_r-gw,cy-ring_r-gw))
        # Solid ring
        rs = pygame.Surface(((ring_r+2)*2,(ring_r+2)*2), pygame.SRCALPHA)
        pygame.draw.circle(rs,(*state_col,160),(ring_r+2,ring_r+2),ring_r,2)
        s.blit(rs,(cx-ring_r-2,cy-ring_r-2))

        # ── Face image (cross-fade) ───────────────────────────────────────
        cur  = self.faces.get(self.state)  or self.faces.get('idle')
        prev = self.faces.get(self.prev_state) or self.faces.get('idle')
        if cur is None: return
        if self.blend_t < 1.0 and prev is not None and prev is not cur:
            t = smooth(self.blend_t)
            prev_s = prev.copy(); prev_s.set_alpha(int(255*(1.0-t))); s.blit(prev_s,(fx,fy))
            cur_s  = cur.copy();  cur_s.set_alpha(int(255*t));        s.blit(cur_s, (fx,fy))
        else:
            s.blit(cur,(fx,fy))

        # ── MIC indicator ────────────────────────────────────────────────
        mc=MIC_ON if self.mic_active else MIC_OFF
        pygame.draw.circle(s,mc,(fx+FACE_W-28,fy+28),13)
        lt=self.fn_xs.render('MIC',True,(200,220,200) if self.mic_active else (80,80,80))
        s.blit(lt,(fx+FACE_W-28-lt.get_width()//2,fy+46))

        # ── State badge (below face) ─────────────────────────────────────
        bt=self.fn_s.render(self.state.upper(),True,(235,245,225))
        bw=bt.get_width()+22; bh2=bt.get_height()+9
        bx3=fx+FACE_W//2-bw//2; by3=fy+FACE_H+8
        badge=pygame.Surface((bw,bh2),pygame.SRCALPHA)
        pygame.draw.rect(badge,(*state_col,40),(0,0,bw,bh2),border_radius=10)
        pygame.draw.rect(badge,(*state_col,120),(0,0,bw,bh2),width=1,border_radius=10)
        s.blit(badge,(bx3,by3)); s.blit(bt,(bx3+11,by3+4))

    def _draw_subtitle(self, s):
        sy=FACE_AREA
        sub_bg=pygame.Surface((W,SUB_H),pygame.SRCALPHA)
        pygame.draw.rect(sub_bg,(4,10,2,195),(0,0,W,SUB_H))
        pygame.draw.line(sub_bg,(45,95,25,155),(0,0),(W,0),1)
        s.blit(sub_bg,(0,sy))

        if self.subtitle and self.sub_alpha>2:
            words=self.subtitle.split(); line=''; lines=[]
            for w in words:
                test=line+(' ' if line else '')+w
                if self.fn_sub.size(test)[0]<W-50: line=test
                else: lines.append(line); line=w
            if line: lines.append(line)
            total_h=len(lines)*22; start_y=sy+(SUB_H-total_h)//2
            for i,ln in enumerate(lines):
                surf=self.fn_sub.render(ln,True,SUB_TEXT); surf.set_alpha(int(self.sub_alpha))
                s.blit(surf,(W//2-surf.get_width()//2,start_y+i*22))

        if self.mic_active:
            pulse=0.5+0.5*math.sin(self.t*6); a2=int(pulse*200)
            dot_s=pygame.Surface((22,22),pygame.SRCALPHA); pygame.draw.circle(dot_s,(*MIC_ON,a2),(11,11),11)
            s.blit(dot_s,(14,sy+SUB_H//2-11))
            lt=self.fn_s.render('LISTENING...',True,MIC_ON); lt.set_alpha(int(pulse*230))
            s.blit(lt,(42,sy+SUB_H//2-lt.get_height()//2))

    def _draw_hud(self, s):
        hy=H-HUD_H; d=self.sensors
        # Full dark glass strip
        hb=pygame.Surface((W,HUD_H),pygame.SRCALPHA)
        pygame.draw.rect(hb,(3,6,12,242),(0,0,W,HUD_H))
        # Top separator line with glow
        pygame.draw.line(hb,(*ACCENT,55),(0,0),(W,0),1)
        pygame.draw.line(hb,(*ACCENT,18),(0,1),(W,1),1)
        s.blit(hb,(0,hy))

        ms  = str(d.get('moisture_status','OPTIMAL'))
        mc  = {'WET':COL_WARN,'OPTIMAL':COL_GOOD,'DRY':COL_WARN,'CRITICAL':COL_BAD}.get(ms,COL_TEXT)
        st  = float(d.get('soil_temp',20))
        stc = COL_BAD if st<10 or st>35 else (COL_WARN if st<15 or st>30 else COL_GOOD)
        pc  = COL_GOOD if d.get('pump_active') else (COL_BAD if ms=='CRITICAL' else COL_DIM)
        mp  = float(d.get('moisture_pct',50))
        hu  = float(d.get('humidity',60))
        pump_on = d.get('pump_active',False)

        PW=W//5
        panels=[
            ('MOISTURE',  f'{mp:.0f}%',                          ms,      mc,   mp/100),
            ('SOIL TEMP', f'{st:.1f}°C',                         'SOIL',  stc,  None),
            ('AIR TEMP',  f'{float(d.get("air_temp",22)):.1f}°C','AIR',   COL_TEXT,None),
            ('HUMIDITY',  f'{hu:.0f}%',                          'REL.HUM',COL_TEXT,hu/100),
            ('PUMP',      'ACTIVE' if pump_on else 'STANDBY',    'IRRIG', pc,   None),
        ]
        for i,(hdr,val,sub,col,bar) in enumerate(panels):
            px=i*PW
            # Card with colored tint
            card=pygame.Surface((PW-4,HUD_H-8),pygame.SRCALPHA)
            pygame.draw.rect(card,(*col,14),(0,0,PW-4,HUD_H-8),border_radius=8)
            pygame.draw.rect(card,(*col,50),(0,0,PW-4,HUD_H-8),width=1,border_radius=8)
            s.blit(card,(px+2,hy+4))
            # Header
            hs=self.fn_xs.render(hdr,True,COL_DIM)
            s.blit(hs,(px+PW//2-hs.get_width()//2,hy+8))
            # Main value (pulse on active states)
            va=255
            if i==4 and pump_on:
                va=int(180+75*(0.5+0.5*math.sin(self.t*3.5)))
            vs=self.fn_xl.render(val,True,col); vs.set_alpha(va)
            s.blit(vs,(px+PW//2-vs.get_width()//2,hy+22))
            # Sub label
            ss2=self.fn_xs.render(sub,True,(*col[:3],160) if len(col)==3 else col)
            s.blit(ss2,(px+PW//2-ss2.get_width()//2,hy+59))
            # Progress bar
            if bar is not None:
                bx2,bw2,bh2=px+10,PW-20,5; by2=hy+HUD_H-11
                pygame.draw.rect(s,(12,20,14),(bx2,by2,bw2,bh2),border_radius=3)
                fill=max(4,int(bw2*bar))
                pygame.draw.rect(s,col,(bx2,by2,fill,bh2),border_radius=3)
                gt=pygame.Surface((10,10),pygame.SRCALPHA)
                pygame.draw.circle(gt,(*col,130),(5,5),4)
                s.blit(gt,(bx2+fill-5,by2-2))

    def _draw_overlay(self, s):
        el=int(time.time()-self.start_time); mm,ss2=el//60,el%60
        # Top bar
        tb=pygame.Surface((W,34),pygame.SRCALPHA)
        pygame.draw.rect(tb,(3,6,12,210),(0,0,W,34))
        pygame.draw.line(tb,(*ACCENT,50),(0,33),(W,33),1)
        s.blit(tb,(0,0))
        # Animated underline below title
        tlen=200; tx0=W//2-tlen//2
        anim_x=int((self.t*80)%(tlen+60))-30
        pygame.draw.line(s,ACCENT,(tx0,33),(tx0+tlen,33),1)
        ul=pygame.Surface((40,2),pygame.SRCALPHA)
        pygame.draw.rect(ul,(*ACCENT,200),(0,0,40,2))
        s.blit(ul,(tx0+anim_x,33))
        # Title
        title=self.fn_m.render('TERRA  GUIDE',True,ACCENT)
        s.blit(title,(W//2-title.get_width()//2,8))
        # Right: FPS + uptime
        info=self.fn_xs.render(f'FPS {self.fps_display:.0f}   UP {mm:02d}:{ss2:02d}',True,COL_DIM)
        s.blit(info,(W-info.get_width()-10,11))
        # Left: state dot + label
        sc2={'talking':ACCENT,'listening':ACCENT2,'thinking':(170,90,220),
             'angry':COL_BAD,'happy':COL_GOOD}.get(self.state,COL_DIM)
        pulse4=0.5+0.5*math.sin(self.t*3.5)
        dot=pygame.Surface((12,12),pygame.SRCALPHA)
        pygame.draw.circle(dot,(*sc2,int(160+95*pulse4)),(6,6),5)
        s.blit(dot,(10,11))
        st_lbl=self.fn_xs.render(self.state.upper(),True,sc2)
        s.blit(st_lbl,(26,12))


def run_face(cmd_queue=None, sensor_data=None):
    pygame.init()
    pygame.mixer.init(frequency=44100,size=-16,channels=2,buffer=512)
    screen=pygame.display.set_mode((W,H)); pygame.display.set_caption("Terra Guide 🌱")
    clock=pygame.time.Clock(); face=FarmerFace(screen)
    if cmd_queue: face.cmd_queue=cmd_queue

    KEY_MAP={pygame.K_1:'idle',pygame.K_2:'happy',pygame.K_3:'sad',pygame.K_4:'angry',
             pygame.K_5:'talking',pygame.K_6:'thinking',pygame.K_7:'surprised',
             pygame.K_8:'confused',pygame.K_9:'listening',pygame.K_0:'laughing'}

    DEMO=[('idle','',4.5),('happy','Good morning farmer! Ready to work!',3.5),
          ('talking','Soil moisture is at 54 percent. Looks optimal.',4.0),
          ('thinking','Analyzing field conditions...',3.0),('listening','',3.0),
          ('sad','Moisture is dropping. Consider watering soon.',3.5),
          ('surprised','Obstacle detected at 15 centimeters!',2.5),('laughing','Great harvest season ahead!',3.5)]
    demo_i=0; demo_t=0.0
    demo_sensors=[
        dict(moisture_pct=72,moisture_status='WET',     soil_temp=17.5,air_temp=21.0,humidity=72,pump_active=False),
        dict(moisture_pct=54,moisture_status='OPTIMAL', soil_temp=21.0,air_temp=24.0,humidity=62,pump_active=False),
        dict(moisture_pct=31,moisture_status='DRY',     soil_temp=26.5,air_temp=29.0,humidity=46,pump_active=True),
        dict(moisture_pct=11,moisture_status='CRITICAL',soil_temp=30.5,air_temp=32.0,humidity=38,pump_active=True),
    ]
    si=0; st2=0.0; prev_t=time.time(); running=True

    while running:
        now=time.time(); dt=clamp(now-prev_t,0,0.05); prev_t=now
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: running=False
            elif ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE: running=False
                elif ev.key in KEY_MAP: face.set_face(KEY_MAP[ev.key])

        if not cmd_queue:
            demo_t+=dt
            if demo_t>DEMO[demo_i][2]:
                demo_t=0.0; demo_i=(demo_i+1)%len(DEMO)
                st,txt,_=DEMO[demo_i]; face.set_face(st,txt)

        st2+=dt
        if st2>4.0: st2=0.0; si=(si+1)%len(demo_sensors)
        face.update_sensors(demo_sensors[si])
        if sensor_data: face.update_sensors(sensor_data)

        face.update(dt,clock.get_fps())
        screen.fill(SKY_TOP); face.draw()
        pygame.display.flip(); clock.tick(60)

    pygame.quit()


if __name__=='__main__':
    run_face()