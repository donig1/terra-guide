"""
Terra Guide — tts_engine.py
100% Human English TTS: edge-tts (Microsoft Neural) → gTTS → pyttsx3 fallback

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
import asyncio
import tempfile


class TTSEngine:
    """
    Three-tier TTS (best to worst quality):
      1. edge-tts — Microsoft Neural TTS. 100% human-sounding English voice.
                    Requires internet. No API key needed.
      2. gTTS     — Google Text-to-Speech. Clear English. Requires internet.
      3. pyttsx3  — Offline fallback. Lower quality but always works.

    Runs in a background thread so it never blocks the face animation.
    """

    # Microsoft Neural voice — sounds fully human
    EDGE_VOICE = 'en-US-GuyNeural'   # natural male; swap to 'en-US-JennyNeural' for female

    def __init__(self, prefer_online: bool = True, lang: str = 'en'):
        self.lang          = lang
        self.prefer_online = prefer_online
        self._queue        = queue.Queue()
        self._speaking     = False
        self._backend      = None   # 'edge', 'gtts', 'pyttsx3', or None
        self._pyttsx_eng   = None
        self._pygame_ready = False

        self._init_backends()

        self._thread = threading.Thread(target=self._worker, daemon=True, name='TTS-Worker')
        self._thread.start()
        print(f"[TTS] Started — backend: {self._backend}")

    # ── Init ─────────────────────────────────────────────────────────────────

    def _init_backends(self):
        # 1. Try edge-tts (Microsoft Neural — most human)
        if self.prefer_online:
            try:
                import edge_tts  # noqa: F401
                import pygame
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                self._pygame_ready = True
                self._backend = 'edge'
                return
            except ImportError:
                print("[TTS] edge-tts not installed — trying gTTS")
            except Exception as e:
                print(f"[TTS] edge-tts/pygame init failed ({e}) — trying gTTS")

        # 2. Try gTTS (Google, clear English)
        if self.prefer_online and self._backend is None:
            try:
                from gtts import gTTS  # noqa: F401
                import pygame
                if not self._pygame_ready:
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                    self._pygame_ready = True
                self._backend = 'gtts'
                return
            except ImportError:
                print("[TTS] gTTS not installed — falling back to pyttsx3")
            except Exception as e:
                print(f"[TTS] gTTS/pygame init failed ({e}) — falling back to pyttsx3")

        # 3. pyttsx3 (offline fallback)
        self._init_pyttsx3()

    def _init_pyttsx3(self):
        try:
            import pyttsx3
            eng = pyttsx3.init()
            eng.setProperty('rate', 148)
            eng.setProperty('volume', 1.0)
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
            self._backend    = 'pyttsx3'
        except Exception as e:
            print(f"[TTS] pyttsx3 init failed: {e}")
            self._backend = None

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
                if self._backend == 'edge':
                    self._speak_edge(text)
                elif self._backend == 'gtts':
                    self._speak_gtts(text)
                elif self._backend == 'pyttsx3' and self._pyttsx_eng:
                    self._speak_pyttsx3(text)
                else:
                    print(f"[TTS] (no backend) {text}")
            except Exception as e:
                print(f"[TTS] Error: {e}")
                # cascade fallback
                try:
                    if self._backend == 'edge':
                        self._speak_gtts(text)
                    elif self._pyttsx_eng:
                        self._speak_pyttsx3(text)
                except Exception:
                    pass
            finally:
                self._speaking = False

    # ── edge-tts backend (Microsoft Neural — 100% human) ─────────────────────

    def _speak_edge(self, text: str):
        import edge_tts
        import pygame

        fd, tmp_path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)

        async def _save():
            comm = edge_tts.Communicate(text, self.EDGE_VOICE)
            await comm.save(tmp_path)

        asyncio.run(_save())

        try:
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.04)
        finally:
            try:
                pygame.mixer.music.unload()
                os.unlink(tmp_path)
            except Exception:
                pass

    # ── gTTS backend ──────────────────────────────────────────────────────────

    def _speak_gtts(self, text: str):
        from gtts import gTTS
        import pygame

        tts = gTTS(text=text, lang=self.lang, slow=False)

        fd, tmp_path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)
        tts.save(tmp_path)

        try:
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.04)
        finally:
            try:
                pygame.mixer.music.unload()
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