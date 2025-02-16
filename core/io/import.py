import os
import pydicom
import numpy as np

def load_dicom_series(directory):
    """Đọc loạt ảnh DICOM và tạo volume 3D"""
    slices = [pydicom.dcmread(os.path.join(directory, f)) for f in sorted(os.listdir(directory))]
    slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
    volume = np.stack([s.pixel_array for s in slices])
    return volume, slices[0].PatientPosition  # ('HFS' = Head First Supine)

# Ví dụ:
# ct_volume, patient_pos = load_dicom_series("data/CT/")
# pet_volume, _ = load_dicom_series("data/PET/")