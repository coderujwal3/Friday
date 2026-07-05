import argparse
from dotenv import load_dotenv

from friday.assistant import FridayAssistant
from friday.config import AssistantConfig

load_dotenv()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Friday assistant.")
    parser.add_argument("--text-mode", action="store_true", help="Read commands from the terminal instead of microphone input.")
    parser.add_argument("--llm-router", action="store_true", help="Use an LLM as a fallback when embedding confidence is low.")
    parser.add_argument("--no-speech", action="store_true", help="Print responses without speaking them aloud.")
    parser.add_argument("--threshold", type=float, default=0.55, help="Minimum embedding confidence required to execute a tool.")
    parser.add_argument("--voice-threshold", type=float, default=0.50, help="Minimum speaker similarity required for voice verification.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = AssistantConfig(
        embedding_threshold=args.threshold,
        voice_threshold=args.voice_threshold,
    )
    assistant = FridayAssistant(
        config=config,
        text_mode=args.text_mode,
        llm_router=args.llm_router,
    )
    assistant.run()


if __name__ == "__main__":
    main()
