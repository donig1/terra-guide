"""
Terra Guide — pi_main.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NJE FILE — NIS GJITHE ROBOTIN:

  1. Arduino → CMD:AUTO   (robot nis ndjekjen e vijës)
  2. arduino_thread        — lexon JSON nga Arduino çdo 200ms
  3. emotion_thread        — reagon ndaj lëvizjes / pengesave
  4. farming_thread        — servo Pi GPIO (plow, scan, dispense)
  5. dashboard_thread      — Flask port 5000 (opsional)
  6. Fytyra fullscreen     — pygame në ekranin e Pi-t (main thread)

Ekzekutim: python3 pi_main.py
"""

import threading
import queue
import time
import math
import random

# ── Queue e komandave për fytyra ─────────────────────────────────────────
cmd_queue   = queue.Queue()
sensor_data = {}          # dict i ndarë mes të gjitha thread-eve




# ═════════════════════════════════════════════════════════════════════════
# THREAD 1 — Arduino: lexo JSON, dërgo CMD:AUTO, update sensor_data
# ═════════════════════════════════════════════════════════════════════════
def arduino_thread(arduino):
    """
    Lexon JSON nga Arduino çdo 200ms dhe update-on sensor_data.
    Arduino tashmë menaxhon vetë linjën (CMD:AUTO i dërguar nga main).
    """
    sim_t = 0.0

    while True:
        sim_t += 0.3

        if arduino and arduino.connected:
            data = arduino.read_data()
            if data is None:
                time.sleep(0.1)
                continue
        else:
            # Simulim — lëvizje normale me pengesa rastësore
            dirs = ['FORWARD', 'FORWARD', 'FORWARD', 'LEFT', 'RIGHT', 'STOP']
            dist = round(abs(60 + math.sin(sim_t * 0.4) * 50), 1)
            data = {
                'distance':        dist,
                'ir_left':         0,
                'ir_right':        0,
                'direction':       random.choice(dirs),
                'servo_angle':     90,
                'mode':            'AUTO',
                'obstacle':        'NEAR' if dist < 15 else ('CLOSE' if dist < 30 else 'CLEAR'),
                'moisture_pct':    round(55 + math.sin(sim_t * 0.2) * 20, 1),
                'moisture_status': 'OPTIMAL',
                'moisture_raw':    512,
                'soil_temp':       round(21 + math.sin(sim_t * 0.1) * 4, 1),
                'air_temp':        round(24 + math.sin(sim_t * 0.15) * 3, 1),
                'humidity':        round(62 + math.sin(sim_t * 0.12) * 12, 0),
                'can_plant':       True,
                'crop':            'domate',
            }
            time.sleep(0.3)

        sensor_data.update(data)


# ═════════════════════════════════════════════════════════════════════════
# THREAD 2 — Emocione: reagon ndaj lëvizjes dhe pengesave
# ═════════════════════════════════════════════════════════════════════════
def emotion_thread():
    """
    Shikon direction + obstacle + moisture nga sensor_data
    dhe dërgon emocionin e duhur tek fytyra.
    """
    _last_state = [None]

    def emit(state, text):
        if state != _last_state[0]:
            _last_state[0] = state
            cmd_queue.put({'state': state, 'text': text, 'mic': False})

    time.sleep(3)   # prit të niset Arduino

    while True:
        time.sleep(0.5)
        if not sensor_data:
            continue

        direction = sensor_data.get('direction', 'STOP')
        obstacle  = sensor_data.get('obstacle',  'CLEAR')
        moisture  = sensor_data.get('moisture_status', 'OPTIMAL')
        dist      = sensor_data.get('distance', 999)
        pct       = sensor_data.get('moisture_pct', 50)

        # Obstacle nearby — high priority
        if obstacle == 'NEAR' or dist < 15:
            emit('angry', f'Obstacle! {dist:.0f}cm')
        elif obstacle == 'CLOSE' or dist < 30:
            emit('confused', f'Object close {dist:.0f}cm')

        # Normal movement
        elif direction == 'FORWARD':
            emit('happy', 'Following the line...')
        elif direction in ('LEFT', 'RIGHT'):
            emit('thinking', f'Turning {direction.lower()}')
        elif direction == 'STOP':
            emit('idle', 'Stopped')

        # Soil status (low priority)
        elif moisture == 'DRY':
            emit('sad', f'Soil dry {pct:.0f}%')
        elif moisture == 'WET':
            emit('confused', f'Soil too wet {pct:.0f}%')
        elif moisture == 'CRITICAL':
            emit('angry', f'Moisture critical {pct:.0f}%')
        else:
            emit('happy', f'All good — moisture {pct:.0f}%')


# ═════════════════════════════════════════════════════════════════════════
# THREAD 3 — Farming / Servo Pi GPIO
# ═════════════════════════════════════════════════════════════════════════
def farming_thread(farming_ops):
    if farming_ops is None:
        return
    time.sleep(4)
    try:
        farming_ops.start_soil_monitoring(interval=30.0)
        print("[Farm] Monitorimi i tokës aktiv")
    except Exception as e:
        print(f"[Farm] {e}")


# ═════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 60)
    print("  ARES-X  |  Terra Guide — Raspberry Pi")
    print("=" * 60)

    # ── 1. Arduino ────────────────────────────────────────────
    arduino = None
    try:
        from arduino_comm import ArduinoComm
        arduino = ArduinoComm()
        if arduino.connected:
            print("[Main] Arduino: U LIDH")
            time.sleep(0.5)
            # Nis ndjekjen automatike të vijës menjëherë
            arduino.send("CMD:AUTO")
            print("[Main] Arduino: CMD:AUTO dërguar — robot nis vijën")
        else:
            print("[Main] Arduino: jo i lidhur — simulim aktiv")
    except Exception as e:
        print(f"[Main] Arduino gabim: {e}")

    # ── 2. Farming Operations + Servo Pi GPIO ─────────────────
    pi_servos   = None
    farming_ops = None
    try:
        from farming_operations import FarmingOperations
        farming_ops = FarmingOperations(arduino=arduino, sensor_data=sensor_data)
        pi_servos   = getattr(getattr(farming_ops, 'servos', None), '_pi', None)
        print("[Main] Farming Ops + Servo GPIO: AKTIV")
    except Exception as e:
        print(f"[Main] Farming ops: {e}")

    # ── 3. Nis threads ────────────────────────────────────────
    threads = [
        threading.Thread(target=arduino_thread,  args=(arduino,),       daemon=True, name='Arduino'),
        threading.Thread(target=emotion_thread,                          daemon=True, name='Emotion'),
        threading.Thread(target=farming_thread,  args=(farming_ops,),   daemon=True, name='Farming'),
    ]
    for t in threads:
        t.start()

    print("[Main] All threads active\n")

    # ── 4. Fytyra Fullscreen në Pi ────────────────────────────
    # import lazy këtu — pas DISPLAY=:0 setup
    try:
        from face_engine import run_face
        cmd_queue.put({'state': 'happy', 'text': 'ARES-X — Following the line!', 'mic': False})
        run_face(cmd_queue=cmd_queue, sensor_data=sensor_data)   # bllokues — loop kryesor

    except Exception as e:
        print(f"[Face] GABIM: {e}")
        print("[Face] Backend aktiv pa fytyra — Ctrl+C për të ndalur")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    # ── 5. Pastrim pas mbylljes ───────────────────────────────
    print("\n[Main] Duke ndalur robotin...")
    if arduino and arduino.connected:
        arduino.send("CMD:STOP")
        print("[Main] CMD:STOP dërguar tek Arduino")
    if pi_servos:
        try:
            pi_servos.cleanup()
        except Exception:
            pass
    print("[Main] Ndalur.")
