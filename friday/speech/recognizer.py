import importlib


class TextCommandRecognizer:
    def listen(self) -> str:
        return input("You: ").strip()


class MicrophoneCommandRecognizer:
    def __init__(self):
        sr = importlib.import_module("speech_recognition")
        self.sr = sr
        self.recognizer = sr.Recognizer()

    def listen(self) -> str:
        try:
            with self.sr.Microphone() as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = self.recognizer.listen(source, timeout=7, phrase_time_limit=12)
            print("Recognizing...")
            query = self.recognizer.recognize_google(audio, language="en-IN")
            print(f"You: {query}")
            return query.strip()
        except self.sr.WaitTimeoutError:
            print("No speech heard. Listening again...")
        except self.sr.UnknownValueError:
            print("Could not understand the audio. Listening again...")
        except self.sr.RequestError as error:
            print(f"Speech recognition service error: {error}")
        except OSError as error:
            print(f"Microphone error: {error}")
        except Exception as error:
            print(f"Voice input error: {error}. Listening again...")
        return ""
