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


def write_txt(segments: list[dict], output_path: str, lang_key: str = "english"):
    """Write plain text transcript with timestamps."""
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in segments:
            ts = _format_timestamp_txt(seg["start"])
            f.write(f"{ts} {seg[lang_key]}\n")
    print(f"[Writer] {output_path}")


def write_srt(segments: list[dict], output_path: str, lang_key: str = "english"):
    """Write SRT subtitle file."""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = _format_timestamp_srt(seg["start"])
            end = _format_timestamp_srt(seg["end"])
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{seg[lang_key]}\n\n")
    print(f"[Writer] {output_path}")


def write_vtt(segments: list[dict], output_path: str, lang_key: str = "english"):
    """Write WebVTT subtitle file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            start = _format_timestamp_vtt(seg["start"])
            end = _format_timestamp_vtt(seg["end"])
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{seg[lang_key]}\n\n")
    print(f"[Writer] {output_path}")


def write_all(segments: list[dict], output_dir: str, base_name: str):
    """Write all formats for both languages."""
    os.makedirs(output_dir, exist_ok=True)

    # Sanitize filename
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in base_name)
    safe_name = safe_name[:80].strip()

    files = []
    for lang_key, lang_code in [("english", "en"), ("spanish", "es")]:
        # Check if segments have this key
        if not segments or lang_key not in segments[0]:
            continue

        base = os.path.join(output_dir, f"{safe_name}_{lang_code}")

        write_txt(segments, f"{base}.txt", lang_key)
        write_srt(segments, f"{base}.srt", lang_key)
        write_vtt(segments, f"{base}.vtt", lang_key)
        files.extend([f"{base}.txt", f"{base}.srt", f"{base}.vtt"])

    return files
