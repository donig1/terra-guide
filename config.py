# ============================================
# config.py – ARES-X V3 Konfigurimet
# ============================================

# ── Serial (Arduino Mega) ──────────────────
SERIAL_PORT = '/dev/ttyACM0'
SERIAL_BAUD = 9600

# ── HuskyLens ─────────────────────────────
HUSKYLENS_MODE     = 'I2C'       # 'I2C' ose 'UART'
HUSKYLENS_I2C_ADDR = 0x32
HUSKYLENS_UART     = '/dev/ttyAMA0'
HUSKYLENS_BAUD     = 9600

# ── Servo (pin në Arduino) ─────────────────
SERVO_PIN_ARDUINO  = 9

# ── Ferma ──────────────────────────────────
FARM = {
    "crop":               "domate",
    "field_area_m2":      500,
    "seed_spacing_cm":    40,      # distanca mes farave (cm)
    "optimal_depth_cm":   3,       # thellesia e mbjelljes (cm)
    "market_price_kg":    0.80,
    "yield_kg_m2":        4,
    "stops_per_row":      10,      # pikat e matjes per rresht
}

# ── Pragjet Sensorësh ──────────────────────
THRESHOLDS = {
    # Soil Moisture VL1.2 (0=i lagur, 1023=thatë)
    "moisture_wet":       300,
    "moisture_ok":        500,
    "moisture_dry":       700,
    "moisture_critical":  850,
    # Temperatura tokës DS18B20
    "soil_temp_min":      8,
    "soil_temp_plant":    12,
    "soil_temp_optimal":  20,
    "soil_temp_max":      32,
    # Temperatura ajrit DHT22
    "air_temp_max":       35,
    # Lagështia ajrit
    "humidity_low":       30,
    "humidity_high":      80,
    # Pengesa
    "obstacle_cm":        20,
}

# ── Raspberry Pi (IP ne rrjet lokal) ───────
# Ndrysho kete me IP-ne e vertete te Raspberry Pi!
# (komanda: hostname -I  ne terminal te Pi)
PI_IP   = "172.20.10.2"

# ── Dashboard ──────────────────────────────
DASHBOARD_PORT = 5000
DATA_FILE      = "data/farm_data.csv"
LOG_FILE       = "logs/ares_x.log"

# ── Misioni ────────────────────────────────
MAX_STOPS      = 5

# ── Chatbot ────────────────────────────────
CHATBOT_LANGUAGE = "sq"
VOICE_RATE       = 150

# ── Display / Fytyra ───────────────────────
SCREEN_W          = 1024
SCREEN_H          = 768
FULLSCREEN        = True
FPS               = 30

# Madhësia e fytyrës (ul numrin nëse del e madhe)
FACE_SCALE        = 0.25        # 0.32 → ~245px radius

# Qendra e fytyrës
FACE_CENTER_X     = SCREEN_W // 2    # 512
FACE_CENTER_Y     = SCREEN_H // 2    # 384

# Ngjyrat kryesore
BG_COLOR          = (15, 10, 5)      # sfond i errët
SKIN_COLOR        = (139, 90, 43)    # lëkurë fermeri
SKIN_SHADOW       = (100, 60, 20)    # hije lëkure
SKIN_HIGHLIGHT    = (180, 120, 60)   # dritë lëkure
EYE_WHITE         = (240, 235, 225)
EYE_IRIS          = (70, 100, 120)   # blu-gri
EYE_PUPIL         = (20, 15, 10)
HAT_COLOR         = (180, 150, 80)   # kashtë
HAT_SHADOW        = (130, 100, 40)
SHIRT_RED         = (160, 30, 30)    # fanellë e kuqe
SHIRT_DARK        = (40, 10, 10)
LIP_COLOR         = (140, 80, 60)
STUBBLE_COLOR     = (80, 60, 50)
WRINKLE_COLOR     = (100, 65, 30)
CHEEK_BLUSH       = (180, 90, 60, 60)  # RGBA — njollë dielli