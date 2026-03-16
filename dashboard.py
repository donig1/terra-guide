# ============================================
# dashboard.py – Web Dashboard Terra Guide
# http://raspberrypi.local:5000
# ============================================

from flask import Flask, jsonify, render_template_string
from data_logger import read_last
from config import DASHBOARD_PORT

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="sq">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="refresh" content="8">
  <title>Terra Guide Dashboard</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:24px}
    h1{color:#58a6ff;font-size:1.9em;margin-bottom:4px}
    .sub{color:#8b949e;font-size:.85em;margin-bottom:28px}

    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:28px}
    .card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:18px;text-align:center}
    .card .ico{font-size:1.8em;margin-bottom:6px}
    .card .val{font-size:1.9em;font-weight:700;color:#58a6ff}
    .card .lbl{color:#8b949e;font-size:.78em;margin-top:4px}

    .status-bar{padding:14px 20px;border-radius:10px;margin-bottom:20px;font-size:1.1em;font-weight:600}
    .OPTIMAL   {background:#002d22;border-left:5px solid #3fb950}
    .DRY       {background:#2d1600;border-left:5px solid #d29922}
    .CRITICAL  {background:#3d0000;border-left:5px solid #f85149}
    .WET       {background:#001d3d;border-left:5px solid #58a6ff}

    .plant-bar{padding:12px 20px;border-radius:10px;margin-bottom:20px;font-size:1em}
    .HEALTHY   {background:#002d22;border-left:5px solid #3fb950}
    .WARNING   {background:#2d1600;border-left:5px solid #d29922}
    .DISEASE   {background:#3d0000;border-left:5px solid #f85149}
    .CRITICAL_P{background:#3d0000;border-left:5px solid #f85149}
    .UNKNOWN   {background:#161b22;border-left:5px solid #8b949e}

    .plant-bar{background:#161b22;border-left:5px solid #8b949e}

    .section{color:#8b949e;font-size:.8em;text-transform:uppercase;letter-spacing:1px;margin:20px 0 10px}
    table{width:100%;border-collapse:collapse;font-size:.83em}
    th{background:#161b22;color:#8b949e;padding:9px 8px;text-align:left;border-bottom:1px solid #30363d}
    td{padding:8px;border-bottom:1px solid #21262d}
    tr:hover{background:#161b22}
    .ok{color:#3fb950}.warn{color:#d29922}.bad{color:#f85149}
    .refresh{color:#30363d;font-size:.72em;margin-top:18px}

    .pump-on {background:#001d3d;border:1px solid #58a6ff;color:#58a6ff;
               padding:8px 16px;border-radius:8px;display:inline-block;margin-bottom:14px}
    .pump-off{background:#161b22;border:1px solid #30363d;color:#8b949e;
               padding:8px 16px;border-radius:8px;display:inline-block;margin-bottom:14px}
  </style>
</head>
<body>
  <h1>🌾 Terra Guide Dashboard</h1>
  <div class="sub">Sistemi Inteligjent Bujqësor · Rifreskim çdo 8 sek · {{ ts }}</div>

  {% if last %}

  <!-- Status Lagështie -->
  <div class="status-bar {{ last.moisture_status }}">
    💧 Lagështia: {{ last.moisture_pct }}% – {{ last.moisture_status }}
  </div>

  <!-- Status Bime -->
  <div class="plant-bar {% if last.plant_status %}{{ last.plant_status }}{% endif %}">
    🌿 Bima: {{ last.plant_details if last.plant_details else "Duke pritur analizë..." }}
  </div>

  <!-- Pompa -->
  {% if last.pump_activated == 'True' %}
    <div class="pump-on">💧 Pompa: AKTIVE</div>
  {% else %}
    <div class="pump-off">💧 Pompa: joaktive</div>
  {% endif %}

  <!-- Kartat kryesore -->
  <div class="section">📡 Matja e Fundit</div>
  <div class="grid">
    <div class="card">
      <div class="ico">🌡️</div>
      <div class="val">{{ last.soil_temp }}°C</div>
      <div class="lbl">Temp. Tokës</div>
    </div>
    <div class="card">
      <div class="ico">💧</div>
      <div class="val">{{ last.moisture_pct }}%</div>
      <div class="lbl">Lagështia Tokës</div>
    </div>
    <div class="card">
      <div class="ico">🌤️</div>
      <div class="val">{{ last.air_temp }}°C</div>
      <div class="lbl">Temp. Ajrit</div>
    </div>
    <div class="card">
      <div class="ico">💦</div>
      <div class="val">{{ last.humidity }}%</div>
      <div class="lbl">Lagështia Ajrit</div>
    </div>
    <div class="card">
      <div class="ico">🌱</div>
      <div class="val {% if last.planting_suitable=='True' %}ok{% else %}bad{% endif %}">
        {{ '✅ PO' if last.planting_suitable=='True' else '❌ JO' }}
      </div>
      <div class="lbl">Gati për Mbjellë?</div>
    </div>
    <div class="card">
      <div class="ico">📊</div>
      <div class="val">{{ last.planting_score }}/100</div>
      <div class="lbl">{{ last.planting_grade }}</div>
    </div>
  </div>

  <!-- Historia -->
  <div class="section">📋 Historia</div>
  <table>
    <tr>
      <th>Ora</th><th>Temp Tokë</th><th>Lagështia</th>
      <th>Ajër</th><th>Mbjellë?</th><th>Bima</th><th>Pompa</th>
    </tr>
    {% for r in history %}
    <tr>
      <td>{{ r.timestamp[11:19] }}</td>
      <td>{{ r.soil_temp }}°C</td>
      <td class="
        {% if r.moisture_status=='OPTIMAL' %}ok
        {% elif r.moisture_status=='WET' %}warn
        {% else %}bad{% endif %}">
        {{ r.moisture_pct }}%
      </td>
      <td>{{ r.air_temp }}°C</td>
      <td class="{{ 'ok' if r.planting_suitable=='True' else 'bad' }}">
        {{ '✅' if r.planting_suitable=='True' else '❌' }}
      </td>
      <td>{{ r.plant_status if r.plant_status else '—' }}</td>
      <td>{{ '💧' if r.pump_activated=='True' else '—' }}</td>
    </tr>
    {% endfor %}
  </table>

  {% else %}
  <p style="color:#8b949e;margin-top:40px">⏳ Duke pritur të dhëna nga Arduino...</p>
  {% endif %}

  <p class="refresh">Terra Guide · {{ ts }}</p>
</body>
</html>
"""

@app.route('/')
def index():
    from datetime import datetime
    rows    = read_last(30)
    last    = rows[-1] if rows else {}
    history = list(reversed(rows))
    return render_template_string(HTML, last=last, history=history,
                                  ts=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

@app.route('/api/latest')
def api_latest():
    rows = read_last(1)
    return jsonify(rows[0] if rows else {})

@app.route('/api/history')
def api_history():
    return jsonify(read_last(50))
# Gjendja e fytyrës — përditësohet nga chatbot
face_state = {"state": "idle", "text": ""}

@app.route('/api/face_state')
def api_face_state():
    return jsonify(face_state)

@app.route('/api/set_face', methods=['POST'])
def api_set_face():
    from flask import request
    data = request.json
    face_state["state"] = data.get("state", "idle")
    face_state["text"]  = data.get("text",  "")
    return jsonify({"ok": True})
def run_dashboard():
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=False, use_reloader=False)
