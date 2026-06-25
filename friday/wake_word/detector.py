class ConsoleWakeWordDetector:
    """Development wake-word detector; replace with OpenWakeWord in production."""

    def __init__(self, wake_word: str = "friday"):
        self.wake_word = wake_word.lower()

    def wait(self) -> None:
        print(f"Say/type '{self.wake_word}' to wake the assistant.")
        while True:
            text = input("> ").strip().lower()
            if self.wake_word in text:
                return