import logging
from typing import List, Dict, Any, Optional, Sequence, Union, Tuple
import numpy as np

from quangstation.core.data import ROIContour, ROIMask
from quangstation.core.data.images import CTImage, DoseImage
from quangstation.core.data.plan import RTPlan, PlanPhotonBeam
from quangstation.core.processing.radiotherapyTechniques.baseTechnique import RadiotherapyTechnique

logger = logging.getLogger(__name__)

class ThreeDCRT(RadiotherapyTechnique):
    """
    3D Conformal Radiation Therapy (3DCRT) technique.
    
    3DCRT uses beams shaped to match the contour of the target
    from different directions.
    """
    
    def __init__(self):
        super().__init__("3DCRT")
        self._num_beams = 4
        self._beam_energy = 6  # MV
        
    @property
    def num_beams(self) -> int:
        """Get the number of beams"""
        return self._num_beams
    
    @num_beams.setter
    def num_beams(self, value: int) -> None:
        """Set the number of beams"""
        if value < 1:
            raise ValueError("Number of beams must be at least 1")
        self._num_beams = value
        
    @property
    def beam_energy(self) -> float:
        """Get the beam energy in MV"""
        return self._beam_energy
    
    @beam_energy.setter
    def beam_energy(self, value: float) -> None:
        """Set the beam energy in MV"""
        if value <= 0:
            raise ValueError("Beam energy must be positive")
        self._beam_energy = value
    
    def createPlan(self, ct: CTImage, targets: List[Union[ROIContour, ROIMask]], 
                  oars: List[Union[ROIContour, ROIMask]], prescriptions: List[float]) -> RTPlan:
        """
        Create a 3DCRT plan.
        
        Parameters
        ----------
        ct : CTImage
            The planning CT image
        targets : List[Union[ROIContour, ROIMask]]
            List of target structures
        oars : List[Union[ROIContour, ROIMask]]
            List of organs at risk
        prescriptions : List[float]
            List of prescription doses for targets (in Gy)
            
        Returns
        -------
        RTPlan
            The created 3DCRT plan
        """
        if not targets:
            raise ValueError("At least one target must be specified")
        
        if len(targets) != len(prescriptions):
            raise ValueError("Number of targets must match number of prescriptions")
        
        # Create a new photon plan
        plan = RTPlan(name="3DCRT Plan", patient=ct.patient)
        plan.numberOfFractionsPlanned = 30  # Default fractionation
        
        # Get the center of the primary target
        target_center = None
        if isinstance(targets[0], ROIContour):
            target_center = targets[0].getCenterOfMass(
                origin=ct.origin, 
                gridSize=ct.gridSize, 
                spacing=ct.spacing
            )
        else:  # ROIMask
            target_center = targets[0].centerOfMass
        
        # Calculate beam angles for equally spaced beams
        angle_increment = 360 / self._num_beams
        
        # Create beams
        for i in range(self._num_beams):
            angle = i * angle_increment
            
            # Create a photon beam
            beam = PlanPhotonBeam()
            beam.beamName = f"Beam_{i+1}"
            beam.gantryAngle = angle
            beam.collimatorAngle = 0
            beam.couchAngle = 0
            beam.sad = 1000  # 100cm = 1000mm (standard SAD)
            beam.energy = self._beam_energy
            
            # Set isocenter to target center
            beam.isocenter = target_center
            
            # Set aperture based on target
            # For simplicity, we're creating a basic rectangular aperture
            # This would be more complex in a real system with MLC
            if isinstance(targets[0], ROIMask):
                # Project target onto beam's eye view and set aperture
                # This is simplified - real implementation would use ray tracing
                beam.setApertureFromTarget(targets[0])
            else:
                # Default aperture if we can't calculate from ROI
                beam.setDefaultAperture(width=80, height=80)  # mm
            
            # Add beam to plan
            plan.appendBeam(beam)
        
        # Set prescription
        total_prescription = sum(prescriptions)
        for i, beam in enumerate(plan.beams):
            # Equal weight to all beams
            beam.weight = 1.0 / self._num_beams
            beam.mu = total_prescription * 100 / self._num_beams  # Simplified MU calculation
        
        # Emit signal that plan was created
        self.planCreatedSignal.emit(plan)
        
        return plan
    
    def optimizePlan(self, plan: RTPlan, iterations: int = 100) -> RTPlan:
        """
        Optimize a 3DCRT plan.
        
        For 3DCRT, optimization is mainly about adjusting beam weights and shapes.
        
        Parameters
        ----------
        plan : RTPlan
            The plan to optimize
        iterations : int, optional
            Number of optimization iterations, by default 100
            
        Returns
        -------
        RTPlan
            The optimized plan
        """
        if not plan or not plan.beams:
            raise ValueError("Invalid plan or plan with no beams")
        
        # For 3DCRT, optimization is limited compared to IMRT/VMAT
        # We'll implement a simple forward planning approach
        
        # Adjust weights for better coverage
        # This is a simplified version - real optimization would be more complex
        total_weight = 1.0
        num_beams = len(plan.beams)
        
        for i, beam in enumerate(plan.beams):
            # Simple weight adjustment - in reality this would be based on dose calculation
            beam.weight = total_weight / num_beams
        
        # Signal that plan was updated
        self.planUpdatedSignal.emit(plan)
        
        return plan
    
    def calculateDose(self, plan: RTPlan, ct: CTImage) -> DoseImage:
        """
        Calculate dose for a 3DCRT plan.
        
        Parameters
        ----------
        plan : RTPlan
            The treatment plan
        ct : CTImage
            The planning CT image
            
        Returns
        -------
        DoseImage
            The calculated dose distribution
        """
        if not plan or not plan.beams:
            raise ValueError("Invalid plan or plan with no beams")
        
        # Create empty dose image with same dimensions as CT
        dose = DoseImage.createEmptyDoseWithSameMetaData(ct)
        
        # Signal progress start
        self.computationProgressSignal.emit(0)
        
        # Calculate dose contribution from each beam
        # This is highly simplified - real dose calculation would use ray tracing or Monte Carlo
        for i, beam in enumerate(plan.beams):
            # Simulate a simple dose distribution for each beam
            beam_dose = self._calculate_beam_dose(beam, ct)
            
            # Add weighted contribution to total dose
            dose.imageArray += beam_dose * beam.weight
            
            # Signal progress
            progress = (i + 1) / len(plan.beams) * 100
            self.computationProgressSignal.emit(progress)
        
        # Signal progress complete
        self.computationProgressSignal.emit(100)
        
        return dose
    
    def _calculate_beam_dose(self, beam: PlanPhotonBeam, ct: CTImage) -> np.ndarray:
        """
        Calculate dose contribution from a single beam.
        This is a simplified model - real dose calculation would be more complex.
        
        Parameters
        ----------
        beam : PlanPhotonBeam
            The beam
        ct : CTImage
            The CT image
            
        Returns
        -------
        np.ndarray
            The dose distribution from this beam
        """
        # Create empty dose array
        dose_array = np.zeros_like(ct.imageArray)
        
        # Get grid coordinates
        x_grid, y_grid, z_grid = np.meshgrid(
            np.arange(ct.gridSize[0]),
            np.arange(ct.gridSize[1]),
            np.arange(ct.gridSize[2]),
            indexing='ij'
        )
        
        # Convert to physical coordinates
        x_phys = ct.origin[0] + x_grid * ct.spacing[0]
        y_phys = ct.origin[1] + y_grid * ct.spacing[1]
        z_phys = ct.origin[2] + z_grid * ct.spacing[2]
        
        # Calculate distance from each point to isocenter
        if beam.isocenter is not None:
            iso_x, iso_y, iso_z = beam.isocenter
            distance = np.sqrt(
                (x_phys - iso_x)**2 + 
                (y_phys - iso_y)**2 + 
                (z_phys - iso_z)**2
            )
        else:
            # Default to center of image if isocenter not set
            center = np.array([
                ct.origin[i] + ct.gridSize[i] * ct.spacing[i] / 2 
                for i in range(3)
            ])
            distance = np.sqrt(
                (x_phys - center[0])**2 + 
                (y_phys - center[1])**2 + 
                (z_phys - center[2])**2
            )
        
        # Convert gantry angle to radians
        angle_rad = np.radians(beam.gantryAngle)
        
        # Calculate beam axis vector
        beam_axis = np.array([
            np.sin(angle_rad),
            0,
            -np.cos(angle_rad)
        ])
        
        # For simplicity, calculate distance from point to beam central axis
        # This is a simplified approach - real calculation would be more complex
        if beam.isocenter is not None:
            # Vector from isocenter to each point
            v_x = x_phys - iso_x
            v_y = y_phys - iso_y
            v_z = z_phys - iso_z
            
            # Cross product magnitude gives distance to line
            dist_to_axis = np.sqrt(
                (v_y * beam_axis[2] - v_z * beam_axis[1])**2 +
                (v_z * beam_axis[0] - v_x * beam_axis[2])**2 +
                (v_x * beam_axis[1] - v_y * beam_axis[0])**2
            )
            
            # Project on beam axis to get depth
            depth = v_x * beam_axis[0] + v_y * beam_axis[1] + v_z * beam_axis[2]
            
            # Simple beam model: exponential falloff with depth, gaussian profile
            # These parameters would be beam-energy dependent in a real system
            mu = 0.0063 * ct.imageArray  # Attenuation coefficient depends on CT number
            sigma = 30.0  # mm - beam width parameter
            
            # Depth dose: exponential attenuation
            depth_dose = np.exp(-mu * depth)
            
            # Lateral dose: gaussian
            lateral_dose = np.exp(-0.5 * (dist_to_axis / sigma)**2)
            
            # Combine for final dose
            dose_array = depth_dose * lateral_dose
            
            # Scale by beam energy
            dose_array *= beam.energy / 6.0  # Normalized to 6MV
        
        return dose_array 