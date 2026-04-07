$py = "C:\Users\abela\AppData\Local\Programs\Python\Python314\python.exe"
& $py -c "from faster_whisper import WhisperModel; print('Descargando modelo...'); WhisperModel('small', device='cpu', compute_type='int8'); print('Modelo listo')"
