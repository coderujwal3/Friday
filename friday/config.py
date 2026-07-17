from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AssistantConfig:
    assistant_name: str = "Friday"
    user_name: str = "Ujwal"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_threshold: float = 0.60
    llm_model: str = "gpt-4.1-mini"
    shutdown_phrase: str = "turn off assistant"
    wake_phrases: tuple[str, ...] = field(default_factory=lambda: (
        "hey friday",
        "hi friday",
        "wake up friday",
        "jago friday",
        "get up friday",
        "let's get to the work",
        "let's start the work",
        "good morning friday",
        "good noon friday",
        "good evening friday",
    ))
    pause_phrases: tuple[str, ...] = field(default_factory=lambda: (
        "stop listening friday",
        "pause friday",
        "go to sleep friday",
        "stop listening",
        "go to sleep",
        "good night friday",
    ))
    dry_run_dangerous_tools: bool = True               # False: if really want to shutdown the pc, False: if you want to just mimic the shutdown process (do not shuts the pc)
    voice_db_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent / "auth" / "voice_db")
    voice_threshold: float = 0.50
    data_dir: Path = field(default_factory=lambda: Path.home() / ".friday")
