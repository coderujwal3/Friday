# Friday Voice DB

This directory stores speaker embeddings used by Friday's voice verification flow.

## How to use

1. Run the enrollment helper to record one or more examples of your voice.
2. The helper saves normalized speaker embeddings as `.npy` files in this directory.
3. During authentication, Friday uses Silero VAD + SpeechBrain ECAPA-TDNN to verify incoming audio against these embeddings.

## Recommended setup

- Enroll at least 5-10 recordings of your voice using the same microphone.
- Use consistent phrases and an environment similar to normal operation.
- Keep the file names meaningful, e.g. `ujwal_01.npy`, `ujwal_02.npy`, etc.
