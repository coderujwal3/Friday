from friday.auth.face import FaceAuthenticator
from friday.auth.speaker import SpeakerVerifier
from friday.config import AssistantConfig
from friday.intent.router import IntentRouter
from friday.speaker import Speaker
from friday.speech.recognizer import MicrophoneCommandRecognizer, TextCommandRecognizer
from friday.tools.system_tools import build_default_registry
from friday.wake_word.detector import ConsoleWakeWordDetector, SpeechWakeWordDetector


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
            wake_query = self.wake_word.wait()
            if not self._authenticate():
                self.speaker.say("Authentication failed. Try again")
                continue

            if wake_query:
                query = wake_query
            else:
                query = ""

            while True:
                if not query:
                    query = self.recognizer.listen()
                if not query:
                    continue

                if self._is_pause_command(query):
                    self.speaker.say("Okay Boss, just call me when you need.")
                    break

                if self._is_shutdown_command(query):
                    self.speaker.say("Have a good day sir, goodbye")
                    return

                result = self.router.route(query)
                if result.tool_name is None:
                    self.speaker.say("I could not confidently match that command.")
                    query = ""
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

    def _authenticate(self) -> bool:
        voice_auth_result = self.speaker_verifier.verify(expected_user=self.user_name)
        if voice_auth_result:
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
                self.speaker.say(f"Welcome {authenticated_user}, how can I help?")
            elif authenticated:
                self.speaker.say("Welcome, how can I help?")

            return authenticated and voice_auth_result
