# Script khởi động Quangstation với môi trường Conda
# Để chạy: powershell -ExecutionPolicy Bypass -File start_quangstation_conda_windows.ps1

# Kiểm tra Anaconda
if (-not $env:CONDA_EXE) {
    Write-Host "Không tìm thấy Anaconda. Vui lòng cài đặt Anaconda hoặc Miniconda." -ForegroundColor Red
    exit
}

# Đặt tên môi trường
$ENV_NAME = "quangstation_310"

# Kiểm tra xem môi trường có tồn tại không
$envExists = conda env list | Select-String $ENV_NAME
if (-not $envExists) {
    Write-Host "Môi trường $ENV_NAME không tồn tại. Vui lòng chạy install_quangstation_310.ps1 trước." -ForegroundColor Red
    exit
}

Write-Host "Kích hoạt môi trường Conda '$ENV_NAME'..." -ForegroundColor Green

# Kích hoạt môi trường Conda
conda activate $ENV_NAME

# Thiết lập PYTHONPATH
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$scriptPath\quangstation_core;$scriptPath\quangstation_gui"

Write-Host "Khởi động Quangstation..." -ForegroundColor Green

# Chạy chương trình
python "$scriptPath\quangstation_gui\quangstation\gui\main.py" 