import importlib
import re
from dataclasses import dataclass
from typing import Iterable
from ..config import AssistantConfig


@dataclass
class WakeWordResult:
    command: str
    audio: bytes | None = None
    sample_rate: int | None = None


class ConsoleWakeWordDetector:
    """Simple text-mode wake-word detector for development."""

    def __init__(
        self,
        wake_phrases: Iterable[str] | None = None,
        pause_phrases: Iterable[str] | None = None,
    ):
        self.wake_phrases = [phrase.strip().lower() for phrase in (wake_phrases or ["friday"])]
        self.pause_phrases = [phrase.strip().lower() for phrase in (pause_phrases or [])]

    def wait(self) -> WakeWordResult:
        phrases = ", ".join(self.wake_phrases)
        print(f"Say/type one of the wake phrases: {phrases}")
        while True:
            text = input("> ").strip().lower()
            if not text:
                continue
            if self.is_wake_phrase(text):
                return WakeWordResult(command=self.extract_command(text))
            print("No wake phrase detected. Try again.")

    def is_wake_phrase(self, text: str) -> bool:
        normalized = self._normalize(text)
        return any(phrase in normalized for phrase in self.wake_phrases)

    def is_pause_phrase(self, text: str) -> bool:
        normalized = self._normalize(text)
        return any(phrase in normalized for phrase in self.pause_phrases)

    def extract_command(self, text: str) -> str:
        normalized = self._normalize(text)
        for phrase in sorted(self.wake_phrases, key=len, reverse=True):
            if normalized == phrase:
                return ""
            if normalized.startswith(f"{phrase} "):
                return normalized[len(phrase):].strip()
        return ""

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()


class SpeechWakeWordDetector(ConsoleWakeWordDetector):
    def __init__(
        self,
        wake_phrases: Iterable[str] | None = None,
        pause_phrases: Iterable[str] | None = None,
        timeout: float = 6.0,
        phrase_time_limit: float = 8.0,
    ):
        super().__init__(wake_phrases, pause_phrases)
        sr = importlib.import_module("speech_recognition")
        self.sr = sr
        self.recognizer = sr.Recognizer()
        self.timeout = timeout
        self.phrase_time_limit = phrase_time_limit

    def _is_shutdown_command(self, query: str) -> bool:
        normalized = " ".join(query.lower().split())
        shutdown_phrase = " ".join(AssistantConfig().shutdown_phrase.lower().split())
        return normalized in {"exit", "quit", "stop"} or shutdown_phrase in normalized

    def wait(self) -> WakeWordResult:
        print("Listening for the wake phrase...")
        while True:
            try:
                with self.sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=self.timeout, phrase_time_limit=self.phrase_time_limit)
                raw_wav = audio.get_wav_data()
                query = self.recognizer.recognize_google(audio, language="en-IN").strip().lower()
                print(f"Heard: {query}")
                if self.is_wake_phrase(query):
                    return WakeWordResult(command=self.extract_command(query), audio=raw_wav, sample_rate=16000)
                if self._is_shutdown_command(query):
                    return WakeWordResult(command=query, audio=raw_wav, sample_rate=16000)
                
            except self.sr.WaitTimeoutError:
                print("Waiting for the wake phrase...")
            except self.sr.UnknownValueError:
                print("Could not understand audio. Listening again...")
            except self.sr.RequestError as error:
                print(f"Speech recognition service error: {error}")
            except OSError as error:
                print(f"Microphone error: {error}")
            except Exception as error:
                print(f"Wake word listener error: {error}")
            # continue listening until a wake phrase is found