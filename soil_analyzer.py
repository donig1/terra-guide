# ============================================
# soil_analyzer.py – Analiza e Tokës
# Kontrollon: mbjellë farë? ujitje? shëndet?
# ============================================

from config import THRESHOLDS, FARM

class SoilAnalyzer:

    def __init__(self):
        self.thr = THRESHOLDS
        self.cfg = FARM

    # ─── Lagështia ────────────────────────────

    def moisture_percent(self, raw):
        """Konverto ADC raw (0-1023) → % (0=thatë, 100=i lagur)"""
        pct = round((1 - raw / 1023) * 100, 1)
        return max(0, min(100, pct))

    def moisture_status(self, raw):
        """Kthen statusin e lagështisë dhe mesazhin"""
        if raw < self.thr["moisture_wet"]:
            return "WET",      "Tokë shumë e lagur"
        elif raw < self.thr["moisture_ok"]:
            return "OPTIMAL",  "Lagështia optimale"
        elif raw < self.thr["moisture_dry"]:
            return "DRY",      "Tokë e thatë"
        else:
            return "CRITICAL", "Tokë kritikisht e thatë"

    def needs_irrigation(self, raw):
        """A ka nevojë për ujitje?"""
        return raw >= self.thr["moisture_dry"]

    # ─── Temperatura Tokës ────────────────────

    def soil_temp_status(self, temp):
        if temp < self.thr["soil_temp_min"]:
            return "TOO_COLD",  f"Tokë shumë e ftohtë ({temp}°C)"
        elif temp < self.thr["soil_temp_plant"]:
            return "COLD",      f"Tokë e ftohtë ({temp}°C) – suboptimale"
        elif temp <= self.thr["soil_temp_optimal"] + 5:
            return "OPTIMAL",   f"Temperatura optimale ({temp}°C)"
        elif temp <= self.thr["soil_temp_max"]:
            return "WARM",      f"Tokë e ngrohtë ({temp}°C) – pranueshme"
        else:
            return "HOT",       f"Tokë shumë e nxehtë ({temp}°C) – stres termik"

    # ─── A është e përshtatshme për mbjellë? ──

    def suitable_for_planting(self, soil_temp, moisture_raw, air_temp, humidity):
        """
        Kontrollon të gjithë kushtet për mbjellë farë.
        Kthen: { suitable: bool, score: 0-100, reasons: [], warnings: [] }
        """
        score    = 100
        reasons  = []
        warnings = []

        # Temperatura tokës
        t_status, _ = self.soil_temp_status(soil_temp)
        if t_status == "TOO_COLD":
            score -= 40
            reasons.append(f"❌ Tokë shumë e ftohtë ({soil_temp}°C) – fara nuk mbin")
        elif t_status == "COLD":
            score -= 20
            warnings.append(f"⚠️ Temperatura ({soil_temp}°C) nën optimalen – mbirja e ngadalshme")
        elif t_status == "HOT":
            score -= 30
            reasons.append(f"❌ Tokë shumë e nxehtë ({soil_temp}°C) – fara mund të dëmtohet")
        else:
            reasons.append(f"✅ Temperatura tokës optimale ({soil_temp}°C)")

        # Lagështia
        m_status, _ = self.moisture_status(moisture_raw)
        if m_status == "WET":
            score -= 25
            warnings.append("⚠️ Tokë shumë e lagur – rrezik kalbëzimi i farës")
        elif m_status == "CRITICAL":
            score -= 35
            reasons.append("❌ Tokë shumë e thatë – fara nuk mbin pa ujë")
        elif m_status == "DRY":
            score -= 15
            warnings.append("⚠️ Lagështia pak e ulët – ujit pak para mbjelljes")
        else:
            reasons.append("✅ Lagështia e tokës optimale")

        # Temperatura ajrit
        if air_temp < 10:
            score -= 20
            reasons.append(f"❌ Ajër shumë i ftohtë ({air_temp}°C)")
        elif air_temp > self.thr["air_temp_max"]:
            score -= 15
            warnings.append(f"⚠️ Ajër i nxehtë ({air_temp}°C) – mbulo farën")
        else:
            reasons.append(f"✅ Temperatura e ajrit e mirë ({air_temp}°C)")

        # Lagështia ajrit
        if humidity < self.thr["humidity_low"]:
            score -= 10
            warnings.append(f"⚠️ Ajër shumë i thatë ({humidity}%) – uji më shpesh")
        elif humidity > self.thr["humidity_high"]:
            score -= 10
            warnings.append(f"⚠️ Lagështi e lartë ajri ({humidity}%) – rrezik kërpudhash")

        score = max(0, score)
        suitable = score >= 60

        return {
            "suitable": suitable,
            "score":    score,
            "grade":    self._grade(score),
            "reasons":  reasons,
            "warnings": warnings,
        }

    def _grade(self, score):
        if score >= 85: return "A – Kushte të shkëlqyera"
        if score >= 70: return "B – Kushte të mira"
        if score >= 55: return "C – Kushte mesatare"
        if score >= 40: return "D – Kushte të dobëta"
        return                 "F – Mos mbill tani"

    # ─── Raporti i Plotë ──────────────────────

    def full_report(self, data):
        """
        Input:  data dict nga Arduino
        Output: dict me të gjithë analizat
        """
        raw      = data.get("moisture", 500)
        s_temp   = data.get("soil_temp", 20)
        a_temp   = data.get("air_temp", 22)
        humidity = data.get("humidity", 50)

        m_status, m_msg = self.moisture_status(raw)
        t_status, t_msg = self.soil_temp_status(s_temp)
        planting        = self.suitable_for_planting(s_temp, raw, a_temp, humidity)
        irrigate        = self.needs_irrigation(raw)

        return {
            "moisture_raw":    raw,
            "moisture_pct":    self.moisture_percent(raw),
            "moisture_status": m_status,
            "moisture_msg":    m_msg,
            "soil_temp":       s_temp,
            "temp_status":     t_status,
            "temp_msg":        t_msg,
            "air_temp":        a_temp,
            "humidity":        humidity,
            "needs_irrigation": irrigate,
            "planting":        planting,
        }

    def speak_report(self, report):
        """Tekst i gatshëm për chatbot"""
        lines = []

        lines.append(f"Temperatura e tokës është {report['soil_temp']} gradë. "
                     f"{report['temp_msg']}.")

        lines.append(f"Lagështia e tokës është {report['moisture_pct']} përqind. "
                     f"{report['moisture_msg']}.")

        if report["needs_irrigation"]:
            lines.append("Toka ka nevojë për ujitje. Po aktivizoj pompën.")
        else:
            lines.append("Lagështia e tokës është e mirë. Nuk nevojitet ujitje.")

        p = report["planting"]
        if p["suitable"]:
            lines.append(f"Toka është e përshtatshme për mbjellë farë. "
                         f"Nota: {p['grade']}.")
        else:
            lines.append(f"Toka nuk është e gatshme për mbjellë. "
                         f"Nota: {p['grade']}.")

        return " ".join(lines)