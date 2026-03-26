"""
Terra Guide — pi_main.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ky file ekzekutohet NE RASPBERRY PI.

Nis:
  1. arduino_thread   — lexon sensoret (cdo 0.5s)
  2. chatbot_thread   — voice loop (mikrofon → GPT → komanda)
  3. auto_emotion_thread — monitoron statusin e tokës
  4. dashboard thread — Flask server ne port 5000

Fytyra NUK niset ketu — ajo del ne laptop (laptop_face.py).
"""

import threading
import queue
import time
import math
import random

cmd_queue   = queue.Queue()
sensor_data = {}

try:
    import dashboard as _dash
    _DASH_OK = True
except Exception:
    _DASH_OK = False

try:
    from face_engine import run_face
    _FACE_OK = True
except Exception:
    _FACE_OK = False


# ── Arduino thread ────────────────────────────────────────────────────────
def arduino_thread():
    try:
        from arduino_comm import ArduinoComm
        arduino = ArduinoComm()
        use_real = True
        print("[Arduino] Lidhur me hardware-in real")
    except Exception:
        arduino  = None
        use_real = False
        print("[Arduino] Hardware jo i gjetur — simulim aktiv")

    t = 0.0
    while True:
        t += 0.5

        if use_real and arduino:
            data = arduino.read_data()
        else:
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
                'can_plant':       status == 'OPTIMAL',
                'crop':            'tomatoes',
            }

        sensor_data.update(data)
        if _DASH_OK:
            try: _dash._live_sensors.update(data)
            except Exception: pass
        time.sleep(0.5)


# ── Chatbot thread ────────────────────────────────────────────────────────
def chatbot_thread(farming_ops=None):
    time.sleep(2.5)
    try:
        from chatbot import ChatBot
        bot = ChatBot(face_queue=cmd_queue, sensor_data=sensor_data, farming_ops=farming_ops)
        bot.run_voice_loop()
    except ImportError as e:
        print(f"[Chatbot] Import error: {e}")
    except Exception as e:
        print(f"[Chatbot] Error: {e}")


# ── Auto emotion thread ───────────────────────────────────────────────────
def auto_emotion_thread():
    """Monitoron sensoret dhe ndryshon fytyren automatikisht."""
    _last = {'status': None}

    def _emit(state, text):
        if state != _last['status']:
            _last['status'] = state
            cmd_queue.put({'state': state, 'text': text, 'mic': False})

    while True:
        time.sleep(2)
        if not sensor_data:
            continue
        status = sensor_data.get('moisture_status', 'OPTIMAL')
        pct    = float(sensor_data.get('moisture_pct', 50))

        if   status == 'OPTIMAL':  _emit('happy',    f'Lagështia optimale {pct:.0f}%')
        elif status == 'DRY':      _emit('sad',       f'Toka e thatë {pct:.0f}%')
        elif status == 'WET':      _emit('confused',  f'Toka shumë e lagët {pct:.0f}%')
        elif status == 'CRITICAL': _emit('angry',     f'Gjendje kritike {pct:.0f}%')


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 50)
    print("  Terra Guide — Raspberry Pi")
    print("=" * 50)

    # Arduino
    arduino = None
    try:
        from arduino_comm import ArduinoComm
        arduino = ArduinoComm()
    except Exception as e:
        print(f"[Main] Arduino init: {e}")

    farming_ops = None
    if arduino:
        try:
            from farming_operations import FarmingOperations
            farming_ops = FarmingOperations(arduino)
            print("[Main] Farming operations OK")
        except Exception as e:
            print(f"[Main] Farming ops: {e}")

    t1 = threading.Thread(target=arduino_thread,      daemon=True, name='Arduino')
    t2 = threading.Thread(target=chatbot_thread,      args=(farming_ops,), daemon=True, name='ChatBot')
    t3 = threading.Thread(target=auto_emotion_thread, daemon=True, name='AutoEmotion')
    t1.start()
    t2.start()
    t3.start()

    if _DASH_OK:
        t4 = threading.Thread(target=_dash.run_dashboard, daemon=True, name='Dashboard')
        t4.start()
        print('[Dashboard] Duke u nisur ne port 5000...')

    if _FACE_OK:
        print("[Face] Duke nisur pygame ne Pi...")
        run_face(cmd_queue=cmd_queue, sensor_data=sensor_data)
    else:
        print("[Face] pygame/face_engine nuk u ngarkua — duke pritur...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Pi] Ndërprerë nga përdoruesi.")
