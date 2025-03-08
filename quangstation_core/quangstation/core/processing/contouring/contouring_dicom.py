import cv2
import numpy as np
import logging

from quangstation.core.data.images import Image3D, CTImage
from quangstation.core.data import ROIContour
from quangstation.core import Event

logger = logging.getLogger(__name__)

class ContouringTool:
    """
    Interactive tool for manual contouring of medical images.
    Allows drawing contours on 2D slices of a 3D volume.
    """
    
    def __init__(self):
        self.contourChangedSignal = Event()
        self.contourCompletedSignal = Event()
        self._reset_state()
        
    def _reset_state(self):
        self.drawing = False
        self.mode = True  # True for rectangle, False for freehand
        self.ix, self.iy = -1, -1
        self.contour_points = []
        self.current_slice = 0
        self.total_slices = 0
        self.contour_slices = {}  # Dictionary to store contours for each slice
        self.image_3d = None
        self.current_image = None
        self.current_display = None
        self.structure_name = ""
        self.color = (0, 255, 0)
        
    def draw_contour(self, event, x, y, flags, param):
        """Mouse callback function for drawing"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y
            if not self.mode:  # Freehand mode
                self.contour_points.append((x, y))
                
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                if self.mode:  # Rectangle mode
                    img_copy = self.current_display.copy()
                    cv2.rectangle(img_copy, (self.ix, self.iy), (x, y), self.color, 2)
                    cv2.imshow(f'Contouring: {self.structure_name} - Slice {self.current_slice+1}/{self.total_slices}', img_copy)
                else:  # Freehand mode
                    self.contour_points.append((x, y))
                    cv2.line(self.current_display, self.contour_points[-2], self.contour_points[-1], self.color, 2)
                    cv2.imshow(f'Contouring: {self.structure_name} - Slice {self.current_slice+1}/{self.total_slices}', self.current_display)
                    
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            if self.mode:  # Rectangle mode
                cv2.rectangle(self.current_display, (self.ix, self.iy), (x, y), self.color, 2)
                # Save rectangle points
                self.contour_points = [(self.ix, self.iy), (x, self.iy), (x, y), (self.ix, y)]
            # Emit signal that contour changed
            self.contourChangedSignal.emit(self.current_slice, self.contour_points)
    
    def start_contouring(self, image_3d, structure_name, contour_color=(0, 255, 0)):
        """
        Start the contouring process on a 3D image
        
        Parameters
        ----------
        image_3d : Image3D
            3D image to contour
        structure_name : str
            Name of the structure being contoured
        contour_color : tuple
            RGB color tuple for display
        """
        self._reset_state()
        self.image_3d = image_3d
        self.structure_name = structure_name
        self.color = contour_color
        self.total_slices = image_3d.imageArray.shape[0]
        
        self._show_current_slice()
        
        cv2.namedWindow(f'Contouring: {self.structure_name} - Slice {self.current_slice+1}/{self.total_slices}')
        cv2.setMouseCallback(f'Contouring: {self.structure_name} - Slice {self.current_slice+1}/{self.total_slices}', 
                            lambda event, x, y, flags, param: self.draw_contour(event, x, y, flags, param))
        
        self._contouring_interface_loop()
        
        return self._create_roi_contour()
    
    def _show_current_slice(self):
        """Prepare and display the current slice"""
        self.current_image = self.image_3d.imageArray[self.current_slice].copy()
        
        # Normalize to 0-255 for display
        norm_image = cv2.normalize(self.current_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        self.current_display = cv2.cvtColor(norm_image, cv2.COLOR_GRAY2BGR)
        
        # If this slice already has contours, draw them
        if self.current_slice in self.contour_slices:
            points = self.contour_slices[self.current_slice]
            if len(points) > 2:
                points_array = np.array(points, dtype=np.int32)
                cv2.polylines(self.current_display, [points_array], True, self.color, 2)
        
        window_name = f'Contouring: {self.structure_name} - Slice {self.current_slice+1}/{self.total_slices}'
        cv2.imshow(window_name, self.current_display)
        
        # Update window name and mouse callback for the new slice
        cv2.setMouseCallback(window_name, 
                           lambda event, x, y, flags, param: self.draw_contour(event, x, y, flags, param))
    
    def _contouring_interface_loop(self):
        """Main loop for the contouring interface"""
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('m'):  # Toggle between rectangle and freehand mode
                self.mode = not self.mode
                if self.mode:
                    logger.info("Switched to rectangle mode")
                else:
                    logger.info("Switched to freehand mode")
                    
            elif key == ord('c'):  # Clear current contour
                self.contour_points = []
                if self.current_slice in self.contour_slices:
                    del self.contour_slices[self.current_slice]
                self._show_current_slice()
                
            elif key == ord('s'):  # Save current contour
                if len(self.contour_points) > 2:
                    self.contour_slices[self.current_slice] = self.contour_points.copy()
                    logger.info(f"Saved contour for slice {self.current_slice+1}")
                
            elif key == ord('n') or key == ord('d'):  # Next slice
                if len(self.contour_points) > 2:
                    self.contour_slices[self.current_slice] = self.contour_points.copy()
                self.current_slice = min(self.current_slice + 1, self.total_slices - 1)
                self.contour_points = []
                self._show_current_slice()
                
            elif key == ord('p') or key == ord('a'):  # Previous slice
                if len(self.contour_points) > 2:
                    self.contour_slices[self.current_slice] = self.contour_points.copy()
                self.current_slice = max(self.current_slice - 1, 0)
                self.contour_points = []
                self._show_current_slice()
                
            elif key == 27 or key == ord('q'):  # ESC or q to quit
                break
        
        cv2.destroyAllWindows()
        # Emit signal that contouring is completed
        self.contourCompletedSignal.emit()
        
    def _create_roi_contour(self):
        """Convert all saved contours to a ROIContour object"""
        if not self.contour_slices:
            logger.warning("No contours created.")
            return None
            
        # Create new ROIContour
        roi_contour = ROIContour(name=self.structure_name, displayColor=self.color)
        
        # Add all contour points from all slices
        spacing = self.image_3d.spacing
        origin = self.image_3d.origin
        
        for slice_idx, points in self.contour_slices.items():
            # Skip slices with too few points
            if len(points) < 3:
                continue
                
            # Convert points to physical coordinates
            physical_points = []
            for x, y in points:
                # Convert pixel coordinates to physical coordinates
                physical_x = origin[0] + x * spacing[0]
                physical_y = origin[1] + y * spacing[1]
                physical_z = origin[2] + slice_idx * spacing[2]
                physical_points.append((physical_x, physical_y, physical_z))
            
            # Add contour to ROIContour object
            roi_contour.addContour(physical_points)
            
        logger.info(f"Created ROI contour '{self.structure_name}' with contours on {len(self.contour_slices)} slices")
        return roi_contour


# Function to start contouring that can be easily called from the UI
def start_contouring(image, structure_name, contour_color=(0, 255, 0)):
    """
    Start the interactive contouring process for a 3D image
    
    Parameters
    ----------
    image : Image3D
        3D image to contour (CT, MRI, etc.)
    structure_name : str
        Name of the structure to contour
    contour_color : tuple
        RGB color tuple for display
        
    Returns
    -------
    ROIContour
        The created ROI contour object, or None if canceled
    """
    if not isinstance(image, Image3D):
        raise TypeError("Image must be an instance of Image3D")
        
    tool = ContouringTool()
    return tool.start_contouring(image, structure_name, contour_color)
