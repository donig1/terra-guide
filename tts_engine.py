"""
Terra Guide — tts_engine.py
Clear English TTS: gTTS (Google, online) → pyttsx3 (offline fallback)

Usage:
    from tts_engine import TTSEngine
    tts = TTSEngine()
    tts.speak("Soil moisture is at 67 percent. Conditions are optimal.")
"""

import threading
import queue
import time
import os
import sys


class TTSEngine:
    """
    Two-tier TTS:
      1. gTTS  — Google Text-to-Speech via internet. Clear, natural English.
      2. pyttsx3 — Offline fallback. Lower quality but always works.

    Runs in a background thread so it never blocks the face animation.
    """

    def __init__(self, prefer_online: bool = True, lang: str = 'en'):
        self.lang          = lang
        self.prefer_online = prefer_online
        self._queue        = queue.Queue()
        self._speaking     = False
        self._use_gtts     = False
        self._pyttsx_eng   = None
        self._pygame_ready = False

        self._init_backends()

        self._thread = threading.Thread(target=self._worker, daemon=True, name='TTS-Worker')
        self._thread.start()
        print(f"[TTS] Started — backend: {'gTTS (Google)' if self._use_gtts else 'pyttsx3 (offline)'}")

    # ── Init ─────────────────────────────────────────────────────────────────

    def _init_backends(self):
        # Try gTTS
        if self.prefer_online:
            try:
                from gtts import gTTS
                import pygame
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                self._pygame_ready = True
                self._use_gtts     = True
            except ImportError:
                print("[TTS] gTTS not installed — falling back to pyttsx3")
            except Exception as e:
                print(f"[TTS] pygame mixer init failed ({e}) — falling back to pyttsx3")

        # Init pyttsx3 (always, as fallback)
        if not self._use_gtts:
            try:
                import pyttsx3
                eng = pyttsx3.init()
                eng.setProperty('rate', 148)
                eng.setProperty('volume', 1.0)
                # pick best English voice
                voices = eng.getProperty('voices')
                chosen = None
                for v in voices:
                    name_l = v.name.lower()
                    id_l   = v.id.lower()
                    if 'english' in name_l or 'en-us' in id_l or 'en_us' in id_l:
                        chosen = v.id
                        break
                if not chosen and voices:
                    chosen = voices[0].id
                if chosen:
                    eng.setProperty('voice', chosen)
                self._pyttsx_eng = eng
            except Exception as e:
                print(f"[TTS] pyttsx3 init failed: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def speak(self, text: str):
        """Queue a sentence to speak. Non-blocking."""
        if text and text.strip():
            self._queue.put(text.strip())

    def is_speaking(self) -> bool:
        return self._speaking or not self._queue.empty()

    def stop(self):
        """Clear queue and stop current speech."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        try:
            import pygame
            pygame.mixer.music.stop()
        except Exception:
            pass

    # ── Worker thread ─────────────────────────────────────────────────────────

    def _worker(self):
        while True:
            text = self._queue.get()
            self._speaking = True
            try:
                if self._use_gtts:
                    self._speak_gtts(text)
                elif self._pyttsx_eng:
                    self._speak_pyttsx3(text)
                else:
                    print(f"[TTS] (no backend) {text}")
            except Exception as e:
                print(f"[TTS] Error: {e}")
                # try fallback
                try:
                    if self._use_gtts and self._pyttsx_eng:
                        self._speak_pyttsx3(text)
                except Exception:
                    pass
            finally:
                self._speaking = False

    # ── gTTS backend ──────────────────────────────────────────────────────────

    def _speak_gtts(self, text: str):
        import tempfile
        from gtts import gTTS
        import pygame

        tts = gTTS(text=text, lang=self.lang, slow=False)

        # write to temp file
        fd, tmp_path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)
        tts.save(tmp_path)

        # play with pygame mixer
        try:
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            # wait until done
            while pygame.mixer.music.get_busy():
                time.sleep(0.04)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    # ── pyttsx3 backend ───────────────────────────────────────────────────────

    def _speak_pyttsx3(self, text: str):
        if not self._pyttsx_eng:
            return
        self._pyttsx_eng.say(text)
        self._pyttsx_eng.runAndWait()


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("TTS Engine Test")
    tts = TTSEngine()

    lines = [
        "Hello farmer! I am Terra Guide, your agricultural assistant.",
        "The soil moisture is at 54 percent. Conditions are optimal for tomatoes.",
        "Soil temperature is 21 degrees Celsius. Perfect for planting.",
        "Warning! Moisture level has dropped to critical. Activating irrigation pump now.",
        "Field scan complete. No obstacles detected. Ready to proceed.",
    ]

    for line in lines:
        print(f"Speaking: {line}")
        tts.speak(line)
        time.sleep(0.5)
        while tts.is_speaking():
            time.sleep(0.1)

    print("Done.")