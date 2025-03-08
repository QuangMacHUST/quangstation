# treatment-planning-system-Quangstation

# Tác giả: Mac Dang Quang

# Cách chạy chương trình:
    python quangstation/quangstation_gui/gui/main.py

# Phiên bản cập nhật (02/16/2025):
- **Contouring**: Thêm công cụ tạo contour trên các lát cắt CT hoặc MRI.
  - Sử dụng panel Contouring để bắt đầu vẽ contour
  - Chọn ảnh CT/MRI, đặt tên cho contour và màu hiển thị
  - Hỗ trợ vẽ contour hình chữ nhật và tự do
  - Lưu và chỉnh sửa contour trên nhiều lát cắt

- **Kỹ thuật xạ trị nâng cao**: Thêm hỗ trợ cho các kỹ thuật xạ trị hiện đại:
  - **3DCRT** (3D Conformal Radiation Therapy): Xạ trị thích ứng hình dạng 3D
  - **VMAT** (Volumetric Modulated Arc Therapy): Xạ trị cung tạo hình với cường độ điều biến
  - **SRS** (Stereotactic Radiosurgery): Xạ phẫu định vị cho u não nhỏ
  - **SBRT** (Stereotactic Body Radiation Therapy): Xạ trị định vị thân thể cho u ngoài não

# Hướng dẫn sử dụng

## Công cụ Contouring:
1. Tải dữ liệu bệnh nhân và ảnh CT/MRI
2. Chọn tab "Contouring" từ thanh công cụ bên trái
3. Chọn ảnh để vẽ contour
4. Nhập tên cho cấu trúc (ví dụ: "PTV", "GTV", "Thận trái")
5. Chọn màu hiển thị
6. Nhấn "Start Contouring" để bắt đầu
7. Trong cửa sổ contouring:
   - Nhấn 'm' để chuyển đổi giữa chế độ vẽ hình chữ nhật và vẽ tự do
   - Nhấn 's' để lưu contour cho lát cắt hiện tại
   - Nhấn 'c' để xóa contour trên lát cắt hiện tại
   - Nhấn 'n' hoặc 'd' để đi tới lát cắt tiếp theo
   - Nhấn 'p' hoặc 'a' để quay lại lát cắt trước
   - Nhấn 'ESC' hoặc 'q' để hoàn thành và lưu contour

## Kỹ thuật xạ trị nâng cao:
1. Tải dữ liệu bệnh nhân và ảnh CT
2. Chọn tab "Radiotherapy" từ thanh công cụ bên trái
3. Chọn kỹ thuật điều trị (3DCRT, VMAT, SRS, SBRT)
4. Thiết lập các thông số kỹ thuật:
   - Số phân đoạn (fractions)
   - Tùy chọn đặc thù cho từng kỹ thuật
5. Chọn tab "Targets" để thêm các cấu trúc mục tiêu:
   - Chọn cấu trúc từ danh sách
   - Nhấn "Add as Target"
   - Thiết lập liều lượng theo đơn vị Gray (Gy)
6. Chọn tab "OARs" để thêm các cơ quan nguy cấp:
   - Chọn cấu trúc từ danh sách
   - Nhấn "Add as OAR"
7. Nhấn "Create Plan" để tạo kế hoạch
8. Nhấn "Optimize Plan" để tối ưu hóa kế hoạch
9. Nhấn "Calculate Dose" để tính toán phân bố liều

# Yêu cầu hệ thống:
- Python 3.8 hoặc cao hơn
- PyQt5
- NumPy, SciPy
- SimpleITK
- OpenCV (cho chức năng contouring)
- Các thư viện khác được liệt kê trong pyproject.toml

# Cài đặt thư viện bổ sung:
```
pip install opencv-python
```