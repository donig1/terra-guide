/*
 * ============================================================
 *  TERRA GUIDE — Arduino UNO
 *  Line Following + Obstacle Avoidance
 *  Komunikim Serial JSON me Raspberry Pi 4
 * ============================================================
 *  LIDHJET:
 *   L298N → ENA=5  IN1=7  IN2=8  ENB=6  IN3=9  IN4=10
 *   IR    → LEFT=3 (INPUT_PULLUP)  RIGHT=2 (INPUT_PULLUP)
 *   SR04  → TRIG=12  ECHO=11
 *   USB   → /dev/ttyACM0 @ 9600 baud
 *
 *  IR LOGJIKA: 1=mbi vijë zezë  0=jashtë vijës
 *
 *  DËRGON tek Pi çdo 300ms:
 *  {"dist":34,"ir_l":1,"ir_r":1,"dir":"FORWARD","mode":"AUTO"}
 *
 *  MERR nga Pi:
 *  CMD:STOP | CMD:FORWARD | CMD:BACKWARD
 *  CMD:LEFT | CMD:RIGHT | CMD:AUTO | CMD:MANUAL
 * ============================================================
 */

// ===== MOTOR L298N =====
const int ENA = 5,  IN1 = 7,  IN2 = 8;
const int ENB = 6,  IN3 = 9,  IN4 = 10;
const int SPEED_NORMAL = 150;
const int SPEED_TURN   = 130;

// ===== IR SENSORËT =====
const int IR_LEFT  = 3;
const int IR_RIGHT = 2;

// ===== HC-SR04 =====
const int TRIG = 12;
const int ECHO = 11;
const int OBSTACLE_CM = 20;

// ===== VARIABLA =====
bool manualMode    = false;
String currentDir  = "STOP";
String lastTurn    = "RIGHT";
String piCommand   = "";
unsigned long lastSend = 0;

// ═════════════════════════════════════════════════════════════
void setup() {
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

  stopRobot();

  Serial.begin(9600);
  delay(500);
  Serial.println("{\"status\":\"READY\",\"device\":\"TERRA_GUIDE\"}");
}

// ═════════════════════════════════════════════════════════════
void loop() {
  // 1. Lexo komanda nga Pi
  readPiCommands();

  // 2. Lexo sensorët
  long dist  = readDistance();
  int  irL   = digitalRead(IR_LEFT);
  int  irR   = digitalRead(IR_RIGHT);

  // 3. AUTO mode — lëvizja autonome
  if (!manualMode) {
    if (dist > 0 && dist < OBSTACLE_CM) {
      avoidObstacle();
    } else {
      followLine(irL, irR);
    }
  }

  // 4. Dërgo JSON çdo 300ms
  if (millis() - lastSend >= 300) {
    lastSend = millis();
    sendJSON(dist, irL, irR);
  }
}

// ═════════════════════════════════════════════════════════════
// NDIQ VIJËN — IR LOGJIKA: 1=zezë  0=bardhë
// ═════════════════════════════════════════════════════════════
void followLine(int irL, int irR) {
  if (irL == 1 && irR == 1) {
    forward();                      // të dy mbi vijë → EC PARA

  } else if (irL == 0 && irR == 1) {
    goRight();                      // majtas doli → KTHEHU DJATHTAS
    lastTurn = "RIGHT";

  } else if (irL == 1 && irR == 0) {
    goLeft();                       // djathtas doli → KTHEHU MAJTAS
    lastTurn = "LEFT";

  } else {
    // të dy jashtë → kërko vijën nga drejtimi i fundit
    if (lastTurn == "LEFT") goLeft();
    else                    goRight();
  }
}

// ═════════════════════════════════════════════════════════════
// SHMANG PENGESËN
// ═════════════════════════════════════════════════════════════
void avoidObstacle() {
  Serial.println("{\"event\":\"OBSTACLE\"}");

  stopRobot();  delay(300);

  // Prapa
  goBackward();
  delay(400);
  stopRobot();  delay(200);

  // Kthehu djathtas derisa të gjejë vijën (max 800ms)
  goRight();
  unsigned long t = millis();
  while (millis() - t < 800) {
    if (digitalRead(IR_LEFT) == 1 || digitalRead(IR_RIGHT) == 1) break;
  }

  stopRobot();  delay(150);
}

// ═════════════════════════════════════════════════════════════
// LËVIZJET
// ═════════════════════════════════════════════════════════════
void forward() {
  analogWrite(ENA, SPEED_NORMAL); analogWrite(ENB, SPEED_NORMAL);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  currentDir = "FORWARD";
}

void goBackward() {
  analogWrite(ENA, SPEED_NORMAL); analogWrite(ENB, SPEED_NORMAL);
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
  currentDir = "BACKWARD";
}

void goLeft() {
  analogWrite(ENA, SPEED_TURN); analogWrite(ENB, SPEED_TURN);
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  currentDir = "LEFT";
}

void goRight() {
  analogWrite(ENA, SPEED_TURN); analogWrite(ENB, SPEED_TURN);
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
  currentDir = "RIGHT";
}

void stopRobot() {
  analogWrite(ENA, 0); analogWrite(ENB, 0);
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
  currentDir = "STOP";
}

// ═════════════════════════════════════════════════════════════
// HC-SR04
// ═════════════════════════════════════════════════════════════
long readDistance() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  long dur = pulseIn(ECHO, HIGH, 20000);
  if (dur == 0) return 999;
  return dur * 0.034 / 2;
}

// ═════════════════════════════════════════════════════════════
// LEX KOMANDA NGA PI
// ═════════════════════════════════════════════════════════════
void readPiCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      piCommand.trim();

      if      (piCommand == "CMD:STOP")     { manualMode = true;  stopRobot();   }
      else if (piCommand == "CMD:FORWARD")  { manualMode = true;  forward();     }
      else if (piCommand == "CMD:BACKWARD") { manualMode = true;  goBackward();  }
      else if (piCommand == "CMD:LEFT")     { manualMode = true;  goLeft();      }
      else if (piCommand == "CMD:RIGHT")    { manualMode = true;  goRight();     }
      else if (piCommand == "CMD:AUTO")     { manualMode = false;                }
      else if (piCommand == "CMD:MANUAL")   { manualMode = true;  stopRobot();   }

      piCommand = "";
    } else {
      piCommand += c;
    }
  }
}

// ═════════════════════════════════════════════════════════════
// DËRGO JSON TEK PI
// ═════════════════════════════════════════════════════════════
void sendJSON(long dist, int irL, int irR) {
  Serial.print("{\"dist\":");
  Serial.print(dist);
  Serial.print(",\"ir_l\":");
  Serial.print(irL);
  Serial.print(",\"ir_r\":");
  Serial.print(irR);
  Serial.print(",\"dir\":\"");
  Serial.print(currentDir);
  Serial.print("\",\"mode\":\"");
  Serial.print(manualMode ? "MANUAL" : "AUTO");
  Serial.println("\"}");
}