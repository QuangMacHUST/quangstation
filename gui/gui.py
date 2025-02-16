import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import numpy as np
from core.io.import import load_dicom_series
from core.processing.contouring.contouring_dicom import contour_dicom

class DICOMViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DICOM Viewer and Contouring")
        self.geometry("800x600")
        
        self.load_button = tk.Button(self, text="Load DICOM Series", command=self.load_dicom)
        self.load_button.pack()
        
        self.canvas = tk.Canvas(self, width=512, height=512)
        self.canvas.pack()
        
        self.img = None
        self.volume = None

    def load_dicom(self):
        directory = filedialog.askdirectory()
        if directory:
            self.volume, _ = load_dicom_series(directory)
            self.display_image(self.volume[0])

    def display_image(self, img):
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img = Image.fromarray(img)
        self.img = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img)
        
    def contour_image(self):
        if self.volume is not None:
            contour_dicom(self.volume)
        else:
            messagebox.showerror("Error", "Please load a DICOM series first.")

if __name__ == "__main__":
    app = DICOMViewer()
    app.mainloop()
