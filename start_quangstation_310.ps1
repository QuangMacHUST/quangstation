# Script khởi động Quangstation với môi trường Conda
# Để chạy: powershell -ExecutionPolicy Bypass -File start_quangstation_310.ps1

# Kiểm tra Anaconda
if (-not $env:CONDA_EXE) {
    Write-Host "Không tìm thấy Anaconda. Vui lòng cài đặt Anaconda hoặc Miniconda." -ForegroundColor Red
    exit
}

Write-Host "Kích hoạt môi trường Conda 'quangstation_310'..." -ForegroundColor Green

# Kích hoạt môi trường Conda
conda activate quangstation_310

# Thiết lập PYTHONPATH
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$scriptPath\quangstation_core;$scriptPath\quangstation_gui"

Write-Host "Khởi động Quangstation..." -ForegroundColor Green

# Chạy chương trình
python "$scriptPath\quangstation_gui\quangstation\gui\main.py" 