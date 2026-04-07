"""Offline processing pipeline for audio/video files."""

import os
import time
import numpy as np

from config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_BEAM_SIZE,
    SOURCE_LANGUAGE,
    TARGET_LANGUAGE,
    WHISPER_SAMPLE_RATE,
)
import subtitle_writer


class FileProcessor:
    """Processes audio files: transcribe + translate + generate subtitles."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self._model = None

    def _load_model(self):
        from faster_whisper import WhisperModel

        device = WHISPER_DEVICE
        compute_type = WHISPER_COMPUTE_TYPE

        if device == "auto":
            try:
                import ctranslate2
                if "cuda" in ctranslate2.get_supported_compute_types("cuda"):
                    device = "cuda"
                    compute_type = "float16"
                else:
                    device = "cpu"
            except Exception:
                device = "cpu"

        print(f"[Processor] Loading model '{WHISPER_MODEL}' on {device} ({compute_type})...")
        start = time.time()
        self._model = WhisperModel(
            WHISPER_MODEL, device=device, compute_type=compute_type
        )
        print(f"[Processor] Model loaded in {time.time() - start:.1f}s")

    def _load_audio(self, audio_path: str) -> np.ndarray:
        """Load audio file into numpy array at 16kHz mono."""
        # Try using faster-whisper's built-in decoder (uses ffmpeg if available)
        try:
            from faster_whisper.audio import decode_audio
            audio = decode_audio(audio_path, sampling_rate=WHISPER_SAMPLE_RATE)
            return audio
        except Exception:
            pass

        # Fallback: try numpy for raw WAV
        import wave
        try:
            with wave.open(audio_path, "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                from utils import prepare_audio_for_whisper
                audio = prepare_audio_for_whisper(
                    frames,
                    wf.getsampwidth(),
                    wf.getnchannels(),
                    wf.getframerate(),
                    WHISPER_SAMPLE_RATE,
                )
                return audio
        except Exception:
            raise RuntimeError(
                f"Cannot load audio from {audio_path}. "
                "Install ffmpeg for broader format support."
            )

    def _transcribe(self, audio: np.ndarray) -> list[dict]:
        """Transcribe audio and return segments with timestamps."""
        duration = len(audio) / WHISPER_SAMPLE_RATE
        print(f"[Processor] Audio duration: {duration / 60:.1f} min")
        print(f"[Processor] Transcribing with '{WHISPER_MODEL}'...")

        start = time.time()
        segments_iter, info = self._model.transcribe(
            audio,
            language=SOURCE_LANGUAGE,
            beam_size=WHISPER_BEAM_SIZE,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500, speech_pad_ms=300),
        )

        segments = []
        last_print = 0
        for seg in segments_iter:
            text = seg.text.strip()
            if text:
                segments.append({
                    "text": text,
                    "start": seg.start,
                    "end": seg.end,
                })
                # Progress update every 30 seconds of audio
                if seg.end - last_print > 30:
                    pct = min(100, seg.end / duration * 100)
                    print(f"[Processor] {pct:5.1f}% ({seg.end:.0f}s / {duration:.0f}s) - {len(segments)} segments")
                    last_print = seg.end

        elapsed = time.time() - start
        speed = duration / elapsed if elapsed > 0 else 0
        print(f"[Processor] Transcription done: {len(segments)} segments in {elapsed:.0f}s ({speed:.1f}x realtime)")
        return segments

    def _translate(self, segments: list[dict]) -> list[dict]:
        """Translate all segments."""
        from deep_translator import GoogleTranslator

        translator = GoogleTranslator(source=SOURCE_LANGUAGE, target=TARGET_LANGUAGE)
        total = len(segments)
        print(f"[Processor] Translating {total} segments ({SOURCE_LANGUAGE}→{TARGET_LANGUAGE})...")

        for i, seg in enumerate(segments):
            try:
                seg["english"] = seg["text"]
                seg["spanish"] = translator.translate(seg["text"])
            except Exception as e:
                seg["english"] = seg["text"]
                seg["spanish"] = f"[error] {seg['text']}"
                print(f"[Processor] Translation error on segment {i + 1}: {e}")

            # Progress every 20 segments
            if (i + 1) % 20 == 0 or (i + 1) == total:
                pct = (i + 1) / total * 100
                print(f"[Processor] Translated {i + 1}/{total} ({pct:.0f}%)")

        return segments

    def process(self, audio_path: str, title: str = "transcript") -> list[str]:
        """Full pipeline: load → transcribe → translate → write files."""
        print()
        print("=" * 60)
        print(f"  Processing: {title}")
        print("=" * 60)

        self._load_model()

        # 1. Load audio
        print(f"[Processor] Loading audio: {audio_path}")
        audio = self._load_audio(audio_path)

        # 2. Transcribe
        segments = self._transcribe(audio)
        if not segments:
            print("[Processor] No speech detected.")
            return []

        # 3. Translate
        segments = self._translate(segments)

        # 4. Write output files
        print(f"[Processor] Writing output files...")
        files = subtitle_writer.write_all(segments, self.output_dir, title)

        print()
        print("=" * 60)
        print(f"  Done! {len(segments)} segments processed")
        print(f"  Output: {self.output_dir}/")
        for f in files:
            print(f"    {os.path.basename(f)}")
        print("=" * 60)

        return files
