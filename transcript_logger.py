"""Writes timestamped transcript files (EN + ES) to disk."""

import os
import threading
import queue
from datetime import datetime

from config import TRANSCRIPT_DIR


class TranscriptLogger:
    """Consumes display_queue items and appends to transcript files."""

    def __init__(self, display_queue: queue.Queue):
        self.display_queue = display_queue
        self._stop_event = threading.Event()
        self._session_start = None
        self._en_file = None
        self._es_file = None

    def _open_files(self):
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        en_path = os.path.join(TRANSCRIPT_DIR, f"{ts}_en.txt")
        es_path = os.path.join(TRANSCRIPT_DIR, f"{ts}_es.txt")
        self._en_file = open(en_path, "a", encoding="utf-8")
        self._es_file = open(es_path, "a", encoding="utf-8")
        self._session_start = datetime.now()
        print(f"[Logger] Transcripts: {en_path}")
        print(f"[Logger]             {es_path}")

    def _format_time(self, timestamp: float) -> str:
        """Format elapsed time as [HH:MM:SS]."""
        if self._session_start is None:
            return "[00:00:00]"
        elapsed = timestamp - self._session_start.timestamp()
        if elapsed < 0:
            elapsed = 0
        h = int(elapsed // 3600)
        m = int((elapsed % 3600) // 60)
        s = int(elapsed % 60)
        return f"[{h:02d}:{m:02d}:{s:02d}]"

    def run(self):
        """Main logging loop. Call from a thread."""
        self._open_files()

        while not self._stop_event.is_set():
            try:
                item = self.display_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            ts = self._format_time(item["timestamp"])
            self._en_file.write(f"{ts} {item['english']}\n")
            self._en_file.flush()
            self._es_file.write(f"{ts} {item['spanish']}\n")
            self._es_file.flush()

        self._close_files()
        print("[Logger] Stopped.")

    def _close_files(self):
        if self._en_file:
            self._en_file.close()
        if self._es_file:
            self._es_file.close()

    def stop(self):
        """Signal the logging loop to stop."""
        self._stop_event.set()
