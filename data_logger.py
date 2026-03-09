# ============================================
# data_logger.py – Regjistrim CSV
# ============================================

import csv, os
from datetime import datetime
from config import DATA_FILE

FIELDS = [
    "timestamp",
    "moisture_raw", "moisture_pct", "moisture_status",
    "soil_temp", "temp_status",
    "air_temp", "humidity",
    "planting_suitable", "planting_score", "planting_grade",
    "needs_irrigation",
    "plant_status", "plant_details",
    "pump_activated",
]

def init():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.isfile(DATA_FILE):
        with open(DATA_FILE, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()
        print(f"[LOG] 📄 {DATA_FILE} krijuar")

def save(soil_report, plant_health=None, pump=False):
    p = soil_report.get("planting", {})
    row = {
        "timestamp":          datetime.now().isoformat(),
        "moisture_raw":       soil_report.get("moisture_raw", ""),
        "moisture_pct":       soil_report.get("moisture_pct", ""),
        "moisture_status":    soil_report.get("moisture_status", ""),
        "soil_temp":          soil_report.get("soil_temp", ""),
        "temp_status":        soil_report.get("temp_status", ""),
        "air_temp":           soil_report.get("air_temp", ""),
        "humidity":           soil_report.get("humidity", ""),
        "planting_suitable":  p.get("suitable", ""),
        "planting_score":     p.get("score", ""),
        "planting_grade":     p.get("grade", ""),
        "needs_irrigation":   soil_report.get("needs_irrigation", ""),
        "plant_status":       plant_health.get("status", "") if plant_health else "",
        "plant_details":      plant_health.get("details", "") if plant_health else "",
        "pump_activated":     pump,
    }
    with open(DATA_FILE, 'a', newline='') as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)

def read_last(n=20):
    if not os.path.isfile(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return list(csv.DictReader(f))[-n:]