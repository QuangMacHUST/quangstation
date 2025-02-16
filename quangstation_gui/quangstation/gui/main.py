import logging
import unittest

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QFont

from quangstation.core.data import PatientList
from quangstation.core.utils.programSettings import ProgramSettings
from quangstation.gui.viewController import ViewController


def viewController():
    # instantiate the main quangstation_core window
    _viewController = ViewController(patientList)
    _viewController.mainConfig = mainConfig

    return _viewController

logger = logging.getLogger(__name__)

patientList = PatientList()

mainConfig = ProgramSettings()

logger.info("Instantiate quangstation gui")
app = QApplication.instance()
if not app:
    app = QApplication([])

def runWithMainWindow(mainWindow):
    # options = parseArgs(sys.argv[1:])
    logger.info("Start quangstation gui")

    mainWindow.show()
    #display a message box
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setText(" ------------------------------DISCLAIMER------------------------------ \nquangstation is not a medical device, it is purely intended for research purposes and should only be used as such. It is neither FDA or CE approved.")
    msg.setFont(QFont("Arial", 12))
    msg.setWindowTitle("Disclaimer")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()

    app.exec_()

    mainWindow.close()
    #del mainWindow

def run():
    _viewController = viewController()
    runWithMainWindow(_viewController.mainWindow)

if __name__ == '__main__':
    run()

class MainTestCase(unittest.TestCase):
    def testViewController(self):
        _viewController = viewController()

    def testRun(self):
        print("Testing main window with view controller")
        _viewController = viewController()
        _viewController.mainWindow.show()
        _viewController.mainWindow.close()
