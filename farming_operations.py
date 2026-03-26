"""
farming_operations.py – Operacionet e kultivimit për ARES-X V3
─────────────────────────────────────────────────────────────
Koordinon:
- Plugunimi i vazhdueshëm      → Servo 1 (Pi GPIO 17)
- Skanimi periodik i sensorit  → Servo 2 (Pi GPIO 27)
- Shpërndarje fare             → Servo 3 (Pi GPIO 22)

Servo motorët kontrollohen nga Raspberry Pi GPIO.
sensor_data['robot_action'] vendoset live → fytyra reagon.
"""

import threading
import time
from servo_controller import ServoController


class FarmingOperations:
    """Koordinator i operacioneve të kultivimit."""
    
    def __init__(self, arduino=None, sensor_data: dict = None):
        self.arduino = arduino
        self.servos = ServoController(arduino)
        self.sensor_data = sensor_data or {}   # referenca e shared dict
        self.is_plowing = False
        self.is_scanning = False
        self.plow_thread = None
        self.scan_thread = None

    def _set_action(self, action: str):
        """Vendos veprimin aktual të robotit → fytyra reagon live."""
        self.sensor_data['robot_action'] = action
    
    # ────────────────────────────────────────────────────────────────
    # PLUGUNIM (Hapur dheu)
    # ────────────────────────────────────────────────────────────────
    
    def start_plowing(self, interval: float = 3.0):
        if self.is_plowing:
            print("[FARM] Plugunimi është tashmë aktiv")
            return
        self.is_plowing = True
        self._set_action('PLOWING')
        print(f"[FARM] Nis plugunim të vazhdueshëm (çdo {interval}s)")
        self.servos.start_continuous_plow(interval=interval)
    
    def stop_plowing(self):
        if not self.is_plowing:
            return
        self.is_plowing = False
        self._set_action('MOVING')
        self.servos.stop_plow()
        print("[FARM] Plugunimi i ndërprerë")
    
    # ────────────────────────────────────────────────────────────────
    # SKANIM SENZORI (Matje lagështie toke)
    # ────────────────────────────────────────────────────────────────
    
    def start_soil_monitoring(self, interval: float = 30.0):
        if self.is_scanning:
            print("[FARM] Monitorimi i sensorit është tashmë aktiv")
            return
        self.is_scanning = True
        print(f"[FARM] Nis monitorim të sensorit (çdo {interval}s)")
        self.servos.start_periodic_scan(interval=interval)
    
    def stop_soil_monitoring(self):
        if not self.is_scanning:
            return
        self.is_scanning = False
        self.servos.stop_scan()
        print("[FARM] Monitorimi i sensorit i ndërprerë")
    
    def manual_soil_scan(self):
        """Bëj një skanim manual të sensorit menjëherë."""
        self._set_action('SCANNING')
        print("[FARM] Manual soil scan...")
        self.servos.sensor_scan()
        self._set_action('MOVING')
    
    # ────────────────────────────────────────────────────────────────
    # SHPËRNDARJE FARE (Kazan)
    # ────────────────────────────────────────────────────────────────
    
    def dispense_seeds(self, amount: str = "normal"):
        """Shpërnda fare sipas sasisë — vendos robot_action=PLANTING."""
        pulses = {"light": 1, "normal": 3, "heavy": 5}.get(amount, 3)
        self._set_action('PLANTING')
        print(f"[FARM] Shpërndarje fare ({amount}, {pulses} pulse)")
        self.servos.hopper_dispense(pulses)
        self._set_action('MOVING')

    # ────────────────────────────────────────────────────────────────
    # SKENARË KOMPLEKSE
    # ────────────────────────────────────────────────────────────────
    
    def automatic_farming_cycle(self):
        """
        Cikli automatik i kultivimit:
        1. Plugunim (3 cikle)
        2. Skanim senzori
        3. Shpërndarje fare
        4. Monitorim periodik
        """
        print("[FARM] Nis cikli automatik i kultivimit...")
        
        # Fase 1: Plugunim
        print("\n[FARM] Faza 1: Plugunim")
        self.servos.plow_cycle(repetitions=3)
        time.sleep(2)
        
        # Fase 2: Skanim senzori
        print("\n[FARM] Faza 2: Skanim senzori")
        self.servos.sensor_scan()
        time.sleep(2)
        
        # Fase 3: Shpërndarje fare
        print("\n[FARM] Faza 3: Shpërndarje fare")
        self.servos.hopper_dispense(3)
        time.sleep(2)
        
        # Fase 4: Nis monitorim periodik
        print("\n[FARM] Faza 4: Monitorim periodik (çdo 30s)")
        self.start_soil_monitoring(interval=30.0)
        
        print("[FARM] Cikli i kultivimit i nisur me sukses!")
    
    # ────────────────────────────────────────────────────────────────
    # EMERGENCY STOP
    # ────────────────────────────────────────────────────────────────
    
    def emergency_stop(self):
        """Ndali të gjithë operacionet menjëherë."""
        print("[FARM] 🚨 EMERGENCY STOP - Ndali të gjithë operacionet")
        self.stop_plowing()
        self.stop_soil_monitoring()
        self.servos.reset_all()
    
    # ────────────────────────────────────────────────────────────────
    # RAPORTUESI I STATUSIT
    # ────────────────────────────────────────────────────────────────
    
    def get_status(self) -> dict:
        """Kthye statusin e operacioneve."""
        return {
            "is_plowing": self.is_plowing,
            "is_scanning": self.is_scanning,
            "arduino_connected": self.arduino.connected,
        }
    
    def print_status(self):
        """Printo statusin e operacioneve."""
        status = self.get_status()
        print(f"""
[FARM STATUS]
  Plugunim: {'AKTIV' if status['is_plowing'] else 'INAKTIV'}
  Skanim senzori: {'AKTIV' if status['is_scanning'] else 'INAKTIV'}
  Arduino: {'LIDHUR' if status['arduino_connected'] else 'NËBREZIM'}
""")


# ════════════════════════════════════════════════════════════════════
# DEMO / TEST
# ════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from arduino_comm import ArduinoComm
    
    arduino = ArduinoComm()
    farm = FarmingOperations(arduino)
    
    print("═" * 60)
    print("ARES-X V3 – OPERACIONET E KULTIVIMIT")
    print("═" * 60)
    
    # Demo 1: Cikli automatik
    print("\n>>> DEMO 1: CIKLI AUTOMATIK")
    farm.automatic_farming_cycle()
    time.sleep(5)
    
    # Raporti i statusit
    farm.print_status()
    
    # Demo 2: Plugunim manual me kontroll
    print("\n>>> DEMO 2: PLUGUNIM MANUAL (10 sekonda)")
    farm.start_plowing(interval=2.0)
    time.sleep(10)
    farm.stop_plowing()
    time.sleep(2)
    
    # Demo 3: Emergency stop
    print("\n>>> DEMO 3: EMERGENCY STOP")
    farm.start_plowing()
    time.sleep(3)
    farm.emergency_stop()
    time.sleep(2)
    
    # Final status
    print("\n>>> FINAL STATUS")
    farm.print_status()
    
    print("\n═" * 60)
    print("DEMO I PËRFUNDUAR")
    print("═" * 60)
