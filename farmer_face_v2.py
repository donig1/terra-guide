import pygame
import threading
import time
import requests

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Terra Guide")
clock = pygame.time.Clock()

font_med   = pygame.font.SysFont("dejavusans", 32)
font_small = pygame.font.SysFont("dejavusans", 22)
font_tiny  = pygame.font.SysFont("dejavusans", 18)

SIZE = (WIDTH, HEIGHT)

def load(name):
    try:
        img = pygame.image.load(name).convert_alpha()
        return pygame.transform.scale(img, SIZE)
    except Exception as e:
        print(f"[IMG] {name}: {e}")
        s = pygame.Surface(SIZE, pygame.SRCALPHA)
        s.fill((30, 80, 30, 255))
        return s

idle_img      = load("idle.png")
talk1_img     = load("talking1.png")
talk2_img     = load("talking2.png")
thinking_img  = load("thinking.png")
listening_img = load("listening.png")
blink_img     = load("blink.png")

state      = "idle"
face_text  = ""
last_blink = time.time()

sensor_data = {
    "soil_temp": "--", "moisture_pct": "--",
    "air_temp": "--", "planting_suitable": "--",
    "moisture_status": "OPTIMAL", "temp_status": "OPTIMAL",
}

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
        time.sleep(0.5)

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
        time.sleep(3)

threading.Thread(target=fetch_face_state, daemon=True).start()
threading.Thread(target=fetch_sensors,    daemon=True).start()

def draw_sensors():
    cards = [
        ("Soil Temp",  str(sensor_data.get("soil_temp",    "--")) + "C",
         sensor_data.get("temp_status", "OPTIMAL")),
        ("Moisture",   str(sensor_data.get("moisture_pct", "--")) + "%",
         sensor_data.get("moisture_status", "OPTIMAL")),
        ("Air Temp",   str(sensor_data.get("air_temp",     "--")) + "C",
         "OPTIMAL"),
        ("Plant?",
         "YES" if sensor_data.get("planting_suitable") == "True" else "NO",
         "OPTIMAL" if sensor_data.get("planting_suitable") == "True" else "DRY"),
    ]

    card_w = 160
    card_h = 70
    gap    = 12
    total  = len(cards) * card_w + (len(cards)-1) * gap
    x0     = (WIDTH - total) // 2
    y0     = HEIGHT - 90

    for i, (lbl, val, status) in enumerate(cards):
        x = x0 + i * (card_w + gap)
        if status in ("DRY", "TOO_COLD", "HOT", "CRITICAL"):
            border = (255, 80, 80)
            bg     = (80, 10, 10, 180)
        else:
            border = (0, 200, 60)
            bg     = (0, 60, 10, 180)

        s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        s.fill(bg)
        screen.blit(s, (x, y0))
        pygame.draw.rect(screen, border, (x, y0, card_w, card_h), 2, border_radius=10)

        val_s = font_med.render(val,  True, (150, 255, 150))
        lbl_s = font_tiny.render(lbl, True, (100, 200, 100))
        screen.blit(val_s, (x + card_w//2 - val_s.get_width()//2, y0 + 8))
        screen.blit(lbl_s, (x + card_w//2 - lbl_s.get_width()//2, y0 + card_h - 22))

def draw_status():
    labels = {
        "idle":      ("Ready!",        (100, 220, 100)),
        "talking":   ("Speaking...",   (100, 200, 255)),
        "listening": ("Listening...",  (80,  180, 255)),
        "thinking":  ("Thinking...",   (255, 220, 80)),
        "alarm":     ("ALARM!",        (255, 80,  80)),
    }
    text, color = labels.get(state, ("...", (200, 200, 200)))

    s = pygame.Surface((300, 45), pygame.SRCALPHA)
    s.fill((0, 0, 0, 140))
    screen.blit(s, (WIDTH//2 - 150, 20))

    surf = font_med.render(text, True, color)
    screen.blit(surf, (WIDTH//2 - surf.get_width()//2, 28))

def draw_text():
    if not face_text or state != "talking":
        return
    max_w = WIDTH - 100
    words = face_text.split()
    line, lines = "", []
    for w in words:
        test = line + w + " "
        if font_small.size(test)[0] > max_w:
            lines.append(line)
            line = w + " "
        else:
            line = test
    if line:
        lines.append(line)

    box_h = len(lines) * 30 + 16
    box_y = HEIGHT - 100 - box_h

    s = pygame.Surface((max_w + 40, box_h), pygame.SRCALPHA)
    s.fill((0, 0, 0, 170))
    screen.blit(s, (50, box_y))
    pygame.draw.rect(screen, (0, 180, 60), (50, box_y, max_w+40, box_h), 1, border_radius=8)

    for j, ln in enumerate(lines):
        surf = font_small.render(ln.strip(), True, (200, 255, 200))
        screen.blit(surf, (WIDTH//2 - surf.get_width()//2, box_y + 8 + j*30))

def draw_face():
    global last_blink
    if state == "listening":
        screen.blit(listening_img, (0, 0))
    elif state == "thinking":
        screen.blit(thinking_img, (0, 0))
    elif state == "talking":
        if int(time.time() * 8) % 2 == 0:
            screen.blit(talk1_img, (0, 0))
        else:
            screen.blit(talk2_img, (0, 0))
    elif state == "alarm":
        screen.blit(idle_img, (0, 0))
    else:
        if time.time() - last_blink > 4:
            screen.blit(blink_img, (0, 0))
            pygame.display.flip()
            time.sleep(0.1)
            last_blink = time.time()
        else:
            screen.blit(idle_img, (0, 0))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_1: state = "idle"
            if event.key == pygame.K_2: state = "talking"
            if event.key == pygame.K_3: state = "listening"
            if event.key == pygame.K_4: state = "thinking"
            if event.key == pygame.K_5: state = "alarm"

    draw_face()
    draw_status()
    draw_text()
    draw_sensors()

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
