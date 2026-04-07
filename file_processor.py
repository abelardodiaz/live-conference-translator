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
        try:
            from faster_whisper.audio import decode_audio
            audio = decode_audio(audio_path, sampling_rate=WHISPER_SAMPLE_RATE)
            return audio
        except Exception:
            pass

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
        print(f"[Processor] Transcribing with '{WHISPER_MODEL}' (lang={SOURCE_LANGUAGE})...")

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
                if seg.end - last_print > 30:
                    pct = min(100, seg.end / duration * 100)
                    print(f"[Processor] {pct:5.1f}% ({seg.end:.0f}s / {duration:.0f}s) - {len(segments)} segments")
                    last_print = seg.end

        elapsed = time.time() - start
        speed = duration / elapsed if elapsed > 0 else 0
        print(f"[Processor] Transcription done: {len(segments)} segments in {elapsed:.0f}s ({speed:.1f}x realtime)")
        return segments

    def _translate(self, segments: list[dict]) -> list[dict]:
        """Translate all segments using bulk batching to minimize API requests."""
        # Skip translation if source == target
        if SOURCE_LANGUAGE == TARGET_LANGUAGE:
            print(f"[Processor] Source = target ({SOURCE_LANGUAGE}), skipping translation.")
            for seg in segments:
                seg["source"] = seg["text"]
            return segments

        from deep_translator import GoogleTranslator

        translator = GoogleTranslator(source=SOURCE_LANGUAGE, target=TARGET_LANGUAGE)
        total = len(segments)

        # Batch segments into chunks of ~4500 chars to minimize requests
        CHAR_LIMIT = 4500
        batches = []
        current_batch = []
        current_len = 0

        for seg in segments:
            text = seg["text"]
            if current_len + len(text) + 1 > CHAR_LIMIT and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_len = 0
            current_batch.append(text)
            current_len += len(text) + 1

        if current_batch:
            batches.append(current_batch)

        print(f"[Processor] Translating {total} segments in {len(batches)} batches ({SOURCE_LANGUAGE}→{TARGET_LANGUAGE})...")

        translated_texts = []
        for i, batch in enumerate(batches):
            joined = "\n".join(batch)
            try:
                result = translator.translate(joined)
                parts = result.split("\n")
                # Handle case where Google merges/splits lines differently
                if len(parts) == len(batch):
                    translated_texts.extend(parts)
                else:
                    # Fallback: assign what we can, pad or trim
                    translated_texts.extend(parts[:len(batch)])
                    if len(parts) < len(batch):
                        translated_texts.extend(["[translation incomplete]"] * (len(batch) - len(parts)))
            except Exception as e:
                print(f"[Processor] Batch {i + 1} translation error: {e}")
                translated_texts.extend([f"[error] {t}" for t in batch])

            print(f"[Processor] Batch {i + 1}/{len(batches)} done")

        # Assign back to segments
        for seg, translated in zip(segments, translated_texts):
            seg["source"] = seg["text"]
            seg["translated"] = translated

        print(f"[Processor] Translation complete: {total} segments, {len(batches)} API requests")
        return segments

    def process(self, audio_path: str, title: str = "transcript") -> list[str]:
        """Full pipeline: load → transcribe → translate → write files."""
        print()
        print("=" * 60)
        print(f"  Processing: {title}")
        print(f"  Source: {SOURCE_LANGUAGE} | Target: {TARGET_LANGUAGE}")
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
        has_translation = SOURCE_LANGUAGE != TARGET_LANGUAGE
        print("[Processor] Writing output files...")
        files = subtitle_writer.write_all(
            segments,
            self.output_dir,
            title,
            source_lang=SOURCE_LANGUAGE,
            target_lang=TARGET_LANGUAGE if has_translation else None,
        )

        print()
        print("=" * 60)
        print(f"  Done! {len(segments)} segments processed")
        print(f"  Output: {self.output_dir}/")
        for f in files:
            print(f"    {os.path.basename(f)}")
        print("=" * 60)

        return files
