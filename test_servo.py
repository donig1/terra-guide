"""
test_servo.py — Testo servo motoret
Ekzekuto: python3 test_servo.py
"""
from pi_servo_controller import PiServoController
import time

print("=" * 40)
print("  TESTI I SERVO MOTOREVE")
print("=" * 40)

s = PiServoController()
time.sleep(1)

print("\n[1/3] Servo 1 — PLUGU")
print("  Duke shkuar ne 0 grade...")
s.plow(0)
time.sleep(1)
print("  Duke shkuar ne 180 grade...")
s.plow(180)
time.sleep(1)

print("\n[2/3] Servo 2 — SENSORI")
print("  Duke shkuar ne 0 grade...")
s.scan(0)
time.sleep(1)
print("  Duke shkuar ne 90 grade...")
s.scan(90)
time.sleep(1)

print("\n[3/3] Servo 3 — KAZANI")
print("  Duke hapur kazanin...")
s.dispense(True)
time.sleep(2)
print("  Duke mbyllur kazanin...")
s.dispense(False)
time.sleep(1)

print("\n" + "=" * 40)
print("  GJITHE SERVOT U TESTUAN!")
print("=" * 40)

s.cleanup()
