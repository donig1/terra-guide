"""
calibrate_servo.py — Kalibrimi Interaktiv i Servo Motorëve
══════════════════════════════════════════════════════════
Ekzekuto në Raspberry Pi:
  python3 calibrate_servo.py

Si funksionon:
  1. Zgjedh servosin (1=Plugun, 2=Sensor, 3=Kazan)
  2. Shkruaj duty cycle (provoji nga 2.5 deri 12.5)
  3. Shiko fizikisht ku ndalet servosi
  4. Gjej: ku është 0°, ku është 90°, ku është 180°
  5. Në fund shfaq konfigurimin e saktë për pi_servo_controller.py

SHEMBULL:
  Provoji: 5.0 → servo shkon në 0°   → kjo është DUTY_MIN
  Provoji: 7.5 → servo shkon në 90°  → kjo është DUTY_MID
  Provoji: 10.0 → servo shkon në 180° → kjo është DUTY_MAX
"""

import time
import sys

# ── Import GPIO ──────────────────────────────────────────────────
try:
    import RPi.GPIO as GPIO
    print("[GPIO] RPi.GPIO ngarkuar")
except ImportError:
    try:
        import lgpio as GPIO
        print("[GPIO] lgpio ngarkuar (Pi 5)")
    except ImportError:
        print("[GABIM] RPi.GPIO / lgpio nuk u gjet!")
        print("Instalo: sudo pip3 install rpi-lgpio --break-system-packages")
        sys.exit(1)

# ── Pins ─────────────────────────────────────────────────────────
PINS = {
    1: {"pin": 17, "name": "PLUGUN   (GPIO 17)"},
    2: {"pin": 27, "name": "SENSOR   (GPIO 27)"},
    3: {"pin": 22, "name": "KAZAN    (GPIO 22)"},
}

PWM_FREQ = 50   # Hz

# ── Setup GPIO ───────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

pwm_objects = {}
for s in PINS.values():
    GPIO.setup(s["pin"], GPIO.OUT)
    pwm = GPIO.PWM(s["pin"], PWM_FREQ)
    pwm.start(0)
    pwm_objects[s["pin"]] = pwm

print("\n" + "═"*55)
print("  ARES-X — Kalibrimi i Servo Motorëve")
print("═"*55)
print("  Duty cycle standard: 2.5 (min) → 7.5 (mes) → 12.5 (max)")
print("  Shumë servo: 5.0 (0°) → 7.5 (90°) → 10.0 (180°)")
print("═"*55)

# ── Rezultatet e kalibrimit ───────────────────────────────────────
calibration = {
    1: {"min": 5.0, "mid": 7.5, "max": 10.0},
    2: {"min": 5.0, "mid": 7.5, "max": 10.0},
    3: {"stop": 7.5, "fwd": 10.0, "bwd": 5.0},
}

def set_duty(pin, duty):
    """Vendos duty cycle për nje pin."""
    duty = round(max(2.0, min(13.0, duty)), 2)
    pwm_objects[pin].ChangeDutyCycle(duty)
    return duty

def stop_all():
    for s in PINS.values():
        pwm_objects[s["pin"]].ChangeDutyCycle(0)

def calibrate_servo(servo_id):
    info = PINS[servo_id]
    pin  = info["pin"]
    name = info["name"]

    print(f"\n{'─'*50}")
    print(f"  Servo {servo_id}: {name}")
    print(f"{'─'*50}")

    if servo_id in (1, 2):
        # Servo standard — gjej 0° dhe 180°
        print("  Provoji duty cycle nga 2.5 deri 12.5")
        print("  Komandat: numër (p.sh. 5.0)  |  0  |  90  |  180  |  q (dil)")
        print()

        found = {"min": None, "mid": None, "max": None}

        while True:
            try:
                inp = input(f"  [{name.strip()}] duty / kënd > ").strip().lower()

                if inp == 'q':
                    break

                # Shkurtore këndësh
                if inp == '0':
                    val = calibration[servo_id]["min"]
                    duty = set_duty(pin, val)
                    print(f"    → Duke shkuar në 0° (duty={duty}%)")
                    continue
                elif inp == '90':
                    val = calibration[servo_id]["mid"]
                    duty = set_duty(pin, val)
                    print(f"    → Duke shkuar në 90° (duty={duty}%)")
                    continue
                elif inp == '180':
                    val = calibration[servo_id]["max"]
                    duty = set_duty(pin, val)
                    print(f"    → Duke shkuar në 180° (duty={duty}%)")
                    continue

                duty = float(inp)
                duty = set_duty(pin, duty)
                print(f"    → Duty cycle: {duty}%  |  ku ndalet servosi?")
                print(f"       Shkruaj  'min'  nëse ky është 0°")
                print(f"       Shkruaj  'mid'  nëse ky është 90°")
                print(f"       Shkruaj  'max'  nëse ky është 180°")
                print(f"       Ose provojo një duty tjetër")

                mark = input("    Cakto si (min/mid/max) ose Enter për skip: ").strip().lower()
                if mark in ("min", "mid", "max"):
                    calibration[servo_id][mark] = duty
                    found[mark] = duty
                    print(f"    ✓ {mark} = {duty}% ruajtur")

            except ValueError:
                print("    Shkruaj një numër (p.sh. 5.2) ose q")
            except KeyboardInterrupt:
                break

        print(f"\n  Rezultatet për Servo {servo_id} ({name.strip()}):")
        print(f"    DUTY_MIN (0°)   = {calibration[servo_id]['min']}")
        print(f"    DUTY_MID (90°)  = {calibration[servo_id]['mid']}")
        print(f"    DUTY_MAX (180°) = {calibration[servo_id]['max']}")

    else:
        # Kazan — continuous rotation — gjej stop/fwd/bwd
        print("  Servo CONTINUOUS — gjej: STOP, PARA, PRAPA")
        print("  Komandat: numër (p.sh. 7.5)  |  q (dil)")
        print()

        while True:
            try:
                inp = input(f"  [KAZAN] duty > ").strip().lower()

                if inp == 'q':
                    break

                duty = float(inp)
                duty = set_duty(pin, duty)
                print(f"    → Duty: {duty}%  |  ç'bën servosi?")

                mark = input("    Cakto si (stop/fwd/bwd) ose Enter: ").strip().lower()
                if mark in ("stop", "fwd", "bwd"):
                    calibration[servo_id][mark] = duty
                    print(f"    ✓ {mark} = {duty}% ruajtur")

            except ValueError:
                print("    Shkruaj një numër ose q")
            except KeyboardInterrupt:
                break

        stop_all()
        print(f"\n  Rezultatet për Kazan:")
        print(f"    HOPPER_STOP    = {calibration[3]['stop']}")
        print(f"    HOPPER_FORWARD = {calibration[3]['fwd']}")
        print(f"    HOPPER_BACK    = {calibration[3]['bwd']}")

    stop_all()


# ── Menu kryesore ─────────────────────────────────────────────────
def main():
    try:
        while True:
            print("\n" + "═"*55)
            print("  MENU KALIBRIMI")
            print("  1 → Kalibroi Servo 1: PLUGUN   (GPIO 17)")
            print("  2 → Kalibroi Servo 2: SENSOR   (GPIO 27)")
            print("  3 → Kalibroi Servo 3: KAZAN    (GPIO 22)")
            print("  4 → Shfaq konfigurimin final")
            print("  q → Dil")
            print("═"*55)

            choice = input("  Zgjedhja > ").strip().lower()

            if choice == 'q':
                break
            elif choice in ('1', '2', '3'):
                calibrate_servo(int(choice))
            elif choice == '4':
                print_config()
            else:
                print("  Shkruaj 1, 2, 3 ose q")

    except KeyboardInterrupt:
        pass

    finally:
        stop_all()
        GPIO.cleanup()
        print("\n[GPIO] Pastrim i kryer.")
        print_config()


def print_config():
    """Shfaq konfigurimin final — kopjo në pi_servo_controller.py"""
    print("\n" + "═"*55)
    print("  KONFIGURIMI FINAL — kopjo në pi_servo_controller.py")
    print("═"*55)
    c1 = calibration[1]
    c2 = calibration[2]
    c3 = calibration[3]
    print()
    print(f"# Servo 1 — PLUGUN (GPIO 17)")
    print(f"PLOW_MIN  = {c1['min']}   # 0°")
    print(f"PLOW_MID  = {c1['mid']}   # 90°")
    print(f"PLOW_MAX  = {c1['max']}   # 180°")
    print()
    print(f"# Servo 2 — SENSOR (GPIO 27)")
    print(f"SENS_MIN  = {c2['min']}   # 0°")
    print(f"SENS_MID  = {c2['mid']}   # 90°")
    print(f"SENS_MAX  = {c2['max']}   # 180°")
    print()
    print(f"# Servo 3 — KAZAN (GPIO 22)")
    print(f"HOPPER_STOP    = {c3['stop']}")
    print(f"HOPPER_FORWARD = {c3['fwd']}")
    print(f"HOPPER_BACK    = {c3['bwd']}")
    print()
    print("# Funksioni konvertimit (vendos në pi_servo_controller.py):")
    print("def _angle_to_duty_plow(angle):   # PLUGUN")
    print(f"    return {c1['min']} + (angle / 180.0) * ({c1['max']} - {c1['min']})")
    print()
    print("def _angle_to_duty_sensor(angle): # SENSOR")
    print(f"    return {c2['min']} + (angle / 180.0) * ({c2['max']} - {c2['min']})")
    print("═"*55)


if __name__ == '__main__':
    main()
