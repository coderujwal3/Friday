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


    # utilities methods (launch any command, check application is open or not, finding any directory or file, etc.)
    def launch(command: list[str], success_message: str) -> str:
        executable = command[0]
        if shutil.which(executable) is None:
            speaker.say(f"Matched the tool, but '{executable}' is not installed on this machine.")
            return f"Matched the tool, but '{executable}' is not installed on this machine."
        print(f"{("-"*20)} command for execution {command} {("-"*20)}")
        subprocess.Popen(command)
        return success_message
    
    def is_open(program: str) -> bool:
        dictionary = {
            "chrome": ["chrome.exe", "chrome", "google-chrome"],
            "code": ["code.exe", "code", "visual studio code"],
            "whatsapp": ["WhatsApp.exe", "WhatsApp.Root.exe", "WhatsApp"]
        }

        if program in dictionary:
            # Iterate through all running processes
            for proc in psutil.process_iter(['name']):
                try:
                    # Check if any running process name matches Chrome
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


    


    # functionality methods (open, close, etc.)
    ## open methods
    def open_code(_: str) -> str:
        candidates = ["open code", "open vs code", "open visual studio code", "open friday code", "open IDE"]
        for candidate in candidates:
            if shutil.which(candidate) is not None:
                if candidate in ["friday project open karo", "open friday code", "open friday project", "friday project kholo", "apna code kholo", "vs code me friday ko open karo"]:
                    project_path = "E://Programming/Virtual_Voice_Assistant/Friday/"
                    if os.path.exists(project_path):
                        system = platform.system().lower()
                        command = ["subprocess.run(['explorer', os.path.normpath(path)])"] if system == "windows" else [subprocess.run(["xdg-open", project_path])]
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
            time.sleep(2)
            try:
                os.system("taskkill /f /im WhatsApp.Root.exe")  # for WhatsApp Beta - if using WhatsApp then change it to: WhatsApp.exe
            except Exception as e:
                speaker.say("WhatsApp application is not open, or there is any error in function")
                return "WhatsApp issue (close_whatsapp)"
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
    registry.register(Tool("open_code", "Open Visual Studio Code IDE", ["open code", "open visual studio code", "open vs code", "vs code chalu karo", "code kholo", "vs code kholo", "friday project open karo", "open friday code", "open friday project", "friday project kholo", "apna code kholo", "vs code me friday ko open karo"], open_code))

    registry.register(Tool("open_chrome", "Open Chrome or the default browser.", ["open chrome", "launch browser", "start google chrome", "I need my browser", "chrome kholo", "browser", "browser chalu karo"], open_chrome))

    registry.register(Tool("open_youtube", "Open Youtube in default browser.", ["open Youtube", "open YT", "YT", "start youtube", "start YT", "Youtube kholo", "YT kholo", "youtube chalu karo"], open_youtube))

    registry.register(Tool("open_instagram", "Open Instagram in default browser.", ["open instagram", "launch instagram", "open IG", "open insta", "insta chalu karo", "instgram kholo"], open_instagram))
    
    registry.register(Tool("open_notepad", "Open a note-taking app or file browser.", ["open notepad", "start notes", "write a quick note"], open_notepad))

    registry.register(Tool("open_whatsapp", "Open a chat app or WhatsApp application", ["open whatsapp", "chat application", "start Whatsapp", "whatsapp kholo", "whatsapp chalu karo"], open_whatsapp))


# close functionalities
    registry.register(Tool("close_code", "Close the Visual Studio Code IDE", ["close IDE", "close vs code", "close visual studio code", "code band karo", "vs code band kardo", "IDE band karo"], close_code))

    registry.register(Tool("close_whatsapp", "Close the WhatsApp Application.", ["close whatsapp", "whatsapp band karo"], close_whatsapp))

    registry.register(Tool("close_chrome", "Close the Browser or Google Chrome.", ["Close chrome", "close google chrome","chrome band karo", "google chrome band karo", "chrome band kardo", "chrome profile band karo"], close_chrome))

    registry.register(Tool("close_chrome_tabs", "Close all chrome browser tabs", ["Close All tabs", "sare tabs band kar do", "close each tabs", "close chrome tabs", "browser tabs band kardo"], close_chrome_tabs))



# utilities functionalities
    registry.register(Tool("current_time", "Tell the current local time.", ["what time is it", "tell me the time", "current time please", "time batao", "time kya hua hai", "current time batao"], current_time))
    
    # make dangerous "True" when you actually don't want to shutdown (mimic shutdown). If using False then understand that - all programs will be closed and the system will get shutdown --forcefully.
    registry.register(Tool("shutdown_pc", "Shutdown the computer.", ["shutdown pc", "power off computer", "power off system", "laptop band karo"], shutdown, dangerous=False))
    



    # # Conversational tools for small talk and greetings
    # registry.register(Tool(
    #     "greeting",
    #     "Respond to greetings and hello.",
    #     ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "hey friday"],
    #     ConversationHandler.handle_greeting
    # ))
    
    # registry.register(Tool(
    #     "how_are_you",
    #     "Respond to questions about how you are doing.",
    #     ["how are you", "how are you doing", "how's it going", "how you doing", "you okay", "all okay", "you alright", "kaise ho"],
    #     ConversationHandler.handle_how_are_you
    # ))
    
    # registry.register(Tool(
    #     "what_up",
    #     "Respond to casual questions about what you're up to. You can update the response, don't try to copy paste the response",
    #     ["what's up", "whats up", "what you doing", "what have you done", "what you been doing", "kya kar rahe ho", "kya haal chaal bidu", "kaisa chal raha bro", "all exciting ?"],
    #     ConversationHandler.handle_what_up
    # ))
    
    # registry.register(Tool(
    #     "small_talk",
    #     "Respond to general small talk and casual conversation.",
    #     ["thanks", "thank you", "nice", "that's cool", "that sounds good", "interesting", "awesome", "good job"],
    #     ConversationHandler.handle_small_talk
    # ))


# complex functionalities
    registry.register(Tool(
        "send_whatsapp_msg", "Send WhatsApp message to the directed person or group.", ["send message", "send whatsapp message", "message bhejo", "whatsapp message bhejo"],
        send_whatsapp_msg
    ))

    return registry