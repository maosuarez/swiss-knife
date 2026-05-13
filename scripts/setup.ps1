# Swiss Knife - Bootstrap para Windows
# Ejecutar una vez desde el directorio del proyecto:
#   powershell -ExecutionPolicy Bypass -File setup.ps1

$ENV_NAME = "tools-env"
$CONDA = "conda"

Write-Host "==> Verificando conda env..." -ForegroundColor Cyan
$envExists = & $CONDA env list 2>&1 | Select-String $ENV_NAME
if (-not $envExists) {
    Write-Host "==> Creando env con Python 3.11..." -ForegroundColor Yellow
    & $CONDA create -n $ENV_NAME python=3.11 -y
}

Write-Host "==> Instalando binarios via conda-forge (ffmpeg, pandoc)..." -ForegroundColor Cyan
& $CONDA install -n $ENV_NAME -c conda-forge ffmpeg pandoc -y

Write-Host "==> Instalando dependencias Python y registrando knife..." -ForegroundColor Cyan
$pip = Join-Path $env:USERPROFILE "miniconda3\envs\$ENV_NAME\Scripts\pip.exe"
& $pip install -e $PSScriptRoot\..

$scriptsPath = Join-Path $env:USERPROFILE "miniconda3\envs\$ENV_NAME\Scripts"

Write-Host ""
Write-Host "Listo. Usa knife desde cualquier terminal:" -ForegroundColor Green
Write-Host "  1. Activa el env:  conda activate $ENV_NAME"
Write-Host "  2. Ejecuta:        knife --list"
Write-Host ""
Write-Host "PATH permanente (opcional):" -ForegroundColor Yellow
Write-Host "  $scriptsPath"
