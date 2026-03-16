"""
TerraFace  —  Stili Pixar / Disney Cartoon
Teknika:
  • Shtresa të shumta ngjyrash për illuzionin e gradientit
  • Outline të trasha si cel-shading
  • Hije (drop-shadow) dhe highlight në çdo element
  • Animacion i lëmuar (blink, talk, eyebrow, wheat-sway)
"""

import pygame, math, random, time

# ─── Ngjyra kryesore ─────────────────────────────────────────────────────────
# Lëkura
SK1  = (242, 194, 140)   # Bazë
SK2  = (255, 218, 168)   # Highlight
SK3  = (210, 158, 100)   # Hije
SK4  = (185, 128,  72)   # Hije e thellë
# Flokë
HR1  = (218, 168,  44)   # Bionde bazë
HR2  = (242, 202,  90)   # Highlight
HR3  = (170, 124,  20)   # Hije
# Kapelë
HT1  = (205, 175, 105)   # Kashte bazë
HT2  = (228, 205, 148)   # Highlight
HT3  = (162, 132,  68)   # Hije
HT4  = (120,  88,  30)   # Hije e thellë
HBN  = ( 95,  52,  18)   # Shirita
# Sytë
EW   = (252, 252, 250)   # E bardha
EIR  = ( 92,  54,  22)   # Iris kafe
EPP  = ( 15,   8,   3)   # Pupila
# Dhëmbë
TH   = (250, 252, 248)
# Gruri
WH1  = (215, 175,  52)
WH2  = (245, 210,  98)
WH3  = (168, 128,  22)
# Outline
OL   = ( 42,  22,   8)
OL2  = ( 80,  42,  15)


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))


class TerraFace:

    def __init__(self, screen, W, H):
        self.screen = screen
        self.W = W
        self.H = H
        self.cx = W // 2
        self.cy = H // 2 + 20

        # Gjendje
        self.mode     = "idle"
        self.emotion  = "smile"
        self.talking  = False
        self.listening= False
        self.moisture = 65.0
        self.status   = "TERRA GUIDE · GATI"

        # Animacion
        self.blink_t    = 0.0
        self.blink_int  = 3.2
        self.is_blink   = False
        self.talk_t     = 0.0
        self.mouth_o    = 0.0
        self.t          = 0.0        # kohë globale
        self.wheat_t    = 0.0
        self.plant_grow = 0.0
        self.mic_t      = 0.0
        self.eyebrow_raise = 0.0     # 0..1
        self.squint     = 0.0        # 0..1  (thinking)
        self.happy_cheek= 0.0        # 0..1

        # Grimcat
        self.parts = []
        self.p_timer = 0.0

        pygame.font.init()
        self._init_fonts()

    def _init_fonts(self):
        for name in ["Verdana","Arial","dejavusans",None]:
            try:
                self.fnt_sm = pygame.font.SysFont(name, 12, bold=True)
                self.fnt_md = pygame.font.SysFont(name, 15, bold=True)
                self.fnt_xl = pygame.font.SysFont(name, 22, bold=True)
                break
            except Exception:
                continue

    def set_state(self, mode, emotion, talking, listening, moisture, status):
        self.mode      = mode
        self.emotion   = emotion
        self.talking   = talking
        self.listening = listening
        self.moisture  = moisture
        self.status    = status

    # ─── UPDATE ──────────────────────────────────────────────────────────────

    def update(self, dt):
        self.t       += dt
        self.wheat_t  = math.sin(self.t * 1.6) * 5

        # Blink
        self.blink_t += dt
        if self.blink_t >= self.blink_int:
            self.is_blink = True
            if self.blink_t >= self.blink_int + 0.11:
                self.is_blink = False
                self.blink_t  = 0.0
                self.blink_int= 2.6 + random.random() * 2.8

        # Goja
        if self.talking:
            self.talk_t  += dt * 8.5
            self.mouth_o  = (math.sin(self.talk_t)+1)/2 * 0.65
        else:
            self.mouth_o  = max(0.0, self.mouth_o - dt*6)

        # Emocion → target
        target_raise = 0.0
        target_squint= 0.0
        target_cheek = 0.0
        if self.emotion == "happy":
            target_raise = 0.15; target_cheek = 1.0
        elif self.emotion == "thinking":
            target_raise = -0.3; target_squint = 0.5
        elif self.emotion == "curious":
            target_raise = 0.5
        elif self.emotion == "focused":
            target_squint = 0.25

        spd = dt * 4
        self.eyebrow_raise += (target_raise  - self.eyebrow_raise) * spd * 3
        self.squint        += (target_squint - self.squint)        * spd * 3
        self.happy_cheek   += (target_cheek  - self.happy_cheek)   * spd * 3

        # Bimë
        if self.mode == "planting":
            self.plant_grow = min(1.0, self.plant_grow + dt*0.35)
        else:
            self.plant_grow = max(0.0, self.plant_grow - dt*0.6)

        # Mikrofon
        if self.listening:
            self.mic_t += dt * 4
        else:
            self.mic_t = 0.0

        # Grimcat
        self._upd_parts(dt)

    def _upd_parts(self, dt):
        self.p_timer += dt
        if self.p_timer > 0.08 and self.mode in ("planting","analyzing"):
            self.p_timer = 0
            self.parts.append({
                "x": self.cx + random.randint(-50,50),
                "y": self.cy + 105,
                "vx": random.uniform(-1.5,1.5),
                "vy": random.uniform(-3,-0.8),
                "life": 1.0,
                "r": random.randint(2,5),
                "c": random.choice([(118,72,28),(88,48,12),(148,98,42),(168,118,58)]),
            })
        self.parts = [
            {**p, "x":p["x"]+p["vx"], "y":p["y"]+p["vy"],
             "vy":p["vy"]+0.13, "life":p["life"]-dt*1.3}
            for p in self.parts if p["life"]>0
        ]

    # ─── DRAW ────────────────────────────────────────────────────────────────

    def draw(self):
        # Sfond me gradient
        self._draw_bg()
        self._draw_particles()
        self._draw_shadow()
        self._draw_neck()
        self._draw_face()
        self._draw_ears()
        self._draw_hair()
        self._draw_hat()
        self._draw_eyebrows()
        self._draw_eyes()
        self._draw_nose()
        self._draw_cheeks()
        self._draw_stubble()
        self._draw_mouth()
        self._draw_wheat()
        self._draw_plant_sprout()
        if self.listening:
            self._draw_mic()
        self._draw_hud()
        self._draw_sidebar()

    # ─── SFOND ───────────────────────────────────────────────────────────────

    def _draw_bg(self):
        # Gradient manual: lart → poshtë
        for y in range(self.H):
            t = y / self.H
            c = lerp_color((18,38,18), (6,15,6), t)
            pygame.draw.line(self.screen, c, (0,y), (self.W,y))
        # Unaza dekorative
        for r in [280, 220, 160]:
            alpha = 18
            s = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(s,(80,160,80,alpha),(r,r),r,2)
            self.screen.blit(s,(self.cx-r,self.cy-r-20))

    def _draw_shadow(self):
        # Hija e trupit poshtë
        s = pygame.Surface((240,50),pygame.SRCALPHA)
        pygame.draw.ellipse(s,(0,0,0,70),s.get_rect())
        self.screen.blit(s,(self.cx-120,self.cy+150))

    # ─── QAFA ────────────────────────────────────────────────────────────────

    def _draw_neck(self):
        cx,cy = self.cx, self.cy
        # Hija
        sh=pygame.Surface((88,80),pygame.SRCALPHA)
        pygame.draw.rect(sh,(0,0,0,50),sh.get_rect(),border_radius=14)
        self.screen.blit(sh,(cx-40,cy+122))
        # Lëkura — 3 shtresa
        for col,rx,ry in [(SK4,38,62),(SK3,36,60),(SK1,34,58)]:
            pygame.draw.rect(self.screen,col,
                pygame.Rect(cx-rx,cy+118,rx*2,ry),border_radius=12)
        pygame.draw.rect(self.screen,OL,
            pygame.Rect(cx-38,cy+118,76,62),3,border_radius=12)
        # Linja e qafës
        pygame.draw.line(self.screen,SK4,(cx-28,cy+122),(cx-28,cy+168),3)

    # ─── FYTYRA ──────────────────────────────────────────────────────────────

    def _draw_face(self):
        cx,cy = self.cx,self.cy

        def face_pts(rx_base, ry_base, jaw_squeeze=14):
            pts=[]
            for i in range(360):
                a=math.radians(i)
                rx=rx_base
                ry=ry_base
                if 195<i<345:
                    factor=math.sin(math.radians((i-195)*180/150))
                    ry=ry_base - jaw_squeeze*factor
                pts.append((cx+int(rx*math.cos(a)),
                             cy+int(ry*math.sin(a))))
            return pts

        # Hija e fytyrës
        sh=pygame.Surface((250,275),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,55),sh.get_rect())
        self.screen.blit(sh,(cx-129,cy-140))

        # Shtresa 1 — hije e thellë (kontur)
        pygame.draw.polygon(self.screen, SK4, face_pts(116,134,18))
        # Shtresa 2 — hije mesatare
        pygame.draw.polygon(self.screen, SK3, face_pts(113,131,16))
        # Shtresa 3 — bazë
        pygame.draw.polygon(self.screen, SK1, face_pts(110,128,14))
        # Shtresa 4 — highlight i madh majtas-lart
        hl_pts=[]
        for i in range(180,360):
            a=math.radians(i)
            hl_pts.append((cx-10+int(72*math.cos(a)),
                           cy- 8+int(88*math.sin(a))))
        pygame.draw.polygon(self.screen, SK2, hl_pts)

        # Outline
        pygame.draw.polygon(self.screen, OL, face_pts(110,128,14), 4)

    # ─── VESHËT ──────────────────────────────────────────────────────────────

    def _draw_ears(self):
        cx,cy=self.cx,self.cy
        for side in [-1,1]:
            ex=cx+side*108; ey=cy+12
            # Hija
            sh=pygame.Surface((42,56),pygame.SRCALPHA)
            pygame.draw.ellipse(sh,(0,0,0,50),sh.get_rect())
            self.screen.blit(sh,(ex-23+side*3,ey-30))
            # Shtresat
            for col,rx,ry in [(SK4,20,28),(SK3,18,26),(SK1,16,24)]:
                pygame.draw.ellipse(self.screen,col,
                    pygame.Rect(ex-rx,ey-ry,rx*2,ry*2))
            pygame.draw.ellipse(self.screen,OL,
                pygame.Rect(ex-20,ey-28,40,56),4)
            # Helix brendshëm
            for col,rx,ry in [(SK3,10,16),(SK4,8,14)]:
                pygame.draw.ellipse(self.screen,col,
                    pygame.Rect(ex-rx,ey-ry,rx*2,ry*2))
            pygame.draw.ellipse(self.screen,OL2,
                pygame.Rect(ex-10,ey-16,20,32),2)
            # Highlight
            hl=pygame.Surface((10,16),pygame.SRCALPHA)
            pygame.draw.ellipse(hl,(255,230,190,120),hl.get_rect())
            self.screen.blit(hl,(ex-side*14-5,ey-14))

    # ─── FLOKËT ──────────────────────────────────────────────────────────────

    def _draw_hair(self):
        cx,cy=self.cx,self.cy
        # Flokë anash — 3 shtresa secila anë
        for side in [-1,1]:
            # Shtresa e errët (hija)
            pts_d=[
                (cx+side*98, cy-58),
                (cx+side*120,cy-25),
                (cx+side*118,cy+18),
                (cx+side*108,cy+18),
                (cx+side*100,cy-50),
            ]
            pygame.draw.polygon(self.screen,HR3,pts_d)
            # Shtresa bazë
            pts_m=[
                (cx+side*94, cy-60),
                (cx+side*115,cy-28),
                (cx+side*112,cy+14),
                (cx+side*102,cy+14),
                (cx+side*96, cy-52),
            ]
            pygame.draw.polygon(self.screen,HR1,pts_m)
            # Highlight
            pts_l=[
                (cx+side*86, cy-62),
                (cx+side*100,cy-38),
                (cx+side*96, cy-28),
                (cx+side*82, cy-55),
            ]
            pygame.draw.polygon(self.screen,HR2,pts_l)
            # Kontur
            pygame.draw.polygon(self.screen,OL,pts_m,3)

    # ─── KAPELA ──────────────────────────────────────────────────────────────

    def _draw_hat(self):
        cx,cy=self.cx,self.cy

        # ── Brim (strehë) ─────────────────────────────────
        # Hija e brimës
        sh=pygame.Surface((328,60),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,65),sh.get_rect())
        self.screen.blit(sh,(cx-170,cy-136))

        # Shtresa poshtë (hije e errët)
        pygame.draw.ellipse(self.screen,HT4,
            pygame.Rect(cx-158,cy-130,316,56))
        # Shtresa hija mesatare
        pygame.draw.ellipse(self.screen,HT3,
            pygame.Rect(cx-155,cy-132,310,52))
        # Shtresa bazë
        pygame.draw.ellipse(self.screen,HT1,
            pygame.Rect(cx-152,cy-134,304,50))
        # Highlight mbi brim
        pygame.draw.ellipse(self.screen,HT2,
            pygame.Rect(cx-128,cy-133,95,18))
        # Highlight i vogël
        pygame.draw.ellipse(self.screen,HT2,
            pygame.Rect(cx-50, cy-131,40,10))
        pygame.draw.ellipse(self.screen,OL,
            pygame.Rect(cx-152,cy-134,304,50),4)

        # ── Trupi kapelës ─────────────────────────────────
        body=[
            (cx-94, cy-128),
            (cx-72, cy-218),
            (cx-10, cy-236),
            (cx+10, cy-236),
            (cx+72, cy-218),
            (cx+94, cy-128),
        ]
        # Hija djathtas
        shadow_body=[
            (cx+18, cy-128),
            (cx+56, cy-214),
            (cx+76, cy-214),
            (cx+96, cy-128),
        ]
        pygame.draw.polygon(self.screen,HT4,shadow_body)

        # Shtresat e trupit
        for col,pts in [
            (HT3,[
                (cx-92,cy-128),(cx-70,cy-216),(cx-9,cy-234),
                (cx+9,cy-234),(cx+70,cy-216),(cx+92,cy-128)]),
            (HT1,body),
        ]:
            pygame.draw.polygon(self.screen,col,pts)

        # Highlight i gjatë majtas
        hl_body=[
            (cx-88,cy-130),(cx-68,cy-214),
            (cx-28,cy-230),(cx-6, cy-228),
            (cx-4, cy-130),
        ]
        pygame.draw.polygon(self.screen,HT2,hl_body)

        # Teksturë kashte — linja diagonale
        for i in range(10):
            lx=cx-86+i*20
            pygame.draw.line(self.screen,HT3,
                (lx,cy-130),(lx+6,cy-215),1)

        pygame.draw.polygon(self.screen,OL,body,4)

        # ── Shiriti ───────────────────────────────────────
        band=[
            (cx-92,cy-142),(cx-92,cy-126),
            (cx+92,cy-126),(cx+92,cy-142),
        ]
        pygame.draw.polygon(self.screen,HBN,band)
        # Highlight shirita
        pygame.draw.line(self.screen,(130,75,30),
            (cx-90,cy-142),(cx+90,cy-142),2)
        pygame.draw.polygon(self.screen,OL,band,2)

        # ── Tufë e vogël dekoruese ─────────────────────────
        self._draw_small_leaf(cx+58, cy-150)

    def _draw_small_leaf(self,x,y):
        sw=math.sin(self.t*1.4)*4
        for col,pts in [
            (WH3,[(x,y),(x+20+int(sw),y-16),(x+30+int(sw),y-8),(x+12,y+4)]),
            (WH1,[(x,y),(x+18+int(sw),y-14),(x+28+int(sw),y-6),(x+10,y+3)]),
        ]:
            pygame.draw.polygon(self.screen,col,pts)
        pygame.draw.line(self.screen,WH3,(x,y),(x+16+int(sw),y-10),2)

    # ─── VETULLAT ────────────────────────────────────────────────────────────

    def _draw_eyebrows(self):
        cx,cy=self.cx,self.cy
        BR=HR3; OLB=(30,15,5)
        raise_px=int(self.eyebrow_raise*16)
        squint_ang=self.squint*12

        for side,sx in [(-1,cx-74),(1,cx+18)]:
            pts=[]
            for i in range(60):
                t_=i/59
                x=sx+int(58*t_)
                # Kurbë natyrale + raise + squint
                curve=-int(12*math.sin(t_*math.pi))
                if side==1: squint_offset=int(squint_ang*(t_-0.5))
                else:       squint_offset=-int(squint_ang*(t_-0.5))
                y=cy-54+curve+squint_offset-raise_px
                pts.append((x,y))
            if len(pts)>1:
                # Hija
                sh_pts=[(x+2,y+3) for x,y in pts]
                pygame.draw.lines(self.screen,(0,0,0,0),False,sh_pts,10)
                # Vetulla
                pygame.draw.lines(self.screen,BR,False,pts,10)
                pygame.draw.lines(self.screen,OLB,False,pts,2)
                # Highlight
                hl=[(x,y-2) for x,y in pts[10:42]]
                if len(hl)>1:
                    pygame.draw.lines(self.screen,HR2,False,hl,3)

    # ─── SYTË ────────────────────────────────────────────────────────────────

    def _draw_eyes(self):
        cx,cy=self.cx,self.cy
        sq=int(self.squint*10)
        for ex in [cx-44,cx+44]:
            self._draw_eye(ex, cy-22, sq)

    def _draw_eye(self,ex,ey,sq):
        # Hija e syrit
        sh=pygame.Surface((80,60),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,55),sh.get_rect())
        self.screen.blit(sh,(ex-42,ey-28))

        if self.is_blink:
            # Sy i mbyllur — qepalla e poshtme takon të sipërmën
            pygame.draw.ellipse(self.screen,SK1,
                pygame.Rect(ex-34,ey-8,68,20))
            pygame.draw.arc(self.screen,OL,
                pygame.Rect(ex-34,ey-16,68,34),
                math.pi,2*math.pi,6)
            return

        # ─ E bardha ─────────────────────────────────────────
        # Hija brendshme (ambient occlusion)
        pygame.draw.ellipse(self.screen,SK3,
            pygame.Rect(ex-36,ey-28+sq,72,52-sq*2))
        # Bazë e bardhë
        pygame.draw.ellipse(self.screen,EW,
            pygame.Rect(ex-34,ey-26+sq,68,48-sq*2))
        # Highlight e bardhës
        pygame.draw.ellipse(self.screen,(255,255,255),
            pygame.Rect(ex-28,ey-24+sq,32,20))
        pygame.draw.ellipse(self.screen,OL,
            pygame.Rect(ex-34,ey-26+sq,68,48-sq*2),4)

        # ─ Iris ──────────────────────────────────────────────
        ir=20
        # Hija e irisit
        pygame.draw.circle(self.screen,(60,32,10),(ex+2,ey+2),ir)
        # Shtresa e errët
        pygame.draw.circle(self.screen,(70,40,14),(ex,ey),ir)
        # Shtresat me ngjyra të ndryshme (gradient manual)
        for r_,c_ in [(ir,(88,52,20)),(ir-4,(105,65,26)),(ir-8,(120,78,32))]:
            pygame.draw.circle(self.screen,c_,(ex,ey),r_)
        # Rrezet e irisit
        for i in range(12):
            a=math.radians(i*30)
            x1=ex+int(9*math.cos(a)); y1=ey+int(9*math.sin(a))
            x2=ex+int(18*math.cos(a)); y2=ey+int(18*math.sin(a))
            pygame.draw.line(self.screen,(70,40,12),(x1,y1),(x2,y2),1)

        # ─ Pupila ────────────────────────────────────────────
        pygame.draw.circle(self.screen,(20,10,4),(ex,ey),10)
        pygame.draw.circle(self.screen,EPP,(ex,ey),8)

        # ─ Shkëlqimet ────────────────────────────────────────
        # Kryesori
        pygame.draw.circle(self.screen,(255,255,255),(ex-8,ey-8),7)
        pygame.draw.circle(self.screen,(220,240,255),(ex-6,ey-6),4)
        # I dyti
        pygame.draw.circle(self.screen,(255,255,255),(ex+7,ey-4),4)
        pygame.draw.circle(self.screen,(200,230,255),(ex+8,ey-5),2)

        # ─ Qepalla lart (trashë, e kthyer) ───────────────────
        pygame.draw.arc(self.screen,OL,
            pygame.Rect(ex-36,ey-32+sq,72,40),
            math.pi*0.08, math.pi*0.92, 7)
        # Ciliat
        for i in range(8):
            a=math.radians(162-i*20)
            x1=ex+int(34*math.cos(a)); y1=ey+int(26*math.sin(a))
            x2=ex+int(42*math.cos(a)); y2=ey+int(34*math.sin(a))
            pygame.draw.line(self.screen,OL,(x1,y1),(x2,y2),3)

        # ─ Qepalla poshtë ────────────────────────────────────
        pygame.draw.arc(self.screen,OL2,
            pygame.Rect(ex-34,ey-18,68,36),
            math.pi*1.1, math.pi*1.9, 2)

    # ─── HUNDA ───────────────────────────────────────────────────────────────

    def _draw_nose(self):
        cx,cy=self.cx,self.cy
        nx,ny=cx,cy+30

        # Hija
        sh=pygame.Surface((52,54),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,50),sh.get_rect())
        self.screen.blit(sh,(nx-28,ny-4))

        # Maja e hundës — shtresa
        for col,rx,ry in [(SK4,22,26),(SK3,20,24),(SK1,18,22)]:
            pygame.draw.ellipse(self.screen,col,
                pygame.Rect(nx-rx,ny-ry+2,rx*2,ry*2))

        # Urat e hundës
        pygame.draw.line(self.screen,SK4,(cx-14,cy-2),(cx-18,cy+22),3)
        pygame.draw.line(self.screen,SK4,(cx+14,cy-2),(cx+18,cy+22),3)

        # Vrimët e hundës
        for side,ox in [(-1,-12),(1,2)]:
            pygame.draw.ellipse(self.screen,SK4,
                pygame.Rect(nx+ox,ny+8,14,10))
            pygame.draw.ellipse(self.screen,OL,
                pygame.Rect(nx+ox,ny+8,14,10),2)

        # Highlight
        pygame.draw.circle(self.screen,SK2,(nx-5,ny-4),7)
        pygame.draw.circle(self.screen,OL,(nx-5,ny-4),7,1)

        pygame.draw.ellipse(self.screen,OL,
            pygame.Rect(nx-22,ny-20,44,46),3)

    # ─── FAQET ───────────────────────────────────────────────────────────────

    def _draw_cheeks(self):
        if self.happy_cheek < 0.05: return
        cx,cy=self.cx,self.cy
        alpha=int(self.happy_cheek*110)
        for side in [-1,1]:
            s=pygame.Surface((70,42),pygame.SRCALPHA)
            pygame.draw.ellipse(s,(242,140,108,alpha),s.get_rect())
            self.screen.blit(s,(cx+side*58-35,cy+38-21))

    # ─── MJEKRA / STUBBLE ────────────────────────────────────────────────────

    def _draw_stubble(self):
        cx,cy=self.cx,self.cy
        # Hija e mjekrës
        s=pygame.Surface((175,98),pygame.SRCALPHA)
        pygame.draw.ellipse(s,(SK4[0],SK4[1],SK4[2],70),s.get_rect())
        self.screen.blit(s,(cx-88,cy+55))
        # Pikat e stubble-it
        random.seed(123)
        for _ in range(70):
            sx=cx+random.randint(-80,80)
            sy=cy+random.randint(62,105)
            if (sx-cx)**2/80**2+(sy-(cy+82))**2/44**2<0.9:
                col=lerp_color(SK3,SK4,random.random())
                pygame.draw.circle(self.screen,col,(sx,sy),random.randint(1,2))

    # ─── GOJA ────────────────────────────────────────────────────────────────

    def _draw_mouth(self):
        cx,cy=self.cx,self.cy
        my=cy+74

        # Buzët
        LIP_U=(188,112,75)
        LIP_D=(162,88, 55)
        LIP_L=(215,142,100)
        M_IN =(62, 18,  8)
        TOOTH=(252,252,250)

        if self.mouth_o < 0.04:
            # ─ Buzëqeshje e mbyllur ──────────────────────────
            # Gropa e faqes (dimple)
            for side in [-1,1]:
                pygame.draw.circle(self.screen,SK3,
                    (cx+side*66,my-4),5)

            # Harku i buzëqeshjes — shtresa
            for col,yoff,lw in [(OL,2,7),(LIP_U,0,5),(LIP_L,-2,3)]:
                pygame.draw.arc(self.screen,col,
                    pygame.Rect(cx-74,my-22+yoff,148,58),
                    math.pi+0.20, 2*math.pi-0.20, lw)

            # Dhëmbët e dukshëm
            clip=pygame.Rect(cx-64,my-2,128,28)
            pygame.draw.ellipse(self.screen,TOOTH,clip)
            # Ndarjet mes dhëmbëve
            for tx in range(-3,4):
                pygame.draw.line(self.screen,(195,195,192),
                    (cx+tx*19,my-2),(cx+tx*19,my+26),2)
            pygame.draw.line(self.screen,(190,190,188),
                (cx-62,my+1),(cx+62,my+1),2)
            pygame.draw.ellipse(self.screen,OL,clip,3)

            # Buza e poshtme
            for col,yoff,lw in [(OL,4,5),(LIP_D,2,4)]:
                pygame.draw.arc(self.screen,col,
                    pygame.Rect(cx-62,my+2+yoff,124,30),
                    0.15, math.pi-0.15, lw)

        else:
            # ─ Goja e hapur (duke folur) ──────────────────────
            h=max(8,int(self.mouth_o*46))

            # Brendësia
            mr=pygame.Rect(cx-62,my-h//2,124,h)
            pygame.draw.ellipse(self.screen,M_IN,mr)

            # Dhëmbët sipër
            tr=pygame.Rect(cx-54,my-h//2+3,108,h//2-2)
            pygame.draw.rect(self.screen,TOOTH,tr,border_radius=6)
            for tx in range(-2,3):
                pygame.draw.line(self.screen,(190,190,188),
                    (cx+tx*22,my-h//2+3),(cx+tx*22,my+3),2)
            pygame.draw.line(self.screen,(185,185,182),
                (cx-52,my+2),(cx+52,my+2),2)

            # Dhëmbët poshtë
            bt=pygame.Rect(cx-44,my+h//3,88,h//3)
            pygame.draw.rect(self.screen,TOOTH,bt,border_radius=5)

            # Buza
            pygame.draw.ellipse(self.screen,LIP_U,
                pygame.Rect(cx-66,my-h//2-8,132,h//2+8),)
            pygame.draw.ellipse(self.screen,M_IN,
                pygame.Rect(cx-58,my-h//2+2,116,h-4))
            pygame.draw.ellipse(self.screen,OL,mr,4)

    # ─── KASHTA / GRURI ──────────────────────────────────────────────────────

    def _draw_wheat(self):
        cx,cy=self.cx,self.cy
        wy=cy+80; sw=self.wheat_t

        for side in [-1,1]:
            # Bishti
            p0=(cx+side*5,wy)
            p1=(cx+side*65+int(sw),wy+8)
            p2=(cx+side*138+int(sw*1.3),wy-12)

            # Hija
            pygame.draw.line(self.screen,(0,0,0),(p0[0]+3,p0[1]+3),
                (p2[0]+3,p2[1]+3),4)
            # Shtresat
            pygame.draw.lines(self.screen,WH3,False,[p0,p1,p2],6)
            pygame.draw.lines(self.screen,WH1,False,[p0,p1,p2],3)
            pygame.draw.lines(self.screen,WH2,False,[p0,p1,p2],1)

            # Kokat e grurit — 3 grupe
            for i,frac in enumerate([0.58,0.76,0.92]):
                kx=int(p0[0]+(p2[0]-p0[0])*frac)
                ky=int(p0[1]+(p2[1]-p0[1])*frac)
                base=-90-side*42+i*side*10
                for j in range(7):
                    a=math.radians(base+j*side*24+sw*0.4)
                    lx=kx+int(16*math.cos(a))
                    ly=ky+int(16*math.sin(a))
                    # Bisht i degës
                    pygame.draw.line(self.screen,WH3,(kx,ky),(lx,ly),3)
                    pygame.draw.line(self.screen,WH1,(kx,ky),(lx,ly),2)
                    # Kokrra ovale
                    for col,rr in [(WH3,7),(WH1,6),(WH2,4)]:
                        pygame.draw.ellipse(self.screen,col,
                            pygame.Rect(lx-rr//2,ly-rr//3,rr,rr//2*3//2+2))
                    pygame.draw.ellipse(self.screen,OL,
                        pygame.Rect(lx-4,ly-3,8,6),1)

    # ─── BIMA QË RRITET ─────────────────────────────────────────────────────

    def _draw_plant_sprout(self):
        if self.plant_grow<0.05: return
        g=self.plant_grow
        cx=self.cx+98; cy=self.cy+138
        GREEN1=(60,188,68); GREEN2=(100,220,60); GREEN3=(30,140,40)
        sw2=math.sin(self.t*2)*3*g

        stem_h=int(52*g)
        pygame.draw.line(self.screen,GREEN3,(cx,cy),(cx+int(sw2),cy-stem_h),4)
        pygame.draw.line(self.screen,GREEN1,(cx,cy),(cx+int(sw2),cy-stem_h),2)

        if g>0.35:
            for side,ang0 in [(-1,-130),(1,-50)]:
                a=math.radians(ang0+sw2*side)
                lx=cx+int(sw2)+int(22*math.cos(a))
                ly=cy-int(stem_h*0.55)+int(22*math.sin(a))
                pts=[(cx+int(sw2),cy-int(stem_h*0.55)),
                     (cx+int(sw2)+int(20*math.cos(a)),
                      cy-int(stem_h*0.55)+int(20*math.sin(a)))]
                pygame.draw.polygon(self.screen,GREEN1,
                    [(cx+int(sw2),cy-int(stem_h*0.55)),
                     (lx,ly),(lx-side*8,ly+6)])
                pygame.draw.polygon(self.screen,GREEN2,
                    [(cx+int(sw2)+side*2,cy-int(stem_h*0.55)-2),
                     (lx-side*4,ly-4),(lx-side*10,ly+2)])

    # ─── GRIMCAT ────────────────────────────────────────────────────────────

    def _draw_particles(self):
        for p in self.parts:
            a=int(p["life"]*230)
            s=pygame.Surface((p["r"]*2,p["r"]*2),pygame.SRCALPHA)
            pygame.draw.circle(s,(*p["c"],max(0,min(255,a))),
                (p["r"],p["r"]),p["r"])
            self.screen.blit(s,(int(p["x"])-p["r"],int(p["y"])-p["r"]))

    # ─── MIKROFON ───────────────────────────────────────────────────────────

    def _draw_mic(self):
        cx,cy=self.cx,self.cy
        pulse=math.sin(self.mic_t)*0.5+0.5
        for i in range(4):
            r=int(30+i*22+pulse*15)
            a=int(160-i*38-pulse*30)
            s=pygame.Surface((r*2+4,r*2+4),pygame.SRCALPHA)
            pygame.draw.circle(s,(255,60,140,max(0,a)),(r+2,r+2),r,2)
            self.screen.blit(s,(cx-r-2,cy+68-r-2))

    # ─── HUD ────────────────────────────────────────────────────────────────

    def _draw_hud(self):
        # Titulli
        shadow=self.fnt_xl.render("TERRA GUIDE",True,(0,0,0))
        lbl   =self.fnt_xl.render("TERRA GUIDE",True,(210,178,95))
        self.screen.blit(shadow,(self.cx-shadow.get_width()//2+2,7))
        self.screen.blit(lbl,   (self.cx-lbl.get_width()//2,    5))

        # Shiriti animuar
        pw=int(85+45*math.sin(self.t*1.5))
        pygame.draw.line(self.screen,(60,48,12),(self.cx-pw+1,32),(self.cx+pw+1,32),2)
        pygame.draw.line(self.screen,(195,158,60),(self.cx-pw,31),(self.cx+pw,31),2)

        # Status
        mc={"idle":(180,180,180),"moving":(80,210,255),
            "analyzing":(255,215,55),"listening":(255,85,155),
            "planting":(85,248,95)}.get(self.mode,(180,180,180))
        sh=self.fnt_md.render(self.status,True,(0,0,0))
        lb=self.fnt_md.render(self.status,True,mc)
        self.screen.blit(sh,(self.cx-sh.get_width()//2+1,self.H-22))
        self.screen.blit(lb,(self.cx-lb.get_width()//2,  self.H-23))

    def _draw_sidebar(self):
        # Shiriti i lagështisë
        bx,by=self.W-48,42
        bh,bw=self.H-78,16

        # Sfond
        s=pygame.Surface((bw+8,bh+8),pygame.SRCALPHA)
        pygame.draw.rect(s,(0,0,0,80),s.get_rect(),border_radius=8)
        self.screen.blit(s,(bx-4,by-4))

        pygame.draw.rect(self.screen,(30,22,8),
            pygame.Rect(bx,by,bw,bh),border_radius=6)
        pygame.draw.rect(self.screen,(140,108,38),
            pygame.Rect(bx,by,bw,bh),2,border_radius=6)

        fh=int((self.moisture/100)*(bh-4))
        fc=((255,75,38) if self.moisture<30 else
            (255,175,28) if self.moisture<55 else (72,205,75))
        # Gradient bari — shtresa
        for i in range(fh):
            t=i/max(fh,1)
            c=lerp_color(lerp_color(fc,(255,255,255),0.3),fc,t)
            pygame.draw.line(self.screen,c,
                (bx+2,by+bh-2-i),(bx+bw-2,by+bh-2-i))
        pygame.draw.rect(self.screen,(140,108,38),
            pygame.Rect(bx,by,bw,bh),2,border_radius=6)

        # Etiketa
        l=self.fnt_sm.render("H₂O",True,(175,138,48))
        self.screen.blit(l,(bx+bw//2-l.get_width()//2,by-16))
        v=self.fnt_sm.render(f"{int(self.moisture)}%",True,fc)
        self.screen.blit(v,(bx+bw//2-v.get_width()//2,by+bh+4))

        # Tastiera info
        keys=[("1","IDLE"),("2","MOVE"),("3","ANAL"),("4","LIST"),("5","PLANT")]
        for i,(k,label) in enumerate(keys):
            ky=by+20+i*28
            col=(72,205,75) if self.mode==label.lower()[:4] or \
                (self.mode=="idle" and k=="1") else (80,80,80)
            kb=self.fnt_sm.render(f"[{k}]",True,col)
            self.screen.blit(kb,(8,ky))