"""Audio utility helpers: resampling and format conversion."""

import numpy as np


def resample(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Resample audio using linear interpolation.

    Works well for clean integer ratios like 48000→16000 (3:1).
    """
    if src_rate == dst_rate:
        return audio
    ratio = dst_rate / src_rate
    n_samples = int(len(audio) * ratio)
    indices = np.linspace(0, len(audio) - 1, n_samples)
    return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)


def stereo_to_mono(audio: np.ndarray, channels: int) -> np.ndarray:
    """Convert interleaved multi-channel audio to mono by averaging channels."""
    if channels == 1:
        return audio
    # Reshape interleaved samples into (n_frames, channels) and average
    audio = audio.reshape(-1, channels)
    return audio.mean(axis=1).astype(np.float32)


def bytes_to_float32(data: bytes, sample_width: int) -> np.ndarray:
    """Convert raw audio bytes to float32 numpy array in [-1.0, 1.0]."""
    if sample_width == 4:
        # 32-bit float (WASAPI default)
        return np.frombuffer(data, dtype=np.float32)
    elif sample_width == 2:
        # 16-bit int
        arr = np.frombuffer(data, dtype=np.int16)
        return arr.astype(np.float32) / 32768.0
    elif sample_width == 3:
        # 24-bit int — pad to 32-bit
        n_samples = len(data) // 3
        padded = bytearray(n_samples * 4)
        for i in range(n_samples):
            padded[i * 4 + 1] = data[i * 3]
            padded[i * 4 + 2] = data[i * 3 + 1]
            padded[i * 4 + 3] = data[i * 3 + 2]
        arr = np.frombuffer(bytes(padded), dtype=np.int32)
        return arr.astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")


def prepare_audio_for_whisper(
    raw_bytes: bytes,
    sample_width: int,
    channels: int,
    src_rate: int,
    dst_rate: int = 16000,
) -> np.ndarray:
    """Full pipeline: bytes → float32 → mono → resample to 16kHz."""
    audio = bytes_to_float32(raw_bytes, sample_width)
    audio = stereo_to_mono(audio, channels)
    audio = resample(audio, src_rate, dst_rate)
    return audio
