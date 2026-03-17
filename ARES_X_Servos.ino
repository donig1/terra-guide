/*
 * ARES-X V3 – Kontrolluesi i Servo Motorëve
 * Arduino Mega 2560
 * 
 * Komanda në serial:
 *   SERVO:servo_id,angle
 * Shembuj:
 *   SERVO:1,180  (Plugun në 180°)
 *   SERVO:2,40   (Sensori në 40°)
 *   SERVO:3,360  (Kazani rrotacion i plotë)
 */

#include <Servo.h>

// Pin të servo motorëve (Arduino Mega PWM pins)
const int SERVO_PLOW_PIN   = 9;     // Plugun (servo 1)
const int SERVO_SENSOR_PIN = 10;    // Soil moisture sensor (servo 2)
const int SERVO_HOPPER_PIN = 11;    // Kazan fare (servo 3)

// Objektet servo
Servo servoPlow;
Servo servoSensor;
Servo servoHopper;

// Pozicionet aktuale
int anglePlow = 180;     // Fillestar
int angleSensor = 90;    // Fillestar (lart)
int angleHopper = 0;     // Fillestar

// ═══════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(9600);
  delay(1000);
  
  // Inicijalizimi i servo motorëve
  servoPlow.attach(SERVO_PLOW_PIN);
  servoSensor.attach(SERVO_SENSOR_PIN);
  servoHopper.attach(SERVO_HOPPER_PIN);
  
  // Pozicionet fillestare
  servoPlow.write(anglePlow);
  servoSensor.write(angleSensor);
  servoHopper.write(angleHopper);
  
  delay(500);
  
  Serial.println("READY");
  Serial.println("[SERVO] Të gjithë servot të inicijalizuar");
  Serial.println("  Servo 1 (Plugun) → 180°");
  Serial.println("  Servo 2 (Sensori) → 90°");
  Serial.println("  Servo 3 (Kazani) → 0°");
}

// ═══════════════════════════════════════════════════════════════
void loop() {
  // Mbaj gjallë serial communication
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.startsWith("SERVO:")) {
      handleServoCommand(command);
    }
  }
}

// ═══════════════════════════════════════════════════════════════
void handleServoCommand(String cmd) {
  /*
   * Format: SERVO:servo_id,angle
   * Shembull: SERVO:1,150
   */
  
  // Hiq "SERVO:" prefiksin
  cmd = cmd.substring(6);
  
  // Ndaj servo_id dhe angle
  int commaIdx = cmd.indexOf(',');
  if (commaIdx == -1) {
    Serial.println("ERROR: Format SERVO:id,angle");
    return;
  }
  
  int servoId = cmd.substring(0, commaIdx).toInt();
  int angle = cmd.substring(commaIdx + 1).toInt();
  
  // Validim
  if (servoId < 1 || servoId > 3) {
    Serial.println("ERROR: servo_id duhet të jetë 1-3");
    return;
  }
  if (angle < 0 || angle > 360) {
    Serial.println("ERROR: këndi duhet të jetë 0-360");
    return;
  }
  
  // Lëviz servo
  switch (servoId) {
    case 1:  // Plugun
      servoPlow.write(angle);
      anglePlow = angle;
      Serial.print("[SERVO1] Plugun → ");
      Serial.print(angle);
      Serial.println("°");
      break;
      
    case 2:  // Sensori
      servoSensor.write(angle);
      angleSensor = angle;
      Serial.print("[SERVO2] Sensori → ");
      Serial.print(angle);
      Serial.println("°");
      break;
      
    case 3:  // Kazani
      // Për rrotacion të plotë 360°, duhet të bëj atë shtrirje
      if (angle == 360) {
        // Rrotacion i plotë: 0° → 180° → 0°
        servoHopper.write(180);
        delay(1000);  // Kohë për rrotim
        servoHopper.write(0);
        angleHopper = 0;
        Serial.println("[SERVO3] Kazani → RROTIM I PLOTË (360°)");
      } else {
        servoHopper.write(angle);
        angleHopper = angle;
        Serial.print("[SERVO3] Kazani → ");
        Serial.print(angle);
        Serial.println("°");
      }
      break;
  }
}

// ═══════════════════════════════════════════════════════════════
// STATUS REPORT (opsional)
// Nëse nevojitet rapportuesi i pozicionesh
void reportStatus() {
  Serial.print("STATUS:");
  Serial.print(anglePlow);
  Serial.print(",");
  Serial.print(angleSensor);
  Serial.print(",");
  Serial.println(angleHopper);
}
