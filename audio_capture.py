"""WASAPI loopback audio capture for Windows system audio."""

import threading
import queue
import time
import numpy as np

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    pyaudio = None

from utils import prepare_audio_for_whisper
from config import WHISPER_SAMPLE_RATE, AUDIO_CHUNK_MAX_SECONDS


class AudioCapture:
    """Captures system audio via WASAPI loopback and pushes processed chunks to a queue."""

    def __init__(self, audio_queue: queue.Queue, device_index: int | None = None):
        self.audio_queue = audio_queue
        self.device_index = device_index
        self._stop_event = threading.Event()
        self._pa = None

    def _get_loopback_device(self):
        """Find the default WASAPI loopback device or use the specified index."""
        self._pa = pyaudio.PyAudio()

        if self.device_index is not None:
            info = self._pa.get_device_info_by_index(self.device_index)
            print(f"[Audio] Using device: {info['name']}")
            return info

        # Use the default WASAPI loopback (mirrors default output)
        try:
            wasapi_info = self._pa.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            raise RuntimeError("WASAPI not available. This tool requires Windows.")

        default_speakers = self._pa.get_device_info_by_index(
            wasapi_info["defaultOutputDevice"]
        )

        # Find the loopback device for the default speakers
        for i in range(self._pa.get_device_count()):
            dev = self._pa.get_device_info_by_index(i)
            if dev.get("name", "").startswith(default_speakers["name"]):
                if dev.get("isLoopbackDevice", False):
                    print(f"[Audio] Loopback device: {dev['name']}")
                    return dev

        raise RuntimeError(
            f"Could not find loopback device for: {default_speakers['name']}. "
            "Ensure you have PyAudioWPatch installed (not regular PyAudio)."
        )

    @staticmethod
    def list_devices():
        """Print all available audio devices (for troubleshooting)."""
        if pyaudio is None:
            print("PyAudioWPatch not installed.")
            return
        pa = pyaudio.PyAudio()
        print("\nAvailable audio devices:")
        print("-" * 60)
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            loopback = " [LOOPBACK]" if dev.get("isLoopbackDevice", False) else ""
            print(f"  [{i}] {dev['name']}{loopback}")
            print(f"       Channels: {dev['maxInputChannels']}in/{dev['maxOutputChannels']}out  Rate: {int(dev['defaultSampleRate'])}Hz")
        print("-" * 60)
        pa.terminate()

    def run(self):
        """Main capture loop. Call from a thread."""
        if pyaudio is None:
            raise ImportError(
                "PyAudioWPatch is required. Install with: pip install PyAudioWPatch"
            )

        device = self._get_loopback_device()
        channels = int(device["maxInputChannels"])
        rate = int(device["defaultSampleRate"])
        sample_width = pyaudio.get_sample_size(pyaudio.paInt16)
        # Use paInt16 for broader compatibility; some loopback devices
        # don't support paFloat32 directly.
        audio_format = pyaudio.paInt16

        # How many frames per read — ~0.5 second chunks for responsiveness
        frames_per_buffer = int(rate * 0.5)

        print(f"[Audio] Capturing: {rate}Hz, {channels}ch, {sample_width * 8}-bit")
        print(f"[Audio] Resampling to {WHISPER_SAMPLE_RATE}Hz mono for Whisper")

        stream = self._pa.open(
            format=audio_format,
            channels=channels,
            rate=rate,
            input=True,
            input_device_index=int(device["index"]),
            frames_per_buffer=frames_per_buffer,
        )

        buffer = bytearray()
        max_buffer_bytes = int(
            AUDIO_CHUNK_MAX_SECONDS * rate * channels * sample_width
        )
        # Minimum audio to send (2 seconds worth) to avoid tiny useless chunks
        min_buffer_bytes = int(2 * rate * channels * sample_width)

        try:
            while not self._stop_event.is_set():
                try:
                    data = stream.read(frames_per_buffer, exception_on_overflow=False)
                except OSError:
                    continue

                buffer.extend(data)

                # Check if we have enough audio to process
                if len(buffer) >= max_buffer_bytes:
                    self._push_chunk(bytes(buffer), sample_width, channels, rate)
                    buffer.clear()
                elif len(buffer) >= min_buffer_bytes:
                    # Check for silence (low energy) to find natural break points
                    recent = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                    energy = np.sqrt(np.mean(recent ** 2))
                    if energy < 200:  # silence threshold
                        self._push_chunk(bytes(buffer), sample_width, channels, rate)
                        buffer.clear()

        finally:
            stream.stop_stream()
            stream.close()
            # Flush remaining buffer
            if len(buffer) >= min_buffer_bytes:
                self._push_chunk(bytes(buffer), sample_width, channels, rate)
            if self._pa:
                self._pa.terminate()
            print("[Audio] Capture stopped.")

    def _push_chunk(self, raw_bytes: bytes, sample_width: int, channels: int, rate: int):
        """Convert raw audio and push to the queue."""
        audio = prepare_audio_for_whisper(raw_bytes, sample_width, channels, rate, WHISPER_SAMPLE_RATE)
        if len(audio) > 0:
            self.audio_queue.put(audio)

    def stop(self):
        """Signal the capture loop to stop."""
        self._stop_event.set()
