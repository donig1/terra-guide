

# ============================================
# chatbot.py - Terra Guide Chatbot me ChatGPT
# ============================================

import threading
import requests
import time
import subprocess
from openai import OpenAI
from ares_knowledge import get_system_prompt

OPENAI_API_KEY = "your-api-key-here"
client = OpenAI(api_key=OPENAI_API_KEY)

def speak_text(text):
    print(f"\nTerra Guide: {text}\n")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        # Zë burri
        voices = engine.getProperty('voices')
        for v in voices:
            if 'male' in v.name.lower() or 'david' in v.name.lower():
                engine.setProperty('voice', v.id)
                break
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[TTS] {e}")
        import subprocess
        subprocess.run(["espeak", "-v", "en+m3", "-s", "140", text], 
                       capture_output=True)
def set_face(state, text=""):
    try:
        requests.post("http://localhost:5000/api/set_face",
                      json={"state": state, "text": text}, timeout=1)
    except:
        pass

try:
    import speech_recognition as sr
    _recognizer = sr.Recognizer()
    _mic        = sr.Microphone(device_index=2)
    STT_OK      = True
    print("[STT] Microphone ready")
except Exception as e:
    print(f"[STT] {e}")
    STT_OK = False


class Chatbot:

    def __init__(self, soil_analyzer):
        self.soil             = soil_analyzer
        self._stop            = False
        self.last_sensor_data = {}
        self.last_soil_report = {}
        self.pump_active      = False
        self.history          = []
        print("[CHAT] Terra Guide ChatGPT ready")

    def ask_gpt(self, user_text):
        try:
            self.history.append({"role": "user", "content": user_text})
            if len(self.history) > 10:
                self.history = self.history[-10:]

            system = get_system_prompt(self.last_soil_report)

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system},
                    *self.history
                ],
                max_tokens=150,
                temperature=0.7
            )

            answer = response.choices[0].message.content.strip()
            self.history.append({"role": "assistant", "content": answer})
            return answer

        except Exception as e:
            print(f"[GPT] Error: {e}")
            return "Sorry, I had a connection problem. Please try again!"

    def speak(self, text):
        set_face("talking", text)
        speak_text(text)
        set_face("idle", "")

    def listen(self, timeout=6):
        set_face("listening")
        if not STT_OK:
            try:
                text = input("You: ").strip()
                return text
            except:
                return ""

        print("Listening...")
        try:
            with _mic as source:
                _recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = _recognizer.listen(source, timeout=timeout,
                                           phrase_time_limit=8)
            set_face("thinking")
            for lang in ["en-US"]:
                try:
                    text = _recognizer.recognize_google(audio, language=lang)
                    print(f"You: {text}")
                    return text
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    break
        except sr.WaitTimeoutError:
            pass
        except Exception as e:
            print(f"[STT] {e}")
        return ""

    def simulate_pump(self, activate):
        self.pump_active = activate
        print(f"[PUMP] {'ACTIVE' if activate else 'INACTIVE'}")

    def update_data(self, sensor_data, soil_report):
        self.last_sensor_data = sensor_data
        self.last_soil_report = soil_report
        print("[CHAT] Sensor data updated")

    def run_voice_loop(self):
        self.speak("Hello! I am Terra Guide, your intelligent farm robot. How can I help you?")
        while not self._stop:
            text = self.listen(timeout=6)
            if text:
                set_face("thinking")
                response = self.ask_gpt(text)
                if response:
                    self.speak(response)
            time.sleep(0.3)

    def start(self):
        t = threading.Thread(target=self.run_voice_loop, daemon=True)
        t.start()
        print("[CHAT] Terra Guide active - listening...")

    def stop(self):
        self._stop = True
