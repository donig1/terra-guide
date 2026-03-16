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
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────
MAX_HISTORY    = 14        # messages kept in GPT context
LISTEN_TIMEOUT = 7         # seconds to wait for speech start
LISTEN_PHRASE  = 10        # max seconds of speech
SILENCE_LOOPS  = 3         # idle loops before auto-greeting
ENERGY_THRESH  = 350       # microphone sensitivity (lower = more sensitive)


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


# ─── TTS (gTTS + pygame) ───────────────────────────────────────────────────
def speak_gtts(text: str):
    """Speak text using gTTS (Google). Blocks until done."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fd, path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)
        tts.save(path)

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.04)
    except Exception as e:
        print(f"[TTS] gTTS error: {e}")
        _speak_pyttsx3(text)
    finally:
        try: os.unlink(path)
        except: pass


def _speak_pyttsx3(text: str):
    """Offline fallback TTS."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 148)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        for v in voices:
            if 'english' in v.name.lower() or 'en_us' in v.id.lower():
                engine.setProperty('voice', v.id); break
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

    def __init__(self, face_queue: queue.Queue, sensor_data: dict):
        self.face_q      = face_queue
        self.sensor_data = sensor_data
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
        # prefer USB mic if available
        for i, name in enumerate(mics):
            if any(k in name.lower() for k in ('usb','array','micro','input')):
                self.mic = sr.Microphone(device_index=i)
                print(f"[Mic] Using: {name}")
                return
        # default
        self.mic = sr.Microphone()
        print(f"[Mic] Using default microphone")

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
                print("[Mic] Listening...")
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