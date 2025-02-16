import torch
from monai.networks.nets import UNet
from monai.data import DataLoader, Dataset

# Load model AI đã trained
model = UNet(spatial_dims=3, in_channels=1, out_channels=5)  # 5 lớp: tumor + 4 OARs
model.load_state_dict(torch.load("model_contour.pth"))

# Dự đoán contour từ CT volume
input_tensor = torch.from_numpy(ct_volume).unsqueeze(0).unsqueeze(0).float()
with torch.no_grad():
    pred_mask = model(input_tensor).argmax(dim=1).squeeze().numpy()

# Lưu contour sang RT Structure Set
def save_rtss_from_mask(pred_mask, ct_series):
    # ... (tham khảo code trước để chuyển mask → DICOM RTSS)