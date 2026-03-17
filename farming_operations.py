"""
farming_operations.py – Operacionet e kultivimit për ARES-X V3
─────────────────────────────────────────────────────────────
Menaxhon operacionet e fermës si:
- Plugunimi i vazhdueshëm
- Skanimi periodik i sensorit
- Shpërndarje fare
- Ujitja automatike
"""

import threading
import time
from servo_controller import ServoController
from arduino_comm import ArduinoComm


class FarmingOperations:
    """Koordinator i operacioneve të kultivimit."""
    
    def __init__(self, arduino: ArduinoComm):
        self.arduino = arduino
        self.servos = ServoController(arduino)
        self.is_plowing = False
        self.is_scanning = False
        self.plow_thread = None
        self.scan_thread = None
    
    # ────────────────────────────────────────────────────────────────
    # PLUGUNIM (Hapur dheu)
    # ────────────────────────────────────────────────────────────────
    
    def start_plowing(self, interval: float = 3.0):
        """
        Nis plugunimin e vazhdueshëm.
        Cikli: 180° → 150° (hap) → 180° (mbyll)
        Përsërit çdo 'interval' sekonda.
        """
        if self.is_plowing:
            print("[FARM] Plugunimi është tashmë aktiv")
            return
        
        self.is_plowing = True
        print(f"[FARM] Nis plugunim të vazhdueshëm (çdo {interval}s)")
        self.servos.start_continuous_plow(interval=interval)
    
    def stop_plowing(self):
        """Ndalon plugunimin."""
        if not self.is_plowing:
            print("[FARM] Plugunimi nuk është aktiv")
            return
        
        self.is_plowing = False
        self.servos.stop_plow()
        print("[FARM] Plugunimi i ndërprerë")
    
    # ────────────────────────────────────────────────────────────────
    # SKANIM SENZORI (Matje lagështie toke)
    # ────────────────────────────────────────────────────────────────
    
    def start_soil_monitoring(self, interval: float = 30.0):
        """
        Nis monitorimin periodik të tokës.
        Çdo 'interval' sekonda, uli sensorin, lexo, dhe ngre prap.
        """
        if self.is_scanning:
            print("[FARM] Monitorimi i sensorit është tashmë aktiv")
            return
        
        self.is_scanning = True
        print(f"[FARM] Nis monitorim të sensorit (çdo {interval}s)")
        self.servos.start_periodic_scan(interval=interval)
    
    def stop_soil_monitoring(self):
        """Ndalon monitorimin e sensorit."""
        if not self.is_scanning:
            print("[FARM] Monitorimi i sensorit nuk është aktiv")
            return
        
        self.is_scanning = False
        self.servos.stop_scan()
        print("[FARM] Monitorimi i sensorit i ndërprerë")
    
    def manual_soil_scan(self):
        """Bëj një skanim manual të sensorit menjëherë."""
        print("[FARM] Manual soil scan...")
        self.servos.sensor_scan()
    
    # ────────────────────────────────────────────────────────────────
    # SHPËRNDARJE FARE (Kazan)
    # ────────────────────────────────────────────────────────────────
    
    def dispense_seeds(self, amount: str = "normal"):
        """
        Shpërnda fare sipas sasisë.
        
        amount: "light" (1 pulse), "normal" (3 pulse), "heavy" (5 pulse)
        """
        pulses = {
            "light": 1,
            "normal": 3,
            "heavy": 5,
        }.get(amount, 3)
        
        print(f"[FARM] Shpërndarje fare ({amount}, {pulses} pulse)")
        self.servos.hopper_dispense(pulses)
    
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
