import logging
from typing import List, Dict, Any, Optional, Sequence, Union, Tuple
import numpy as np

from quangstation.core.data import ROIContour, ROIMask
from quangstation.core.data.images import CTImage, DoseImage
from quangstation.core.data.plan import RTPlan, PlanPhotonBeam
from quangstation.core.processing.radiotherapyTechniques.baseTechnique import RadiotherapyTechnique
from quangstation.core.processing.radiotherapyTechniques.srs import SRS

logger = logging.getLogger(__name__)

class SBRT(SRS):
    """
    Stereotactic Body Radiation Therapy (SBRT) technique.
    
    SBRT is similar to SRS but applied to body tumors rather than brain.
    It delivers precisely-targeted radiation in fewer high-dose treatments
    than traditional therapy.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "SBRT"
        self._num_fractions = 5  # Typical SBRT uses 3-5 fractions
        
    @property
    def num_fractions(self) -> int:
        """Get the number of fractions"""
        return self._num_fractions
    
    @num_fractions.setter
    def num_fractions(self, value: int) -> None:
        """Set the number of fractions"""
        if value < 1:
            raise ValueError("Number of fractions must be at least 1")
        self._num_fractions = value
    
    def createPlan(self, ct: CTImage, targets: List[Union[ROIContour, ROIMask]], 
                  oars: List[Union[ROIContour, ROIMask]], prescriptions: List[float]) -> RTPlan:
        """
        Create an SBRT plan.
        
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
            The created SBRT plan
        """
        # Create plan using SRS technique
        plan = super().createPlan(ct, targets, oars, prescriptions)
        
        # Modify for SBRT
        plan.name = "SBRT Plan"
        plan.numberOfFractionsPlanned = self._num_fractions
        
        # SBRT may use more conformal planning with tighter OAR constraints
        # and different fractionation scheme
        
        # Adjust MU calculations for fractionation
        # In real planning, this would be based on dose calculation and prescription
        for beam in plan.beams:
            # Distribute MU across fractions
            beam.mu = beam.mu / self._num_fractions
        
        # Apply SBRT-specific customizations
        self._apply_sbrt_specific_settings(plan, targets, oars)
        
        # Emit signal that plan was created
        self.planCreatedSignal.emit(plan)
        
        return plan
    
    def _apply_sbrt_specific_settings(self, plan: RTPlan, targets: List[Union[ROIContour, ROIMask]],
                                     oars: List[Union[ROIContour, ROIMask]]) -> None:
        """
        Apply SBRT-specific settings to a plan.
        
        Parameters
        ----------
        plan : RTPlan
            The plan to modify
        targets : List[Union[ROIContour, ROIMask]]
            List of target structures
        oars : List[Union[ROIContour, ROIMask]]
            List of organs at risk
        """
        # Get target volume to adjust planning parameters
        target_volume = 0
        if isinstance(targets[0], ROIMask):
            target_volume = targets[0].getVolume()
        else:  # ROIContour
            # This would get the binary mask and calculate volume
            pass
        
        # SBRT typically uses larger margins than SRS
        # For simplicity we're adjusting aperture size by a factor
        for beam in plan.beams:
            for cp in beam.controlPoints:
                if 'mlcPositions' in cp:
                    # Adjust MLC positions for larger margins
                    # This is a simplified approach - real planning would be more sophisticated
                    for i in range(0, len(cp['mlcPositions']), 2):
                        if i+1 < len(cp['mlcPositions']):
                            # Adjust left leaf
                            if cp['mlcPositions'][i] < 0:
                                cp['mlcPositions'][i] *= 1.2  # Increase margin by 20%
                            # Adjust right leaf
                            if cp['mlcPositions'][i+1] > 0:
                                cp['mlcPositions'][i+1] *= 1.2  # Increase margin by 20%
                
                # Adjust jaw positions for larger field size
                if 'jawPositions' in cp:
                    for key in cp['jawPositions']:
                        cp['jawPositions'][key] *= 1.2  # Increase by 20%
    
    def optimizePlan(self, plan: RTPlan, iterations: int = 100) -> RTPlan:
        """
        Optimize an SBRT plan.
        
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
        # Use SRS optimization as base
        plan = super().optimizePlan(plan, iterations)
        
        # Add SBRT-specific optimization if needed
        # For example, SBRT might need different optimization constraints
        # for certain OARs compared to intracranial SRS
        
        # Signal that plan was updated
        self.planUpdatedSignal.emit(plan)
        
        return plan
    
    def calculateDose(self, plan: RTPlan, ct: CTImage) -> DoseImage:
        """
        Calculate dose for an SBRT plan.
        
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
        # Use SRS dose calculation as base
        dose = super().calculateDose(plan, ct)
        
        # Apply SBRT-specific dose calculation adjustments if needed
        # For example, SBRT might need to account for respiratory motion
        
        return dose
    
    def _get_mlc_positions_for_target(self, gantry_angle, target, radius):
        """
        Create MLC positions for SBRT.
        For SBRT, apertures are typically larger than SRS but still conformal.
        
        Parameters
        ----------
        gantry_angle : float
            Gantry angle in degrees
        target : Union[ROIContour, ROIMask]
            Target structure
        radius : float
            Approximate radius of target in mm
            
        Returns
        -------
        list
            List of MLC leaf positions
        """
        # Get base MLC positions from SRS implementation
        mlc_positions = self._get_mlc_positions_for_srs(gantry_angle, target, radius)
        
        # Apply SBRT-specific adjustments
        # For SBRT, we typically use larger margins around the target
        # This is simplified - real planning would use more sophisticated approach
        for i in range(len(mlc_positions)):
            # Add margin to MLC positions
            # Negative positions (left leaves) become more negative
            # Positive positions (right leaves) become more positive
            if mlc_positions[i] < 0:
                mlc_positions[i] *= 1.5  # Increase margin by 50%
            elif mlc_positions[i] > 0:
                mlc_positions[i] *= 1.5  # Increase margin by 50%
        
        return mlc_positions 