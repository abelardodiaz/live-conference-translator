#!/usr/bin/env python3
"""Live Conference Translator — real-time system audio transcription and translation.

Captures system audio via WASAPI loopback, transcribes with faster-whisper,
translates EN→ES with Google Translate, and displays live in terminal.

Usage:
    python main.py                        # default (small model)
    python main.py --model medium         # better quality (needs more RAM/GPU)
    python main.py --model tiny           # fastest, lower quality
    python main.py --list-devices         # show available audio devices
    python main.py --device 5             # use specific audio device index
"""

import argparse
import queue
import signal
import sys
import threading
import time

import config
from audio_capture import AudioCapture
from transcriber import Transcriber
from translator import Translator
from transcript_logger import TranscriptLogger
from display import Display


def parse_args():
    parser = argparse.ArgumentParser(
        description="Live Conference Translator — real-time audio transcription & translation"
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Whisper model size (default: {config.WHISPER_MODEL}). "
             "Options: tiny, base, small, medium, large-v3, distil-large-v3",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Audio device index (use --list-devices to see available devices)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit",
    )
    parser.add_argument(
        "--target-lang",
        default=None,
        help=f"Target language for translation (default: {config.TARGET_LANGUAGE})",
    )
    parser.add_argument(
        "--compute",
        default=None,
        help=f"Compute type: int8, float16, float32 (default: {config.WHISPER_COMPUTE_TYPE})",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Handle --list-devices
    if args.list_devices:
        AudioCapture.list_devices()
        return

    # Apply CLI overrides to config
    if args.model:
        config.WHISPER_MODEL = args.model
    if args.target_lang:
        config.TARGET_LANGUAGE = args.target_lang
    if args.compute:
        config.WHISPER_COMPUTE_TYPE = args.compute

    # Create queues
    audio_queue = queue.Queue(maxsize=10)
    text_queue = queue.Queue(maxsize=50)
    logger_queue = queue.Queue(maxsize=50)
    display_queue = queue.Queue(maxsize=50)

    # Create components
    # Translator fans out to both logger and display queues
    capture = AudioCapture(audio_queue, device_index=args.device)
    transcriber = Transcriber(audio_queue, text_queue)
    translator = Translator(text_queue, [logger_queue, display_queue])
    logger = TranscriptLogger(logger_queue)
    display = Display(display_queue)

    # Start worker threads
    workers = [
        threading.Thread(target=capture.run, name="AudioCapture", daemon=True),
        threading.Thread(target=transcriber.run, name="Transcriber", daemon=True),
        threading.Thread(target=translator.run, name="Translator", daemon=True),
        threading.Thread(target=logger.run, name="Logger", daemon=True),
    ]

    print("=" * 60)
    print("  Live Conference Translator")
    print(f"  Model: {config.WHISPER_MODEL} | Lang: {config.SOURCE_LANGUAGE}→{config.TARGET_LANGUAGE}")
    print("=" * 60)
    print("\nStarting pipeline...")

    for t in workers:
        t.start()
        time.sleep(0.1)

    # Handle Ctrl+C gracefully
    def shutdown(sig=None, frame=None):
        print("\n\nShutting down...")
        capture.stop()
        transcriber.stop()
        translator.stop()
        logger.stop()
        display.stop()

        for t in workers:
            t.join(timeout=3.0)

        print(f"\nSession complete. {display.segment_count} segments transcribed.")
        print(f"Transcripts saved in: {config.TRANSCRIPT_DIR}")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    # Run display in main thread (blocks until stopped)
    try:
        display.run()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
