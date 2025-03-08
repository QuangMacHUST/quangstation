import logging
from typing import List, Dict, Any, Optional, Sequence, Union, Tuple
import numpy as np

from quangstation.core.data import ROIContour, ROIMask
from quangstation.core.data.images import CTImage, DoseImage
from quangstation.core.data.plan import RTPlan, PlanPhotonBeam
from quangstation.core.processing.radiotherapyTechniques.baseTechnique import RadiotherapyTechnique

logger = logging.getLogger(__name__)

class VMAT(RadiotherapyTechnique):
    """
    Volumetric Modulated Arc Therapy (VMAT) technique.
    
    VMAT delivers radiation by rotating the gantry around the patient
    with continuously varying beam aperture and dose rate.
    """
    
    def __init__(self):
        super().__init__("VMAT")
        self._num_arcs = 1
        self._beam_energy = 6  # MV
        self._control_points_per_arc = 90  # 4-degree spacing
        
    @property
    def num_arcs(self) -> int:
        """Get the number of arcs"""
        return self._num_arcs
    
    @num_arcs.setter
    def num_arcs(self, value: int) -> None:
        """Set the number of arcs"""
        if value < 1:
            raise ValueError("Number of arcs must be at least 1")
        self._num_arcs = value
        
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
        
    @property
    def control_points_per_arc(self) -> int:
        """Get the number of control points per arc"""
        return self._control_points_per_arc
    
    @control_points_per_arc.setter
    def control_points_per_arc(self, value: int) -> None:
        """Set the number of control points per arc"""
        if value < 10:
            raise ValueError("Number of control points must be at least 10")
        self._control_points_per_arc = value
    
    def createPlan(self, ct: CTImage, targets: List[Union[ROIContour, ROIMask]], 
                  oars: List[Union[ROIContour, ROIMask]], prescriptions: List[float]) -> RTPlan:
        """
        Create a VMAT plan.
        
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
            The created VMAT plan
        """
        if not targets:
            raise ValueError("At least one target must be specified")
        
        if len(targets) != len(prescriptions):
            raise ValueError("Number of targets must match number of prescriptions")
        
        # Create a new photon plan
        plan = RTPlan(name="VMAT Plan", patient=ct.patient)
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
        
        # Create arcs
        for arc_idx in range(self._num_arcs):
            # Create a photon beam to represent the arc
            beam = PlanPhotonBeam()
            beam.beamName = f"Arc_{arc_idx+1}"
            beam.isVMAT = True  # Flag as VMAT
            beam.sad = 1000  # 100cm = 1000mm (standard SAD)
            beam.energy = self._beam_energy
            
            # Set isocenter to target center
            beam.isocenter = target_center
            
            # Set arc parameters
            if self._num_arcs == 1:
                # Full 360-degree arc
                start_angle = 0
                stop_angle = 360
            else:
                # Divide 360 into equal arcs with different starting points
                arc_length = 360 / self._num_arcs
                start_angle = arc_idx * arc_length
                stop_angle = start_angle + arc_length
            
            beam.arcStartAngle = start_angle
            beam.arcStopAngle = stop_angle
            beam.arcDirection = 1  # 1 = clockwise, -1 = counterclockwise
            
            # Create control points along the arc
            control_point_spacing = (stop_angle - start_angle) / self._control_points_per_arc
            for cp_idx in range(self._control_points_per_arc + 1):  # +1 to include end point
                angle = start_angle + cp_idx * control_point_spacing
                
                # Create a control point
                cp = {
                    'gantryAngle': angle,
                    'collimatorAngle': 0,
                    'couchAngle': 0,
                    'doseRate': 600,  # MU/min
                    'mlcPositions': self._get_mlc_positions_for_target(angle, targets[0]),
                    'jawPositions': {'X1': -100, 'X2': 100, 'Y1': -100, 'Y2': 100},  # mm
                    'weight': 1.0 / self._control_points_per_arc
                }
                
                # Add control point to beam
                beam.addControlPoint(cp)
            
            # Add beam to plan
            plan.appendBeam(beam)
        
        # Set prescription
        total_prescription = sum(prescriptions)
        for beam in plan.beams:
            # Equal weight to all arcs
            beam.weight = 1.0 / self._num_arcs
            beam.mu = total_prescription * 100 / self._num_arcs  # Simplified MU calculation
        
        # Emit signal that plan was created
        self.planCreatedSignal.emit(plan)
        
        return plan
    
    def optimizePlan(self, plan: RTPlan, iterations: int = 100) -> RTPlan:
        """
        Optimize a VMAT plan.
        
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
        
        # For VMAT, optimization involves adjusting MLC positions, dose rates, etc.
        # This is a complex process that typically uses inverse planning
        # Here, we'll implement a simplified approach
        
        # Signal progress start
        self.computationProgressSignal.emit(0)
        
        # Simple iterative optimization
        for iter_idx in range(iterations):
            # Update progress
            progress = (iter_idx + 1) / iterations * 100
            self.computationProgressSignal.emit(progress)
            
            # For each beam (arc)
            for beam_idx, beam in enumerate(plan.beams):
                # For each control point
                for cp_idx, cp in enumerate(beam.controlPoints):
                    # Adjust MLC positions based on objectives
                    # In a real system, this would be based on dose calculation and objectives
                    # Here we're just making small random adjustments for demonstration
                    if 'mlcPositions' in cp:
                        for leaf_idx in range(len(cp['mlcPositions'])):
                            # Small random adjustment (would be based on cost function in real system)
                            adjustment = np.random.uniform(-0.5, 0.5)
                            cp['mlcPositions'][leaf_idx] += adjustment
                            
                    # Adjust dose rate for better delivery efficiency
                    if 'doseRate' in cp:
                        # Ensure dose rate is within valid range
                        cp['doseRate'] = max(100, min(600, cp['doseRate'] + np.random.uniform(-10, 10)))
        
        # Signal that plan was updated
        self.planUpdatedSignal.emit(plan)
        
        return plan
    
    def calculateDose(self, plan: RTPlan, ct: CTImage) -> DoseImage:
        """
        Calculate dose for a VMAT plan.
        
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
        
        # For each beam (arc)
        total_control_points = sum(len(beam.controlPoints) for beam in plan.beams)
        cp_count = 0
        
        for beam_idx, beam in enumerate(plan.beams):
            # Create dose grid for this arc
            arc_dose = np.zeros_like(ct.imageArray)
            
            # For each control point
            for cp_idx, cp in enumerate(beam.controlPoints):
                # Calculate contribution from this control point
                cp_dose = self._calculate_control_point_dose(cp, beam, ct)
                
                # Add to arc dose
                arc_dose += cp_dose * cp.get('weight', 1.0 / len(beam.controlPoints))
                
                # Update progress
                cp_count += 1
                progress = cp_count / total_control_points * 100
                self.computationProgressSignal.emit(progress)
            
            # Add arc contribution to total dose
            dose.imageArray += arc_dose * beam.weight
        
        # Signal progress complete
        self.computationProgressSignal.emit(100)
        
        return dose
    
    def _calculate_control_point_dose(self, control_point, beam, ct):
        """
        Calculate dose contribution from a single control point.
        This is a simplified model.
        
        Parameters
        ----------
        control_point : dict
            The control point data
        beam : PlanPhotonBeam
            The beam (arc) this control point belongs to
        ct : CTImage
            The CT image
            
        Returns
        -------
        np.ndarray
            The dose distribution from this control point
        """
        # Create empty dose array
        dose_array = np.zeros_like(ct.imageArray)
        
        # Get gantry angle
        angle = control_point.get('gantryAngle', 0)
        
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
        
        # Calculate beam axis
        angle_rad = np.radians(angle)
        beam_axis = np.array([
            np.sin(angle_rad),
            0,
            -np.cos(angle_rad)
        ])
        
        # Get isocenter
        if beam.isocenter is not None:
            iso_x, iso_y, iso_z = beam.isocenter
        else:
            # Default to center of image
            iso_x = ct.origin[0] + ct.gridSize[0] * ct.spacing[0] / 2
            iso_y = ct.origin[1] + ct.gridSize[1] * ct.spacing[1] / 2
            iso_z = ct.origin[2] + ct.gridSize[2] * ct.spacing[2] / 2
        
        # Vector from isocenter to each point
        v_x = x_phys - iso_x
        v_y = y_phys - iso_y
        v_z = z_phys - iso_z
        
        # Project onto beam direction to get depth
        depth = v_x * beam_axis[0] + v_y * beam_axis[1] + v_z * beam_axis[2]
        
        # Calculate perpendicular distance to beam axis
        dist_to_axis = np.sqrt(
            (v_y * beam_axis[2] - v_z * beam_axis[1])**2 +
            (v_z * beam_axis[0] - v_x * beam_axis[2])**2 +
            (v_x * beam_axis[1] - v_y * beam_axis[0])**2
        )
        
        # Apply MLC modulation effect
        # This is highly simplified - real calculation would be more complex
        mlc_effect = np.ones_like(dist_to_axis)
        
        if 'mlcPositions' in control_point:
            # Simplified MLC model - real one would be much more complex
            mlc_positions = control_point['mlcPositions']
            
            # Project points to beam's eye view coordinates
            bev_x = v_x * np.cos(angle_rad) - v_z * np.sin(angle_rad)
            bev_y = v_y
            
            # Apply MLC effect - simplified as a series of rectangular openings
            leaf_width = 5.0  # mm
            mlc_effect = np.zeros_like(dist_to_axis)
            
            for i in range(0, len(mlc_positions), 2):
                if i+1 < len(mlc_positions):
                    left_pos = mlc_positions[i]
                    right_pos = mlc_positions[i+1]
                    
                    # Y position of this leaf pair
                    leaf_y_min = -100 + i/2 * leaf_width
                    leaf_y_max = leaf_y_min + leaf_width
                    
                    # Create aperture for this leaf pair
                    aperture = ((bev_x >= left_pos) & (bev_x <= right_pos) & 
                               (bev_y >= leaf_y_min) & (bev_y <= leaf_y_max))
                    
                    # Add to overall MLC effect
                    mlc_effect = np.maximum(mlc_effect, aperture)
        
        # Simple beam model: exponential falloff with depth, gaussian profile, MLC modulation
        mu = 0.0063 * ct.imageArray  # Attenuation coefficient depends on CT number
        sigma = 30.0  # mm - beam width parameter
        
        # Depth dose: exponential attenuation
        depth_dose = np.exp(-mu * depth)
        
        # Lateral dose: gaussian
        lateral_dose = np.exp(-0.5 * (dist_to_axis / sigma)**2)
        
        # Combine for final dose
        dose_array = depth_dose * lateral_dose * mlc_effect
        
        # Apply energy effect
        dose_array *= beam.energy / 6.0  # Normalized to 6MV
        
        # Apply dose rate effect
        dose_rate = control_point.get('doseRate', 600) / 600.0  # Normalize to max rate
        dose_array *= dose_rate
        
        return dose_array
    
    def _get_mlc_positions_for_target(self, gantry_angle, target):
        """
        Create initial MLC positions to conform to target.
        This is a simplified version for demonstration.
        
        Parameters
        ----------
        gantry_angle : float
            Gantry angle in degrees
        target : Union[ROIContour, ROIMask]
            Target structure
            
        Returns
        -------
        list
            List of MLC leaf positions
        """
        # For simplicity, we'll return a basic MLC pattern
        # In a real system, this would project the target onto the beam's eye view
        # and calculate optimal leaf positions
        
        # Standard 60-leaf MLC (30 pairs)
        mlc_positions = []
        
        # Create a simple aperture - would be based on target shape in real system
        for i in range(30):  # 30 leaf pairs
            if 10 <= i <= 20:  # Create an opening in the middle
                mlc_positions.extend([-30, 30])  # Left and right leaves (mm)
            else:
                mlc_positions.extend([0, 0])  # Closed leaves
        
        return mlc_positions 