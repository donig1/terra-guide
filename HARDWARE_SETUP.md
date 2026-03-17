# Terra Guide — Hardware Setup Guide
## Raspberry Pi + Arduino Mega Integration

---

## 📋 Përmbajtja

1. [Hardware Requirements](#hardware-requirements)
2. [Arduino Setup](#arduino-setup)
3. [Raspberry Pi Setup](#raspberry-pi-setup)
4. [Wiring Diagram](#wiring-diagram)
5. [Software Installation](#software-installation)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Hardware Requirements

### Core Components

| Component | Quantity | Notes |
|-----------|----------|-------|
| **Raspberry Pi 4/5** | 1 | 4GB RAM minimum |
| **Arduino Mega 2560** | 1 | PWM pins required |
| **Servo Motors** | 3 | MG996R or similar (6V-12V) |
| **Soil Moisture Sensor** | 1 | Analog output (YL-69 + YL-38) |
| **USB Cable** | 1 | A-B type for Arduino |
| **Power Supply** | 2 | 5V for Pi, 12V for servos |

### Servo Motors

| Servo | Purpose | Voltage | Current |
|-------|---------|---------|---------|
| **Plow Servo** | Digging soil | 6-12V | 1-2A |
| **Sensor Servo** | Lowering soil sensor | 6-12V | 1-2A |
| **Hopper Servo** | Seed dispensing | 6-12V | 1-2A |

### Sensors

| Sensor | Type | Output | Purpose |
|--------|------|--------|---------|
| **Soil Moisture** | Analog | 0-1023 | Soil water content |
| **Microphone** | USB | Audio | Voice commands |

---

## Arduino Setup

### 1. Upload Arduino Sketch

1. Open Arduino IDE
2. Load `ARES_X_Servos.ino`
3. Select board: **Arduino Mega 2560**
4. Select port: **/dev/ttyACM0** (or similar)
5. Upload sketch

### 2. Serial Communication

Arduino listens for commands in format:
```
SERVO:servo_id,angle\n
```

**Example commands:**
```
SERVO:1,180    // Plow servo to 180°
SERVO:2,40     // Sensor servo to 40°
SERVO:3,360    // Hopper servo full rotation
```

---

## Raspberry Pi Setup

### 1. Hardware Connections

#### USB Connection
- Connect Arduino Mega to Raspberry Pi USB port
- Arduino will appear as `/dev/ttyACM0` or `/dev/ttyUSB0`

#### Servo Power Supply
- **IMPORTANT:** Do not power servos from Raspberry Pi USB
- Use external 12V power supply for servos
- Connect servo ground to Arduino ground

#### Soil Moisture Sensor
- Connect to Arduino analog pin A0
- Power: 5V from Arduino
- Ground: Arduino GND
- Signal: Arduino A0

### 2. Pin Assignments (Arduino Mega)

| Component | Arduino Pin | Type | Purpose |
|-----------|-------------|------|---------|
| **Plow Servo** | 9 | PWM | Soil digging |
| **Sensor Servo** | 10 | PWM | Lower soil sensor |
| **Hopper Servo** | 11 | PWM | Seed dispensing |
| **Soil Moisture** | A0 | Analog | Moisture reading |
| **Serial RX** | 0 | Digital | USB communication |
| **Serial TX** | 1 | Digital | USB communication |

---

## Wiring Diagram

```
[Raspberry Pi 4/5]          [Arduino Mega 2560]
     USB ──────────────────────── USB (Programming)
                                   ┌─────────────────┐
                                   │  SERVO PINS    │
     [External Power 12V] ─────────┼─ 9: Plow Servo │
                                   │ 10: Sensor Servo│
                                   │ 11: Hopper Servo│
                                   └─────────────────┘
                                   ┌─────────────────┐
                                   │  SENSOR PINS   │
     [Soil Moisture Sensor] ───────┼─ A0: Moisture  │
     VCC ── 5V Arduino            │ GND: Ground    │
     GND ── GND Arduino           │ SIG: A0        │
                                   └─────────────────┘
```

### Detailed Servo Wiring

Each servo needs 3 wires:
- **Red:** Power (12V external)
- **Black/Brown:** Ground (Arduino GND)
- **Yellow/Orange:** Signal (PWM pins 9,10,11)

---

## Software Installation

### 1. Raspberry Pi OS Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-dev -y
sudo apt install mpg123 -y  # For TTS audio

# Install Python packages
pip install -r requirements.txt --break-system-packages
```

### 2. Environment Setup

Create `.env` file in project directory:

```bash
# .env file
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Audio Setup (Optional)

```bash
# Configure audio output
sudo raspi-config
# Advanced Options > Audio > Force 3.5mm headphone jack

# Test audio
speaker-test -c2 -t wav
```

### 4. Microphone Setup

```bash
# USB microphone should work automatically
# Test with:
arecord -l  # List audio devices
arecord -d 5 test.wav  # Record 5 seconds
aplay test.wav  # Play back
```

---

## Testing

### 1. Arduino Test

```bash
# Connect Arduino and check serial
ls /dev/ttyACM* /dev/ttyUSB*

# Test serial communication
python3 -c "
import serial
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.write(b'SERVO:1,180\n')
print('Sent SERVO:1,180')
"
```

### 2. Servo Test

```python
# servo_test.py
from arduino_comm import ArduinoComm
from servo_controller import ServoController

arduino = ArduinoComm()
servos = ServoController(arduino)

# Test each servo
servos.reset_all()  # All to default positions
time.sleep(2)

servos.plow_cycle(1)  # Test plow
time.sleep(2)

servos.sensor_scan()  # Test sensor
time.sleep(2)

servos.hopper_dispense(1)  # Test hopper
```

### 3. Sensor Test

```python
# sensor_test.py
from arduino_comm import ArduinoComm

arduino = ArduinoComm()
while True:
    data = arduino.read_data()
    if data:
        print(f"Soil Moisture: {data.get('moisture_pct', 'N/A')}%")
    time.sleep(1)
```

### 4. Voice Test

```python
# voice_test.py
from chatbot import ChatBot

bot = ChatBot(face_queue=None, sensor_data={})
print("Say something...")
text = bot.listen()
print(f"You said: {text}")
```

### 5. Full System Test

```bash
# Run the complete robot
python robot_control.py
```

---

## Troubleshooting

### Problem: Arduino Not Detected

**Solutions:**
```bash
# Check USB devices
lsusb
ls /dev/ttyACM* /dev/ttyUSB*

# Reset Arduino
# Press reset button on Arduino Mega

# Check permissions
sudo usermod -a -G dialout $USER
# Logout and login again
```

### Problem: Servos Not Moving

**Solutions:**
1. Check power supply (12V, 3A minimum)
2. Verify PWM pins (9,10,11)
3. Test with Arduino IDE servo example
4. Check servo signal wires

### Problem: No Audio Output

**Solutions:**
```bash
# Check audio devices
aplay -l

# Configure audio output
sudo raspi-config
# Advanced Options > Audio > Force 3.5mm

# Test TTS
python3 -c "
from gtts import gTTS
import os
tts = gTTS('Hello world', lang='en')
tts.save('test.mp3')
os.system('mpg123 test.mp3')
"
```

### Problem: Voice Recognition Not Working

**Solutions:**
1. Check microphone connection
2. Test microphone with `arecord`
3. Verify internet connection (Google STT)
4. Check API key for OpenAI

### Problem: Serial Communication Errors

**Solutions:**
1. Check baud rate (9600)
2. Verify USB cable
3. Reset Arduino
4. Check for other programs using serial port

---

## Safety Guidelines

⚠️ **Electrical Safety:**
- Never power servos from Raspberry Pi USB
- Use appropriate voltage (12V) for servos
- Ground all components properly
- Use fuses to protect circuits

⚠️ **Mechanical Safety:**
- Test servo movements slowly first
- Keep hands clear of moving parts
- Secure all mechanical components
- Monitor for overheating

⚠️ **Software Safety:**
- Always have emergency stop available
- Test in simulation mode first
- Backup configurations
- Monitor system resources

---

## Quick Start Commands

```bash
# 1. Setup environment
cd ~/Desktop/Terra\ Guide
pip install -r requirements.txt --break-system-packages

# 2. Upload Arduino sketch
# Open ARES_X_Servos.ino in Arduino IDE
# Upload to Arduino Mega

# 3. Test connections
python3 -c "from arduino_comm import ArduinoComm; print('Arduino:', ArduinoComm().connected)"

# 4. Run robot
python robot_control.py
```

---

## Voice Commands Reference

| Command | Action |
|---------|--------|
| "Start plowing" | Begin continuous plowing |
| "Stop plowing" | Stop plowing |
| "Scan soil" | Manual soil moisture scan |
| "Start monitoring" | Periodic soil monitoring |
| "Dispense seeds" | Dispense normal amount of seeds |
| "Start farming" | Run automatic farming cycle |
| "Emergency stop" | Stop all operations |

---

## Contact & Support

For issues:
1. Check Arduino serial monitor
2. Review Python console output
3. Test individual components
4. Verify wiring connections

Terra Guide v3 — Smart Farming Robot! 🌱🤖
