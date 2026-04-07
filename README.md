# Live Conference Translator

Captura audio del sistema en Windows en tiempo real, lo transcribe (inglés) con Whisper y lo traduce al español. También procesa videos de YouTube y archivos locales offline.

## Petición original

> Necesito capturar en vivo el audio de la computadora en Windows usando Python. Estoy en conferencias en Discord (pero no importa la app). Quiero traducirlo en tiempo real a español, y al menos transcribirlo en inglés para luego tratarlo.

## Stack

| Componente | Tecnología |
|-----------|-----------|
| Captura audio | **PyAudioWPatch** (WASAPI Loopback) - captura audio del sistema sin software extra |
| Transcripción | **Faster-Whisper** (local) - 4x más rápido que Whisper, gratis, CPU/GPU |
| Traducción | **deep-translator** (Google Translate) - gratis, sin API key |
| Descarga videos | **yt-dlp** - YouTube y cientos de sitios más |
| Display | Terminal con colores ANSI |

## Modos de uso

### Modo Live — conferencias en tiempo real

Captura el audio del sistema (lo que suena por parlantes/audífonos) y muestra subtítulos en terminal.

```powershell
python main.py                        # modelo small (default)
python main.py --model tiny           # más rápido, menos calidad
python main.py --list-devices         # ver dispositivos de audio
python main.py --device 5             # elegir dispositivo específico
```

### Modo Offline — YouTube y archivos locales

Descarga y procesa videos completos. Genera archivos .txt, .srt y .vtt en ambos idiomas.

```powershell
# Desde URL (YouTube, Vimeo, Twitter, TikTok, etc.)
python main.py --url "https://youtube.com/watch?v=xxxxx"

# Desde archivo local
python main.py --file "C:\Users\abela\Downloads\conferencia.mp4"

# Con opciones
python main.py --url "https://..." --model medium --target-lang pt
python main.py --file video.mp3 --output-dir "C:\mis-transcripts"
```

## Setup (Windows PowerShell)

```powershell
.\setup.ps1
```

O manual:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install yt-dlp    # solo si usarás modo offline
python main.py
```

La primera vez descarga el modelo Whisper (~500MB para `small`).

## Opciones CLI

| Opción | Descripción |
|--------|-------------|
| `--url URL` | URL de YouTube u otro sitio para procesar offline |
| `--file PATH` | Archivo local de audio/video para procesar offline |
| `--model NAME` | Modelo Whisper: tiny, base, small, medium, large-v3 |
| `--device N` | Índice de dispositivo de audio (modo live) |
| `--list-devices` | Listar dispositivos de audio disponibles |
| `--target-lang XX` | Idioma destino: es, pt, fr, de, etc. |
| `--compute TYPE` | Tipo de cómputo: int8, float16, float32 |
| `--output-dir PATH` | Directorio de salida (modo offline) |

## Modelos disponibles

| Modelo | RAM | Calidad | Velocidad CPU |
|--------|-----|---------|---------------|
| tiny | ~1GB | Baja | Muy rápido |
| base | ~1GB | Media | Rápido |
| **small** | ~2GB | **Buena** | **Moderado (default)** |
| medium | ~5GB | Muy buena | Lento |
| large-v3 | ~10GB | Excelente | Muy lento (necesita GPU) |

## Arquitectura

```
MODO LIVE:
[WASAPI Loopback] → audio_queue → [Faster-Whisper] → text_queue → [Translator] → display
                                         ↓                              ↓
                                   transcript_en.txt              transcript_es.txt

MODO OFFLINE:
[yt-dlp / archivo] → [Faster-Whisper] → [Translator] → .txt + .srt + .vtt
```

## Archivos

| Archivo | Función |
|---------|---------|
| `main.py` | Entry point — detecta modo live vs offline |
| `audio_capture.py` | Captura WASAPI loopback (modo live) |
| `transcriber.py` | Faster-whisper con VAD (modo live) |
| `translator.py` | Google Translate EN→ES (modo live) |
| `display.py` | Terminal con colores (modo live) |
| `transcript_logger.py` | Guarda transcripts en tiempo real |
| `downloader.py` | yt-dlp wrapper (modo offline) |
| `file_processor.py` | Pipeline completo offline |
| `subtitle_writer.py` | Genera .txt, .srt, .vtt |
| `config.py` | Configuración central |
| `utils.py` | Helpers de audio |
| `setup.ps1` | Setup automático para Windows |

## Notas

- **Modo live solo funciona en Windows** (WASAPI es API de Windows)
- **Modo offline funciona en cualquier OS** (Linux, Mac, Windows)
- Si Discord usa un dispositivo de audio diferente, usar `--list-devices` y `--device N`
- Transcripts live se guardan en `transcripts/`
- Output offline se guarda en `output/` (o `--output-dir`)
- Latencia modo live: 3-8 segundos desde voz hasta texto en pantalla
- yt-dlp soporta YouTube, Vimeo, Twitter, TikTok, y cientos más
