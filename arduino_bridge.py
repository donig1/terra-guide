"""
ARES-X — arduino_bridge.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lidh Arduino Mega ↔ Raspberry Pi përmes USB Serial.

• Lexon JSON nga Arduino çdo 300ms
• Përditëson face_engine me gjendjen e robotit
• Dërgon komanda te Arduino (STOP, FORWARD, AUTO, etj.)
• Ndryshon emocionin e fytyrës bazuar në sensorë

Të dhënat nga Arduino:
  {"dist":34,"ir_l":0,"ir_r":0,"dir":"FORWARD","servo":90,"mode":"AUTO"}

Komandat te Arduino:
  CMD:STOP / CMD:FORWARD / CMD:LEFT / CMD:RIGHT / CMD:AUTO / CMD:MANUAL
  SERVO:90
"""

import serial
import json
import time
import threading
import queue

# ─── Konfigurim ────────────────────────────────────────────
SERIAL_PORT  = '/dev/ttyACM0'   # ndrysho në /dev/ttyACM1 nëse nuk punon
BAUD_RATE    = 9600
RECONNECT_S  = 3                # sekonda para rilidhjeje

# Distanca në cm — kur bëhet emocion i fytyrës
DIST_SCARED  = 10   # shumë afër → angry/scared
DIST_WARN    = 25   # afër       → worried
DIST_OK      = 50   # larg       → normal


class ArduinoBridge:
    """
    Lidhet me Arduino dhe lexon/dërgon të dhëna.

    Përdorim:
        bridge = ArduinoBridge(face=face_obj, sensor_data=face.sensors)
        bridge.start()

        # Dërgo komandë
        bridge.send("CMD:STOP")
        bridge.send("CMD:AUTO")
        bridge.send("SERVO:45")
    """

    def __init__(self, face=None, sensor_data=None):
        self.face        = face          # FarmerFace objekt (opsional)
        self.sensor_data = sensor_data   # dict i sensorëve (shared reference)
        self.ser         = None
        self.running     = False
        self.connected   = False

        # Të dhënat më të fundit nga Arduino
        self.robot_data = {
            'dist':   999,
            'ir_l':   0,
            'ir_r':   0,
            'dir':    'STOP',
            'servo':  90,
            'mode':   'AUTO',
        }

        # Queue për komandat që dërgohen te Arduino
        self._cmd_queue = queue.Queue()

        # Lock për serial (thread-safe)
        self._lock = threading.Lock()

    # ── Lidhu me Arduino ────────────────────────────────────
    def _connect(self):
        while self.running:
            try:
                self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                time.sleep(2)   # Arduino riniset kur hapet serial
                self.connected = True
                print(f'[Bridge] ✅ Lidhur me Arduino në {SERIAL_PORT}')
                self._set_face('happy', 'Arduino i lidhur!', 1.5)
                return True
            except serial.SerialException as e:
                self.connected = False
                print(f'[Bridge] ❌ Lidhja dështoi: {e}')
                print(f'[Bridge] Duke provuar përsëri në {RECONNECT_S}s...')
                self._set_face('sad', 'Arduino nuk u gjet...', 2.0)
                time.sleep(RECONNECT_S)
        return False

    # ── Loop leximi ─────────────────────────────────────────
    def _read_loop(self):
        while self.running:
            if not self.connected:
                self._connect()
                continue

            try:
                with self._lock:
                    line = self.ser.readline().decode('utf-8').strip()

                if not line:
                    continue

                # Merr JSON
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    # Mesazh status (jo JSON) — printo vetëm
                    if line:
                        print(f'[Arduino] {line}')
                    continue

                # Ruaj të dhënat
                self.robot_data.update(data)

                # Përditëso sensors dict (i shared me face_engine)
                if self.sensor_data is not None:
                    self.sensor_data['obstacle_cm'] = data.get('dist', 999)
                    self.sensor_data['robot_dir']   = data.get('dir',  'STOP')
                    self.sensor_data['robot_mode']  = data.get('mode', 'AUTO')

                # Përditëso fytyrën
                self._update_face(data)

                # Print debug
                dist = data.get('dist', 999)
                d    = data.get('dir', '?')
                m    = data.get('mode', '?')
                print(f'[Arduino] dist={dist}cm dir={d} mode={m}', end='\r')

            except serial.SerialException:
                print('\n[Bridge] Serial u shkëput — duke u rilidh...')
                self.connected = False
                if self.ser:
                    try: self.ser.close()
                    except: pass
                time.sleep(RECONNECT_S)

            except Exception as e:
                print(f'\n[Bridge] Read error: {e}')
                time.sleep(0.1)

    # ── Loop shkrimit (komandat) ─────────────────────────────
    def _write_loop(self):
        while self.running:
            try:
                cmd = self._cmd_queue.get(timeout=0.5)
                if self.connected and self.ser:
                    with self._lock:
                        self.ser.write(f'{cmd}\n'.encode('utf-8'))
                    print(f'\n[Bridge] → Arduino: {cmd}')
            except queue.Empty:
                continue
            except Exception as e:
                print(f'[Bridge] Write error: {e}')

    # ── Përditëso fytyrën bazuar në të dhëna ────────────────
    def _update_face(self, data):
        if self.face is None:
            return

        dist = data.get('dist', 999)
        d    = data.get('dir',  'STOP')

        # Emocion bazuar në distancë
        if dist < DIST_SCARED:
            self.face.set_face('angry', f'Pengesë! {dist}cm')
        elif dist < DIST_WARN:
            self.face.set_face('surprised', f'Kujdes! {dist}cm')
        elif d == 'FORWARD' and dist > DIST_OK:
            # Lëviz normal — mos ndërhyj shumë në emocione
            pass
        elif d == 'STOP':
            pass   # chatbot/voice vendos emocionin

    # ── Helper: vendos fytyrën me vonesë ────────────────────
    def _set_face(self, state, text='', duration=0):
        if self.face is None:
            return
        self.face.set_face(state, text)
        if duration > 0:
            def reset():
                time.sleep(duration)
                self.face.set_face('idle')
            threading.Thread(target=reset, daemon=True).start()

    # ── API publike ──────────────────────────────────────────
    def send(self, cmd: str):
        """Dërgo komandë te Arduino. Thread-safe."""
        self._cmd_queue.put(cmd)

    def stop_robot(self):
        self.send('CMD:STOP')

    def forward(self):
        self.send('CMD:FORWARD')

    def left(self):
        self.send('CMD:LEFT')

    def right(self):
        self.send('CMD:RIGHT')

    def backward(self):
        self.send('CMD:BACKWARD')

    def auto_mode(self):
        """Arduino lëviz vetë (line following + obstacle avoidance)."""
        self.send('CMD:AUTO')

    def manual_mode(self):
        """Raspberry Pi kontrollon lëvizjen."""
        self.send('CMD:MANUAL')

    def set_servo(self, angle: int):
        """Kthehu servo-n (0-180)."""
        angle = max(0, min(180, angle))
        self.send(f'SERVO:{angle}')

    def get_distance(self) -> int:
        return self.robot_data.get('dist', 999)

    def get_direction(self) -> str:
        return self.robot_data.get('dir', 'STOP')

    def is_obstacle(self) -> bool:
        return self.get_distance() < DIST_WARN

    # ── Start / Stop ─────────────────────────────────────────
    def start(self):
        self.running = True
        threading.Thread(target=self._read_loop,  daemon=True, name='ArduinoRead').start()
        threading.Thread(target=self._write_loop, daemon=True, name='ArduinoWrite').start()
        print('[Bridge] Arduino Bridge startoi!')

    def stop(self):
        self.running = False
        if self.ser:
            try: self.ser.close()
            except: pass
        print('[Bridge] Arduino Bridge u ndal.')


# ─── Test i pavarur (pa face_engine) ───────────────────────
if __name__ == '__main__':
    print('=== ARES-X Arduino Bridge TEST ===')
    print(f'Duke u lidhur me {SERIAL_PORT} @ {BAUD_RATE}...')

    bridge = ArduinoBridge()
    bridge.start()

    print('Komandat: w=para  s=ndalo  a=majtas  d=djathtas  m=auto  q=dil')
    print('Servo: 1=majtas(150)  2=qendër(90)  3=djathtas(30)')

    try:
        while True:
            cmd = input().strip().lower()
            if cmd == 'w': bridge.forward();    print('→ FORWARD')
            elif cmd == 's': bridge.stop_robot();  print('→ STOP')
            elif cmd == 'a': bridge.left();      print('→ LEFT')
            elif cmd == 'd': bridge.right();     print('→ RIGHT')
            elif cmd == 'b': bridge.backward();  print('→ BACKWARD')
            elif cmd == 'm': bridge.auto_mode(); print('→ AUTO MODE')
            elif cmd == '1': bridge.set_servo(150); print('→ SERVO 150°')
            elif cmd == '2': bridge.set_servo(90);  print('→ SERVO 90°')
            elif cmd == '3': bridge.set_servo(30);  print('→ SERVO 30°')
            elif cmd == 'q': break
            elif cmd == 'status':
                print(f'Distanca: {bridge.get_distance()}cm')
                print(f'Drejtimi: {bridge.get_direction()}')
                print(f'Pengesë: {bridge.is_obstacle()}')
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()