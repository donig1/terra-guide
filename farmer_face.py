import pygame
import math
import random
import threading
import requests

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()
pygame.display.set_caption("ARES-X")

# ── Fontet ──────────────────────────────────
font_big    = pygame.font.SysFont("dejavusans", 48, bold=True)
font_med    = pygame.font.SysFont("dejavusans", 32)
font_small  = pygame.font.SysFont("dejavusans", 22)
font_tiny   = pygame.font.SysFont("dejavusans", 18)

# ── Gjendja globale ─────────────────────────
state       = "idle"
blink       = False
blink_timer = 0

sensor_data = {
    "soil_temp":         "--",
    "moisture_pct":      "--",
    "air_temp":          "--",
    "planting_suitable": "--",
    "needs_irrigation":  "False",
    "moisture_status":   "OPTIMAL"
}

face_text = ""   # Teksti që shfaqet kur flet

# ── API Threads ─────────────────────────────

def fetch_face_state():
    global state, face_text
    while True:
        try:
            r    = requests.get("http://localhost:5000/api/face_state", timeout=1)
            data = r.json()
            state     = data.get("state", "idle")
            face_text = data.get("text",  "")
        except:
            pass
        pygame.time.wait(500)

def fetch_sensors():
    global sensor_data
    while True:
        try:
            r = requests.get("http://localhost:5000/api/latest", timeout=1)
            d = r.json()
            if d:
                sensor_data.update(d)
        except:
            pass
        pygame.time.wait(3000)

threading.Thread(target=fetch_face_state, daemon=True).start()
threading.Thread(target=fetch_sensors,    daemon=True).start()

# ── Ngjyrat ─────────────────────────────────
BG_COLOR      = (15, 47, 31)
FACE_NORMAL   = (216, 155, 132)
FACE_ALARM    = (255, 90,  90)
FACE_HAPPY    = (220, 170, 140)
FACE_LISTEN   = (200, 160, 130)
GREEN_GLOW    = (0,   200, 80)
BLUE_GLOW     = (50,  150, 255)
RED_GLOW      = (255, 50,  50)

# ── Grimca background ───────────────────────
particles = [
    {
        "x": random.randint(0, 1920),
        "y": random.randint(0, 1080),
        "speed": random.uniform(0.5, 2),
        "size": random.randint(2, 6),
        "alpha": random.randint(50, 150)
    }
    for _ in range(40)
]

def update_particles():
    for p in particles:
        p["y"] += p["speed"]
        p["x"] += math.sin(p["y"] * 0.02) * 0.5
        if p["y"] > HEIGHT:
            p["y"] = -10
            p["x"] = random.randint(0, WIDTH)

def draw_particles():
    for p in particles:
        s = pygame.Surface((p["size"], p["size"]*2), pygame.SRCALPHA)
        s.fill((0, 180, 60, p["alpha"]))
        screen.blit(s, (int(p["x"]), int(p["y"])))

# ── Valë zanore ─────────────────────────────
wave_phase = 0

def draw_wave(cx, cy, color, active):
    global wave_phase
    wave_phase += 0.2
    bars = 9
    for i in range(bars):
        if active:
            h = 15 + math.sin(wave_phase + i * 0.8) * 20
        else:
            h = 5
        x = cx - (bars * 14) // 2 + i * 14
        pygame.draw.rect(screen, color,
                         (x, cy - int(h)//2, 8, int(h)),
                         border_radius=4)

# ── Vizato sensorët ─────────────────────────
def draw_sensors(cy_bottom):
    cards = [
        ("Temp. Tokes",  str(sensor_data.get("soil_temp",    "--")) + "°C",
         sensor_data.get("temp_status", "OPTIMAL")),
        ("Lagështia",    str(sensor_data.get("moisture_pct", "--")) + "%",
         sensor_data.get("moisture_status", "OPTIMAL")),
        ("Temp. Ajrit",  str(sensor_data.get("air_temp",     "--")) + "°C",
         "OPTIMAL"),
        ("Mbjellë?",
         "PO" if sensor_data.get("planting_suitable") == "True" else "JO",
         "OPTIMAL" if sensor_data.get("planting_suitable") == "True" else "DRY"),
    ]

    card_w = 160
    card_h = 80
    gap    = 20
    total  = len(cards) * card_w + (len(cards)-1) * gap
    x0     = (WIDTH - total) // 2
    y0     = cy_bottom + 30

    for i, (lbl, val, status) in enumerate(cards):
        x = x0 + i * (card_w + gap)

        # Ngjyra sipas statusit
        if status in ("DRY", "TOO_COLD", "HOT"):
            border = (255, 80, 80)
            bg     = (80, 10, 10, 180)
        elif status in ("CRITICAL",):
            border = (255, 50, 50)
            bg     = (100, 0, 0, 180)
        else:
            border = (0, 180, 60)
            bg     = (0, 60, 20, 180)

        # Background karte
        s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        s.fill((*bg[:3], 180))
        screen.blit(s, (x, y0))
        pygame.draw.rect(screen, border, (x, y0, card_w, card_h),
                         2, border_radius=12)

        # Vlera
        val_surf = font_med.render(val, True, (130, 255, 130))
        screen.blit(val_surf,
                    (x + card_w//2 - val_surf.get_width()//2,
                     y0 + 12))

        # Label
        lbl_surf = font_tiny.render(lbl, True, (100, 180, 100))
        screen.blit(lbl_surf,
                    (x + card_w//2 - lbl_surf.get_width()//2,
                     y0 + card_h - 26))

# ── Vizato fermerin ─────────────────────────
def draw_farmer(t):
    global blink, blink_timer

    cx = WIDTH  // 2
    cy = HEIGHT // 2 - 60

    # Lëvizje sipas gjendjes
    if state == "idle":
        cy += int(math.sin(t * 1.5) * 5)
    if state == "alarm":
        cx += int(math.sin(t * 25) * 10)

    # Ngjyra fytyre
    if state == "alarm":
        face_color = FACE_ALARM
        glow_col   = RED_GLOW
    elif state == "happy":
        face_color = FACE_HAPPY
        glow_col   = GREEN_GLOW
    elif state == "listening":
        face_color = FACE_LISTEN
        glow_col   = BLUE_GLOW
    else:
        face_color = FACE_NORMAL
        glow_col   = GREEN_GLOW

    # Glow rreth kokës
    for r in range(140, 118, -4):
        alpha = max(0, 40 - (140-r)*4)
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*glow_col, alpha), (r, r), r)
        screen.blit(s, (cx-r, cy-r))

    # Koka
    pygame.draw.circle(screen, face_color, (cx, cy), 120)

    # ── Blink ──
    blink_timer += 1
    if blink_timer > random.randint(150, 220):
        blink = True
    if blink:
        eye_h = 4
        if blink_timer > 230:
            blink      = False
            blink_timer = 0
    else:
        eye_h = 28

    if state == "happy":    eye_h = 6
    if state == "alarm":    eye_h = 32
    if state == "listening": eye_h = 32

    # Sytë
    pygame.draw.ellipse(screen, (255,255,255),
                        (cx-65, cy-45, 55, eye_h))
    pygame.draw.ellipse(screen, (255,255,255),
                        (cx+10, cy-45, 55, eye_h))

    # Pupilat ndjekin miun/gishtin
    mx, my = pygame.mouse.get_pos()
    px = (mx - cx) * 0.025
    py = (my - cy) * 0.025
    px = max(-12, min(12, px))
    py = max(-8,  min(8,  py))

    if eye_h > 10:
        # Pupila
        pygame.draw.circle(screen, (40,40,40),
                           (cx-37+int(px), cy-28+int(py)), 11)
        pygame.draw.circle(screen, (40,40,40),
                           (cx+37+int(px), cy-28+int(py)), 11)
        # Drita syrit
        pygame.draw.circle(screen, (255,255,255),
                           (cx-33+int(px), cy-33+int(py)), 4)
        pygame.draw.circle(screen, (255,255,255),
                           (cx+41+int(px), cy-33+int(py)), 4)

    # ── Vetullat ──
    brow_y = cy - 80
    if state == "alarm":
        pygame.draw.line(screen, (130,130,130),
                         (cx-75, brow_y+15), (cx-25, brow_y), 7)
        pygame.draw.line(screen, (130,130,130),
                         (cx+25, brow_y),    (cx+75, brow_y+15), 7)
    elif state == "happy":
        pygame.draw.line(screen, (130,130,130),
                         (cx-75, brow_y),    (cx-25, brow_y-10), 7)
        pygame.draw.line(screen, (130,130,130),
                         (cx+25, brow_y-10), (cx+75, brow_y), 7)
    elif state == "listening":
        pygame.draw.line(screen, (130,130,130),
                         (cx-75, brow_y-5),  (cx-25, brow_y-5), 7)
        pygame.draw.line(screen, (130,130,130),
                         (cx+25, brow_y-12), (cx+75, brow_y-5), 7)
    else:
        pygame.draw.line(screen, (130,130,130),
                         (cx-75, brow_y),    (cx-25, brow_y), 7)
        pygame.draw.line(screen, (130,130,130),
                         (cx+25, brow_y),    (cx+75, brow_y), 7)

    # ── Hunda ──
    pygame.draw.circle(screen, (255,160,150), (cx, cy+15), 28)
    pygame.draw.circle(screen, (200,120,110), (cx-10, cy+20), 10)
    pygame.draw.circle(screen, (200,120,110), (cx+10, cy+20), 10)

    # ── Mustaqet ──
    must_y = cy + 48
    if state == "happy":    must_y -= 10
    if state == "talking":  must_y -= 5

    # E majtë
    points_l = [
        (cx-10, must_y),
        (cx-40, must_y-15),
        (cx-80, must_y-5),
        (cx-70, must_y+15),
        (cx-30, must_y+10),
    ]
    pygame.draw.polygon(screen, (210,210,210), points_l)
    pygame.draw.polygon(screen, (180,180,180), points_l, 2)

    # E djathtë
    points_r = [
        (cx+10, must_y),
        (cx+40, must_y-15),
        (cx+80, must_y-5),
        (cx+70, must_y+15),
        (cx+30, must_y+10),
    ]
    pygame.draw.polygon(screen, (210,210,210), points_r)
    pygame.draw.polygon(screen, (180,180,180), points_r, 2)

    # ── Goja ──
    mouth_y = cy + 75
    if state == "talking":
        mouth_open = int(25 + math.sin(t * 15) * 20)
        pygame.draw.ellipse(screen, (120,20,20),
                            (cx-45, mouth_y, 90, mouth_open))
        # Dhëmbët
        pygame.draw.ellipse(screen, (240,240,240),
                            (cx-35, mouth_y+2, 70, 12))
    elif state == "happy":
        pygame.draw.arc(screen, (180,30,30),
                        (cx-50, mouth_y-10, 100, 60),
                        0, math.pi, 6)
    elif state == "alarm":
        pygame.draw.ellipse(screen, (180,20,20),
                            (cx-40, mouth_y, 80, 55))
    else:
        pygame.draw.ellipse(screen, (150,60,60),
                            (cx-40, mouth_y, 80, 22))

    # ── Mjekrra ──
    pygame.draw.ellipse(screen, (200,200,200),
                        (cx-65, cy+95, 130, 65))

    # ── Veshët ──
    pygame.draw.ellipse(screen, face_color,
                        (cx-148, cy-30, 38, 60))
    pygame.draw.ellipse(screen, face_color,
                        (cx+110, cy-30, 38, 60))

    # Vath
    pygame.draw.circle(screen, (200,180,100), (cx-129, cy+35), 6)
    pygame.draw.circle(screen, (200,180,100), (cx+129, cy+35), 6)

    # ── Flokët gri ──
    pygame.draw.ellipse(screen, (180,180,180),
                        (cx-118, cy-115, 236, 50))

    # ── Kapela kashte ──
    # Strehë
    pygame.draw.ellipse(screen, (210,185,110),
                        (cx-170, cy-168, 340, 75))
    pygame.draw.ellipse(screen, (190,165,90),
                        (cx-170, cy-168, 340, 75), 3)
    # Kupolë
    pygame.draw.ellipse(screen, (215,190,115),
                        (cx-105, cy-235, 210, 150))
    pygame.draw.ellipse(screen, (190,165,90),
                        (cx-105, cy-235, 210, 150), 3)
    # Shirit i kuq
    pygame.draw.rect(screen, (180,40,40),
                     (cx-105, cy-178, 210, 22))

    # ── Trupi (overall) ──
    body_y = cy + 140
    pygame.draw.rect(screen, (40,90,160),
                     (cx-110, body_y, 220, 120),
                     border_radius=15)
    # Brez
    pygame.draw.rect(screen, (60,40,20),
                     (cx-110, body_y, 220, 22))
    pygame.draw.rect(screen, (200,160,30),
                     (cx-18, body_y+4, 36, 14),
                     border_radius=4)
    # Xhep me logo
    pygame.draw.rect(screen, (50,100,175),
                     (cx-95, body_y+30, 60, 50),
                     border_radius=5)
    pygame.draw.rect(screen, (80,140,220),
                     (cx-95, body_y+30, 60, 50), 2,
                     border_radius=5)
    logo = font_tiny.render("ARES-X", True, (150,220,255))
    screen.blit(logo, (cx-90, body_y+48))

    # ── Valë zanore ──
    wave_active = state in ("talking", "listening")
    wave_color  = BLUE_GLOW if state == "listening" else GREEN_GLOW
    draw_wave(cx, cy + 290, wave_color, wave_active)

    # ── Teksti kur flet ──
    if face_text and state == "talking":
        max_w  = 600
        words  = face_text.split()
        line   = ""
        lines  = []
        for w in words:
            test = line + w + " "
            if font_small.size(test)[0] > max_w:
                lines.append(line)
                line = w + " "
            else:
                line = test
        if line:
            lines.append(line)

        box_h = len(lines) * 30 + 20
        box_y = cy + 310
        s = pygame.Surface((max_w+40, box_h), pygame.SRCALPHA)
        s.fill((0, 60, 20, 200))
        screen.blit(s, (cx - max_w//2 - 20, box_y))
        pygame.draw.rect(screen, GREEN_GLOW,
                         (cx-max_w//2-20, box_y, max_w+40, box_h),
                         1, border_radius=10)
        for j, ln in enumerate(lines):
            surf = font_small.render(ln.strip(), True, (180, 255, 180))
            screen.blit(surf, (cx - surf.get_width()//2,
                               box_y + 10 + j*30))

    return cy + 175   # kthen pozicionin e poshtëm për sensorët

# ── Loop kryesor ────────────────────────────
running = True
while running:
    t = pygame.time.get_ticks() / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            # Taste për testim manual
            if event.key == pygame.K_1: state = "idle"
            if event.key == pygame.K_2: state = "talking"
            if event.key == pygame.K_3: state = "listening"
            if event.key == pygame.K_4: state = "alarm"
            if event.key == pygame.K_5: state = "happy"

    screen.fill(BG_COLOR)

    # Grimcat background
    update_particles()
    draw_particles()

    # Titulli
    title = font_big.render("ARES-X", True, (80, 255, 100))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 20))

    # Fermeri
    bottom_y = draw_farmer(t)

    # Sensorët
    draw_sensors(bottom_y)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()