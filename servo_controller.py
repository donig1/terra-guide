"""
servo_controller.py – Kontrolli i tre servo motorëve për ARES-X V3
──────────────────────────────────────────────────────────────────
1. Servo Plugun (PLOW_SERVO) - Pin 9
   - Pozicioni fillestar: 180°
   - Hap dheu duke lëvizur 30° në krahun orar (180° → 150°)
   - Kthehet prap në 180°
   - Duhet të lëvizet vazhdimisht për të hapur gropat

2. Servo Soil Sensor (SENSOR_SERVO) - Pin 10
   - Lëviz në krahun orar (rrethore)
   - Lëviz 50° për të ulur sensorin (p.sh. 90° → 40°)
   - Pas një fare kohe ngrihet prap (40° → 90°)
   - Përdoret për skenimin periodik

3. Servo Kazan Fare (HOPPER_SERVO) - Pin 11
   - Rrotacion i plotë 360°
   - Hapje kazan për shpërndarje fare
"""

import threading
import time
from arduino_comm import ArduinoComm

class ServoController:
    """Kontrolluesi i servo motorëve."""
    
    # Pin të servo motorëve në Arduino
    PLOW_SERVO   = 1    # Plugun
    SENSOR_SERVO = 2    # Soil moisture sensor
    HOPPER_SERVO = 3    # Kazan fare
    
    def __init__(self, arduino: ArduinoComm):
        self.arduino = arduino
        self._lock = threading.Lock()
        self.running = False
        
    # ────────────────────────────────────────────────────────────────
    # 1. SERVO PLUGUN (Hapur dheu)
    # ────────────────────────────────────────────────────────────────
    
    def plow_cycle(self, repetitions: int = 1):
        """
        Cikli i plugunimit: hap dheu në mënyrë rituale.
        Pozicioni fillestar: 180°
        Lëviz 30° në krahun orar: 180° → 150°
        Kthehet: 150° → 180°
        Përsërit sipas numrit të kërkesës.
        """
        for i in range(repetitions):
            print(f"[PLOW] Cikli {i+1}/{repetitions}")
            self._send_servo(self.PLOW_SERVO, 180)  # Pozicioni fillestar
            time.sleep(0.5)
            self._send_servo(self.PLOW_SERVO, 150)  # Hap dheu (30°)
            time.sleep(1.0)
            self._send_servo(self.PLOW_SERVO, 180)  # Kthehet prap
            time.sleep(0.5)
    
    def start_continuous_plow(self, interval: float = 2.0):
        """
        Nis plugunimin vazhdimisht me interval kohe.
        """
        def plow_thread():
            while self.running:
                self.plow_cycle(1)
                time.sleep(interval)
        
        self.running = True
        t = threading.Thread(target=plow_thread, daemon=True)
        t.start()
        print("[PLOW] Plugunimi i vazhdueshëm i nisur")
    
    def stop_plow(self):
        """Ndalon plugunimin e vazhdueshëm."""
        self.running = False
        print("[PLOW] Plugunimi i vazhdueshëm i ndërprerë")
    
    # ────────────────────────────────────────────────────────────────
    # 2. SERVO SOIL MOISTURE SENSOR (Skenime periodike)
    # ────────────────────────────────────────────────────────────────
    
    def sensor_scan(self):
        """
        Uli dhe ngre sensori tokës në mënyrë periodike.
        Pozicioni fillestar: 90° (lart)
        Uli sensori: 90° → 40° (50° poshtë)
        Pret: 2-3 sekonda
        Ngre sensori: 40° → 90°
        """
        print("[SENSOR] Skanon tokën...")
        self._send_servo(self.SENSOR_SERVO, 90)  # Lart
        time.sleep(0.5)
        self._send_servo(self.SENSOR_SERVO, 40)  # Poshtë (50°)
        time.sleep(2.5)  # Matja zgjat 2-3 sekonda
        self._send_servo(self.SENSOR_SERVO, 90)  # Ngre prap
        print("[SENSOR] Skanim i përfunduar")
    
    def start_periodic_scan(self, interval: float = 30.0):
        """
        Nis kërkimin periodik të sensorit me interval.
        """
        def scan_thread():
            while self.running:
                self.sensor_scan()
                time.sleep(interval)
        
        self.running = True
        t = threading.Thread(target=scan_thread, daemon=True)
        t.start()
        print(f"[SENSOR] Kërkimi periodik i nisur (çdo {interval}s)")
    
    def stop_scan(self):
        """Ndalon kërkimin periodik."""
        self.running = False
        print("[SENSOR] Kërkimi periodik i ndërprerë")
    
    # ────────────────────────────────────────────────────────────────
    # 3. SERVO KAZAN FARE (Hapje dhe mbyllje)
    # ────────────────────────────────────────────────────────────────
    
    def hopper_open(self, duration: float = 5.0):
        """
        Hap kazanin e farave me rrotacion të plotë 360°.
        Pozicioni fillestar: 0°
        Rrotacion i plotë: 0° → 360° → 0°
        Qëndron i hapur për kohën e specifikuar.
        """
        print("[HOPPER] Hap kazanin...")
        self._send_servo(self.HOPPER_SERVO, 0)    # Pozicioni fillestar
        time.sleep(0.5)
        self._send_servo(self.HOPPER_SERVO, 360)  # Rrotacion i plotë
        time.sleep(duration)  # Qëndron i hapur
        self._send_servo(self.HOPPER_SERVO, 0)    # Kthehet në pozicionin fillestar
        print("[HOPPER] Kazani është i mbyllur")
    
    def hopper_dispense(self, pulses: int = 3):
        """
        Shpërndan fare me pulse të shumta.
        Çdo puls = një rrotacion të plotë.
        """
        print(f"[HOPPER] Shpërndan fare ({pulses} pulse)...")
        for i in range(pulses):
            print(f"  Pulse {i+1}/{pulses}")
            self._send_servo(self.HOPPER_SERVO, 0)
            time.sleep(0.3)
            self._send_servo(self.HOPPER_SERVO, 360)
            time.sleep(1.0)
            self._send_servo(self.HOPPER_SERVO, 0)
            time.sleep(0.5)
        print("[HOPPER] Shpërndarje e përfunduar")
    
    # ────────────────────────────────────────────────────────────────
    # Metoda të përgjithshme
    # ────────────────────────────────────────────────────────────────
    
    def _send_servo(self, servo_id: int, angle: int):
        """Dërgo komandën e servo motors tek Arduino."""
        cmd = f"SERVO:{servo_id},{angle}"
        with self._lock:
            self.arduino.send(cmd)
        print(f"  {cmd}")
    
    def reset_all(self):
        """Ridefinizo të gjithë servot në pozicionet fillestare."""
        print("[SERVO] Risistem të gjithë servot...")
        self._send_servo(self.PLOW_SERVO, 180)    # Plugun në 180°
        time.sleep(0.5)
        self._send_servo(self.SENSOR_SERVO, 90)   # Sensori në 90° (lart)
        time.sleep(0.5)
        self._send_servo(self.HOPPER_SERVO, 0)    # Kazani në 0°
        time.sleep(0.5)
        print("[SERVO] Të gjithë servot janë në pozicionet fillestare")


# ════════════════════════════════════════════════════════════════════
# DEMO / TEST
# ════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from arduino_comm import ArduinoComm
    
    arduino = ArduinoComm()
    servos = ServoController(arduino)
    
    # Reset
    servos.reset_all()
    time.sleep(2)
    
    # Test 1: Plugun (3 cikle)
    print("\n=== TEST 1: PLUGUN ===")
    servos.plow_cycle(3)
    time.sleep(2)
    
    # Test 2: Sensori tokës
    print("\n=== TEST 2: SENSORI TOKËS ===")
    servos.sensor_scan()
    time.sleep(2)
    
    # Test 3: Kazan fare (3 pulse)
    print("\n=== TEST 3: KAZAN FARE ===")
    servos.hopper_dispense(3)
    time.sleep(2)
    
    # Test 4: Plugunimi i vazhdueshëm (për 10 sekonda)
    print("\n=== TEST 4: PLUGUNIM I VAZHDUESHËM (10s) ===")
    servos.start_continuous_plow(interval=2.0)
    time.sleep(10)
    servos.stop_plow()
    
    # Test 5: Kërkimi i sensorit i vazhdueshëm (për 15 sekonda)
    print("\n=== TEST 5: KËRKIM I SENSORIT I VAZHDUESHËM (15s) ===")
    servos.start_periodic_scan(interval=5.0)
    time.sleep(15)
    servos.stop_scan()
    
    # Reset përfundimisht
    print("\n=== RESET PËRFUNDIMISHT ===")
    servos.reset_all()
