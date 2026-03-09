# ============================================
# arduino_comm.py – Komunikimi Serial me Arduino
# Format: DATA:moisture,soilTemp,airTemp,humidity,distance
# ============================================

import serial
import time
import threading
import random
from config import SERIAL_PORT, SERIAL_BAUD

class ArduinoComm:

    def __init__(self):
        self.ser        = None
        self.connected  = False
        self._lock      = threading.Lock()
        self.last_data  = {}
        self._connect()

    def _connect(self):
        ports = [SERIAL_PORT, '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']
        for port in ports:
            try:
                self.ser       = serial.Serial(port, SERIAL_BAUD, timeout=1)
                time.sleep(2)
                self.connected = True
                print(f"[ARDUINO] ✅ Lidhur në {port}")
                return
            except:
                continue
        print("[ARDUINO] ⚠️  Nuk u gjet – mënyra simulim aktive")

    def send(self, cmd):
        """Dërgo komandë tek Arduino: FOLLOW, STOP, IRRIGATE, SERVO_SCAN, etj."""
        if not self.connected:
            print(f"[ARDUINO] simulim → {cmd}")
            return
        try:
            with self._lock:
                self.ser.write((cmd + '\n').encode())
        except Exception as e:
            print(f"[ARDUINO] Gabim dërgim: {e}")

    def read_line(self):
        if not self.connected:
            return None
        try:
            with self._lock:
                if self.ser.in_waiting > 0:
                    return self.ser.readline().decode('utf-8', errors='ignore').strip()
        except:
            pass
        return None

    def parse(self, line):
        """
        Arduino dërgon:
        DATA:moisture,soilTemp,airTemp,humidity,distance
        STATUS:STOP_POINT
        OBS:15.2
        """
        if not line:
            return None, None

        if line.startswith("DATA:"):
            try:
                p = line.replace("DATA:", "").split(",")
                data = {
                    "moisture":  int(p[0]),      # 0-1023 raw ADC
                    "soil_temp": float(p[1]),    # °C DS18B20
                    "air_temp":  float(p[2]),    # °C DHT22
                    "humidity":  float(p[3]),    # % DHT22
                    "distance":  float(p[4]),    # cm HC-SR04
                }
                self.last_data = data
                return "DATA", data
            except Exception as e:
                print(f"[PARSE] {e}")
                return None, None

        if line.startswith("STATUS:"):
            return "STATUS", line.replace("STATUS:", "")

        if line.startswith("OBS:"):
            return "OBS", float(line.replace("OBS:", ""))

        return None, None

    def simulate(self):
        """Të dhëna të simuluara realisht"""
        return {
            "moisture":  random.randint(200, 900),
            "soil_temp": round(random.uniform(10, 30), 1),
            "air_temp":  round(random.uniform(15, 35), 1),
            "humidity":  round(random.uniform(35, 80), 1),
            "distance":  round(random.uniform(25, 200), 1),
        }