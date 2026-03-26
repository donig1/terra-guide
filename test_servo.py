from pi_servo_controller import PiServoController
import time

servo = PiServoController()
time.sleep(1)

print("\n=== TEST 1: PLUGUN (GPIO 17) ===")
print("Duke lëvizur në 0° — prit 5 sek...")
servo.plow(0);    time.sleep(5)
print("Duke lëvizur në 90° — prit 5 sek...")
servo.plow(90);   time.sleep(5)
print("Duke lëvizur në 180° — prit 5 sek...")
servo.plow(180);  time.sleep(5)
print("Duke u kthyer në pozicionin fillestar (180°)...")
servo.plow(180);  time.sleep(2)
print("✓ PLUGUN OK")

print("\n=== TEST 2: SENSOR (GPIO 27) ===")
print("Duke lëvizur në 0° — prit 5 sek...")
servo.scan(0);    time.sleep(5)
print("Duke lëvizur në 90° — prit 5 sek...")
servo.scan(90);   time.sleep(5)
print("Duke lëvizur në 180° — prit 5 sek...")
servo.scan(180);  time.sleep(5)
print("Duke u kthyer në pozicionin fillestar (90°)...")
servo.scan(90);   time.sleep(2)
print("✓ SENSOR OK")

print("\n=== TEST 3: KAZAN (GPIO 22) ===")
print("Duke rrotulluar 5 sekonda...")
servo.dispense(True);  time.sleep(5)
print("Duke ndalur — prit 2 sek...")
servo.dispense(False); time.sleep(2)
print("✓ KAZAN OK")

print("\n=== RESET ===")
servo.reset_all()
servo.cleanup()
print("✓ Test i përfunduar!")