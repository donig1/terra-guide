"""
Terra Guide — main.py  (v3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Launches 3 threads:
  1. arduino_thread  — reads sensors → sensor_data dict
  2. chatbot_thread  — voice loop (listen → GPT → speak → face)
  3. main thread     — pygame face (run_face blocks here)

Keys during run:
  1-9, 0 = manual face state
  ESC     = quit
"""

import threading
import queue
import time
import math
import random

from face_engine import run_face

# ── Shared state ─────────────────────────────────────────────────────────
cmd_queue   = queue.Queue()    # chatbot → face
sensor_data = {}               # arduino → chatbot + face


# ── Arduino thread ────────────────────────────────────────────────────────
def arduino_thread():
    try:
        from arduino_comm import ArduinoComm
        arduino = ArduinoComm()
        use_real = True
        print("[Arduino] Connected to real hardware")
    except Exception:
        arduino  = None
        use_real = False
        print("[Arduino] Hardware not found — using simulation")

    t = 0.0
    while True:
        t += 0.5

        if use_real and arduino:
            data = arduino.read_data()
        else:
            # ── Simulation ──────────────────────────────────────
            raw = int(450 + math.sin(t * 0.28) * 220)
            raw = max(0, min(1023, raw))
            pct = round((1 - raw / 1023) * 100, 1)

            if   raw < 300: status = 'WET'
            elif raw < 500: status = 'OPTIMAL'
            elif raw < 700: status = 'DRY'
            else:           status = 'CRITICAL'

            data = {
                'moisture_raw':    raw,
                'moisture_pct':    pct,
                'moisture_status': status,
                'soil_temp':       round(21 + math.sin(t * 0.18) * 5, 1),
                'air_temp':        round(24 + math.sin(t * 0.13) * 3, 1),
                'humidity':        round(60 + math.sin(t * 0.22) * 14, 0),
                'distance':        round(80 + random.uniform(-10, 10), 1),
                'pump_active':     status in ('DRY', 'CRITICAL'),
                'crop':            'tomatoes',
            }

        sensor_data.update(data)
        time.sleep(0.5)


# ── Chatbot thread ────────────────────────────────────────────────────────
def chatbot_thread(farming_ops=None):
    # Wait for pygame/face to init
    time.sleep(2.5)

    try:
        from chatbot import ChatBot
        bot = ChatBot(face_queue=cmd_queue, sensor_data=sensor_data, farming_ops=farming_ops)
        bot.run_voice_loop()

    except ImportError as e:
        print(f"[Chatbot] Import error: {e}")
        _demo_mode()

    except Exception as e:
        print(f"[Chatbot] Error: {e}")
        _demo_mode()


def _demo_mode():
    """Fallback demo if chatbot fails — cycles through messages."""
    print("[Chatbot] Running in demo mode (no voice)")
    MSGS = [
        ('happy',    "Good morning! I am Terra Guide, your field assistant."),
        ('talking',  "Soil moisture is currently optimal for tomatoes."),
        ('thinking', "Analyzing temperature and humidity trends..."),
        ('sad',      "Moisture levels are starting to drop. Monitor closely."),
        ('surprised',"Obstacle detected just ahead! Stopping now."),
        ('laughing', "Great news — rain is forecast for tomorrow!"),
        ('angry',    "Critical alert! Pump activated immediately."),
        ('idle',     ""),
    ]
    i = 0
    while True:
        state, text = MSGS[i % len(MSGS)]
        cmd_queue.put({'state': state, 'text': text, 'mic': False})
        i += 1
        time.sleep(5.0)


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("🌱 Terra Guide starting...")

    # Initialize Arduino communication
    try:
        from arduino_comm import ArduinoComm
        arduino = ArduinoComm()
    except Exception as e:
        print(f"[Main] Arduino init error: {e}")
        arduino = None
    
    # Initialize farming operations (servo control)
    farming_ops = None
    if arduino:
        try:
            from farming_operations import FarmingOperations
            farming_ops = FarmingOperations(arduino)
            print("[Main] Farming operations initialized ✓")
        except Exception as e:
            print(f"[Main] Farming operations error: {e}")

    t1 = threading.Thread(target=arduino_thread, daemon=True, name='Arduino')
    t2 = threading.Thread(target=chatbot_thread, args=(farming_ops,), daemon=True, name='ChatBot')
    t1.start()
    t2.start()

    # pygame must run on main thread
    run_face(cmd_queue=cmd_queue, sensor_data=sensor_data)

    print("Terra Guide stopped.")