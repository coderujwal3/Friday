import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from friday.auth.speaker import SpeakerVerifier

def main() -> None:
    parser = argparse.ArgumentParser(description="Enroll a speaker voice into Friday's voice database.")
    parser.add_argument("name", help="Label for the enrolled speaker sample, e.g. 'ujwal_01'.")
    args = parser.parse_args()

    verifier = SpeakerVerifier()
    saved_path = verifier.enroll(args.name)
    if saved_path:
        print(f"Saved voice embedding to: {saved_path}")
    else:
        print("Enrollment failed. Please try again.")


if __name__ == "__main__":
    main()
