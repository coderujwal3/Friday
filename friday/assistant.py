from friday.auth.face import FaceAuthenticator
from friday.auth.speaker import SpeakerVerifier
from friday.config import AssistantConfig
from friday.intent.router import IntentRouter
from friday.speaker import Speaker
from friday.speech.recognizer import MicrophoneCommandRecognizer, TextCommandRecognizer
from friday.tools.system_tools import build_default_registry
from friday.wake_word.detector import ConsoleWakeWordDetector


class FridayAssistant:
    def __init__(self, config: AssistantConfig, text_mode: bool, llm_router: bool):
        self.config = config
        self.speaker = Speaker()
        self.wake_word = ConsoleWakeWordDetector()
        self.speaker_verifier = SpeakerVerifier(config)
        self.recognizer = TextCommandRecognizer() if text_mode else MicrophoneCommandRecognizer()
        self.registry = build_default_registry(config)
        self.router = IntentRouter(self.registry, config, use_llm=llm_router)
        self.user_name = None

    def run(self) -> None:
        self.wake_word.wait()
        if not self._authenticate():
            self.speaker.say("Authentication failed. Try again")
            self.run()
            return
        while True:
            query = self.recognizer.listen()
            if not query:
                continue
            if self._is_shutdown_command(query):
                self.speaker.say("Have a good day sir, goodbye")
                return
            
            result = self.router.route(query)
            if result.tool_name is None:
                self.speaker.say("I could not confidently match that command.")
                continue
            message = self.registry.execute(result.tool_name, query)
            # self.speaker.say(f"{message} Matched by {result.source} with confidence {result.confidence:.2f}.")
            print(f"{message} Matched by {result.source} with confidence {result.confidence:.2f}.")

    def _is_shutdown_command(self, query: str) -> bool:
        normalized = " ".join(query.lower().split())
        shutdown_phrase = " ".join(self.config.shutdown_phrase.lower().split())
        return normalized in {"exit", "quit", "stop"} or shutdown_phrase in normalized

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
