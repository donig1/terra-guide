#!/usr/bin/env python3
# ============================================
# main.py – ARES-X V3 Kontrolli Kryesor
# Ekzekuto: python3 main.py
# ============================================

import time
import threading

from arduino_comm  import ArduinoComm
from soil_analyzer import SoilAnalyzer
from chatbot       import Chatbot
from data_logger   import init, save
from dashboard     import run_dashboard

# ══════════════════════════════════════════
print("╔══════════════════════════════════════╗")
print("║   ARES-X  V3  –  Duke u nisur...     ║")
print("╚══════════════════════════════════════╝\n")

# ── Inicializim ───────────────────────────
arduino = ArduinoComm()
soil    = SoilAnalyzer()
init()

# ── Chatbot ───────────────────────────────
bot = Chatbot(soil_analyzer=soil)
bot.start()

# ── Dashboard ─────────────────────────────
threading.Thread(target=run_dashboard, daemon=True).start()
print("[DASH] 🌐 http://raspberrypi.local:5000\n")

# ── Variabla gjendjes ─────────────────────
stop_count = 0
MAX_STOPS  = 5
last_data  = {}
measuring  = False

# ══════════════════════════════════════════
def measure_and_analyze(sensor_data):
    global stop_count
    stop_count += 1
    pump_used = False

    print(f"\n{'═'*48}")
    print(f"  📍 PIKË MATJEJE  {stop_count}/{MAX_STOPS}")
    print(f"{'═'*48}")

    # ── 1. Analizo tokën ──────────────────
    report = soil.full_report(sensor_data)
    print(f"  🌡️  Temp Tokë   : {report['soil_temp']}°C  → {report['temp_msg']}")
    print(f"  💧  Lagështia   : {report['moisture_pct']}%  → {report['moisture_msg']}")
    print(f"  🌤️  Temp Ajrit  : {report['air_temp']}°C")
    print(f"  💦  Lag. Ajrit  : {report['humidity']}%")

    # ── 2. Kontrollo mbjellë ──────────────
    p = report["planting"]
    print(f"\n  🌱 Gati për mbjellë? {'PO ✅' if p['suitable'] else 'JO ❌'}")
    print(f"     Nota: {p['grade']} ({p['score']}/100)")
    for r in p["reasons"] + p["warnings"]:
        print(f"     {r}")

    # ── 3. Ujitje nëse duhet ─────────────
    if report["needs_irrigation"]:
        print(f"\n  💧 UJITJE: Toka e thatë – aktivizoj pompën!")
        arduino.send("IRRIGATE_ON")
        bot.simulate_pump(True)
        pump_used = True
        time.sleep(3)
        arduino.send("IRRIGATE_OFF")
        bot.simulate_pump(False)
        print("  💧 Ujitja u kompletua")
    else:
        print(f"\n  ✅ Ujitje: nuk nevojitet ({report['moisture_pct']}%)")

    # ── 4. Chatbot flet rezultatin ────────
    msg = f"Pika matjeje {stop_count}. "
    msg += soil.speak_report(report)
    bot.speak(msg)

    # ── 5. Përditëso chatbot ──────────────
    bot.update_data(sensor_data, report)

    # ── 6. Ruaj në CSV ───────────────────
    save(report, None, pump_used)

    print(f"\n  📊 Ruajtur | Dashboard: http://raspberrypi.local:5000")
    print(f"{'═'*48}\n")

    # ── 7. Vazhdo misionin ───────────────
    time.sleep(2)
    if stop_count < MAX_STOPS:
        arduino.send("FOLLOW")
    else:
        arduino.send("STOP")
        bot.speak(f"Misioni kompletua. Kreu {MAX_STOPS} matje. Shiko rezultatet në dashboard.")

# ══════════════════════════════════════════
# LOOP KRYESOR
# ══════════════════════════════════════════
try:
    arduino.send("FOLLOW")
    print("[NAV] 🚗 Roboti duke ndjekur linjën...\n")

    while stop_count < MAX_STOPS:
        line = arduino.read_line()

        if line:
            msg_type, data = arduino.parse(line)

            if msg_type == "DATA":
                last_data = data
                print(f"[LIVE] 🌡️{data['soil_temp']}°C | "
                      f"💧{round((1-data['moisture']/1023)*100,1)}% | "
                      f"🌤️{data['air_temp']}°C | "
                      f"📏{data['distance']}cm")

            elif msg_type == "STATUS" and data == "STOP_POINT" and not measuring:
                measuring = True
                sensor    = last_data if last_data else arduino.simulate()
                measure_and_analyze(sensor)
                measuring = False

            elif msg_type == "OBS":
                print(f"[NAV] ⚠️ Pengesë {data}cm – duke pritur...")
                time.sleep(1)

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n[ARES-X] Ndaluar (Ctrl+C)")
    arduino.send("STOP")
    bot.stop()

except Exception as e:
    print(f"\n[ERROR] {e}")
    arduino.send("STOP")
    bot.stop()
    raise