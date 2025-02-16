from core.io.nhapanhdicom import load_dicom_series
from core.processing.contouring.contouring_dicom import contour_dicom

def main():
    # Load DICOM series
    directory = "data/CT/"
    volume, patient_pos = load_dicom_series(directory)
    
    # Contour the DICOM images
    contour_dicom(volume)

if __name__ == "__main__":
    main()
