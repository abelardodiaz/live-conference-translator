"""Real-time terminal display with colored output."""

import threading
import queue
import sys
import os

# ANSI color codes
RESET = "\033[0m"
WHITE = "\033[97m"
GREEN = "\033[92m"
DIM = "\033[90m"
CYAN = "\033[96m"
BOLD = "\033[1m"


def enable_ansi_windows():
    """Enable ANSI escape codes on Windows terminal."""
    if sys.platform == "win32":
        os.system("")  # triggers VT100 mode on Windows 10+


class Display:
    """Shows live transcript in terminal with colored EN/ES lines."""

    def __init__(self, display_queue: queue.Queue):
        self.display_queue = display_queue
        self._stop_event = threading.Event()
        self._segment_count = 0

    def run(self):
        """Main display loop. Call from the main thread."""
        enable_ansi_windows()
        print()
        print(f"{BOLD}{CYAN}{'=' * 60}{RESET}")
        print(f"{BOLD}{CYAN}  Live Conference Translator{RESET}")
        print(f"{BOLD}{CYAN}  Press Ctrl+C to stop{RESET}")
        print(f"{BOLD}{CYAN}{'=' * 60}{RESET}")
        print()

        while not self._stop_event.is_set():
            try:
                item = self.display_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            self._segment_count += 1
            en = item["english"]
            es = item["spanish"]

            print(f"{DIM}#{self._segment_count}{RESET}  {WHITE}{en}{RESET}")
            print(f"     {GREEN}{es}{RESET}")
            print()

    def stop(self):
        """Signal the display loop to stop."""
        self._stop_event.set()

    @property
    def segment_count(self) -> int:
        return self._segment_count
