from pi_servo_controller import PiServoController
import time

servo = PiServoController()
time.sleep(1)

print("\n=== TEST 1: PLUGUN (GPIO 17) ===")
print("Duke lëvizur 180° → 90° → 0° → 180°")
servo.plow(180);  time.sleep(1)
servo.plow(90);   time.sleep(1)
servo.plow(0);    time.sleep(1)
servo.plow(180);  time.sleep(1)
print("✓ PLUGUN OK")

print("\n=== TEST 2: SENSOR (GPIO 27) ===")
print("Duke lëvizur 90° → 40° → 90°")
servo.scan(90);   time.sleep(1)
servo.scan(40);   time.sleep(1)
servo.scan(90);   time.sleep(1)
print("✓ SENSOR OK")

print("\n=== TEST 3: KAZAN (GPIO 22) ===")
print("Duke rrotulluar 2 sekonda...")
servo.dispense(True);  time.sleep(2)
servo.dispense(False); time.sleep(1)
print("✓ KAZAN OK")

print("\n=== RESET ===")
servo.reset_all()
servo.cleanup()
print("✓ Test i përfunduar!")