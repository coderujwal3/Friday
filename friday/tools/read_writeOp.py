from pathlib import Path
from platform import platform
import re
import subprocess
import time
import platform

from click import launch
from friday import speaker
from friday.speaker import Speaker

class read_write_operation:
    def __init__(self, speaker_verifier: Speaker):
        self.speaker = speaker_verifier

    def open_notepad(self,_: str) -> None:
        system = platform.system().lower()
        command = ["notepad ."] if system == "windows" else ["xdg-open", str(Path.home())]
        self.speaker.say("Opening your file")
        subprocess.Popen(command)

    def write_operation(self,query: str) -> str:
        spoken_query = (query or "").strip()
        file_name = None
        content = ""

        if spoken_query:
            normalized_query = re.sub(r"^(?:write|likho)\s+", "", spoken_query, flags=re.I)
            normalized_query = re.sub(r"^it\s+", "", normalized_query, flags=re.I)

            name_match = re.search(r"\b(?:in file|and save as)\s+([a-zA-Z0-9 _.-]+)$", normalized_query, re.I)
            if name_match:
                file_name = name_match.group(1).strip()
                content = normalized_query[:name_match.start()].strip()
            else:
                content = normalized_query.strip()

        if not file_name:
            file_name = f"TXT{int(time.time())}"

        if not content:
            content = ""
            self.speaker.say("No content provided to write.")
            return "No content provided to write."

        filename = f"{file_name}.txt" if not file_name.lower().endswith(".txt") else file_name

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            self.speaker.say(f"File '{filename}' has been written successfully.")
        except Exception:
            self.speaker.say("The file is not opening, there is any issue")

        return "File is written successfully"
