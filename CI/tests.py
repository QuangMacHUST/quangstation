
import os
import unittest

import numpy as np

from quangstation.core.data import PatientList
from quangstation.core.data.images import CTImage
from quangstation.core.data.images import ROIMask
from quangstation.core.data import Patient
from quangstation.core.io import mcsquareIO, scannerReader
from quangstation.core.processing.doseCalculation.doseCalculationConfig import DoseCalculationConfig
from quangstation.core.examples.registration import exampleMorphons
from quangstation.core.examples.segmentation import exampleSegmentation


def checkNoInit():
    import quangstation.core as quangstationCore
    path_to_file = os.path.join(quangstationCore.__path__[0], '..', '__init__.py')
    if os.path.exists(path_to_file):
        raise Exception("There cannot be any __init__.py in """ + path_to_file + " to comply with namespace package definition. Please remove this file!")

    path_to_file = os.path.join(quangstationCore.__path__[0], '..', 'quangstation', '__init__.py')
    if os.path.exists(path_to_file):
        raise Exception(
            "There cannot be any __init__.py in """ + path_to_file + " to comply with namespace package definition. Please remove this file!")

    path_to_file = os.path.join(quangstationCore.__path__[0], '..', '..', '..', 'quangstation_gui', '__init__.py')
    if os.path.exists(path_to_file):
        raise Exception(
            "There cannot be any __init__.py in """ + path_to_file + " to comply with namespace package definition. Please remove this file!")

    path_to_file = os.path.join(quangstationCore.__path__[0], '..', '..', '..', 'quangstation_gui', 'quangstation', '__init__.py')
    if os.path.exists(path_to_file):
        raise Exception(
            "There cannot be any __init__.py in """ + path_to_file + " to comply with namespace package definition. Please remove this file!")

print('TEST')

checkNoInit()

# Examples
exampleMorphons.run()
exampleSegmentation.run()


