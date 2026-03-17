# Terra Guide — Servo Motor Control Guide
## ARES-X V3 — Kultivimet Automatike

---

## 📋 Përmbajtja

1. [Hardware Setup](#hardware-setup)
2. [Servo Configuration](#servo-configuration)
3. [Voice Commands](#voice-commands)
4. [Manual Control](#manual-control)
5. [Farming Operations](#farming-operations)
6. [Troubleshooting](#troubleshooting)

---

## Hardware Setup

### Servo Pin Connections (Arduino Mega 2560)

| Servo | Funksion | Pin | Detaje |
|-------|--------------|-----|--------|
| **1** | Plugun (Plow) | 9 | PWM output |
| **2** | Soil Sensor | 10 | PWM output |
| **3** | Kazan Fare (Hopper) | 11 | PWM output |

### Physical Setup

**1. Servo Plugun (PLOW_SERVO)**
- Pozicioni fillestar: **180°** (mbyllur)
- Hapje: **180° → 150°** (30° në krahun orar)
- Mbyllje: **150° → 180°** (kthehet prap)
- Qëllim: Hap dhe lëviz tokën për të hapur gropat

**2. Servo Sensori Tokës (SENSOR_SERVO)**
- Pozicioni fillestar: **90°** (lart)
- Uli sensori: **90° → 40°** (50° poshtë)
- Ngre sensori: **40° → 90°** (kthehet lart)
- Qëllim: Skanim periodik i lagështisë së tokës

**3. Servo Kazani Fare (HOPPER_SERVO)**
- Pozicioni fillestar: **0°** (mbyllur)
- Hapje: **0° → 360°** (rrotacion i plotë)
- Mbyllje: **360° → 0°** (kthehet në fillestar)
- Qëllim: Hap kazanin dhe shpërndan fare

---

## Servo Configuration

### Arduino Sketch (ARES_X_Servos.ino)

Sketohet Arduino merr komanda përmes serial në formatin:

```
SERVO:servo_id,angle
```

**Shembuj:**
```
SERVO:1,180    → Plugun në 180°
SERVO:2,40     → Sensori në 40°
SERVO:3,360    → Kazan rrotacion i plotë
```

### Python Modules

#### `servo_controller.py`
Kontrolluesi i ulët i servo motorëve.

```python
from servo_controller import ServoController

servos = ServoController(arduino)

# Kontrolli i plugunit
servos.plow_cycle(repetitions=3)           # 3 cikle
servos.start_continuous_plow(interval=2.0) # Vazhduim çdo 2s

# Kontrolli i sensorit
servos.sensor_scan()                        # Skanim manual
servos.start_periodic_scan(interval=30.0)   # Periodik çdo 30s

# Kontrolli i kazanit
servos.hopper_dispense(pulses=3)            # 3 pulse = 3 rrotacione
```

#### `farming_operations.py`
Menaxheri i operacioneve kultivimi (më i lartë nivel).

```python
from farming_operations import FarmingOperations

farm = FarmingOperations(arduino)

# Start/stop operacione
farm.start_plowing(interval=3.0)
farm.stop_plowing()

farm.start_soil_monitoring(interval=30.0)
farm.stop_soil_monitoring()

farm.dispense_seeds(amount="normal")  # "light", "normal", "heavy"

# Cikli automatik
farm.automatic_farming_cycle()

# Emergency
farm.emergency_stop()
```

---

## Voice Commands

### Plowing Commands

```
"Start plowing"
"Begin plow"
"Plow the ground"
"Dig"
"Till soil"
→ Nis plugunim të vazhdueshëm

"Stop plowing"
"Stop digging"
→ Ndalon plugunimin
```

### Soil Monitoring Commands

```
"Scan soil"
"Check soil"
"Measure moisture"
"Test soil"
→ Bëj skanim manual të sensorit

"Start monitoring"
"Monitor soil"
"Continuous scan"
→ Nis monitorim periodik

"Stop monitoring"
"Stop scan"
→ Ndalon monitorimin
```

### Seed Dispensing Commands

```
"Dispense seeds"
"Distribute seeds"
"Sow seeds"
"Scatter seeds"
→ Shpërnda fare (sasi normale si default)

"Dispense light seeds"
→ Sasi e vogël (1 pulse)

"Dispense heavy seeds"
→ Sasi e madhe (5 pulse)
```

### Farming Cycle Commands

```
"Start farming"
"Auto cycle"
"Farming cycle"
"Begin cultivation"
→ Nis cikli automatik të kultivimit:
   1. Plugunimi (3 cikle)
   2. Skanimi i sensorit
   3. Shpërndarja e farave
   4. Monitorimi periodik
```

### Status and Safety Commands

```
"Status"
"What are you doing"
"Farm status"
"Operations"
→ Shfaq statusin e operacioneve aktuale

"Emergency stop"
"Stop all"
"Stop everything"
"Abort"
→ NDALIM EMERGJENCE — të gjitha operacionet ndalohen
```

---

## Manual Control

### Example: Manual Python Control

```python
from arduino_comm import ArduinoComm
from farming_operations import FarmingOperations

# Initialize
arduino = ArduinoComm()
farm = FarmingOperations(arduino)

# Plow cycle (3 repetitions)
farm.servos.plow_cycle(3)

# Soil scan
farm.servos.sensor_scan()

# Dispense seeds
farm.servos.hopper_dispense(pulses=5)

# Continuous plowing for 30 seconds
farm.start_plowing(interval=2.0)
time.sleep(30)
farm.stop_plowing()
```

---

## Farming Operations

### Automatic Farming Cycle

Cikli automatik i kultivimit përfshin:

1. **Plugunim** (3 cikle)
   - Hap gropat
   - Përgatit tokën

2. **Skanim Senzori**
   - Lexo lagështinë e tokës
   - 2-3 sekonda matje

3. **Shpërndarje Fare**
   - 3 pulse (sasi normale)
   - Shpërndan fare në gropat

4. **Monitorim Periodik**
   - Çdo 30 sekonda skanimi
   - Vazhdim derisa të ndalet

```python
farm.automatic_farming_cycle()
# Këto faza ekzekutohen automatikisht
```

---

## Troubleshooting

### Problem: Servo No Motion

**Zgjidhja:**
1. Kontrolloni lidhjet e pin-ave PWM
2. Kontrolloni fuqinë e servo
3. Kontrolloni serial komunikim (print `arduino.connected`)
4. Riprovoni Arduino sketch upload

### Problem: Servo Jittering

**Zgjidhja:**
1. Përmirësoni fuqinë e servo (8-12V, min 3A)
2. Shtoni kondensator të madh (100µF) pranë servo
3. Zvogëloni bande PWM (më pak shumë servo njëkohësisht)

### Problem: Serial Komunikim

**Zgjidhja:**
1. Kontrolloni port (default `/dev/ttyACM0` ose `/dev/ttyUSB0`)
2. Kontrolloni baud rate (default 9600)
3. Testoni me `minicom` ose `screen`

### Problem: Voice Commands Not Working

**Zgjidhja:**
1. Kontrolloni OPENAI_API_KEY në `.env`
2. Kontrolloni mikrofon lidhje
3. Provoni në simulim (Arduino në mënyra simulim)

---

## Security & Safety

⚠️ **Sigurimi:**
- Gjithmonë kontrollo servo motion përpara se të autoatizosh
- Ushtrohuni me sasi të vogla fare me parë
- Mbaj emergency stop komandë në dijeni
- Inspektoni servo përpara seçdo operacioni

⚠️ **Perangje nga power surges:**
- Shtoni protector diode brenda servo
- Përdor external power (8-12V, min 3A)
- Mos lidhni servo direkt me USB power

---

## Contact & Support

Për problem ose pyetje:
1. Kontrolloni Arduino serial monitor
2. Lexo Python console output
3. Inspektoni fizikisht servo lidhje

Terra Guide v3 — Cultivare më inteligjente! 🌱🤖
