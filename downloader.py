"""Download audio from YouTube and other sites via yt-dlp."""

import os
import tempfile

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class Downloader:
    """Downloads audio from URLs using yt-dlp."""

    def __init__(self, temp_dir: str | None = None):
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="lct_")
        self._downloaded_files: list[str] = []

    def download(self, url: str) -> tuple[str, str]:
        """Download audio from URL. Returns (audio_path, title)."""
        if yt_dlp is None:
            raise ImportError("yt-dlp is required for URL mode. Install with: pip install yt-dlp")

        output_template = os.path.join(self.temp_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }],
        }

        # Try without ffmpeg first (some formats work directly)
        try:
            return self._try_download(url, ydl_opts)
        except Exception:
            # Fallback: download without post-processing
            ydl_opts_simple = {
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
            }
            return self._try_download(url, ydl_opts_simple)

    def _try_download(self, url: str, ydl_opts: dict) -> tuple[str, str]:
        """Attempt download with given options."""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "unknown")

            # Find the downloaded file
            if info.get("requested_downloads"):
                audio_path = info["requested_downloads"][0]["filepath"]
            else:
                # Construct path from template
                video_id = info.get("id", "unknown")
                ext = info.get("ext", "webm")
                audio_path = os.path.join(self.temp_dir, f"{video_id}.{ext}")

            if not os.path.exists(audio_path):
                # Look for any file with the video ID
                for f in os.listdir(self.temp_dir):
                    if info.get("id", "xxx") in f:
                        audio_path = os.path.join(self.temp_dir, f)
                        break

            self._downloaded_files.append(audio_path)
            print(f"[Downloader] Downloaded: {title}")
            print(f"[Downloader] File: {audio_path}")
            return audio_path, title

    def cleanup(self):
        """Remove downloaded temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print("[Downloader] Temp files cleaned up.")
