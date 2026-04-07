#!/usr/bin/env python3
"""Live Conference Translator — real-time and offline audio transcription and translation.

Modes:
  Live:    Captures system audio via WASAPI loopback (default)
  Offline: Processes a YouTube URL or local audio/video file

Usage:
    python main.py                                # live — system audio (WASAPI)
    python main.py --mic                          # live — microphone
    python main.py --url "https://youtube.com/..." # offline — download + process
    python main.py --file recording.mp3            # offline — local file
    python main.py --list-devices                  # show audio devices
"""

import argparse
import queue
import signal
import sys
import threading
import time

import config


def parse_args():
    parser = argparse.ArgumentParser(
        description="Live Conference Translator — real-time and offline audio transcription & translation"
    )
    # Mode selection
    parser.add_argument(
        "--url",
        default=None,
        help="YouTube or other URL to download and process offline",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Local audio/video file to process offline",
    )
    # Common options
    parser.add_argument(
        "--model",
        default=None,
        help=f"Whisper model size (default: {config.WHISPER_MODEL}). "
             "Options: tiny, base, small, medium, large-v3, distil-large-v3",
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
    parser.add_argument(
        "--output-dir",
        default=None,
        help=f"Output directory for offline mode (default: {config.OUTPUT_DIR})",
    )
    # Live mode options
    parser.add_argument(
        "--mic",
        action="store_true",
        help="Capture microphone instead of system audio",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Audio device index for system capture (use --list-devices to see available)",
    )
    parser.add_argument(
        "--mic-device",
        type=int,
        default=None,
        help="Audio device index for microphone (use --list-devices to see available)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit",
    )
    return parser.parse_args()


def run_live(args):
    """Run in live capture mode (WASAPI loopback)."""
    from audio_capture import AudioCapture
    from transcriber import Transcriber
    from translator import Translator
    from transcript_logger import TranscriptLogger
    from display import Display

    # Create queues
    audio_queue = queue.Queue(maxsize=10)
    text_queue = queue.Queue(maxsize=50)
    logger_queue = queue.Queue(maxsize=50)
    display_queue = queue.Queue(maxsize=50)

    # Create components
    if args.mic:
        capture = AudioCapture(audio_queue, device_index=args.mic_device, mode="mic")
        source_label = "MICROPHONE"
    else:
        capture = AudioCapture(audio_queue, device_index=args.device, mode="loopback")
        source_label = "SYSTEM AUDIO"
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
    print(f"  Live Conference Translator — {source_label}")
    print(f"  Model: {config.WHISPER_MODEL} | Lang: {config.SOURCE_LANGUAGE}→{config.TARGET_LANGUAGE}")
    print("=" * 60)
    print("\nStarting pipeline...")

    for t in workers:
        t.start()
        time.sleep(0.1)

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

    try:
        display.run()
    except KeyboardInterrupt:
        shutdown()


def run_offline(args):
    """Run in offline mode (file or URL)."""
    from file_processor import FileProcessor

    output_dir = args.output_dir or config.OUTPUT_DIR
    processor = FileProcessor(output_dir=output_dir)

    if args.url:
        from downloader import Downloader

        downloader = Downloader()
        try:
            audio_path, title = downloader.download(args.url)
            processor.process(audio_path, title=title)
        finally:
            downloader.cleanup()
    else:
        import os
        audio_path = args.file
        title = os.path.splitext(os.path.basename(audio_path))[0]
        processor.process(audio_path, title=title)


def main():
    args = parse_args()

    # Handle --list-devices
    if args.list_devices:
        from audio_capture import AudioCapture
        AudioCapture.list_devices()
        return

    # Apply CLI overrides to config
    if args.model:
        config.WHISPER_MODEL = args.model
    if args.target_lang:
        config.TARGET_LANGUAGE = args.target_lang
    if args.compute:
        config.WHISPER_COMPUTE_TYPE = args.compute

    # Route to the right mode
    if args.url or args.file:
        run_offline(args)
    else:
        run_live(args)


if __name__ == "__main__":
    main()
