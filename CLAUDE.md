# CLAUDE.md - Live Conference Translator (web26-077)

## PROJECT.yaml - IMPORTANTE

Este proyecto tiene un archivo `PROJECT.yaml` en la raiz. Es leido por el Project Manager (99999) para monitorear el estado.

**Cuando actualizar:**
- Cambio de version -> actualiza `project.version`
- Siempre actualiza `updated_at` y `updated_by: claude-077`

**NO modificar sin razon:**
- `project.code` - identificador unico
- `server.base_path` - ruta del proyecto

---

## Que es este proyecto

Herramienta CLI Python para Windows que captura audio del sistema (WASAPI loopback), transcribe en tiempo real con faster-whisper, traduce EN->ES con Google Translate, y muestra subtitulos en terminal.

## Arquitectura

Pipeline de 3 threads conectados por queues:
1. `audio_capture.py` - WASAPI loopback -> resample 48kHz->16kHz mono -> audio_queue
2. `transcriber.py` - faster-whisper con Silero VAD -> text_queue
3. `translator.py` - deep-translator (Google) -> fan-out a logger_queue + display_queue

`main.py` orquesta threads + display en main thread. `transcript_logger.py` escribe archivos EN+ES.

## Stack

- **Python 3.10+** (Windows)
- **PyAudioWPatch** - fork de PyAudio con WASAPI loopback
- **faster-whisper** - CTranslate2-based Whisper (local, sin API)
- **deep-translator** - Google Translate wrapper (gratis, sin API key)
- **numpy** - audio processing
- **ruff** - linting (dev)

## Plataforma

- **Ejecucion**: Windows solamente (WASAPI es API nativa de Windows)
- **Desarrollo**: puede editarse desde WSL ya que los archivos estan en /mnt/c/

## Comandos utiles

```bash
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Ejecutar
python main.py
python main.py --model tiny
python main.py --list-devices

# Linting
ruff check .
ruff format .
```

## Estado actual

- v0.1.0 - Implementacion inicial completa y funcional
- setup.ps1 listo para instalar dependencias y descargar modelo

## Proximos pasos potenciales

- GUI con tkinter (paneles EN/ES lado a lado)
- Speaker diarization
- Resumen al final de sesion con IA
- Hotkey para marcar momentos importantes
