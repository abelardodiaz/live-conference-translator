"""Central configuration for live-conference-translator."""

import os

# --- Whisper transcription ---
WHISPER_MODEL = os.environ.get("LCT_MODEL", "small")
# "auto" picks CUDA if available, else CPU
WHISPER_DEVICE = os.environ.get("LCT_DEVICE", "auto")
# int8 for CPU, float16 for CUDA
WHISPER_COMPUTE_TYPE = os.environ.get("LCT_COMPUTE", "int8")
WHISPER_BEAM_SIZE = 5
WHISPER_VAD_FILTER = True

# --- Languages ---
SOURCE_LANGUAGE = "en"
TARGET_LANGUAGE = "es"

# --- Audio capture ---
# Max seconds to buffer before forcing transcription (even without silence)
AUDIO_CHUNK_MAX_SECONDS = 30
# Sample rate expected by Whisper
WHISPER_SAMPLE_RATE = 16000

# --- Transcript output ---
TRANSCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcripts")

# --- Display ---
# "terminal" or "gui" (gui not yet implemented)
DISPLAY_MODE = "terminal"
