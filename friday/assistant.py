from friday.auth.face import FaceAuthenticator
from friday.auth.speaker import SpeakerVerifier
from friday.config import AssistantConfig
from friday.intent.router import IntentRouter
from friday.speaker import Speaker
from friday.speech.recognizer import MicrophoneCommandRecognizer, TextCommandRecognizer
from friday.tools.system_tools import build_default_registry
from friday.wake_word.detector import ConsoleWakeWordDetector, SpeechWakeWordDetector, WakeWordResult


class FridayAssistant:
    def __init__(self, config: AssistantConfig, text_mode: bool, llm_router: bool):
        self.config = config
        self.speaker = Speaker()
        detector_cls = ConsoleWakeWordDetector if text_mode else SpeechWakeWordDetector
        self.wake_word = detector_cls(
            wake_phrases=self.config.wake_phrases,
            pause_phrases=self.config.pause_phrases,
        )
        self.speaker_verifier = SpeakerVerifier(config)
        self.recognizer = TextCommandRecognizer() if text_mode else MicrophoneCommandRecognizer()
        self.registry = build_default_registry(config)
        self.router = IntentRouter(self.registry, config, use_llm=llm_router)
        self.user_name = None

    def run(self) -> None:
        while True:
            self.speaker.say("Enabling Voice Authentication")
            wake_result = self.wake_word.wait()
            if not self._authenticate(raw_wav=wake_result.audio, sample_rate=wake_result.sample_rate):
                self.speaker.say("Authentication failed. Try again")
                continue

            query = wake_result.command or ""

            while True:
                if not query:
                    query = self.recognizer.listen()
                    continue

                if self._is_pause_command(query):
                    self.speaker.say("Okay Boss, just call me when you need.")
                    break

                if self._is_shutdown_command(query):
                    self.speaker.say("Have a good day boss, goodbye")
                    return

                result = self.router.route(query)
                a = 0   # --------------- jugaad - to avoid initial bug (just after verifying voice, the first command is not recognized properly, so this is a temporary fix)
                if result.tool_name is None and a:
                    self.speaker.say("I could not confidently match that command.")
                    query = ""
                    a += 1
                    continue

                message = self.registry.execute(result.tool_name, query)
                print(f"{message} Matched by {result.source} with confidence {result.confidence:.2f}.")
                query = ""

    def _is_shutdown_command(self, query: str) -> bool:
        normalized = " ".join(query.lower().split())
        shutdown_phrase = " ".join(self.config.shutdown_phrase.lower().split())
        return normalized in {"exit", "quit", "stop"} or shutdown_phrase in normalized

    def _is_pause_command(self, query: str) -> bool:
        normalized = " ".join(query.lower().split())
        return any(phrase in normalized for phrase in self.config.pause_phrases)

    def _authenticate(self, raw_wav: bytes | None = None, sample_rate: int | None = None) -> bool:
        voice_auth_result = self.speaker_verifier.verify(
            expected_user=self.user_name,
            raw_wav=raw_wav,
            sample_rate=sample_rate,
        )
        if voice_auth_result:
            self.speaker.say("Voice authentication successful, please see in your camera for face authentication.")
            face_auth_result = FaceAuthenticator.authenticate()
            authenticated = False
            authenticated_user = None

            if isinstance(face_auth_result, list) and len(face_auth_result) >= 1:
                authenticated = bool(face_auth_result[0])
                authenticated_user = face_auth_result[1]
            else:
                authenticated = bool(face_auth_result)

            if authenticated and authenticated_user:
                self.user_name = authenticated_user
                self.speaker.say(f"Welcome {authenticated_user} Boss, how can I help?")
            elif authenticated:
                self.speaker.say("Welcome Boss, how can I help?")

            return authenticated and voice_auth_result
