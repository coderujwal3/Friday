import datetime as dt
import getpass
import json
import os
import platform
import shutil
import subprocess
import webbrowser
import time
import re
import psutil
import pyautogui as pg
from pathlib import Path
from dotenv import load_dotenv

from friday.config import AssistantConfig
from friday.tools.registry import Tool, ToolRegistry
from friday.speaker import Speaker
# from friday.tools.conversation import ConversationHandler
from friday.tools.read_writeOp import read_write_operation

load_dotenv()

CONTACT_BOOK = {
    "mummy": os.getenv("MUMMY"),
    "sister": os.getenv("SISTER"),
    "myself": os.getenv("MYSELF"),
    
    # group contacts
    "multiverse walkers": os.getenv("MULTIVERSEWALKERS")
}


def _open_command(target: str) -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return ["cmd", "/c", "start", "", target]
    if system == "darwin":
        return ["open", target]
    return ["xdg-open", target]


def build_default_registry(config: AssistantConfig) -> ToolRegistry:
    registry = ToolRegistry()
    speaker = Speaker()
    
    # Create instance of read_write_operation
    read_write_op = read_write_operation(speaker)

    # Create screenshots folder if not exist
    DEFAULT_SCREENSHOT_DIR = os.path.join(os.path.expanduser("~"), "Friday_Screenshots")
    os.makedirs(DEFAULT_SCREENSHOT_DIR, exist_ok=True)

    # utilities methods (launch any command, check application is open or not, finding any directory or file, etc.)
    def launch(command: list[str], success_message: str) -> str:
        executable = command[0]
        if shutil.which(executable) is None:
            speaker.say(f"Matched the tool, but '{executable}' is not installed on this machine.")
            return f"Matched the tool, but '{executable}' is not installed on this machine."
        subprocess.Popen(command)
        return success_message
    
    def is_open(program: str) -> bool:
        dictionary = {
            "chrome": ["chrome.exe", "chrome", "google-chrome"],
            "code": ["code.exe", "code", "visual studio code"],
            "whatsapp": ["WhatsApp.exe", "WhatsApp.Root.exe", "WhatsApp"],
            "notepad": ["Notepad.exe", "notepad.exe", "notepad"],
        }

        if program in dictionary:
            # Iterate through all running processes
            for proc in psutil.process_iter(['name']):
                try:
                    # Check if any running process name matches the program
                    if proc.info['name'].lower() in dictionary[program]:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return False
        else:
            speaker.say("Application is already closed. If not then check codebase (is_open() function)")
            return False


    def _get_chrome_local_state_path() -> Path | None:
        username = getpass.getuser()
        if platform.system().lower() == "windows":
            return Path("C:/Users") / username / "AppData/Local/Google/Chrome/User Data/Local State"

        mac_path = Path("/Users") / username / "Library/Application Support/Google/Chrome/Local State"
        if mac_path.exists():
            return mac_path

        linux_path = Path("/home") / username / ".config/google-chrome/Local State"
        return linux_path if linux_path.exists() else None

    def _load_chrome_profiles() -> dict[str, str]:
        local_state_path = _get_chrome_local_state_path()
        if not local_state_path or not local_state_path.exists():
            return {}

        try:
            with local_state_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

        profiles = data.get("profile", {}).get("info_cache", {})
        return {
            folder_name.lower(): profile_info.get("name", folder_name)
            for folder_name, profile_info in profiles.items()
        }

    def _find_chrome_profile_name(query: str, profiles: dict[str, str]) -> str | None:
        query_lower = query.lower()
        for folder_name, display_name in profiles.items():
            if folder_name in query_lower or display_name.lower() in query_lower:
                return folder_name
        return None


    def find_folder(target_folder_name, search_path):
        target_name = (target_folder_name or "").strip().lower()
        if not target_name or not search_path:
            return []

        all_paths = []
        seen = set()
        for root, dirs, _ in os.walk(search_path):
            for directory in dirs:
                if directory.lower() == target_name:
                    path = os.path.join(root, directory)
                    if path not in seen:
                        all_paths.append(path)
                        seen.add(path)
        return all_paths

    


    # functionality methods (open, close, etc.)
    ## open methods
    def open_code(_: str) -> str:
        candidates = ["open code", "open vs code", "open visual studio code", "open friday code", "open IDE"]
        for candidate in candidates:
            if shutil.which(candidate) is not None:
                if candidate in ["friday project open karo", "open friday code", "open friday project", "friday project kholo", "apna code kholo", "vs code me friday ko open karo"]:
                    project_path = "E://Programming/Virtual_Voice_Assistant/Friday/"
                    if os.path.exists(project_path):
                        # system = platform.system().lower()
                        # command = ["subprocess.run(['explorer', os.path.normpath(path)])"] if system == "windows" else [subprocess.run(["xdg-open", project_path])]
                        command = ["code", project_path]
                        speaker.say("Opening Friday Code in visual studio code IDE")
                        return launch(command, "Opening Friday Assistant Project in IDE")
                    else:
                        speaker.say("Friday Project's Path is not missing, it might get changed")
                        return "Friday Project Path is missing"
                else:
                    subprocess.Popen([candidate])
                    speaker.say("Opening VS Code IDE")
                    return "Opening Visual Studio Code IDE"

    def open_chrome(asks: str) -> str:
        chrome_path = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
        if not chrome_path.exists():
            return launch(["C:/Program Files/Google/Chrome/Application/chrome.exe", "--profile-Directory=Default"],"Opening Default Chrome")

        asks_lower = asks.lower() if asks else ""
        profiles = _load_chrome_profiles()
        selected_profile = _find_chrome_profile_name(asks_lower, profiles)

        args = [str(chrome_path)]
        if selected_profile:
            args.append(f"--profile-directory={selected_profile}")
            speaker.say(f"Opening Chrome profile {profiles[selected_profile]}")
            return subprocess.Popen(args) and f"Opening Chrome profile {profiles[selected_profile]}."

        speaker.say("Opening Chrome default profile")
        subprocess.Popen(args + ["--profile-directory=Default"])
        return "Opening Chrome default profile."

    
    def open_youtube(_:str) -> str:
        candidates = ["youtube", "YT", "open youtube", "open YT"]
        for candidate in candidates:
            if shutil.which(candidate) is not None:
                speaker.say("Opening YouTube")
                return "Opening Youtube."
        return launch(_open_command("https://www.youtube.com"), "Opening YouTube in your default browser.")
    
    def open_instagram(_:str) -> str:
        candidates = ["open ig", "IG", "open instagram", "open insta", "insta"]
        for candidate in candidates:
            if shutil.which(candidate) is not None:
                speaker.say("Opening Instagram")
                return "Opening Instagram."
        return launch(_open_command("https://www.instagram.com"), "Opening Instagram in your default browser")

    def open_notepad(_: str) -> str:
        system = platform.system().lower()
        command = ["notepad"] if system == "windows" else ["xdg-open", str(Path.home())]
        speaker.say("Opening notes app")
        return launch(command, "Opening notes.")
    
    def open_whatsapp(_:str) -> str:
        system = platform.system().lower()
        command = ["cmd", "/C", "start whatsapp://"] if system == "windows" else ["xdg-open", "whatsapp://"]
        speaker.say("Opening WhatsApp")
        return launch(command, "Opening WhatsApp.")
    
    ## close methods
    def close_whatsapp(_: str) -> str:
        print("Closing WhatsApp Application.")
        if is_open("whatsapp"):
            speaker.say("Closing WhatsApp application")
            try:
                result = subprocess.run(
                    ["taskkill", "/f", "/t", "/im", "WhatsApp.Root.exe"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    result = subprocess.run(
                        ["taskkill", "/f", "/t", "/im", "WhatsApp.exe"],
                        capture_output=True,
                        text=True,
                    )
                if result.returncode != 0:
                    return f"Failed to close WhatsApp: {result.stderr.strip()}"
            except Exception as e:
                speaker.say("There was an error closing WhatsApp.")
                return f"WhatsApp issue (close_whatsapp): {e}"
        return "WhatsApp Application closed."
    
    def close_code(_: str) -> str:
        print("Closing Visual Studio Code IDE")
        if is_open("code"):
            try:
                speaker.say("Closing VS Code IDE")
                os.system("taskkill /f /im code.exe")
            except Exception as e:
                speaker.say("Failed to close VS Code IDE")
                return "Failed to close IDE: close_code"
        return "Closed VS Code IDE"
    
    def close_notepad(_: str) -> str:
        print("Closing Notepad.")
        if is_open("notepad"):
            speaker.say("Closing Notepad")
            time.sleep(2)
            try:
                os.system("taskkill /f /im notepad.exe")
            except Exception as e:
                speaker.say("Notepad is not open, or there is any error in function")
                return "Notepad issue (close_notepad)"
        return "Notepad closed."

    def close_chrome(_: str) -> str:
        print("Closing Chrome.")
        if is_open("chrome"):
            speaker.say("Closing Chrome")
            time.sleep(2)
            try:
                os.system("taskkill /f /im chrome.exe")
            except Exception as e:
                speaker.say("Chrome is not open, or there is any error in function")
                return "Chrome issue (close_chrome)"
        return "Google Chrome closed."
    
    def close_chrome_tabs(_:str) -> str:
        if is_open("chrome"):
            time.sleep(1.5)
            try:
                open_chrome("open chrome")
                pg.hotkey("ctrl","shift","w")
                speaker.say("Closed All tabs")
                return "Closed all tabs"
            except Exception as e:
                speaker.say("There is any issue in closing all tabs")
                return "There is any issue in closing all tabs"
        speaker.say("Chrome Browser is already closed")
        return "Chrome browser is already closed"

    # complex methods
    ## send whatsapp message
    def send_whatsapp_msg(query: str) -> str:
        query_lower = query.lower().strip()
        if not query_lower:
            return "I could not understand who to send the WhatsApp message to."

        # Match the longest contact name first to avoid prefix collisions
        # like "multiverse walkers" vs a shorter substring.
        recipient = None
        message = None
        for name in sorted(CONTACT_BOOK, key=len, reverse=True):
            pattern = rf"\b{re.escape(name)}\b"
            if re.search(pattern, query_lower):
                recipient = name
                break

        if recipient is None:
            speaker.say("Please specify a contact from the contact book, such as 'send whatsapp message to mummy'")
            return "Please specify a contact from the contact book, such as 'send whatsapp message to mummy'."

        # Extract message text after common trigger phrases.
        if "message to" in query_lower:
            message = query_lower.split("message to", 1)[1].strip()
            if recipient in message:
                message = message.replace(recipient, "").strip()
        elif "send whatsapp" in query_lower:
            message = query_lower.split("send whatsapp", 1)[1].strip()
            if recipient in message:
                message = message.replace(recipient, "").strip()
        else:
            message = query_lower.replace(recipient, "", 1).strip()

        if not message:
            speaker.say("Please tell me what message to send")
            return "Please tell me what message to send."

        destination = CONTACT_BOOK[recipient]
        if destination.startswith("+"):
            print(f"Sending personal message to {recipient} ({destination})...")
            speaker.say(f"Sending personal message to {recipient}")
            webbrowser.open(f"whatsapp://")
            time.sleep(5)
            webbrowser.open(f"whatsapp://send?phone={destination}&text={message}")
            time.sleep(6)
            pg.press("enter")
            speaker.say(f"Message sent to {recipient}")
            return f"Sent WhatsApp message to {recipient}."

        print(f"Sending group message to '{recipient}' ({destination})...")
        speaker.say(f"Sending Group message to '{recipient}")
        webbrowser.open(f"whatsapp://")
        time.sleep(3)

        pg.hotkey("ctrl","f")
        time.sleep(0.5)

        pg.write(recipient)
        time.sleep(1.5)

        pg.press("enter")
        pg.write(message)
        time.sleep(2.5)

        pg.press("enter")
        speaker.say(f"Sent WhatsApp group message to {recipient}.")
        return f"Sent WhatsApp group message to {recipient}."

    def take_screenshot(query: str) -> str:
        try:
            spoken_query = (query or "").strip()
            speaker.say("I’m taking the screenshot now.")

            directory_name = None
            file_name = None

            if spoken_query:
                directory_match = re.search(r"\b(?:in|inside|folder|directory|path)\s+(?:the\s+)?([a-zA-Z0-9 _.-]+)", spoken_query, re.I)
                if directory_match:
                    directory_name = directory_match.group(1).strip()

                name_match = re.search(r"\b(?:name|named|call it|called|title|save as)\s+(?:it\s+)?([a-zA-Z0-9 _.-]+)", spoken_query, re.I)
                if name_match:
                    file_name = name_match.group(1).strip()

            if not file_name:
                file_name = f"screenshot_IMG{int(time.time())}"

            filename = f"{file_name}.png" if not file_name.lower().endswith(".png") else file_name

            resolved_dir = None
            search_roots = []
            home_dir = Path.home()
            search_roots.append(str(home_dir))

            if platform.system().lower() == "windows":
                for root in [home_dir / "Desktop", home_dir / "Documents", home_dir / "Downloads", Path("E:/")]:
                    if root.exists():
                        search_roots.append(str(root))
            else:
                for root in [home_dir / "Desktop", home_dir / "Documents", home_dir / "Downloads", Path("/tmp")]:
                    if root.exists():
                        search_roots.append(str(root))

            if directory_name:
                cleaned_dir = re.sub(r"^(the|a|an)\s+", "", directory_name, flags=re.I).strip()
                for root in search_roots:
                    candidate = Path(root) / cleaned_dir
                    if candidate.exists() and candidate.is_dir():
                        resolved_dir = str(candidate)
                        break

                if not resolved_dir:
                    for root in search_roots:
                        found = find_folder(cleaned_dir, root)
                        if found:
                            resolved_dir = found[0]
                            break

            if not resolved_dir:
                resolved_dir = DEFAULT_SCREENSHOT_DIR
                if directory_name:
                    speaker.say(f"I could not find '{directory_name}', so I'm saving it to the default screenshot folder.")
                else:
                    speaker.say("No folder was specified, so I'm saving it to the default screenshot folder.")
            else:
                # speaker.say(f"Saving the screenshot in {resolved_dir}")
                print(f"Saving the screenshot in {resolved_dir}")

            os.makedirs(resolved_dir, exist_ok=True)
            path = os.path.join(resolved_dir, filename)
            img = pg.screenshot()
            img.save(path)
            # speaker.say(f"Screenshot saved to {path}")
            print(f"Screenshot saved to {path}")
            return f"Screenshot saved to {path}."

        except Exception as e:
            speaker.say("An unexpected error occurred while taking the screenshot.")
            print("Screenshot error:", e)
            return "An unexpected error occurred while taking the screenshot."

    # system methods    
    def current_time(_: str) -> str:
        speaker.say(f"The time is {dt.datetime.now().strftime('%I:%M %p')}")
        return f"The time is {dt.datetime.now().strftime('%I:%M %p')}."

    def shutdown(_: str) -> str:
        if config.dry_run_dangerous_tools:
            return "Shutdown matched, but dry-run mode is enabled."
        system = platform.system().lower()
        command = ["shutdown", "/s", "/t", "4"] if system == "windows" else ["shutdown", "now"]
        subprocess.Popen(command)

        speaker.say("Shutting down the computer")
        return "Shutting down the computer."
    


# Open Applications functionalities
    registry.register(Tool("open_code", "Open Visual Studio Code IDE", ["open code", "open visual studio code", "open vs code", "vs code open karo", "code kholo", "vs code kholo", "friday project open karo", "open friday code", "open friday project", "friday project kholo", "friday code kholo", "friday vs code open karo"], open_code))

    registry.register(Tool("open_chrome", "Open Chrome or the default browser.", ["open chrome", "launch browser", "start google chrome", "I need my browser", "chrome kholo", "browser", "browser open karo"], open_chrome))

    registry.register(Tool("open_youtube", "Open Youtube in default browser.", ["open Youtube", "open YT", "YT", "start youtube", "start YT", "Youtube kholo", "YT kholo", "youtube chalu karo"], open_youtube))

    registry.register(Tool("open_instagram", "Open Instagram in default browser.", ["open instagram", "launch instagram", "open IG", "open insta", "insta chalu karo", "instgram kholo"], open_instagram))
    
    registry.register(Tool("open_notepad", "Open a note-taking app or file browser.", ["open notepad", "start notes", "write a quick note"], open_notepad))

    registry.register(Tool("open_whatsapp", "Open a chat app or WhatsApp application", ["open whatsapp", "chat application", "start Whatsapp", "whatsapp kholo", "whatsapp chalu karo"], open_whatsapp))



# close functionalities
    registry.register(Tool("close_code", "Close the Visual Studio Code IDE", ["close IDE", "close vs code", "close visual studio code", "code band karo", "vs code band kardo", "IDE band karo"], close_code))

    registry.register(Tool("close_whatsapp", "Close the WhatsApp Application.", ["close whatsapp", "whatsapp band karo"], close_whatsapp))

    registry.register(Tool("close_chrome", "Close the Browser or Google Chrome.", ["Close chrome", "close google chrome","chrome band karo", "google chrome band karo", "chrome band kardo", "chrome profile band karo"], close_chrome))
    
    registry.register(Tool("close_notepad", "Close the Notepad Application.", ["close notepad", "notepad band karo", "notes application band karo", "notes app band karo"], close_notepad))

    registry.register(Tool("close_chrome_tabs", "Close all chrome browser tabs", ["Close All tabs", "sare tabs band kar do", "close each tabs", "close chrome tabs", "browser tabs band kardo"], close_chrome_tabs))



# utilities functionalities
    registry.register(Tool("current_time", "Tell the current local time.", ["what time is it", "tell me the time", "current time please", "time batao", "time kya hua hai", "current time batao"], current_time))
    
    # make dangerous "True" when you actually don't want to shutdown (mimic shutdown). If using False then understand that - all programs will be closed and the system will get shutdown --forcefully.
    registry.register(Tool("shutdown_pc", "Shutdown the computer.", ["shutdown pc", "power off computer", "power off system", "laptop band karo"], shutdown, dangerous=True))
    


# conversation functionalities
    # registry.register(Tool(
    #     "conversation",
    #     "Respond to greetings, small talk, and casual conversation.",
    #     ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "how are you", "what's up", "thanks", "thank you", "nice", "cool", "awesome", "interesting", "hey friday"],
    #     ConversationHandler.handle,
    # ))

## Write in file functionality
    registry.register(Tool(
        "read_write_operation", 
        "Perform write operations for file.", 
        ["write file", "file likho", "write", "likho", "write hello how are you and save as hello", "write hello how are you in file hello", "write hello how are you in file hello", "write hello how are you and save as hello", "write hello how are you in file hello and save as hello"],
        read_write_op.write_operation
    ))


# complex functionalities
    registry.register(Tool(
        "send_whatsapp_msg", "Send WhatsApp message to the directed person or group.", ["send message", "send whatsapp message", "message bhejo", "whatsapp message bhejo"],
        send_whatsapp_msg
    ))

    registry.register(Tool(
        "take_screenshot", "Take a screenshot and save it to the specified directory.", ["take screenshot", "capture screen", "screenshot le lo", "screen capture karo"],
        take_screenshot
    ))

    return registry