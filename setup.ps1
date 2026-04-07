# setup.ps1 - Live Conference Translator setup for Windows
# Run from PowerShell as: .\setup.ps1

Write-Host "=== Live Conference Translator - Windows Setup ===" -ForegroundColor Cyan

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "ERROR: Python not found. Install from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "Python: $(python --version)" -ForegroundColor Green

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}
& .\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "Downloading Whisper small model (~500MB, first time only)..." -ForegroundColor Yellow
python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8'); print('Model ready')"

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host "To run:  .\venv\Scripts\Activate.ps1; python main.py" -ForegroundColor White
