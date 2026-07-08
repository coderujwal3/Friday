import re
import time
from friday.speaker import Speaker

class read_write_operation:
    def __init__(self, speaker_verifier: Speaker):
        self.speaker = speaker_verifier

    def write_operation(self,query: str) -> str:
        spoken_query = (query or "").strip()
        file_name = None
        content = ""

        if spoken_query:
            content_match = re.search(r"\b(?:|write|likho|)\s+(?:it\s+)?([a-zA-Z0-9 _.-]+)", spoken_query, re.I)
            name_match = re.search(r"\b(?:|in file|and save as|)\s+(?:it\s+)?([a-zA-Z0-9 _.-]+)", spoken_query, re.I)
            if name_match:
                file_name = name_match.group(1).strip()
            if content_match:
                content = content_match.group(1).strip()

        if not file_name:
            file_name = f"TXT{int(time.time())}"

        filename = f"{file_name}.txt" if not file_name.lower().endswith(".txt") else file_name

        try:
            with open(filename, "w") as f:
                f.write(content)
            self.speaker.say(f"File '{filename}' has been written successfully.")
        except Exception as e:
            self.speaker.say("The file is not opening, there is any issue")

        return "File is written successfully"
