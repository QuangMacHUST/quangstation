import cv2
import numpy as np
from core.io.nhapanhdicom import load_dicom_series

# Initialize global variables
drawing = False  # True if the mouse is pressed
mode = True  # If True, draw rectangle. Press 'm' to toggle to curve
ix, iy = -1, -1
color = (0, 255, 0)  # Default color is green

# Mouse callback function
def draw_contour(event, x, y, flags, param):
    global ix, iy, drawing, mode, color

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            if mode:
                cv2.rectangle(img, (ix, iy), (x, y), color, -1)
            else:
                cv2.circle(img, (x, y), 5, color, -1)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        if mode:
            cv2.rectangle(img, (ix, iy), (x, y), color, -1)
        else:
            cv2.circle(img, (x, y), 5, color, -1)

def contour_dicom(volume, structure_name, contour_color):
    global img, color
    color = contour_color
    # Display the first slice for contouring
    img = volume[0]
    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    cv2.namedWindow(f'Contouring: {structure_name}')
    cv2.setMouseCallback(f'Contouring: {structure_name}', draw_contour)

    while True:
        cv2.imshow(f'Contouring: {structure_name}', img)
        k = cv2.waitKey(1) & 0xFF
        if k == ord('m'):
            mode = not mode
        elif k == 27:
            break

    cv2.destroyAllWindows()

# Load DICOM series
directory = "data/CT/"
volume, patient_pos = load_dicom_series(directory)

contour_dicom(volume, "Liver", (0, 255, 0))
