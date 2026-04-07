# Live Conference Translator

Captura audio del sistema en Windows en tiempo real, lo transcribe (inglés) con Whisper y lo traduce al español. Ideal para conferencias en Discord, Zoom, Meet, etc.

## Petición original

> Necesito capturar en vivo el audio de la computadora en Windows usando Python. Estoy en conferencias en Discord (pero no importa la app). Quiero traducirlo en tiempo real a español, y al menos transcribirlo en inglés para luego tratarlo.

## Stack

| Componente | Tecnología |
|-----------|-----------|
| Captura audio | **PyAudioWPatch** (WASAPI Loopback) - captura audio del sistema sin software extra |
| Transcripción | **Faster-Whisper** (local) - 4x más rápido que Whisper, gratis, CPU/GPU |
| Traducción | **deep-translator** (Google Translate) - gratis, sin API key |
| Display | Terminal con colores ANSI |

## Arquitectura

```
[WASAPI Loopback] --> audio_queue --> [Faster-Whisper] --> text_queue --> [Translator] --> display
                                            |                                |
                                      transcript_en.txt              transcript_es.txt
```

3 threads con queues + main thread para display. Los transcripts se guardan automáticamente con timestamps.

## Setup (Windows PowerShell)

```powershell
cd C:\Users\abela\prweb\public\live-conference-translator
.\setup.ps1
```

O manual:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

La primera vez descarga el modelo Whisper (~500MB para `small`).

## Uso

```powershell
.\venv\Scripts\Activate.ps1

python main.py                        # modelo small (default)
python main.py --model tiny           # más rápido, menos calidad
python main.py --model medium         # mejor calidad, más lento
python main.py --list-devices         # ver dispositivos de audio
python main.py --device 5             # elegir dispositivo específico
python main.py --target-lang pt       # traducir a portugués
```

## Modelos disponibles

| Modelo | RAM | Calidad | Velocidad CPU |
|--------|-----|---------|---------------|
| tiny | ~1GB | Baja | Muy rápido |
| base | ~1GB | Media | Rápido |
| small | ~2GB | Buena | Moderado |
| medium | ~5GB | Muy buena | Lento |
| large-v3 | ~10GB | Excelente | Muy lento (necesita GPU) |

## Archivos

- `main.py` - Entry point, orquesta todo
- `audio_capture.py` - Captura WASAPI loopback
- `transcriber.py` - Faster-whisper con VAD
- `translator.py` - Google Translate EN→ES
- `display.py` - Terminal con colores
- `transcript_logger.py` - Guarda transcripts
- `config.py` - Configuración central
- `utils.py` - Helpers de audio (resample, stereo→mono)
- `setup.ps1` - Setup automático para Windows

## Notas

- **Solo funciona en Windows** (WASAPI es API de Windows)
- Si Discord usa un dispositivo de audio diferente, usar `--list-devices` y `--device N`
- Los transcripts se guardan en `transcripts/` con formato `YYYY-MM-DD_HHMMSS_en.txt` y `_es.txt`
- Latencia esperada: 3-8 segundos desde voz hasta texto en pantalla
