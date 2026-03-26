/*
 * ARES-X V4 — Arduino Mega 2560 — Kod i Unifikuar
 * =====================================================================
 * Kontrollon: motorët DC (L298N), sensorët IR, HC-SR04, servo
 * Dërgon tek Pi (JSON): {"dist":34,"ir_l":0,"ir_r":0,"dir":"FORWARD","servo":90,"mode":"AUTO"}
 * Merr komanda nga Pi:  CMD:STOP  CMD:AUTO  CMD:MANUAL  SERVO:90
 *
 * LIDHJET:
 *   L298N  ENA=5  IN1=7  IN2=8  ENB=6  IN3=9  IN4=10
 *   IR     IR_LEFT=3(INPUT_PULLUP)  IR_RIGHT=2(INPUT_PULLUP)
 *   HC-SR04 TRIG=12  ECHO=11
 *   SERVO  PIN=13
 *   SERIAL 9600 baud  /dev/ttyACM0
 * =====================================================================
 */

#include <Servo.h>

// ── Motor L298N ─────────────────────────────────────────────────
const int ENA = 5,  IN1 = 7,  IN2 = 8;
const int ENB = 6,  IN3 = 9,  IN4 = 10;
const int MOTOR_SPEED = 150;   // 0-255 (150 ≈ 59%)

// ── Sensorët IR (INPUT_PULLUP: 0=vija, 1=jashtë vijës) ──────────
const int IR_LEFT  = 3;
const int IR_RIGHT = 2;

// ── HC-SR04 ──────────────────────────────────────────────────────
const int TRIG = 12;
const int ECHO = 11;
const float OBSTACLE_CM = 30.0;

// ── Servo ────────────────────────────────────────────────────────
const int SERVO_PIN = 13;
Servo scanServo;
int servoAngle = 90;

// ── Modaliteti ───────────────────────────────────────────────────
bool autoMode = true;
String currentDir = "STOP";

// ── Timing ───────────────────────────────────────────────────────
unsigned long lastSend       = 0;
const unsigned long SEND_MS  = 200;   // dërgo JSON çdo 200ms

// ═════════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(9600);
  delay(1000);

  // Motorë
  pinMode(ENA, OUTPUT); pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(ENB, OUTPUT); pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);

  // IR
  pinMode(IR_LEFT,  INPUT_PULLUP);
  pinMode(IR_RIGHT, INPUT_PULLUP);

  // HC-SR04
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  digitalWrite(TRIG, LOW);

  // Servo
  scanServo.attach(SERVO_PIN);
  scanServo.write(90);

  stopMotors();

  Serial.println("{\"status\":\"READY\",\"msg\":\"ARES-X Boot OK\"}");
}

// ═════════════════════════════════════════════════════════════════
void loop() {
  // Lexo komanda nga Pi
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    handleCommand(cmd);
  }

  // Logjika AUTO
  if (autoMode) {
    float dist = readDistance();
    if (dist > 0 && dist < OBSTACLE_CM) {
      stopMotors();
      checkAndTurn(dist);
    } else {
      followLine();
    }
  }

  // Dërgo JSON çdo SEND_MS
  if (millis() - lastSend >= SEND_MS) {
    lastSend = millis();
    sendJSON();
  }
}

// ── Menaxho komandat nga Pi ──────────────────────────────────────
void handleCommand(String cmd) {
  if      (cmd == "CMD:STOP")    { autoMode = false; stopMotors(); currentDir = "STOP"; }
  else if (cmd == "CMD:FORWARD") { autoMode = false; goForward();  currentDir = "FORWARD"; }
  else if (cmd == "CMD:BACK")    { autoMode = false; goBack();     currentDir = "BACK"; }
  else if (cmd == "CMD:LEFT")    { autoMode = false; goLeft();     currentDir = "LEFT"; }
  else if (cmd == "CMD:RIGHT")   { autoMode = false; goRight();    currentDir = "RIGHT"; }
  else if (cmd == "CMD:AUTO")    { autoMode = true;  currentDir = "AUTO"; }
  else if (cmd == "CMD:MANUAL")  { autoMode = false; stopMotors(); currentDir = "STOP"; }
  else if (cmd.startsWith("SERVO:")) {
    int angle = cmd.substring(6).toInt();
    angle = constrain(angle, 0, 180);
    scanServo.write(angle);
    servoAngle = angle;
  }
}

// ── Ndiq vijën (IR) ──────────────────────────────────────────────
void followLine() {
  int left  = digitalRead(IR_LEFT);
  int right = digitalRead(IR_RIGHT);

  if      (left == 0 && right == 0) { goForward(); currentDir = "FORWARD"; }
  else if (left == 1 && right == 0) { goRight();   currentDir = "RIGHT"; }
  else if (left == 0 && right == 1) { goLeft();    currentDir = "LEFT"; }
  else                               { stopMotors(); currentDir = "STOP"; }
}

// ── Kontroll pengesa + kthim ─────────────────────────────────────
void checkAndTurn(float obsDist) {
  stopMotors();
  delay(300);

  // Skanim i majtë
  scanServo.write(150); servoAngle = 150; delay(500);
  float distLeft = readDistance();

  // Skanim i djathtë
  scanServo.write(30);  servoAngle = 30;  delay(500);
  float distRight = readDistance();

  // Kthehu çentër
  scanServo.write(90);  servoAngle = 90;  delay(300);

  if (distLeft > distRight) {
    goLeft();
    currentDir = "LEFT";
  } else {
    goRight();
    currentDir = "RIGHT";
  }
  delay(400);
  stopMotors();
  currentDir = "STOP";
}

// ── Lëvizjet e motorëve ──────────────────────────────────────────
void goForward() {
  analogWrite(ENA, MOTOR_SPEED); analogWrite(ENB, MOTOR_SPEED);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void goBack() {
  analogWrite(ENA, MOTOR_SPEED); analogWrite(ENB, MOTOR_SPEED);
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
}

void goLeft() {
  analogWrite(ENA, MOTOR_SPEED); analogWrite(ENB, MOTOR_SPEED);
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void goRight() {
  analogWrite(ENA, MOTOR_SPEED); analogWrite(ENB, MOTOR_SPEED);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
}

void stopMotors() {
  analogWrite(ENA, 0); analogWrite(ENB, 0);
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
}

// ── Lexo distancën HC-SR04 (cm) ──────────────────────────────────
float readDistance() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  long duration = pulseIn(ECHO, HIGH, 20000);  // max 20ms ≈ 340cm
  if (duration == 0) return 999.0;
  return duration * 0.034 / 2.0;
}

// ── Dërgo JSON tek Pi ─────────────────────────────────────────────
void sendJSON() {
  float dist = readDistance();
  int irL    = digitalRead(IR_LEFT);
  int irR    = digitalRead(IR_RIGHT);

  Serial.print("{\"dist\":");
  Serial.print(dist, 1);
  Serial.print(",\"ir_l\":");
  Serial.print(irL);
  Serial.print(",\"ir_r\":");
  Serial.print(irR);
  Serial.print(",\"dir\":\"");
  Serial.print(currentDir);
  Serial.print("\",\"servo\":");
  Serial.print(servoAngle);
  Serial.print(",\"mode\":\"");
  Serial.print(autoMode ? "AUTO" : "MANUAL");
  Serial.println("\"}");
}
