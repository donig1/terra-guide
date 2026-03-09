# ============================================
# config.py – ARES-X V3 Konfigurimet
# ============================================

# ── Serial (Arduino Mega) ──────────────────
SERIAL_PORT = '/dev/ttyACM0'
SERIAL_BAUD = 9600

# ── HuskyLens ─────────────────────────────
# Provoje I2C fillimisht, nëse nuk punon kalo UART
HUSKYLENS_MODE     = 'I2C'       # 'I2C' ose 'UART'
HUSKYLENS_I2C_ADDR = 0x32
HUSKYLENS_UART     = '/dev/ttyAMA0'
HUSKYLENS_BAUD     = 9600

# ── Servo (pin në Arduino) ─────────────────
SERVO_PIN_ARDUINO  = 9           # Pin servo në Arduino Mega

# ── Ferma ──────────────────────────────────
FARM = {
    "crop":               "domate",
    "field_area_m2":      500,
    "water_cost_eur_m3":  0.35,
    "market_price_kg":    0.80,
    "pump_l_per_min":     15,
    "pump_time_min":      20,
    "yield_kg_m2":        4,
}

# ── Pragjet Sensorësh ──────────────────────
THRESHOLDS = {
    # Soil Moisture VL1.2 (0=i lagur, 1023=thatë)
    "moisture_wet":       300,    # Nën këtë → shumë i lagur
    "moisture_ok":        500,    # 300-500 → optimal
    "moisture_dry":       700,    # 500-700 → i thatë
    "moisture_critical":  850,    # Mbi këtë → kritikisht thatë

    # Temperatura tokës DS18B20
    "soil_temp_min":      8,      # °C – shumë ftohtë për mbjellë
    "soil_temp_plant":    12,     # °C – minimum për mbjellë
    "soil_temp_optimal":  20,     # °C – optimal
    "soil_temp_max":      32,     # °C – stres termik

    # Temperatura ajrit DHT22
    "air_temp_max":       35,

    # Lagështia ajrit
    "humidity_low":       30,     # % – shumë e thatë
    "humidity_high":      80,     # % – shumë e lagur

    # Pengesa
    "obstacle_cm":        20,
}

# ── Dashboard ──────────────────────────────
DASHBOARD_PORT = 5000
DATA_FILE      = "data/farm_data.csv"
LOG_FILE       = "logs/ares_x.log"

# ── Chatbot ────────────────────────────────
CHATBOT_LANGUAGE = "sq"          # "sq"=shqip, "en"=anglisht
VOICE_RATE       = 150           # Shpejtësia e të folurit