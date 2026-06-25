# Friday Assistant

Friday is a modular starter architecture for a Jarvis-style local assistant:

```text
main.py
  -> wake word detection
  -> face authentication
  -> speaker verification
  -> greeting
  -> speech/text command capture
  -> intent router
  -> function/tool execution
```

The important change from a large `if/elif` command block is the `IntentRouter`. It first uses local sentence embeddings to match natural language to registered tools. If confidence is low, it can ask an LLM router to choose the best tool.

## Quick start

```bash
cd Friday
python main.py --text-mode --skip-auth
```

Example commands:

- `open chrome`
- `launch my browser please`
- `open notepad`
- `what time is it`
- `shutdown pc` *(dry-run by default, change it to True to avoid dry-run)*
- `turn off assistant` *(stops Friday without shutting down the computer)*

Friday speaks responses by default. Do not pass `--no-speech`; if `pyttsx3` or
the Windows speech driver cannot start, the console now prints the exact TTS error.

## Optional LLM fallback

Set an API key and use `--llm-router`:

```bash
export OPENAI_API_KEY=...
python main.py --text-mode --llm-router
```

## Real auth/wake-word integrations

The current classes are intentionally split behind interfaces so you can replace the console/dev implementations with production backends:

- Wake word: OpenWakeWord
- Face auth: InsightFace
- Speaker verification: SpeechBrain ECAPA-TDNN
- Embeddings: SentenceTransformers `all-MiniLM-L6-v2`
- LLM router: OpenAI-compatible tool selection
