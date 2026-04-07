"""Real-time transcription using faster-whisper."""

import threading
import queue
import time

from config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_BEAM_SIZE,
    WHISPER_VAD_FILTER,
    SOURCE_LANGUAGE,
)


class Transcriber:
    """Pulls audio chunks from a queue and produces English text segments."""

    def __init__(self, audio_queue: queue.Queue, text_queue: queue.Queue):
        self.audio_queue = audio_queue
        self.text_queue = text_queue
        self._stop_event = threading.Event()
        self._model = None

    def _load_model(self):
        """Load the faster-whisper model (downloads on first run)."""
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

        print(f"[Transcriber] Loading model '{WHISPER_MODEL}' on {device} ({compute_type})...")
        start = time.time()
        self._model = WhisperModel(
            WHISPER_MODEL,
            device=device,
            compute_type=compute_type,
        )
        elapsed = time.time() - start
        print(f"[Transcriber] Model loaded in {elapsed:.1f}s")

    def run(self):
        """Main transcription loop. Call from a thread."""
        self._load_model()

        while not self._stop_event.is_set():
            try:
                audio = self.audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            duration = len(audio) / 16000
            start = time.time()

            try:
                segments, info = self._model.transcribe(
                    audio,
                    language=SOURCE_LANGUAGE,
                    beam_size=WHISPER_BEAM_SIZE,
                    vad_filter=WHISPER_VAD_FILTER,
                    vad_parameters=dict(
                        min_silence_duration_ms=500,
                        speech_pad_ms=300,
                    ),
                )

                for segment in segments:
                    text = segment.text.strip()
                    if text:
                        self.text_queue.put({
                            "text": text,
                            "start": segment.start,
                            "end": segment.end,
                            "timestamp": time.time(),
                        })
            except Exception as e:
                print(f"[Transcriber] Error: {e}")
                continue

            elapsed = time.time() - start
            speed = duration / elapsed if elapsed > 0 else 0
            print(f"[Transcriber] {duration:.1f}s audio → {elapsed:.1f}s processing ({speed:.1f}x realtime)")

        print("[Transcriber] Stopped.")

    def stop(self):
        """Signal the transcription loop to stop."""
        self._stop_event.set()
