"""
Terra Guide — laptop_face.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ky file ekzekutohet NE LAPTOP.

- Lidhet me Raspberry Pi nepermjet rrjetit (HTTP)
- Merr te dhenat live nga Pi cdo 2 sekonda
- Shfaq Fytyren e Fermerit (pygame) ne ekranin e laptopit
- Fytyra ndryshon emocion ne baze te sensoreve te Pi-t

Konfiguro PI_IP ne config.py me IP-ne e vertete te Pi!
  (ne Pi: hostname -I   ose   ip addr)
"""

import threading
import queue
import time
import math

from face_engine import run_face

try:
    import requests
    _REQ_OK = True
except ImportError:
    _REQ_OK = False
    print("[Laptop] KUJDES: 'requests' nuk eshte instaluar.")
    print("         Ekzekuto:  pip install requests")

try:
    from config import PI_IP, DASHBOARD_PORT
except ImportError:
    PI_IP           = "192.168.1.100"
    DASHBOARD_PORT  = 5000

# ── Shared state ──────────────────────────────────────────────────────────
cmd_queue   = queue.Queue()
sensor_data = {}


# ── Thread 1: Pollon Pi-n per te dhenat live ─────────────────────────────
def sensor_poll_thread():
    """Merr te dhenat e sensoreve nga Pi cdo 2 sekonda."""
    url = f"http://{PI_IP}:{DASHBOARD_PORT}/api/live"
    _connected = False

    while True:
        if not _REQ_OK:
            time.sleep(5)
            continue

        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                sensor_data.update(data)
                if not _connected:
                    print(f"[SensorPoll] U lidh me Pi ne {url}")
                    _connected = True
        except requests.exceptions.ConnectionError:
            if _connected:
                print(f"[SensorPoll] Lidhja me Pi u prish ({PI_IP}) — duke u riprovuar...")
            _connected = False
        except Exception as e:
            print(f"[SensorPoll] Gabim: {e}")
            _connected = False

        time.sleep(2)


# ── Thread 2: Auto-emocion bazuar ne sensoret e Pi-t ─────────────────────
def auto_emotion_thread():
    """Monitoron sensor_data live (cdo 2s) dhe ndryshon fytyren automatikisht."""
    _last = {'state': None}

    def _emit(state, text):
        if state != _last['state']:
            _last['state'] = state
            cmd_queue.put({'state': state, 'text': text, 'mic': False})

    while True:
        time.sleep(2)

        if not sensor_data:
            _emit('idle', '')
            continue

        status    = sensor_data.get('moisture_status', 'OPTIMAL')
        pct       = float(sensor_data.get('moisture_pct', 50))
        action    = sensor_data.get('robot_action', 'MOVING')
        obstacle  = float(sensor_data.get('distance', 999))
        can_plant = sensor_data.get('can_plant', False)

        # Prioritet: pengesa > veprim aktiv > statusi i tokës
        if obstacle < 20:
            _emit('surprised', f'Pengesë {obstacle:.0f}cm! Duke u ndalur...')
        elif action == 'SCANNING':
            _emit('thinking', f'Duke skanuar tokën... lagështi {pct:.0f}%')
        elif action == 'PLANTING':
            _emit('happy', f'Toka optimale — duke mbjellur faren! {pct:.0f}%')
        elif action == 'PLOWING':
            _emit('talking', 'Duke pluguar tokën...')
        elif not can_plant and status == 'DRY':
            _emit('sad', f'Toka e thatë ({pct:.0f}%) — duke kaluar.')
        elif not can_plant and status == 'WET':
            _emit('confused', f'Toka shumë e lagët ({pct:.0f}%) — duke kaluar.')
        elif not can_plant and status == 'CRITICAL':
            _emit('scared', f'Gjendje kritike ({pct:.0f}%) — duke kapërcyer!')
        elif can_plant:
            _emit('happy', f'Kushte optimale {pct:.0f}% — e gatshme për mbjellje!')
        else:
            _emit('idle', '')


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 52)
    print("  Terra Guide — Fytyra (Laptop)")
    print(f"  Duke u lidhur me Pi: http://{PI_IP}:{DASHBOARD_PORT}")
    print("  Nese Pi nuk pergjigjet, fytyra punon offline.")
    print("=" * 52)

    t1 = threading.Thread(target=sensor_poll_thread,  daemon=True, name='SensorPoll')
    t2 = threading.Thread(target=auto_emotion_thread, daemon=True, name='AutoEmotion')
    t1.start()
    t2.start()

    # Fytyra del ne ekranin e laptopit (main thread)
    run_face(cmd_queue=cmd_queue, sensor_data=sensor_data)
