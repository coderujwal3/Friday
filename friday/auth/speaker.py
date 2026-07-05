import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import speech_recognition as sr
from scipy.io import wavfile
from scipy.signal import resample_poly
from speech_recognition import audio

from ..config import AssistantConfig


class SpeakerVerifier:
    """Silero VAD-based audio capture plus SpeechBrain ECAPA-TDNN speaker verification."""

    def __init__(self, config: Optional[AssistantConfig] = None):
        self.config = config if config is not None else AssistantConfig()
        self.voice_db_dir = Path(self.config.voice_db_dir) if self.config.voice_db_dir else Path(__file__).resolve().parent / "voice_db"
        self.voice_db_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rate = 16000
        self._voice_db = self._load_voice_embeddings()
        self._speechbrain_model = None
        self._vad_model = None
        self._vad_utils = None

    def verify(self, expected_user: Optional[str] = None, raw_wav: Optional[bytes] = None, sample_rate: Optional[int] = None) -> bool:
        expected_user = (expected_user or self.config.user_name or "").strip().lower()
        if not expected_user:
            print("Voice verification failed: expected username is not configured.")
            return False
        if not self._voice_db:
            print(f"Voice verification failed: no enrolled voice embeddings found in {self.voice_db_dir}")
            return False

        if raw_wav is None or sample_rate is None:
            print("Starting voice verification. Please say a short phrase after the beep.")
            audio, sample_rate = self._record_microphone_sample(duration=2)
            if audio is None:
                return False
        else:
            audio, sample_rate = self._decode_audio_bytes(raw_wav)
            if audio is None:
                print("Voice verification failed: could not decode wake-word audio.")
                return False

        voice_segment = self._extract_voice_segment(audio, sample_rate)
        if voice_segment is None or len(voice_segment) < self.sample_rate // 2:
            print("Voice verification failed: could not detect a valid speech segment.")
            return False

        embedding = self._compute_embedding(voice_segment)
        if embedding is None:
            return False

        best_user, best_similarity = self._find_best_match(embedding)
        if best_user is None:
            print("Voice verification failed: no matching enrolled voice found.")
            return False

        print(f"Best voice match: {best_user} ({best_similarity:.2f})")
        if best_user.lower() != expected_user.lower():
            print(f"Voice verification failed: speaker does not match expected user '{expected_user}'.")
            return False

        if best_similarity < self.config.voice_threshold:
            print(
                f"Voice verification failed: similarity {best_similarity:.2f} is below threshold {self.config.voice_threshold:.2f}."
            )
            return False

        print("Voice verification successful.")
        return True

    def enroll(self, sample_label: str, duration: int = 2) -> Optional[Path]:
        sample_label = sample_label.strip().replace(" ", "_")
        if not sample_label:
            print("Enrollment failed: please provide a non-empty label.")
            return None

        audio, sample_rate = self._record_microphone_sample(duration=duration)
        if audio is None:
            return None

        voice_segment = self._extract_voice_segment(audio, sample_rate)
        if voice_segment is None:
            print("Enrollment failed: no speech detected in the recording.")
            return None

        embedding = self._compute_embedding(voice_segment)
        if embedding is None:
            return None

        output_file = self.voice_db_dir / f"{sample_label}.npy"
        np.save(output_file, embedding.astype(np.float32))
        print(f"Saved enrolled embedding at {output_file}")
        self._voice_db = self._load_voice_embeddings()
        return output_file

    def _load_voice_embeddings(self) -> Dict[str, List[np.ndarray]]:
        embeddings: Dict[str, List[np.ndarray]] = {}
        if not self.voice_db_dir.exists():
            print(f"Voice DB directory does not exist: {self.voice_db_dir}")
            return embeddings

        npy_files = list(sorted(self.voice_db_dir.glob("*.npy")))
        print(f"Found {len(npy_files)} .npy files in {self.voice_db_dir}")

        for path in npy_files:
            try:
                vector = np.load(path)
                # print(f"Loaded {path.name}: shape={vector.shape}, dtype={vector.dtype}")
            except Exception as e:
                print(f"Failed to load {path.name}: {e}")
                continue
            if vector.ndim != 1:
                print(f"Skipping {path.name}: expected 1D, got {vector.ndim}D")
                continue
            user = path.stem
            if "_" in user:
                user = user.split("_")[0]
            user = user.lower()
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
                embeddings.setdefault(user, []).append(vector)
                # print(f"Added {path.name} to user '{user}' (norm={norm:.4f})")
            else:
                print(f"Skipping {path.name}: zero norm")

        print(f"Loaded embeddings for users: {list(embeddings.keys())}")
        return embeddings

    def _record_microphone_sample(self, duration: int = 2) -> Tuple[Optional[np.ndarray], Optional[int]]:
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
                print("Recording voice sample...")
                audio = recognizer.record(source, duration=duration)
            raw_wav = audio.get_wav_data()
            return self._decode_audio_bytes(raw_wav)
        except Exception as error:
            print(f"Audio capture failed: {error}")
            return None, None

    def _decode_audio_bytes(self, raw_wav: bytes) -> Tuple[Optional[np.ndarray], Optional[int]]:
        try:
            sample_rate, waveform = wavfile.read(io.BytesIO(raw_wav))
            waveform = self._normalize_waveform(waveform)
            if sample_rate != self.sample_rate:
                waveform = self._resample_waveform(waveform, sample_rate, self.sample_rate)
                sample_rate = self.sample_rate
            return waveform, sample_rate
        except Exception as error:
            print(f"Audio decode failed: {error}")
            return None, None

    def _normalize_waveform(self, waveform: np.ndarray) -> np.ndarray:
        if waveform.dtype != np.float32:
            waveform = waveform.astype(np.float32)
        if waveform.ndim > 1:
            waveform = waveform.mean(axis=1)
        peak = np.max(np.abs(waveform))
        if peak > 0:
            waveform = waveform / peak
        return waveform

    def _resample_waveform(self, waveform: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
        if original_rate == target_rate:
            return waveform
        gcd = np.gcd(original_rate, target_rate)
        up = target_rate // gcd
        down = original_rate // gcd
        return resample_poly(waveform, up, down)

    def _ensure_vad_model(self) -> bool:
        if self._vad_model is not None and self._vad_utils is not None:
            return True
        try:
            import torch
            self._vad_model, self._vad_utils = torch.hub.load(
                "snakers4/silero-vad",
                "silero_vad",
                force_reload=False,
            )
            return True
        except Exception as error:
            print(f"Silero VAD model load failed: {error}")
            return False

    def _get_speech_timestamps(self, audio: np.ndarray, sample_rate: int) -> List[Dict[str, int]]:
        if not self._ensure_vad_model():
            return []
        import torch

        audio_tensor = torch.from_numpy(audio).float()
        get_speech_timestamps = self._vad_utils[0]
        try:
            timestamps = get_speech_timestamps(audio_tensor, self._vad_model, sampling_rate=sample_rate)
        except Exception:
            timestamps = get_speech_timestamps(audio_tensor, self._vad_model, sample_rate)
        return timestamps

    def _extract_voice_segment(self, audio: np.ndarray, sample_rate: int) -> Optional[np.ndarray]:
        timestamps = self._get_speech_timestamps(audio, sample_rate)
        if not timestamps:
            return None
        longest_segment = max((audio[int(ts["start"]): int(ts["end"])] for ts in timestamps), key=len, default=None)
        if longest_segment is None or len(longest_segment) < sample_rate // 2:
            return None
        return self._reduce_noise(longest_segment, sample_rate)

    def _reduce_noise(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        try:
            import noisereduce as nr
            noise_clip = audio[: min(len(audio), sample_rate // 4)]
            return nr.reduce_noise(
                y=audio,
                sr=sample_rate,
                y_noise=noise_clip,
                prop_decrease=0.9,
            )
        except Exception as error:
            print(f"Noise reduction failed; using original audio instead: {error}")
            return audio

    def _ensure_speechbrain_model(self):
        if self._speechbrain_model is not None:
            return True
        try:
            try:
                from speechbrain.inference import EncoderClassifier
            except ImportError:
                print("Import Error: speechbrain.inference import EncoderClassifier")

            self._speechbrain_model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
            )
            if hasattr(self._speechbrain_model, "pretrainer"):
                self._speechbrain_model.pretrainer.collect_in = None
            return True
        except Exception as error:
            print(f"SpeechBrain model load failed: {error}")
            return False

    def _compute_embedding(self, audio: np.ndarray) -> Optional[np.ndarray]:
        if not self._ensure_speechbrain_model():
            return None
        import torch

        audio_tensor = torch.from_numpy(audio).unsqueeze(0)
        with torch.no_grad():
            embedding = self._speechbrain_model.encode_batch(audio_tensor)
        if embedding is None:
            return None
        vector = embedding.squeeze(0).cpu().numpy().flatten()
        norm = np.linalg.norm(vector)
        if norm <= 0:
            return None
        return vector / norm

    def _find_best_match(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        best_user = None
        best_similarity = -1.0
        for user, vectors in self._voice_db.items():
            for stored_vector in vectors:
                similarity = float(np.dot(stored_vector, embedding) / (np.linalg.norm(stored_vector) * np.linalg.norm(embedding) + 1e-10))
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_user = user
        return best_user, best_similarity
