# Script cài đặt môi trường Quangstation_310
# Để chạy: powershell -ExecutionPolicy Bypass -File install_quangstation_310.ps1

# Kiểm tra Anaconda
if (-not $env:CONDA_EXE) {
    Write-Host "Không tìm thấy Anaconda. Vui lòng cài đặt Anaconda hoặc Miniconda." -ForegroundColor Red
    exit
}

# Kiểm tra xem môi trường quangstation_310 đã tồn tại chưa
$envExists = conda env list | Select-String "quangstation_310"
if (-not $envExists) {
    Write-Host "Tạo môi trường Conda 'quangstation_310'..." -ForegroundColor Green
    conda create -n quangstation_310 python=3.10 -y
} else {
    Write-Host "Môi trường Conda 'quangstation_310' đã tồn tại." -ForegroundColor Yellow
}

# Kích hoạt môi trường Conda
conda activate quangstation_310

# Cài đặt các thư viện cần thiết
Write-Host "Cài đặt các thư viện cần thiết..." -ForegroundColor Green

conda run -n quangstation_310 pip install --upgrade pip
conda run -n quangstation_310 pip install pydicom
conda run -n quangstation_310 pip install numpy>=1.24.0
conda run -n quangstation_310 pip install scipy
conda run -n quangstation_310 pip install matplotlib
conda run -n quangstation_310 pip install Pillow
conda run -n quangstation_310 pip install PyQt5==5.15.7
conda run -n quangstation_310 pip install pyqtgraph
conda run -n quangstation_310 pip install sparse_dot_mkl
conda run -n quangstation_310 pip install vtk==9.2.6
conda run -n quangstation_310 pip install SimpleITK
conda run -n quangstation_310 pip install pandas
conda run -n quangstation_310 pip install scikit-image
conda run -n quangstation_310 pip install opencv-python
conda run -n quangstation_310 pip install pymedphys==0.40.0

# Cài đặt thư viện tùy chọn
Write-Host "Cài đặt các thư viện tùy chọn..." -ForegroundColor Green
conda run -n quangstation_310 pip install tensorflow
conda run -n quangstation_310 pip install keras
conda run -n quangstation_310 pip install cupy-cuda12x

Write-Host "Cài đặt hoàn tất. Bạn có thể khởi động Quangstation bằng cách chạy:" -ForegroundColor Green
Write-Host "powershell -ExecutionPolicy Bypass -File start_quangstation_310.ps1" -ForegroundColor Cyan 