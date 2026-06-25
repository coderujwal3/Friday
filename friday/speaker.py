import importlib
import importlib.util
import os


class Speaker:
    def say(self, text: str) -> None:
        if not text:
            return
        print(f"[Friday]: {text}")
        try:
            pyttsx3 = importlib.import_module("pyttsx3")
            engine =  pyttsx3.init('sapi5' if os.name == 'nt' else None)
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[1].id)
            engine.setProperty('rate', 160)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print("TTS error:", e)
            