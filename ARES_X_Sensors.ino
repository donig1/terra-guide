/*
 * ARES-X V3 — Arduino Sensor Reader
 * ═══════════════════════════════════════════════════════════════
 * Arduino Mega 2560
 *
 * ROLI: Vetëm lexon sensorët dhe dërgon DATA: tek Raspberry Pi.
 *       Servo motorët kontrollohen DIREKT nga Raspberry Pi (GPIO PWM).
 *       Arduino nuk prek servot — vetëm sensorë!
 *
 * SENSORËT:
 *   A0  → Soil Moisture (VL1.2 analog)
 *   D2  → DS18B20 (temperaturë toke, OneWire)
 *   D3  → DHT22 (temperaturë + lagështi ajri)
 *   D4  → HC-SR04 TRIG (distancë pengesa)
 *   D5  → HC-SR04 ECHO
 *
 * PROTOKOLLI SERIAL (9600 baud → Raspberry Pi /dev/ttyACM0):
 *   Dërgim çdo 500ms:
 *     DATA:moisture_raw,soil_temp,air_temp,humidity,distance
 *   Shembull:
 *     DATA:512,22.4,25.1,63.0,87.5
 *
 *   Statuse speciale:
 *     STATUS:OBSTACLE_NEAR   (distanca < 20cm)
 *     STATUS:READY           (pas boot-it)
 */

#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ── Pin Definitions ──────────────────────────────────────────────
#define MOISTURE_PIN     A0
#define DS18B20_PIN      2
#define DHT_PIN          3
#define DHT_TYPE         DHT22
#define TRIG_PIN         4
#define ECHO_PIN         5

// ── Sensor Objects ───────────────────────────────────────────────
DHT             dht(DHT_PIN, DHT_TYPE);
OneWire         oneWire(DS18B20_PIN);
DallasTemperature ds18b20(&oneWire);

// ── Timing ───────────────────────────────────────────────────────
unsigned long lastSend = 0;
const unsigned long SEND_INTERVAL = 500;   // ms

// ── Obstacle threshold ────────────────────────────────────────────
const float OBSTACLE_CM = 20.0;

// ═══════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(9600);
  delay(1000);

  dht.begin();
  ds18b20.begin();

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  digitalWrite(TRIG_PIN, LOW);

  Serial.println("READY");
  Serial.println("[SENSORS] Arduino inicializuar — vetëm sensorë");
  Serial.println("[SENSORS] Servo kontrollohet nga Raspberry Pi GPIO");
}

// ═══════════════════════════════════════════════════════════════
void loop() {
  unsigned long now = millis();
  if (now - lastSend >= SEND_INTERVAL) {
    lastSend = now;
    sendSensorData();
  }
}

// ── Lexo dhe dërgo të gjitha të dhënat ───────────────────────────
void sendSensorData() {
  // 1. Soil Moisture (analog, 0-1023)
  int moisture = analogRead(MOISTURE_PIN);

  // 2. Temperatura toke (DS18B20)
  ds18b20.requestTemperatures();
  float soilTemp = ds18b20.getTempCByIndex(0);
  if (soilTemp == DEVICE_DISCONNECTED_C) soilTemp = -99.0;

  // 3. Temperatura + lagështi ajri (DHT22)
  float airTemp = dht.readTemperature();
  float humidity = dht.readHumidity();
  if (isnan(airTemp))  airTemp  = -99.0;
  if (isnan(humidity)) humidity = -99.0;

  // 4. Distancë pengese (HC-SR04)
  float distance = measureDistance();

  // ── Dërgim DATA: ────────────────────────────────────────────
  Serial.print("DATA:");
  Serial.print(moisture);   Serial.print(",");
  Serial.print(soilTemp, 1); Serial.print(",");
  Serial.print(airTemp, 1);  Serial.print(",");
  Serial.print(humidity, 1); Serial.print(",");
  Serial.println(distance, 1);

  // ── Alarm pengese ────────────────────────────────────────────
  if (distance > 0 && distance < OBSTACLE_CM) {
    Serial.print("STATUS:OBSTACLE_NEAR:");
    Serial.println(distance, 1);
  }
}

// ── Matje distancë me HC-SR04 ─────────────────────────────────────
float measureDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // timeout 30ms
  if (duration == 0) return 999.9;   // asnjë echo = larg ose gabim
  return (duration * 0.0343) / 2.0;  // cm
}
