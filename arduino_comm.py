# ============================================
# arduino_comm.py – Komunikimi Serial me Arduino
# Format JSON (Arduino → Pi):
#   {"dist":34,"ir_l":0,"ir_r":0,"dir":"FORWARD","servo":90,"mode":"AUTO"}
#   {"status":"READY","msg":"ARES-X Boot OK"}
# Format komandash (Pi → Arduino):
#   CMD:STOP\n   CMD:FORWARD\n   CMD:AUTO\n   CMD:MANUAL\n
# ============================================

import serial
import json
import time
import threading
import random
from config import SERIAL_PORT, SERIAL_BAUD


class ArduinoComm:

    def __init__(self):
        self.ser       = None
        self.connected = False
        self._lock     = threading.Lock()
        self.last_data = {}
        self._connect()

    def _connect(self):
        ports = [SERIAL_PORT, '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
        for port in ports:
            try:
                self.ser       = serial.Serial(port, SERIAL_BAUD, timeout=1)
                time.sleep(2)
                self.connected = True
                print(f"[ARDUINO] Lidhur ne {port}")
                return
            except Exception:
                continue
        print("[ARDUINO] Nuk u gjet – menyra simulim aktive")

    def send(self, cmd):
        """Dergo komande tek Arduino: CMD:STOP, CMD:FORWARD, CMD:AUTO, SERVO:90, etj."""
        if not self.connected:
            print(f"[ARDUINO] simulim -> {cmd}")
            return
        try:
            with self._lock:
                self.ser.write((cmd + '\n').encode())
        except Exception as e:
            print(f"[ARDUINO] Gabim dergim: {e}")

    def read_line(self):
        """Lexo nje rresht nga porta seriale."""
        if not self.connected:
            return None
        try:
            with self._lock:
                if self.ser.in_waiting > 0:
                    return self.ser.readline().decode('utf-8', errors='ignore').strip()
        except Exception:
            pass
        return None

    def parse(self, line):
        """
        Parsoje JSON-in nga Arduino.
        Kthen ("DATA", dict) ose ("STATUS", str) ose (None, None).
        """
        if not line:
            return None, None

        if line.startswith('{'):
            try:
                obj = json.loads(line)
                if 'status' in obj:
                    msg = obj.get('msg', obj['status'])
                    print(f"[ARDUINO] {msg}")
                    return "STATUS", msg
                if 'dist' in obj:
                    self.last_data = obj
                    return "DATA", obj
            except Exception as e:
                print(f"[PARSE] JSON gabim: {e} -- {line}")
        return None, None

    def simulate(self):
        """Kthe te dhena te simuluara kur Arduino nuk eshte i lidhur."""
        dirs = ["FORWARD", "LEFT", "RIGHT", "STOP"]
        return {
            "dist":  random.randint(20, 200),
            "ir_l":  random.randint(0, 1),
            "ir_r":  random.randint(0, 1),
            "dir":   random.choice(dirs),
            "servo": 90,
            "mode":  "AUTO",
        }

    def read_data(self) -> dict:
        """
        Lexo nje pakete te dhenash nga Arduino.
        Kthen dict te unifikuar ose None nese nuk ka te dhena.
        Thirrje kryesore nga arduino_thread ne pi_main.py.
        """
        line = self.read_line()
        if line:
            kind, data = self.parse(line)
            if kind == 'DATA' and data:
                dist = float(data.get('dist', 999))
                if dist < 15:
                    obstacle = 'NEAR'
                elif dist < 30:
                    obstacle = 'CLOSE'
                else:
                    obstacle = 'CLEAR'
                return {
                    'distance':        dist,
                    'ir_left':         int(data.get('ir_l', 0)),
                    'ir_right':        int(data.get('ir_r', 0)),
                    'direction':       data.get('dir', 'STOP'),
                    'servo_angle':     int(data.get('servo', 90)),
                    'mode':            data.get('mode', 'AUTO'),
                    'obstacle':        obstacle,
                    # Vlera shtese per dashboard / fytyra
                    'moisture_pct':    50.0,
                    'moisture_status': 'OPTIMAL',
                    'moisture_raw':    512,
                    'soil_temp':       20.0,
                    'air_temp':        22.0,
                    'humidity':        60.0,
                    'can_plant':       True,
                    'crop':            'domate',
                }
        return None
