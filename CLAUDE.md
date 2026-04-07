# Live Conference Translator - Context for Claude Code

## Qué es este proyecto
Herramienta Python para Windows que captura audio del sistema (WASAPI loopback), transcribe en tiempo real con faster-whisper, traduce EN→ES con Google Translate, y muestra subtítulos en terminal.

## Arquitectura
Pipeline de 3 threads conectados por queues:
1. `audio_capture.py` - WASAPI loopback → resample 48kHz→16kHz mono → audio_queue
2. `transcriber.py` - faster-whisper con Silero VAD → text_queue
3. `translator.py` - deep-translator (Google) → fan-out a logger_queue + display_queue

`main.py` orquesta threads + display en main thread. `transcript_logger.py` escribe archivos EN+ES.

## Dependencias clave
- PyAudioWPatch (fork de PyAudio con WASAPI loopback)
- faster-whisper (CTranslate2-based Whisper)
- deep-translator (Google Translate wrapper)
- numpy (audio processing)

## Plataforma
- **Ejecución**: Windows solamente (WASAPI)
- **Desarrollo**: puede editarse desde WSL ya que los archivos están en /mnt/c/

## Estado actual
- v0.1 - Implementación inicial completa, pendiente de testing en Windows con audio real
- setup.ps1 listo para instalar dependencias y descargar modelo

## Próximos pasos potenciales
- GUI con tkinter (paneles EN/ES lado a lado)
- Speaker diarization
- Resumen al final de sesión con IA
- Hotkey para marcar momentos importantes
