"""Generate subtitle files in multiple formats (.txt, .srt, .vtt)."""

import os


def _format_timestamp_txt(seconds: float) -> str:
    """Format as [HH:MM:SS]."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"[{h:02d}:{m:02d}:{s:02d}]"


def _format_timestamp_srt(seconds: float) -> str:
    """Format as HH:MM:SS,mmm for SRT."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_timestamp_vtt(seconds: float) -> str:
    """Format as HH:MM:SS.mmm for VTT."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def write_txt(segments: list[dict], output_path: str, text_key: str = "source"):
    """Write plain text transcript with timestamps."""
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in segments:
            ts = _format_timestamp_txt(seg["start"])
            text = seg.get(text_key, seg.get("text", ""))
            f.write(f"{ts} {text}\n")
    print(f"[Writer] {output_path}")


def write_srt(segments: list[dict], output_path: str, text_key: str = "source"):
    """Write SRT subtitle file."""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = _format_timestamp_srt(seg["start"])
            end = _format_timestamp_srt(seg["end"])
            text = seg.get(text_key, seg.get("text", ""))
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
    print(f"[Writer] {output_path}")


def write_vtt(segments: list[dict], output_path: str, text_key: str = "source"):
    """Write WebVTT subtitle file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            start = _format_timestamp_vtt(seg["start"])
            end = _format_timestamp_vtt(seg["end"])
            text = seg.get(text_key, seg.get("text", ""))
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
    print(f"[Writer] {output_path}")


def write_all(
    segments: list[dict],
    output_dir: str,
    base_name: str,
    source_lang: str = "en",
    target_lang: str | None = "es",
):
    """Write all formats. If target_lang is None, only source files are generated."""
    os.makedirs(output_dir, exist_ok=True)

    # Sanitize filename
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in base_name)
    safe_name = safe_name[:80].strip()

    files = []

    # Source language files
    base = os.path.join(output_dir, f"{safe_name}_{source_lang}")
    write_txt(segments, f"{base}.txt", "source")
    write_srt(segments, f"{base}.srt", "source")
    write_vtt(segments, f"{base}.vtt", "source")
    files.extend([f"{base}.txt", f"{base}.srt", f"{base}.vtt"])

    # Translated language files (only if translation was done)
    if target_lang and any("translated" in seg for seg in segments):
        base = os.path.join(output_dir, f"{safe_name}_{target_lang}")
        write_txt(segments, f"{base}.txt", "translated")
        write_srt(segments, f"{base}.srt", "translated")
        write_vtt(segments, f"{base}.vtt", "translated")
        files.extend([f"{base}.txt", f"{base}.srt", f"{base}.vtt"])

    return files
