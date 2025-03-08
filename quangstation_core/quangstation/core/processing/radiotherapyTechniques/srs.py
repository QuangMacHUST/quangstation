import logging
from typing import List, Dict, Any, Optional, Sequence, Union, Tuple
import numpy as np

from quangstation.core.data import ROIContour, ROIMask
from quangstation.core.data.images import CTImage, DoseImage
from quangstation.core.data.plan import RTPlan, PlanPhotonBeam
from quangstation.core.processing.radiotherapyTechniques.baseTechnique import RadiotherapyTechnique

logger = logging.getLogger(__name__)

class SRS(RadiotherapyTechnique):
    """
    Stereotactic Radiosurgery (SRS) technique.
    
    SRS delivers precisely-targeted radiation at much higher doses,
    typically in a single session, to treat small brain tumors and 
    other brain disorders.
    """
    
    def __init__(self):
        super().__init__("SRS")
        self._num_arcs = 3  # Multiple arcs are common in SRS
        self._beam_energy = 6  # MV
        self._control_points_per_arc = 90  # 4-degree spacing
        self._collimator_angles = [0, 45, 90]  # Different collimator angles for each arc
        self._couch_angles = [0, 0, 0]  # Default to coplanar beams
        
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
        
        # Adjust collimator angles if needed
        if len(self._collimator_angles) != value:
            # Distribute collimator angles evenly
            step = 90 / max(value, 1)
            self._collimator_angles = [i * step for i in range(value)]
            
        # Adjust couch angles if needed
        if len(self._couch_angles) != value:
            # Default to all coplanar (0 degrees)
            self._couch_angles = [0] * value
            
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
    def collimator_angles(self) -> List[float]:
        """Get the collimator angles for each arc"""
        return self._collimator_angles
    
    @collimator_angles.setter
    def collimator_angles(self, values: List[float]) -> None:
        """Set the collimator angles for each arc"""
        if len(values) != self._num_arcs:
            raise ValueError(f"Must provide {self._num_arcs} collimator angles")
        self._collimator_angles = values
        
    @property
    def couch_angles(self) -> List[float]:
        """Get the couch angles for each arc"""
        return self._couch_angles
    
    @couch_angles.setter
    def couch_angles(self, values: List[float]) -> None:
        """Set the couch angles for each arc"""
        if len(values) != self._num_arcs:
            raise ValueError(f"Must provide {self._num_arcs} couch angles")
        self._couch_angles = values
    
    def createPlan(self, ct: CTImage, targets: List[Union[ROIContour, ROIMask]], 
                  oars: List[Union[ROIContour, ROIMask]], prescriptions: List[float]) -> RTPlan:
        """
        Create an SRS plan.
        
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
            The created SRS plan
        """
        if not targets:
            raise ValueError("At least one target must be specified")
        
        if len(targets) != len(prescriptions):
            raise ValueError("Number of targets must match number of prescriptions")
        
        # Create a new photon plan
        plan = RTPlan(name="SRS Plan", patient=ct.patient)
        plan.numberOfFractionsPlanned = 1  # SRS typically uses a single fraction
        
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
            beam.isVMAT = True  # Use VMAT delivery for SRS arcs
            beam.sad = 1000  # 100cm = 1000mm (standard SAD)
            beam.energy = self._beam_energy
            
            # Set isocenter to target center
            beam.isocenter = target_center
            
            # Set collimator angle for this arc
            beam.collimatorAngle = self._collimator_angles[arc_idx]
            
            # Set couch angle for this arc
            beam.couchAngle = self._couch_angles[arc_idx]
            
            # Set arc parameters
            # Each arc covers 360 degrees
            start_angle = 0
            stop_angle = 360
            
            beam.arcStartAngle = start_angle
            beam.arcStopAngle = stop_angle
            beam.arcDirection = 1  # 1 = clockwise, -1 = counterclockwise
            
            # Create control points along the arc
            control_point_spacing = (stop_angle - start_angle) / self._control_points_per_arc
            for cp_idx in range(self._control_points_per_arc + 1):  # +1 to include end point
                angle = start_angle + cp_idx * control_point_spacing
                
                # For SRS, typically use small apertures (cones or small MLC apertures)
                # Get target volume to determine aperture size
                target_volume = 0
                if isinstance(targets[0], ROIMask):
                    target_volume = targets[0].getVolume()
                else:  # ROIContour
                    # Get binary mask first
                    mask = targets[0].getBinaryMask(
                        origin=ct.origin, 
                        gridSize=ct.gridSize, 
                        spacing=ct.spacing
                    )
                    # Calculate volume
                    target_volume = np.sum(mask) * np.prod(ct.spacing) / 1000.0  # cm³
                
                # Calculate aperture size based on target volume
                # This is a simple approximation - real SRS planning would be more complex
                # Convert volume to equivalent sphere radius
                radius = ((3 * target_volume) / (4 * np.pi))**(1/3) * 10  # mm
                
                # Create an MLC aperture or cone size based on target radius
                # For MLC-based SRS:
                mlc_positions = self._get_mlc_positions_for_srs(angle, targets[0], radius)
                
                # Create a control point
                cp = {
                    'gantryAngle': angle,
                    'collimatorAngle': beam.collimatorAngle,
                    'couchAngle': beam.couchAngle,
                    'doseRate': 600,  # MU/min
                    'mlcPositions': mlc_positions,
                    'jawPositions': {'X1': -radius, 'X2': radius, 'Y1': -radius, 'Y2': radius},  # mm
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
        Optimize an SRS plan.
        
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
        
        # SRS optimization is similar to VMAT optimization but with stricter constraints
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
                    # In SRS, conformality is extremely important
                    if 'mlcPositions' in cp:
                        for leaf_idx in range(0, len(cp['mlcPositions']), 2):
                            if leaf_idx + 1 < len(cp['mlcPositions']):
                                # Smaller adjustments for SRS (tighter control)
                                adjustment = np.random.uniform(-0.2, 0.2)
                                cp['mlcPositions'][leaf_idx] += adjustment
                                cp['mlcPositions'][leaf_idx+1] -= adjustment
        
        # Signal that plan was updated
        self.planUpdatedSignal.emit(plan)
        
        return plan
    
    def calculateDose(self, plan: RTPlan, ct: CTImage) -> DoseImage:
        """
        Calculate dose for an SRS plan.
        
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
        
        # SRS dose calculation is similar to VMAT but higher resolution may be needed
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
                # For SRS, we might use a more precise calculation model
                cp_dose = self._calculate_srs_control_point_dose(cp, beam, ct)
                
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
    
    def _calculate_srs_control_point_dose(self, control_point, beam, ct):
        """
        Calculate dose contribution from a single SRS control point.
        Similar to VMAT but with sharper penumbra.
        
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
        
        # Get angles
        gantry_angle = control_point.get('gantryAngle', 0)
        collimator_angle = control_point.get('collimatorAngle', 0)
        couch_angle = control_point.get('couchAngle', 0)
        
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
        
        # Get isocenter
        if beam.isocenter is not None:
            iso_x, iso_y, iso_z = beam.isocenter
        else:
            # Default to center of image
            iso_x = ct.origin[0] + ct.gridSize[0] * ct.spacing[0] / 2
            iso_y = ct.origin[1] + ct.gridSize[1] * ct.spacing[1] / 2
            iso_z = ct.origin[2] + ct.gridSize[2] * ct.spacing[2] / 2
        
        # Convert angles to radians
        gantry_rad = np.radians(gantry_angle)
        collimator_rad = np.radians(collimator_angle)
        couch_rad = np.radians(couch_angle)
        
        # For SRS with non-coplanar beams, we need to consider couch rotation
        # Create beam axis vectors considering all rotations
        # This is a simplified model - real calculation would involve complex rotations
        
        # Basic beam direction (gantry at 0 points along negative z)
        beam_axis = np.array([0, 0, -1])
        
        # Apply gantry rotation
        beam_axis = np.array([
            np.sin(gantry_rad),
            0,
            -np.cos(gantry_rad)
        ])
        
        # Apply couch rotation (simplified - real calculation more complex)
        if couch_angle != 0:
            # Rotate beam direction around y-axis by couch angle
            beam_axis = np.array([
                beam_axis[0] * np.cos(couch_rad) + beam_axis[2] * np.sin(couch_rad),
                beam_axis[1],
                -beam_axis[0] * np.sin(couch_rad) + beam_axis[2] * np.cos(couch_rad)
            ])
        
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
        # For SRS, this would have a sharper penumbra
        mlc_effect = np.ones_like(dist_to_axis)
        
        if 'mlcPositions' in control_point:
            # Simplified MLC model with sharper falloff for SRS
            mlc_positions = control_point['mlcPositions']
            
            # Project points to beam's eye view coordinates
            # This is a simplified approach - real BEV coordinates more complex
            # especially with couch rotation
            
            # Calculate beam's eye view coordinates
            # For simplicity, we'll just use a basic projection
            # In a real system, this would incorporate all rotations correctly
            bev_x = v_x * np.cos(gantry_rad) - v_z * np.sin(gantry_rad)
            bev_y = v_y
            
            # Apply MLC effect - simplified as a series of rectangular openings
            leaf_width = 5.0  # mm (smaller leaf width for SRS)
            mlc_effect = np.zeros_like(dist_to_axis)
            
            for i in range(0, len(mlc_positions), 2):
                if i+1 < len(mlc_positions):
                    left_pos = mlc_positions[i]
                    right_pos = mlc_positions[i+1]
                    
                    # Y position of this leaf pair
                    leaf_y_min = -50 + i/2 * leaf_width  # Smaller field size for SRS
                    leaf_y_max = leaf_y_min + leaf_width
                    
                    # Create aperture for this leaf pair
                    # SRS has sharper penumbra, so we use a steeper falloff
                    distance_to_edge_x = np.minimum(
                        np.abs(bev_x - left_pos),
                        np.abs(bev_x - right_pos)
                    )
                    distance_to_edge_y = np.minimum(
                        np.abs(bev_y - leaf_y_min),
                        np.abs(bev_y - leaf_y_max)
                    )
                    
                    # Inside aperture
                    inside = ((bev_x >= left_pos) & (bev_x <= right_pos) & 
                             (bev_y >= leaf_y_min) & (bev_y <= leaf_y_max))
                    
                    # Penumbra region (sharper for SRS)
                    penumbra_width = 1.0  # mm (smaller for SRS)
                    
                    # Create penumbra effect - exponential falloff
                    penumbra = np.zeros_like(dist_to_axis)
                    edge_mask = (~inside) & ((distance_to_edge_x <= penumbra_width) | 
                                           (distance_to_edge_y <= penumbra_width))
                    
                    if np.any(edge_mask):
                        min_distance = np.minimum(distance_to_edge_x, distance_to_edge_y)
                        penumbra[edge_mask] = np.exp(-3.0 * min_distance[edge_mask] / penumbra_width)
                    
                    # Combine
                    aperture = inside.astype(float) + penumbra
                    
                    # Add to overall MLC effect
                    mlc_effect = np.maximum(mlc_effect, aperture)
        
        # Simple beam model: exponential falloff with depth, gaussian profile, MLC modulation
        # For SRS, we use a sharper penumbra
        mu = 0.0063 * ct.imageArray  # Attenuation coefficient depends on CT number
        sigma = 15.0  # mm - beam width parameter (smaller for SRS)
        
        # Depth dose: exponential attenuation
        depth_dose = np.exp(-mu * depth)
        
        # Lateral dose: gaussian with sharper falloff for SRS
        lateral_dose = np.exp(-0.5 * (dist_to_axis / sigma)**2)
        
        # Combine for final dose
        dose_array = depth_dose * lateral_dose * mlc_effect
        
        # Apply energy effect
        dose_array *= beam.energy / 6.0  # Normalized to 6MV
        
        return dose_array
    
    def _get_mlc_positions_for_srs(self, gantry_angle, target, radius):
        """
        Create MLC positions for SRS.
        For SRS, apertures are typically smaller and more conformal.
        
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
        # For SRS, we typically use smaller leaf width MLCs and tighter margins
        # This is a simplified model - real planning would project target at each angle
        
        # Standard 60-leaf MLC (30 pairs) with 2.5mm leaf width for SRS
        mlc_positions = []
        
        # Create a circular aperture based on target radius
        # In a real system, this would be based on projecting the target shape
        for i in range(30):  # 30 leaf pairs
            # Y position of this leaf pair
            leaf_y_min = -50 + i * 2.5  # mm, leaf width for SRS
            leaf_y_mid = leaf_y_min + 1.25  # Center of leaf
            
            # For a circular aperture, calculate x positions
            # Distance from isocenter in y direction
            dist_y = abs(leaf_y_mid)
            
            if dist_y < radius:
                # Calculate x position for circular aperture
                x_pos = np.sqrt(radius**2 - dist_y**2)
                mlc_positions.extend([-x_pos, x_pos])
            else:
                # Outside target radius - close leaves
                mlc_positions.extend([0, 0])
        
        return mlc_positions 