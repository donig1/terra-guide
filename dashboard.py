# ============================================
# dashboard.py – Web Dashboard Terra Guide
# http://raspberrypi.local:5000
# ============================================

from flask import Flask, jsonify, render_template_string, request
from data_logger import read_last
from config import DASHBOARD_PORT
import random, math
from datetime import datetime, timedelta

app = Flask(__name__)

# Live sensor data — updated by main.py arduino_thread every 0.5s
_live_sensors = {}

# ── Fake demo data (used when CSV is empty) ────────────────────────────────
def _fake_rows(n=20):
    statuses = ['OPTIMAL','OPTIMAL','OPTIMAL','DRY','WET','CRITICAL']
    grades   = ['A','A','B','B','C','D']
    rows = []
    base = datetime.now() - timedelta(minutes=n*3)
    for i in range(n):
        pct    = round(random.uniform(18, 82), 1)
        st     = 'OPTIMAL' if 30<pct<70 else ('DRY' if pct<=30 else ('WET' if pct>=70 else 'CRITICAL'))
        score  = min(100, max(10, int(pct*1.1 + random.uniform(-5,5))))
        grade  = 'A' if score>=85 else ('B' if score>=70 else ('C' if score>=55 else ('D' if score>=40 else 'F')))
        ts     = (base + timedelta(minutes=i*3)).strftime('%Y-%m-%dT%H:%M:%S')
        seed = 'True' if st == 'OPTIMAL' else 'False'
        rows.append({
            'timestamp': ts,
            'moisture_raw': str(random.randint(300,700)),
            'moisture_pct': str(pct),
            'moisture_status': st,
            'soil_temp': str(round(random.uniform(14,28),1)),
            'temp_status': 'OPTIMAL',
            'air_temp': str(round(random.uniform(18,32),1)),
            'humidity': str(round(random.uniform(38,78),1)),
            'planting_suitable': 'True' if score>=55 else 'False',
            'planting_score': str(score),
            'planting_grade': grade,
            'plant_status': 'HEALTHY' if score>=70 else 'WARNING',
            'plant_details': 'Toka e pershtashme per mbjellje.' if score>=70 else 'Kushte jo optimale — roboti kaloi.',
            'seed_planted': seed,
        })
    return rows

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Terra Guide · Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:       #060b12;
  --bg2:      #0c1320;
  --bg3:      #111927;
  --border:   #1e2d3d;
  --border2:  #243447;
  --text:     #e2eaf4;
  --muted:    #5a7a99;
  --accent:   #00c876;
  --accent2:  #0096ff;
  --warn:     #f5a623;
  --danger:   #ff4444;
  --glass:    rgba(255,255,255,0.03);
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
  font-family:'Inter',sans-serif;
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  padding-bottom:60px;
}

/* ── NAV ──────────────────────────────── */
nav{
  display:flex;align-items:center;justify-content:space-between;
  padding:16px 32px;
  background:rgba(6,11,18,0.88);
  backdrop-filter:blur(16px);
  border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:100;
}
.nav-logo{display:flex;align-items:center;gap:10px;font-weight:700;font-size:1.1em;letter-spacing:.5px}
.nav-logo svg{width:28px;height:28px}
.nav-right{display:flex;align-items:center;gap:16px;font-size:.8em;color:var(--muted)}
.pulse-dot{
  width:8px;height:8px;border-radius:50%;
  background:var(--accent);
  box-shadow:0 0 10px var(--accent);
  animation:pulse 2s infinite;
  display:inline-block;margin-right:6px;
}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(1.3)}}

/* ── LAYOUT ───────────────────────────── */
.page{max-width:1280px;margin:0 auto;padding:32px 24px}

/* ── HERO GRID ────────────────────────── */
.hero{
  display:grid;
  grid-template-columns:320px 1fr;
  gap:20px;
  margin-bottom:24px;
}
@media(max-width:800px){.hero{grid-template-columns:1fr}}

/* ── GAUGE CARD ───────────────────────── */
.gauge-card{
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:20px;
  padding:32px;
  display:flex;flex-direction:column;align-items:center;
  position:relative;overflow:hidden;
}
.gauge-card::before{
  content:'';position:absolute;top:-60px;left:50%;transform:translateX(-50%);
  width:200px;height:200px;border-radius:50%;
  background:radial-gradient(circle, rgba(0,200,118,.12) 0%, transparent 70%);
  pointer-events:none;
}
.gauge-label{font-size:.72em;font-weight:600;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:20px}
.gauge-svg{position:relative}
.gauge-val{
  position:absolute;top:50%;left:50%;transform:translate(-50%,-40%);
  text-align:center;
}
.gauge-val .big{font-size:2.6em;font-weight:700;font-family:'JetBrains Mono',monospace;line-height:1}
.gauge-val .unit{font-size:.8em;color:var(--muted);margin-top:4px}
.gauge-status{
  margin-top:16px;padding:6px 20px;border-radius:20px;
  font-size:.8em;font-weight:600;letter-spacing:1px;text-transform:uppercase;
}
.st-OPTIMAL{background:rgba(0,200,118,.15);color:var(--accent);border:1px solid rgba(0,200,118,.3)}
.st-DRY    {background:rgba(245,166,35,.12);color:var(--warn);border:1px solid rgba(245,166,35,.3)}
.st-WET    {background:rgba(0,150,255,.12);color:var(--accent2);border:1px solid rgba(0,150,255,.3)}
.st-CRITICAL{background:rgba(255,68,68,.12);color:var(--danger);border:1px solid rgba(255,68,68,.3)}

/* ── STAT CARDS GRID ──────────────────── */
.stats-grid{
  display:grid;
  grid-template-columns:repeat(2,1fr);
  gap:16px;
}
.stat-card{
  background:var(--bg2);
  border:1px solid var(--border);
  border-radius:16px;
  padding:20px 22px;
  display:flex;flex-direction:column;gap:8px;
  position:relative;overflow:hidden;
  transition:border-color .2s,transform .2s;
}
.stat-card:hover{border-color:var(--border2);transform:translateY(-2px)}
.stat-card::after{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  border-radius:16px 16px 0 0;
  background:var(--card-accent,var(--border));
}
.stat-icon{font-size:1.4em}
.stat-val{font-size:1.9em;font-weight:700;font-family:'JetBrains Mono',monospace;line-height:1}
.stat-lbl{font-size:.73em;color:var(--muted);text-transform:uppercase;letter-spacing:1px}
.stat-bar{height:4px;background:var(--bg3);border-radius:4px;overflow:hidden;margin-top:auto}
.stat-fill{height:100%;border-radius:4px;background:var(--card-accent,var(--accent));transition:width 1s ease}

/* ── SECTION HEADER ───────────────────── */
.sec-hdr{
  display:flex;align-items:center;gap:10px;
  font-size:.72em;font-weight:600;color:var(--muted);
  text-transform:uppercase;letter-spacing:2px;
  margin-bottom:16px;
}
.sec-hdr::after{content:'';flex:1;height:1px;background:var(--border)}

/* ── CHART CARD ───────────────────────── */
.chart-card{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:20px;padding:24px 28px;
  margin-bottom:24px;
}
.chart-title{font-size:.95em;font-weight:600;margin-bottom:4px}
.chart-sub{font-size:.75em;color:var(--muted);margin-bottom:20px}

/* ── INFO ROW ─────────────────────────── */
.info-row{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:16px;margin-bottom:24px;
}
.info-card{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:16px;padding:18px 20px;
  display:flex;align-items:center;gap:16px;
}
.info-icon{
  width:44px;height:44px;border-radius:12px;
  display:flex;align-items:center;justify-content:center;
  font-size:1.3em;flex-shrink:0;
}
.info-body .lbl{font-size:.72em;color:var(--muted);text-transform:uppercase;letter-spacing:1px}
.info-body .val{font-size:1.15em;font-weight:600;margin-top:2px}

/* ── PUMP STATUS ──────────────────────── */
.pump-badge{
  display:inline-flex;align-items:center;gap:8px;
  padding:10px 20px;border-radius:50px;
  font-size:.85em;font-weight:600;
}
.pump-on {background:rgba(0,150,255,.15);border:1px solid rgba(0,150,255,.4);color:var(--accent2)}
.pump-off{background:rgba(255,255,255,.04);border:1px solid var(--border);color:var(--muted)}

/* ── TABLE ────────────────────────────── */
.table-card{
  background:var(--bg2);border:1px solid var(--border);
  border-radius:20px;overflow:hidden;
}
table{width:100%;border-collapse:collapse;font-size:.82em}
thead tr{background:var(--bg3)}
th{
  padding:12px 16px;text-align:left;color:var(--muted);
  font-size:.7em;text-transform:uppercase;letter-spacing:1.5px;font-weight:600;
  border-bottom:1px solid var(--border);
}
td{padding:12px 16px;border-bottom:1px solid var(--border);color:var(--text)}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:rgba(255,255,255,.02)}
.badge{
  display:inline-block;padding:3px 10px;border-radius:20px;
  font-size:.75em;font-weight:600;font-family:'JetBrains Mono',monospace;
}
.b-ok  {background:rgba(0,200,118,.12);color:#00c876;border:1px solid rgba(0,200,118,.25)}
.b-warn{background:rgba(245,166,35,.12);color:#f5a623;border:1px solid rgba(245,166,35,.25)}
.b-bad {background:rgba(255,68,68,.12); color:#ff4444;border:1px solid rgba(255,68,68,.25)}
.b-info{background:rgba(0,150,255,.12); color:#38b2f5;border:1px solid rgba(0,150,255,.25)}
.mono{font-family:'JetBrains Mono',monospace}

/* ── PROGRESS BAR REFRESH ─────────────── */
.refresh-bar{
  position:fixed;bottom:0;left:0;right:0;height:3px;
  background:var(--border);
}
.refresh-fill{
  height:100%;
  background:linear-gradient(90deg,var(--accent),var(--accent2));
  animation:fill 10s linear infinite;
}
@keyframes fill{from{width:0}to{width:100%}}

/* ── FOOTER ───────────────────────────── */
.footer{text-align:center;color:var(--muted);font-size:.72em;margin-top:40px;padding-top:20px;border-top:1px solid var(--border)}
.glow-green{color:var(--accent);text-shadow:0 0 12px rgba(0,200,118,.4)}
.glow-blue {color:var(--accent2);text-shadow:0 0 12px rgba(0,150,255,.4)}
</style>
</head>
<body>

<!-- NAV -->
<nav>
  <div class="nav-logo">
    <svg viewBox="0 0 28 28" fill="none">
      <circle cx="14" cy="14" r="13" fill="rgba(0,200,118,.12)" stroke="#00c876" stroke-width="1.5"/>
      <path d="M14 8v6l4 3" stroke="#00c876" stroke-width="2" stroke-linecap="round"/>
      <circle cx="14" cy="14" r="2" fill="#00c876"/>
    </svg>
    TERRA GUIDE
  </div>
  <div class="nav-right">
    <span><span class="pulse-dot"></span>LIVE</span>
    <span id="nav-ts">Updated: {{ ts }}</span>
  </div>
</nav>

<div class="page">

<!-- HERO: Gauge + Stats -->
<div class="hero">

  <!-- Moisture Gauge -->
  <div class="gauge-card">
    <div class="gauge-label">Soil Moisture</div>
    <div class="gauge-svg" style="width:200px;height:200px">
      <svg width="200" height="200" viewBox="0 0 200 200">
        <defs>
          <linearGradient id="gGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="{{ gauge_color }}"/>
            <stop offset="100%" stop-color="{{ gauge_color2 }}"/>
          </linearGradient>
        </defs>
        <!-- Track -->
        <circle cx="100" cy="100" r="80"
          fill="none" stroke="#1e2d3d" stroke-width="14"
          stroke-dasharray="415"
          stroke-dashoffset="{{ track_gap }}"
          stroke-linecap="round"
          transform="rotate(135 100 100)"/>
        <!-- Value arc -->
        <circle id="gauge-arc" cx="100" cy="100" r="80"
          fill="none" stroke="url(#gGrad)" stroke-width="14"
          stroke-dasharray="415"
          stroke-dashoffset="{{ arc_offset }}"
          stroke-linecap="round"
          transform="rotate(135 100 100)"
          style="transition:stroke-dashoffset 1.2s ease;filter:drop-shadow(0 0 8px {{ gauge_color }})"/>
        <!-- Ticks -->
        {% for tick in ticks %}
        <line x1="{{ tick.x1 }}" y1="{{ tick.y1 }}" x2="{{ tick.x2 }}" y2="{{ tick.y2 }}"
          stroke="{{ tick.color }}" stroke-width="{{ tick.w }}" stroke-linecap="round"/>
        {% endfor %}
      </svg>
      <div class="gauge-val">
        <div class="big glow-green" id="gauge-val-big">{{ moisture_pct }}<span style="font-size:.45em;color:var(--muted)">%</span></div>
        <div class="unit">MOISTURE</div>
      </div>
    </div>
    <span id="gauge-status" class="gauge-status st-{{ moisture_status }}">{{ moisture_status }}</span>
    <div style="margin-top:20px;width:100%">
      <div style="display:flex;justify-content:space-between;font-size:.72em;color:var(--muted);margin-bottom:6px">
        <span>Planting Score</span>
        <span class="mono">{{ planting_score }}/100</span>
      </div>
      <div style="height:6px;background:var(--bg3);border-radius:6px">
        <div id="score-fill" style="height:100%;width:{{ planting_score }}%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:6px;transition:width 1s ease"></div>
      </div>
      <div style="text-align:center;margin-top:10px">
        <span class="badge {{ 'b-ok' if planting_suitable=='True' else 'b-bad' }}">
          {{ '✓ Ready to Plant' if planting_suitable=='True' else '✗ Not Ready' }}
        </span>
        <span class="badge b-info" style="margin-left:8px">Grade {{ planting_grade }}</span>
      </div>
    </div>
  </div>

  <!-- Stats Grid -->
  <div class="stats-grid">
    <div class="stat-card" style="--card-accent:#00c876">
      <div class="stat-icon">💧</div>
      <div id="v-moisture" class="stat-val glow-green">{{ moisture_pct }}<span style="font-size:.45em;color:var(--muted)"> %</span></div>
      <div class="stat-lbl">Soil Moisture</div>
      <div class="stat-bar"><div id="f-moisture" class="stat-fill" style="width:{{ moisture_pct }}%"></div></div>
    </div>
    <div class="stat-card" style="--card-accent:#0096ff">
      <div class="stat-icon">🌡️</div>
      <div id="v-soiltemp" class="stat-val glow-blue">{{ soil_temp }}<span style="font-size:.45em;color:var(--muted)"> °C</span></div>
      <div class="stat-lbl">Soil Temp</div>
      <div class="stat-bar"><div id="f-soiltemp" class="stat-fill" style="width:{{ (soil_temp|float / 50 * 100)|int }}%;background:var(--accent2)"></div></div>
    </div>
    <div class="stat-card" style="--card-accent:#f5a623">
      <div class="stat-icon">🌤️</div>
      <div id="v-airtemp" class="stat-val" style="color:#f5a623">{{ air_temp }}<span style="font-size:.45em;color:var(--muted)"> °C</span></div>
      <div class="stat-lbl">Air Temp</div>
      <div class="stat-bar"><div id="f-airtemp" class="stat-fill" style="width:{{ (air_temp|float / 50 * 100)|int }}%;background:#f5a623"></div></div>
    </div>
    <div class="stat-card" style="--card-accent:#a78bfa">
      <div class="stat-icon">💦</div>
      <div id="v-humidity" class="stat-val" style="color:#a78bfa">{{ humidity }}<span style="font-size:.45em;color:var(--muted)"> %</span></div>
      <div class="stat-lbl">Air Humidity</div>
      <div class="stat-bar"><div id="f-humidity" class="stat-fill" style="width:{{ humidity }}%;background:#a78bfa"></div></div>
    </div>
  </div>
</div>

<!-- INFO ROW: Plant status + Pump -->
<div class="info-row" style="margin-bottom:24px">
  <div class="info-card">
    <div class="info-icon" style="background:rgba(0,200,118,.1)">🌿</div>
    <div class="info-body">
      <div class="lbl">Plant Health</div>
      <div class="val">
        <span class="badge {{ 'b-ok' if plant_status=='HEALTHY' else 'b-warn' if plant_status=='WARNING' else 'b-bad' }}">
          {{ plant_status or 'UNKNOWN' }}
        </span>
      </div>
      <div style="font-size:.78em;color:var(--muted);margin-top:4px">{{ plant_details or '—' }}</div>
    </div>
  </div>
  <div class="info-card">
    <div class="info-icon" style="background:rgba(0,200,118,.1)">🌱</div>
    <div class="info-body">
      <div class="lbl">Vendimi i Robotit</div>
      <div class="val" style="margin-top:6px">
        <span id="pump-badge" class="pump-badge {{ 'pump-on' if pump_on else 'pump-off' }}">
          {% if pump_on %}<span class="pulse-dot" style="background:var(--accent);box-shadow:0 0 8px var(--accent)"></span>MBJOLLUR{% else %}✗ KALOI{% endif %}
        </span>
      </div>
    </div>
  </div>
  <div class="info-card">
    <div class="info-icon" style="background:rgba(245,166,35,.1)">📡</div>
    <div class="info-body">
      <div class="lbl">System</div>
      <div class="val"><span class="badge b-ok">● ONLINE</span></div>
      <div style="font-size:.78em;color:var(--muted);margin-top:4px">Arduino · Raspberry Pi 5</div>
    </div>
  </div>
</div>

<!-- CHART -->
<div class="sec-hdr">Moisture History</div>
<div class="chart-card" style="margin-bottom:24px">
  <div class="chart-title">Soil Moisture Over Time</div>
  <div class="chart-sub">Last {{ chart_n }} readings · auto-refreshes every 10s</div>
  <div style="height:200px">
    <canvas id="moistureChart"></canvas>
  </div>
</div>

<!-- HISTORY TABLE -->
<div class="sec-hdr">Reading Log</div>
<div class="table-card">
  <table>
    <thead>
      <tr>
        <th>Time</th>
        <th>Moisture</th>
        <th>Status</th>
        <th>Soil °C</th>
        <th>Air °C</th>
        <th>Humidity</th>
        <th>E pershtashme</th>
        <th>Mbjellje</th>
      </tr>
    </thead>
    <tbody>
      {% for r in history %}
      <tr>
        <td class="mono" style="color:var(--muted)">{{ r.timestamp[11:19] }}</td>
        <td class="mono"><strong>{{ r.moisture_pct }}%</strong></td>
        <td>
          <span class="badge
            {% if r.moisture_status=='OPTIMAL' %}b-ok
            {% elif r.moisture_status=='WET' %}b-info
            {% elif r.moisture_status=='DRY' %}b-warn
            {% else %}b-bad{% endif %}">
            {{ r.moisture_status }}
          </span>
        </td>
        <td class="mono">{{ r.soil_temp }}°C</td>
        <td class="mono">{{ r.air_temp }}°C</td>
        <td class="mono">{{ r.humidity }}%</td>
        <td>
          <span class="badge {{ 'b-ok' if r.planting_suitable=='True' else 'b-bad' }}">
            {{ '✓ YES' if r.planting_suitable=='True' else '✗ NO' }}
          </span>
        </td>
        <td>
          {% if r.seed_planted=='True' %}
            <span class="badge b-ok">🌱 PO</span>
          {% else %}
            <span style="color:var(--muted)">✗ JO</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
      {% if not history %}
      <tr><td colspan="8" style="text-align:center;color:var(--muted);padding:32px">No data yet</td></tr>
      {% endif %}
    </tbody>
  </table>
</div>

<div class="footer">
  TERRA GUIDE · Autonomous Farm Robot &nbsp;·&nbsp; {{ ts }}
</div>

</div><!-- .page -->

<!-- Refresh progress bar -->
<div class="refresh-bar"><div class="refresh-fill"></div></div>

<script>
// ── Chart.js moisture history ──────────────────────────────────────────────
const labels  = {{ chart_labels | tojson }};
const data    = {{ chart_data   | tojson }};
const ctx = document.getElementById('moistureChart').getContext('2d');

const grad = ctx.createLinearGradient(0, 0, 0, 200);
grad.addColorStop(0,   'rgba(0,200,118,0.35)');
grad.addColorStop(1,   'rgba(0,200,118,0.00)');

const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels,
    datasets:[{
      data,
      borderColor:'#00c876',
      borderWidth:2,
      backgroundColor:grad,
      pointRadius:3,
      pointBackgroundColor:'#00c876',
      pointBorderColor:'#060b12',
      pointBorderWidth:2,
      tension:0.4,
      fill:true,
    }]
  },
  options:{
    responsive:true,
    maintainAspectRatio:false,
    interaction:{mode:'index',intersect:false},
    plugins:{
      legend:{display:false},
      tooltip:{
        backgroundColor:'#111927',
        borderColor:'#1e2d3d',
        borderWidth:1,
        titleColor:'#5a7a99',
        bodyColor:'#e2eaf4',
        padding:10,
        callbacks:{label:ctx=>' '+ctx.parsed.y+'%'}
      }
    },
    scales:{
      x:{
        grid:{color:'rgba(30,45,61,0.6)'},
        ticks:{color:'#5a7a99',font:{size:10},maxRotation:0,maxTicksLimit:8}
      },
      y:{
        min:0,max:100,
        grid:{color:'rgba(30,45,61,0.6)'},
        ticks:{
          color:'#5a7a99',font:{size:10},
          callback:v=>v+'%',stepSize:25
        }
      }
    }
  }
});

// Auto-refresh every 10s
setTimeout(()=>location.reload(), 10000);
</script>

<script>
// ── Live sensor polling every 3s ───────────────────────────────────────────
const CIRC  = 2 * Math.PI * 80;
const SWEEP = 0.75 * CIRC;
const GAP   = CIRC - SWEEP;

const STATUS_COLS = {
  OPTIMAL:  '#00c876',
  DRY:      '#f5a623',
  WET:      '#0096ff',
  CRITICAL: '#ff4444',
};

function calcArcOffset(pct) {
  const filled = SWEEP * Math.max(0, Math.min(100, pct)) / 100;
  return Math.round(SWEEP - filled + GAP);
}

async function livePoll() {
  try {
    const r = await fetch('/api/live');
    const d = await r.json();
    if (!d || d.moisture_pct === undefined) return;

    const pct    = parseFloat(d.moisture_pct);
    const status = d.moisture_status || 'OPTIMAL';
    const col    = STATUS_COLS[status] || '#00c876';

    // Gauge arc
    const arc = document.getElementById('gauge-arc');
    if (arc) { arc.setAttribute('stroke-dashoffset', calcArcOffset(pct)); arc.style.filter = 'drop-shadow(0 0 8px '+col+')'; }
    // Gauge value + status badge
    const gv = document.getElementById('gauge-val-big');
    if (gv) gv.innerHTML = Math.round(pct) + '<span style="font-size:.45em;color:var(--muted)">%</span>';
    const gs = document.getElementById('gauge-status');
    if (gs) { gs.textContent = status; gs.className = 'gauge-status st-' + status; }

    // Moisture stat
    const vm = document.getElementById('v-moisture');
    if (vm) vm.innerHTML = Math.round(pct) + '<span style="font-size:.45em;color:var(--muted)"> %</span>';
    const fm = document.getElementById('f-moisture');
    if (fm) fm.style.width = pct + '%';

    // Soil temp
    const st  = parseFloat(d.soil_temp || 21);
    const vst = document.getElementById('v-soiltemp');
    if (vst) vst.innerHTML = st.toFixed(1) + '<span style="font-size:.45em;color:var(--muted)"> °C</span>';
    const fst = document.getElementById('f-soiltemp');
    if (fst) fst.style.width = (st / 50 * 100) + '%';

    // Air temp
    const at  = parseFloat(d.air_temp || 22);
    const vat = document.getElementById('v-airtemp');
    if (vat) vat.innerHTML = at.toFixed(1) + '<span style="font-size:.45em;color:var(--muted)"> °C</span>';
    const fat = document.getElementById('f-airtemp');
    if (fat) fat.style.width = (at / 50 * 100) + '%';

    // Humidity
    const hu  = parseFloat(d.humidity || 60);
    const vhu = document.getElementById('v-humidity');
    if (vhu) vhu.innerHTML = Math.round(hu) + '<span style="font-size:.45em;color:var(--muted)"> %</span>';
    const fhu = document.getElementById('f-humidity');
    if (fhu) fhu.style.width = hu + '%';

    // Robot action badge (seed planted or skipped)
    const planted = d.can_plant === true || d.can_plant === 'True' ||
                    d.seed_planted === 'True';
    const pb = document.getElementById('pump-badge');
    if (pb) {
      pb.className = 'pump-badge ' + (planted ? 'pump-on' : 'pump-off');
      pb.innerHTML  = planted
        ? '<span class="pulse-dot" style="background:var(--accent);box-shadow:0 0 8px var(--accent)"></span>MBJOLLUR'
        : '✗ KALOI';
    }

    // Nav timestamp
    const nt = document.getElementById('nav-ts');
    if (nt) nt.textContent = 'Updated: ' + new Date().toLocaleTimeString();

    // Push to chart
    if (typeof chart !== 'undefined') {
      chart.data.labels.push(new Date().toLocaleTimeString());
      chart.data.datasets[0].data.push(Math.round(pct * 10) / 10);
      if (chart.data.labels.length > 30) { chart.data.labels.shift(); chart.data.datasets[0].data.shift(); }
      chart.update('none');
    }

  } catch(e) { console.warn('Live poll error:', e); }
}

setInterval(livePoll, 3000);
setTimeout(livePoll, 500); // first call after 0.5s
</script>
</body>
</html>
"""

# ── Gauge helpers ──────────────────────────────────────────────────────────
def _gauge_params(pct):
    """Return SVG arc params for gauge circle (270° sweep, r=80)."""
    r        = 80
    circ     = 2 * math.pi * r          # ≈ 502.65
    sweep    = 0.75 * circ              # 270° → ≈ 376.99
    gap      = circ - sweep             # ≈ 125.66

    filled   = sweep * max(0, min(100, pct)) / 100
    offset   = sweep - filled + gap

    status  = 'OPTIMAL' if 30 < pct < 70 else ('DRY' if pct <= 30 else ('WET' if pct >= 70 else 'CRITICAL'))
    col_map = {'OPTIMAL': ('#00c876', '#00f0a0'),
               'DRY':     ('#f5a623', '#ff8c00'),
               'WET':     ('#0096ff', '#38b2f5'),
               'CRITICAL':('#ff4444', '#ff8888')}
    c1, c2  = col_map[status]
    return round(sweep + gap), round(offset), c1, c2, status

def _ticks(n=24):
    """Generate tick marks around the gauge (135° to 405°, i.e. 270° sweep)."""
    ticks = []
    cx, cy, r_outer, r_inner = 100, 100, 94, 86
    for i in range(n):
        angle_deg = 135 + (270 / (n - 1)) * i
        angle_rad = math.radians(angle_deg)
        major = (i % 6 == 0)
        ro = r_outer + (3 if major else 0)
        ri = r_inner - (2 if major else 0)
        ticks.append({
            'x1': round(cx + ri * math.cos(angle_rad), 2),
            'y1': round(cy + ri * math.sin(angle_rad), 2),
            'x2': round(cx + ro * math.cos(angle_rad), 2),
            'y2': round(cy + ro * math.sin(angle_rad), 2),
            'color': '#2a3f55' if not major else '#3a5570',
            'w': 2 if major else 1,
        })
    return ticks

# ── Routes ────────────────────────────────────────────────────────────────
face_state = {"state": "idle", "text": ""}

@app.route('/')
def index():
    rows = read_last(30)
    if not rows:
        rows = _fake_rows(20)

    last    = rows[-1]
    history = list(reversed(rows[-15:]))

    pct    = float(last.get('moisture_pct', 50))
    track, arc_off, gc1, gc2, ms = _gauge_params(pct)

    # chart data (chronological order)
    chart_rows  = rows[-20:]
    chart_labels = [r['timestamp'][11:19] for r in chart_rows]
    chart_data   = [float(r.get('moisture_pct', 0)) for r in chart_rows]

    return render_template_string(HTML,
        ts=datetime.now().strftime('%d %b %Y  %H:%M:%S'),
        moisture_pct   = round(pct, 1),
        moisture_status= ms,
        soil_temp      = last.get('soil_temp',  '—'),
        air_temp       = last.get('air_temp',   '—'),
        humidity       = last.get('humidity',   '—'),
        planting_score = last.get('planting_score', 0),
        planting_grade = last.get('planting_grade', '—'),
        planting_suitable = last.get('planting_suitable', 'False'),
        plant_status   = last.get('plant_status', 'UNKNOWN'),
        plant_details  = last.get('plant_details', ''),
        pump_on        = last.get('seed_planted') == 'True' or last.get('can_plant') is True,
        gauge_color    = gc1,
        gauge_color2   = gc2,
        track_gap      = track,
        arc_offset     = arc_off,
        ticks          = _ticks(),
        history        = history,
        chart_labels   = chart_labels,
        chart_data     = chart_data,
        chart_n        = len(chart_data),
    )

@app.route('/api/live')
def api_live():
    """Real-time sensor snapshot polled by dashboard JS every 3s."""
    if _live_sensors:
        return jsonify(dict(_live_sensors))
    rows = read_last(1)
    return jsonify(rows[0] if rows else _fake_rows(1)[0])

@app.route('/api/latest')
def api_latest():
    rows = read_last(1)
    return jsonify(rows[0] if rows else _fake_rows(1)[0])

@app.route('/api/history')
def api_history():
    rows = read_last(50)
    return jsonify(rows if rows else _fake_rows(20))

@app.route('/api/face_state')
def api_face_state():
    return jsonify(face_state)

@app.route('/api/set_face', methods=['POST'])
def api_set_face():
    data = request.json or {}
    face_state["state"] = data.get("state", "idle")
    face_state["text"]  = data.get("text",  "")
    return jsonify({"ok": True})

def run_dashboard():
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=False, use_reloader=False)
