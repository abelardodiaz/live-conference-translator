"""Real-time translation EN→ES using deep-translator."""

import threading
import queue
import time

from config import SOURCE_LANGUAGE, TARGET_LANGUAGE


class Translator:
    """Pulls English text segments and produces Spanish translations."""

    def __init__(self, text_queue: queue.Queue, output_queues: list[queue.Queue]):
        self.text_queue = text_queue
        self.output_queues = output_queues
        self._stop_event = threading.Event()
        self._translator = None

    def _init_translator(self):
        from deep_translator import GoogleTranslator
        self._translator = GoogleTranslator(
            source=SOURCE_LANGUAGE,
            target=TARGET_LANGUAGE,
        )
        print(f"[Translator] Ready: {SOURCE_LANGUAGE} → {TARGET_LANGUAGE}")

    def run(self):
        """Main translation loop. Call from a thread."""
        self._init_translator()

        while not self._stop_event.is_set():
            try:
                item = self.text_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            english = item["text"]
            try:
                spanish = self._translator.translate(english)
            except Exception as e:
                print(f"[Translator] Error: {e}")
                spanish = f"[translation error] {english}"

            result = {
                "english": english,
                "spanish": spanish,
                "start": item.get("start", 0),
                "end": item.get("end", 0),
                "timestamp": item.get("timestamp", time.time()),
            }
            for q in self.output_queues:
                try:
                    q.put(result, timeout=1.0)
                except queue.Full:
                    pass

        print("[Translator] Stopped.")

    def stop(self):
        """Signal the translation loop to stop."""
        self._stop_event.set()
