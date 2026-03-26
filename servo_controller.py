"""
servo_controller.py – Fasadë mbi PiServoController
──────────────────────────────────────────────────────────────────
Servot kontrollohen DIREKT nga Raspberry Pi GPIO (pi_servo_controller.py)
Arduino vetëm lexon sensorët — nuk merret me servot.

Këtë file mund ta importosh si në të kaluarën (backward-compatible).
"""

import threading
import time
from pi_servo_controller import PiServoController

class ServoController:
    """Kontrolluesi i servo motorëve."""
    
    def __init__(self, arduino=None):
        # arduino parametri ruhet për backward-compatibility por nuk përdoret
        self._pi = PiServoController()
        self._lock = threading.Lock()
        self.running = False
        
    # ────────────────────────────────────────────────────────────────
    # 1. SERVO PLUGUN (Hapur dheu)
    # ────────────────────────────────────────────────────────────────
    
    # ── Delegim tek PiServoController ──────────────────────────────

    def plow_cycle(self, repetitions: int = 1):
        self._pi.plow_cycle(repetitions)

    def start_continuous_plow(self, interval: float = 2.0):
        self.running = True
        self._pi.start_continuous_plow(interval)

    def stop_plow(self):
        self.running = False
        self._pi.stop_plow()

    def sensor_scan(self):
        self._pi.sensor_scan()

    def start_periodic_scan(self, interval: float = 30.0):
        self._pi.start_periodic_scan(interval)

    def stop_scan(self):
        self.running = False

    def hopper_open(self, duration: float = 3.0):
        self._pi.hopper_open(duration)

    def hopper_dispense(self, pulses: int = 3):
        self._pi.hopper_dispense(pulses)

    def reset_all(self):
        self._pi.reset_all()


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
