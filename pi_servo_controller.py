"""
pi_servo_controller.py — Kontrolli i Servo Motorëve nga Raspberry Pi GPIO
═══════════════════════════════════════════════════════════════════════════
Servo motorët lidhen DIREKT me Raspberry Pi GPIO pins (PWM).
Arduino nuk kontrollon servot — vetëm lexon sensorët.

LIDHJET (Raspberry Pi → Servo):
  GPIO 17 (Pin 11) → Servo 1: Plugun (PLOW)
  GPIO 27 (Pin 13) → Servo 2: Sensori Lagështie (SENSOR)
  GPIO 22 (Pin 15) → Servo 3: Kazan Fare (HOPPER) [continuous rotation]

SERVO PWM (50 Hz):
  Standard servo: 5% duty = 0°, 7.5% = 90°, 10% = 180°
  Cont. rotation: 7.5% = ndal, 10% = para, 5% = prapa

Instalim: pip install RPi.GPIO
          (ose: pip install pigpio  për saktësi më të mirë)
"""

import threading
import time

# ── Provo të importosh RPi.GPIO, fallback në simulim ──────────────
try:
    import RPi.GPIO as GPIO
    _GPIO_OK = True
    print("[PiServo] RPi.GPIO ngarkuar — modalitet REAL")
except ImportError:
    _GPIO_OK = False
    print("[PiServo] RPi.GPIO nuk u gjet — modalitet SIMULIM aktiv")


# ── Pin të Raspberry Pi (BCM numbering) ──────────────────────────
PIN_PLOW   = 17    # GPIO 17 — Servo 1: Plugun
PIN_SENSOR = 27    # GPIO 27 — Servo 2: Sensor Lagështie
PIN_HOPPER = 22    # GPIO 22 — Servo 3: Kazan Fare (continuous)

PWM_FREQ   = 50    # Hz — standard servo frequency

# ── Konvertimet e këndit → duty cycle ────────────────────────────
def _angle_to_duty(angle: float) -> float:
    """Konverto kënd 0-180° në duty cycle % (5.0–10.0)."""
    return 5.0 + (angle / 180.0) * 5.0

# Continuous rotation (kazan) duty cycles
HOPPER_STOP    = 7.5   # ndal
HOPPER_FORWARD = 10.0  # rrotacion para (hapje fare)
HOPPER_BACK    = 5.0   # rrotacion prapa


class PiServoController:
    """
    Kontrolluesi i servo motorëve nga Raspberry Pi GPIO PWM.
    Përdor simulim automatik nëse RPi.GPIO nuk është i disponueshëm.
    """

    def __init__(self):
        self._lock    = threading.Lock()
        self._running = False
        self._pwm     = {}   # {pin: GPIO.PWM object}
        self._angles  = {PIN_PLOW: 180, PIN_SENSOR: 90, PIN_HOPPER: 0}

        if _GPIO_OK:
            self._setup_gpio()
        else:
            print("[PiServo] Simulim: servo duhen lidhur me GPIO kur Pi të jetë gati")

    # ── Inicializim GPIO ─────────────────────────────────────────
    def _setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in (PIN_PLOW, PIN_SENSOR, PIN_HOPPER):
            GPIO.setup(pin, GPIO.OUT)
            pwm = GPIO.PWM(pin, PWM_FREQ)
            pwm.start(0)
            self._pwm[pin] = pwm
        # Pozicionet fillestare
        self._move(PIN_PLOW,   180)
        time.sleep(0.3)
        self._move(PIN_SENSOR, 90)
        time.sleep(0.3)
        self._duty(PIN_HOPPER, HOPPER_STOP)
        print("[PiServo] GPIO inicializuar — të gjitha servot në pozicionet fillestare")

    def _move(self, pin: int, angle: float):
        """Lëviz servo standard në kënd (0–180°)."""
        duty = _angle_to_duty(max(0, min(180, angle)))
        self._duty(pin, duty)
        self._angles[pin] = angle

    def _duty(self, pin: int, duty: float):
        """Vendos duty cycle direkt."""
        if _GPIO_OK and pin in self._pwm:
            self._pwm[pin].ChangeDutyCycle(duty)
        else:
            name = {PIN_PLOW: 'PLUGUN', PIN_SENSOR: 'SENSOR', PIN_HOPPER: 'KAZAN'}.get(pin, pin)
            print(f"  [SIM] {name} → duty {duty:.1f}%")

    def cleanup(self):
        """Lësho GPIO burimet."""
        if _GPIO_OK:
            for pwm in self._pwm.values():
                pwm.stop()
            GPIO.cleanup()

    # ════════════════════════════════════════════════════════════
    # SERVO 1: PLUGUN  (GPIO 17)
    # ════════════════════════════════════════════════════════════

    def plow_cycle(self, repetitions: int = 1):
        """Hap dheu: 180° → 150° → 180° (×repetitions)."""
        for i in range(repetitions):
            print(f"[PLOW] Cikël {i+1}/{repetitions}")
            with self._lock:
                self._move(PIN_PLOW, 180)
            time.sleep(0.4)
            with self._lock:
                self._move(PIN_PLOW, 150)
            time.sleep(1.0)
            with self._lock:
                self._move(PIN_PLOW, 180)
            time.sleep(0.4)

    def start_continuous_plow(self, interval: float = 2.0):
        """Plugunim i vazhdueshëm në thread."""
        self._running = True
        def _run():
            while self._running:
                self.plow_cycle(1)
                time.sleep(interval)
        threading.Thread(target=_run, daemon=True, name='PiPlow').start()
        print(f"[PLOW] Plugunimi i vazhdueshëm i nisur (çdo {interval}s)")

    def stop_plow(self):
        self._running = False
        with self._lock:
            self._move(PIN_PLOW, 180)
        print("[PLOW] Plugunimi ndalur")

    # ════════════════════════════════════════════════════════════
    # SERVO 2: SENSOR LAGËSHTIE  (GPIO 27)
    # ════════════════════════════════════════════════════════════

    def sensor_scan(self):
        """Uli sensor 90°→40°, prit matje, ngre 40°→90°."""
        print("[SENSOR] Duke skanuar tokën...")
        with self._lock:
            self._move(PIN_SENSOR, 90)
        time.sleep(0.4)
        with self._lock:
            self._move(PIN_SENSOR, 40)   # poshtë — kontakt me tokë
        time.sleep(2.5)                  # prit matje
        with self._lock:
            self._move(PIN_SENSOR, 90)   # ngre
        print("[SENSOR] Skanim i kryer")

    def start_periodic_scan(self, interval: float = 30.0):
        """Skanim periodik i sensorit."""
        def _run():
            while True:
                self.sensor_scan()
                time.sleep(interval)
        threading.Thread(target=_run, daemon=True, name='PiScan').start()
        print(f"[SENSOR] Skanim periodik nisur (çdo {interval}s)")

    # ════════════════════════════════════════════════════════════
    # SERVO 3: KAZAN FARE — Continuous Rotation  (GPIO 22)
    # ════════════════════════════════════════════════════════════

    def hopper_dispense(self, pulses: int = 3):
        """Shpërndaj fare: çdo puls = 1 rrotacion i plotë (≈1s)."""
        print(f"[HOPPER] Shpërndarje fare ({pulses} puls)...")
        for i in range(pulses):
            print(f"  Puls {i+1}/{pulses}")
            with self._lock:
                self._duty(PIN_HOPPER, HOPPER_FORWARD)  # nis rrotacion
            time.sleep(1.0)                              # 1 rrotacion i plotë
            with self._lock:
                self._duty(PIN_HOPPER, HOPPER_STOP)     # ndal
            time.sleep(0.5)
        print("[HOPPER] Shpërndarje e përfunduar")

    def hopper_open(self, duration: float = 3.0):
        """Hap kazanin vazhdimisht për kohën e dhënë."""
        with self._lock:
            self._duty(PIN_HOPPER, HOPPER_FORWARD)
        time.sleep(duration)
        with self._lock:
            self._duty(PIN_HOPPER, HOPPER_STOP)

    # ════════════════════════════════════════════════════════════
    # RESET TË GJITHA
    # ════════════════════════════════════════════════════════════

    def reset_all(self):
        """Kthe të gjitha servot në pozicionet fillestare."""
        print("[PiServo] Duke rivendosur të gjitha servot...")
        with self._lock:
            self._move(PIN_PLOW,   180)
        time.sleep(0.3)
        with self._lock:
            self._move(PIN_SENSOR, 90)
        time.sleep(0.3)
        with self._lock:
            self._duty(PIN_HOPPER, HOPPER_STOP)
        print("[PiServo] Të gjitha servot janë rivendosur")
