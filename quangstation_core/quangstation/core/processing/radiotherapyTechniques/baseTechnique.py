import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Sequence, Union, Tuple

import numpy as np

from quangstation.core import Event
from quangstation.core.data import ROIContour, ROIMask
from quangstation.core.data.images import CTImage, DoseImage
from quangstation.core.data.plan import RTPlan, PlanProtonBeam, PlanPhotonBeam, ObjectivesList

logger = logging.getLogger(__name__)

class RadiotherapyTechnique(ABC):
    """
    Abstract base class for all radiotherapy techniques.
    
    This class defines the common interface for all radiotherapy techniques
    including 3DCRT, VMAT, SRS, and SBRT.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.planCreatedSignal = Event()
        self.planUpdatedSignal = Event()
        self.computationProgressSignal = Event()
        self._objectives = ObjectivesList()
        
    @abstractmethod
    def createPlan(self, ct: CTImage, targets: List[Union[ROIContour, ROIMask]], 
                  oars: List[Union[ROIContour, ROIMask]], prescriptions: List[float]) -> RTPlan:
        """
        Create a treatment plan based on the technique.
        
        Parameters
        ----------
        ct : CTImage
            The planning CT image
        targets : List[Union[ROIContour, ROIMask]]
            List of target structures
        oars : List[Union[ROIContour, ROIMask]]
            List of organs at risk
        prescriptions : List[float]
            List of prescription doses for targets (in same order as targets)
            
        Returns
        -------
        RTPlan
            The created treatment plan
        """
        pass
    
    @abstractmethod
    def optimizePlan(self, plan: RTPlan, iterations: int = 100) -> RTPlan:
        """
        Optimize an existing plan.
        
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
        pass
    
    @abstractmethod
    def calculateDose(self, plan: RTPlan, ct: CTImage) -> DoseImage:
        """
        Calculate the dose for a given plan.
        
        Parameters
        ----------
        plan : RTPlan
            The treatment plan
        ct : CTImage
            The planning CT image
            
        Returns
        -------
        DoseImage
            The calculated dose image
        """
        pass
    
    def setObjectives(self, objectives: ObjectivesList) -> None:
        """
        Set the optimization objectives.
        
        Parameters
        ----------
        objectives : ObjectivesList
            The optimization objectives
        """
        self._objectives = objectives
    
    @property
    def objectives(self) -> ObjectivesList:
        """
        Get the optimization objectives.
        
        Returns
        -------
        ObjectivesList
            The optimization objectives
        """
        return self._objectives 