import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import numpy as np
from core.io.nhapanhdicom import load_dicom_series
from core.processing.contouring.contouring_dicom import contour_dicom

class DICOMViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DICOM Viewer and Contouring")
        self.geometry("800x600")
        
        self.load_button = tk.Button(self, text="Load DICOM Series", command=self.load_dicom)
        self.load_button.pack()
        
        self.name_button = tk.Button(self, text="Name Structure", command=self.name_structure)
        self.name_button.pack()
        
        self.color_button = tk.Button(self, text="Select Color", command=self.select_color)
        self.color_button.pack()
        
        self.contour_button = tk.Button(self, text="Contour Structure", command=self.contour_image)
        self.contour_button.pack()
        
        self.canvas = tk.Canvas(self, width=512, height=512)
        self.canvas.pack()
        
        self.img = None
        self.volume = None
        self.structure_name = None
        self.color = (0, 255, 0)  # Default color is green

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
        
    def name_structure(self):
        self.structure_name = simpledialog.askstring("Input", "Enter the name of the structure:")
        
    def select_color(self):
        color_code = colorchooser.askcolor(title="Choose color")
        if color_code:
            self.color = tuple(int(c) for c in color_code[0])

    def contour_image(self):
        if self.volume is not None and self.structure_name:
            contour_dicom(self.volume, self.structure_name, self.color)
        else:
            messagebox.showerror("Error", "Please load a DICOM series and name the structure first.")

if __name__ == "__main__":
    app = DICOMViewer()
    app.mainloop()
