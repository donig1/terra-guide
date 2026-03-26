"""
Terra Guide — chatbot.py  (v3 — Full voice integration)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voice flow:
  1. LISTEN  → mic on  → face shows 'listening' + MIC dot
  2. STT     → Google Speech Recognition
  3. THINK   → face shows 'thinking'
  4. GPT     → OpenAI GPT-4o-mini with soil data in system prompt
  5. SPEAK   → gTTS (Google, clear English) + face shows 'talking'
  6. IDLE    → face returns to 'idle'

Thread-safe: face is updated via cmd_queue (no HTTP, no blocking).
"""

import os
import time
import queue
import threading
import tempfile
import json

import pygame
import speech_recognition as sr
from openai import OpenAI
from dotenv import load_dotenv
import asyncio

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────
MAX_HISTORY    = 14        # messages kept in GPT context
LISTEN_TIMEOUT = 7         # seconds to wait for speech start
LISTEN_PHRASE  = 10        # max seconds of speech
SILENCE_LOOPS  = 3         # idle loops before auto-greeting
ENERGY_THRESH  = 350       # microphone sensitivity (lower = more sensitive)

# edge-tts voice — 100% human-sounding Microsoft Neural TTS
EDGE_VOICE = 'en-US-GuyNeural'   # natural male; swap to 'en-US-JennyNeural' for female


# ─── System prompt builder ─────────────────────────────────────────────────
def build_system_prompt(sensors: dict) -> str:
    moisture = sensors.get('moisture_pct', 50)
    status   = sensors.get('moisture_status', 'UNKNOWN')
    soil_t   = sensors.get('soil_temp', 20)
    air_t    = sensors.get('air_temp', 22)
    humidity = sensors.get('humidity', 60)
    pump     = 'ACTIVE' if sensors.get('pump_active') else 'OFF'
    crop     = sensors.get('crop', 'tomatoes')

    return f"""You are Terra Guide — a friendly, smart agricultural robot assistant physically present in the farmer's field.
You speak directly to the farmer in clear, natural English.
Keep every reply to 2-3 short sentences. Be helpful, warm, and specific.
Never say "I am an AI" or "I am a language model". You are a robot in the field.

LIVE SENSOR DATA (right now):
  Soil moisture : {moisture:.0f}%  [{status}]
  Soil temp     : {soil_t:.1f}°C
  Air temp      : {air_t:.1f}°C
  Humidity      : {humidity:.0f}%
  Irrigation    : {pump}
  Crop          : {crop}

Use these numbers when relevant. If moisture is CRITICAL or DRY, mention irrigation urgency.
If moisture is WET, warn against over-watering. If pump is ACTIVE, confirm it's running.
Respond in 1-3 short sentences. Do not use bullet points."""


# ─── Emotion picker ────────────────────────────────────────────────────────
def pick_emotion(text: str, sensors: dict) -> str:
    """Guess best face emotion from GPT reply content."""
    t = text.lower()
    if sensors.get('moisture_status') == 'CRITICAL': return 'angry'
    if sensors.get('moisture_status') == 'DRY':      return 'sad'
    if any(w in t for w in ('great','excellent','perfect','wonderful','good news','happy')): return 'happy'
    if any(w in t for w in ('warning','critical','danger','urgent','problem','alert','dry')):  return 'angry'
    if any(w in t for w in ('sorry','unfortunately','bad','low','concern','worry','sad')): return 'sad'
    if any(w in t for w in ('think','analyz','calculat','check','estimat','measur')): return 'thinking'
    if any(w in t for w in ('wow','incredible','amazing','surprising','unexpected')): return 'surprised'
    if any(w in t for w in ('haha','funny','laugh','joke','humor')): return 'laughing'
    return 'talking'


# ─── TTS ─── edge-tts (Microsoft Neural) → pyttsx3 fallback ────────────────
def speak_gtts(text: str):
    """Speak text using edge-tts (human voice). Blocks until done."""
    try:
        import edge_tts
        fd, path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)

        async def _save():
            comm = edge_tts.Communicate(text, EDGE_VOICE)
            await comm.save(path)

        asyncio.run(_save())

        # Play with pygame mixer (cross-platform: Pi + Windows)
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.04)
        finally:
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

    except Exception as e:
        print(f"[TTS] edge-tts error: {e} — falling back to pyttsx3")
        _speak_pyttsx3(text)
    finally:
        try: os.unlink(path)
        except Exception: pass


def _speak_pyttsx3(text: str):
    """Offline fallback TTS with male voice."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 148)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        # Select male voice (usually index 0)
        if voices:
            engine.setProperty('voice', voices[0].id)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS] pyttsx3 error: {e}")


# ─── ChatBot ───────────────────────────────────────────────────────────────
class ChatBot:
    """
    Full voice chatbot with face integration.

    Usage:
        bot = ChatBot(face_queue=cmd_queue, sensor_data=sensor_data)
        bot.run_voice_loop()   # runs forever in its own thread
    """

    def __init__(self, face_queue: queue.Queue, sensor_data: dict, farming_ops=None):
        self.face_q      = face_queue
        self.sensor_data = sensor_data
        self.farming_ops = farming_ops  # Optional farming operations controller
        self.history     = []        # [{role, content}, ...]
        self.client      = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.recognizer  = sr.Recognizer()
        self.recognizer.energy_threshold         = ENERGY_THRESH
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold          = 0.8

        # find microphone
        self.mic = None
        self._init_mic()

    def _init_mic(self):
        mics = sr.Microphone.list_microphone_names()
        print(f"[Mic] Available: {mics}")
        # Kërko USB mic (card 2)
        for i, name in enumerate(mics):
            if any(k in name.lower() for k in ('usb','pnp','array','micro')):
                self.mic = sr.Microphone(device_index=i)
                print(f"[Mic] USB mic gjetur: {name} (index {i})")
                return
        self.mic = sr.Microphone()
        print("[Mic] Duke përdorur mikrofonin default")

    # ── face control ──────────────────────────────────────────────────────
    def _set_face(self, state, text='', mic=False):
        self.face_q.put({'state': state, 'text': text, 'mic': mic})

    # ── GPT ───────────────────────────────────────────────────────────────
    def ask_gpt(self, user_text: str) -> str:
        system = build_system_prompt(self.sensor_data)
        messages = [{'role': 'system', 'content': system}]
        messages += self.history[-MAX_HISTORY:]
        messages.append({'role': 'user', 'content': user_text})

        try:
            resp = self.client.chat.completions.create(
                model='gpt-4o-mini',
                messages=messages,
                max_tokens=120,
                temperature=0.75,
            )
            reply = resp.choices[0].message.content.strip()

            # update history
            self.history.append({'role': 'user',      'content': user_text})
            self.history.append({'role': 'assistant',  'content': reply})
            if len(self.history) > MAX_HISTORY * 2:
                self.history = self.history[-MAX_HISTORY:]

            return reply

        except Exception as e:
            print(f"[GPT] Error: {e}")
            return "I had trouble connecting to my brain. Could you repeat that?"

    # ── STT ───────────────────────────────────────────────────────────────
    def listen(self) -> str | None:
        """Listen for one phrase. Returns text or None."""
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                print("[Mic] Dëgjim...")
                audio = self.recognizer.listen(
                    source,
                    timeout=LISTEN_TIMEOUT,
                    phrase_time_limit=LISTEN_PHRASE
                )
            text = self.recognizer.recognize_google(audio, language='en-US')
            print(f"[STT] Heard: {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[STT] Request error: {e}")
            return None
        except Exception as e:
            print(f"[STT] Error: {e}")
            return None

    # ── speak ─────────────────────────────────────────────────────────────
    def speak(self, text: str, emotion: str = 'talking'):
        """Show talking face, speak, then return to idle."""
        self._set_face(emotion if emotion != 'talking' else 'talking', text)
        speak_gtts(text)
        self._set_face('idle')
    # ── Farming commands ───────────────────────────────────────────────────────
    def _check_for_farming_commands(self, user_text: str) -> str | None:
        """Check if user_text contains farming commands."""
        if not self.farming_ops:
            return None
        
        text_lower = user_text.lower()
        
        # Plowing commands
        if any(cmd in text_lower for cmd in ['plow', 'dig', 'till', 'start plowing', 'begin plow']):
            self.farming_ops.start_plowing(interval=3.0)
            self._set_face('happy', 'Starting plowing operation')
            return "Plowing operation started. I will dig the soil now."
        
        if any(cmd in text_lower for cmd in ['stop plow', 'stop digging', 'stop till']):
            self.farming_ops.stop_plowing()
            self._set_face('idle')
            return "Plowing stopped."
        
        # Soil monitoring commands
        if any(cmd in text_lower for cmd in ['scan soil', 'check soil', 'measure moisture', 'test soil']):
            self.farming_ops.manual_soil_scan()
            self._set_face('thinking', 'Scanning soil...')
            return "Soil scan completed. Sensor reading taken."
        
        if any(cmd in text_lower for cmd in ['start monitoring', 'monitor soil', 'continuous scan']):
            self.farming_ops.start_soil_monitoring(interval=30.0)
            self._set_face('happy')
            return "Soil monitoring started. I will check the soil every 30 seconds."
        
        if any(cmd in text_lower for cmd in ['stop monitoring', 'stop scan', 'no more soil']):
            self.farming_ops.stop_soil_monitoring()
            self._set_face('idle')
            return "Soil monitoring stopped."
        
        # Seed dispensing commands
        if any(cmd in text_lower for cmd in ['dispense seeds', 'distribute seeds', 'sow seeds', 'scatter seeds']):
            if 'light' in text_lower:
                self.farming_ops.dispense_seeds('light')
                self._set_face('talking')
                return "Dispensing light amount of seeds."
            elif 'heavy' in text_lower:
                self.farming_ops.dispense_seeds('heavy')
                self._set_face('talking')
                return "Dispensing heavy amount of seeds."
            else:
                self.farming_ops.dispense_seeds('normal')
                self._set_face('talking')
                return "Dispensing normal amount of seeds."
        
        # Auto cycle
        if any(cmd in text_lower for cmd in ['start farming', 'auto cycle', 'farming cycle', 'begin cultivation']):
            self._set_face('thinking', 'Starting farming cycle...')
            time.sleep(1)
            self.farming_ops.automatic_farming_cycle()
            self._set_face('happy')
            return "Automatic farming cycle has been initiated."
        
        # Status
        if any(cmd in text_lower for cmd in ['status', 'what are you doing', 'farm status', 'operations']):
            self.farming_ops.print_status()
            self._set_face('happy')
            return "Showing current farm operations status."
        
        # Emergency stop
        if any(cmd in text_lower for cmd in ['emergency stop', 'stop all', 'stop everything', 'abort']):
            self.farming_ops.emergency_stop()
            self._set_face('angry')
            return "Emergency stop activated. All operations halted."
        
        return None
        # ── main loop ─────────────────────────────────────────────────────────
    def run_voice_loop(self):
        """Infinite voice loop. Run in a background thread."""
        print("[ChatBot] Voice loop started. Say something!")

        # startup greeting
        time.sleep(2.0)
        greeting = "Hello farmer! I am Terra Guide. I'm ready to help you. Just speak to me!"
        self.speak(greeting, 'happy')

        idle_loops = 0

        while True:
            try:
                # show listening state
                self._set_face('listening', '', mic=True)

                user_text = self.listen()

                if not user_text:
                    idle_loops += 1
                    self._set_face('idle', '', mic=False)

                    # periodic check-in after silence
                    if idle_loops >= SILENCE_LOOPS:
                        idle_loops = 0
                        self._auto_check_in()

                    time.sleep(1.0)
                    continue

                idle_loops = 0

                # show heard text in subtitle
                self._set_face('thinking', f'"{user_text}"', mic=False)
                time.sleep(0.3)

                # Check for farming commands first
                cmd_result = self._check_for_farming_commands(user_text)
                if cmd_result:
                    reply = cmd_result
                    emotion = 'happy'
                else:
                    # get GPT reply
                    reply  = self.ask_gpt(user_text)
                    emotion = pick_emotion(reply, self.sensor_data)

                print(f"[GPT] Reply: {reply}")

                # speak with matching emotion
                self.speak(reply, emotion)

            except KeyboardInterrupt:
                print("[ChatBot] Stopping...")
                break
            except Exception as e:
                print(f"[ChatBot] Unexpected error: {e}")
                self._set_face('confused')
                time.sleep(2.0)

    def _auto_check_in(self):
        """Automatic sensor-based alert when farmer is quiet."""
        d = self.sensor_data
        status = d.get('moisture_status', 'OPTIMAL')

        if status == 'CRITICAL':
            msg = f"Alert! Soil moisture is critical at {d.get('moisture_pct',0):.0f} percent. Irrigation pump is now active."
            self.speak(msg, 'angry')
        elif status == 'DRY':
            msg = f"Heads up! Moisture is low at {d.get('moisture_pct',0):.0f} percent. Consider watering soon."
            self.speak(msg, 'sad')
        elif status == 'OPTIMAL':
            msg = f"All good! Soil moisture is {d.get('moisture_pct',0):.0f} percent. Conditions look great."
            self.speak(msg, 'happy')