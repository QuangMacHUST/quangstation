import logging
import numpy as np
from typing import Optional

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QComboBox, QLineEdit, QColorDialog, QMessageBox)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

from quangstation.core.data.images import Image3D, CTImage
from quangstation.core.data import ROIContour
from quangstation.core.processing.contouring import start_contouring

logger = logging.getLogger(__name__)

class ContouringPanel(QWidget):
    """
    Panel for manual contouring of medical images.
    """
    
    def __init__(self, viewController):
        super().__init__()
        self._viewController = viewController
        self._selectedColor = QColor(0, 255, 0)  # Default green
        self._setupUI()
        
    def _setupUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Image selection section
        imageSelectionLayout = QVBoxLayout()
        layout.addLayout(imageSelectionLayout)
        
        imageLabel = QLabel("Select Image:")
        imageSelectionLayout.addWidget(imageLabel)
        
        self._imageComboBox = QComboBox()
        self._imageComboBox.setToolTip("Select a 3D image for contouring")
        imageSelectionLayout.addWidget(self._imageComboBox)
        
        # ROI name section
        roiNameLayout = QHBoxLayout()
        layout.addLayout(roiNameLayout)
        
        roiNameLabel = QLabel("ROI Name:")
        roiNameLayout.addWidget(roiNameLabel)
        
        self._roiNameEdit = QLineEdit()
        self._roiNameEdit.setPlaceholderText("Enter ROI name")
        roiNameLayout.addWidget(self._roiNameEdit)
        
        # Color selection button
        colorLayout = QHBoxLayout()
        layout.addLayout(colorLayout)
        
        colorLabel = QLabel("Color:")
        colorLayout.addWidget(colorLabel)
        
        self._colorButton = QPushButton()
        self._colorButton.setFixedSize(24, 24)
        self._updateColorButton()
        self._colorButton.clicked.connect(self._selectColor)
        colorLayout.addWidget(self._colorButton)
        colorLayout.addStretch()
        
        # Start contouring button
        self._startButton = QPushButton("Start Contouring")
        self._startButton.clicked.connect(self._startContouring)
        layout.addWidget(self._startButton)
        
        # Spacer
        layout.addStretch()
        
        # Update available images when tab is shown
        self.showEvent = lambda event: self._updateImageList()
        
    def _updateImageList(self):
        """Update the list of available images for contouring"""
        self._imageComboBox.clear()
        
        # Get current patient
        patient = self._viewController.currentPatient
        if not patient:
            return
        
        # Add CT images
        for ct in patient.dataDict.get('CTs', []):
            self._imageComboBox.addItem(f"CT: {ct.name}", ct)
            
        # Add MR images
        for mr in patient.dataDict.get('MRIs', []):
            self._imageComboBox.addItem(f"MR: {mr.name}", mr)
    
    def _selectColor(self):
        """Open color dialog to select ROI color"""
        color = QColorDialog.getColor(self._selectedColor, self, "Select ROI Color")
        if color.isValid():
            self._selectedColor = color
            self._updateColorButton()
    
    def _updateColorButton(self):
        """Update the color button to show the selected color"""
        self._colorButton.setStyleSheet(
            f"background-color: rgb({self._selectedColor.red()}, {self._selectedColor.green()}, {self._selectedColor.blue()});"
        )
    
    def _startContouring(self):
        """Start the contouring process"""
        # Get selected image
        if self._imageComboBox.count() == 0:
            QMessageBox.warning(self, "No Image", "No image available for contouring")
            return
        
        image = self._imageComboBox.currentData()
        if not isinstance(image, Image3D):
            QMessageBox.warning(self, "Invalid Image", "Selected item is not a valid 3D image")
            return
        
        # Get ROI name
        roi_name = self._roiNameEdit.text().strip()
        if not roi_name:
            QMessageBox.warning(self, "Missing Name", "Please enter a name for the ROI")
            return
        
        # Get color
        color = (self._selectedColor.red(), self._selectedColor.green(), self._selectedColor.blue())
        
        try:
            # Check if OpenCV is installed
            import cv2
        except ImportError:
            QMessageBox.critical(self, "Missing Dependency", 
                              "OpenCV (cv2) is required for contouring but not installed.\n"
                              "Please install it using: pip install opencv-python")
            return
        
        # Start contouring process
        try:
            roi_contour = start_contouring(image, roi_name, color)
            
            if roi_contour:
                # Add the contour to the patient
                patient = self._viewController.currentPatient
                if patient:
                    patient.addROIContour(roi_contour)
                    
                    # Show the contour in the viewer
                    self._viewController.showContour(roi_contour)
                    
                    QMessageBox.information(self, "Success", f"ROI '{roi_name}' created successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Could not add contour to patient")
            else:
                QMessageBox.warning(self, "Cancelled", "Contouring was cancelled or no contours were created")
                
        except Exception as e:
            logger.error(f"Error during contouring: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred during contouring:\n{str(e)}") 