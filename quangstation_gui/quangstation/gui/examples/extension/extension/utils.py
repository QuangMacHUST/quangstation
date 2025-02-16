
from quangstation.gui import mainWindow, viewController
from quangstation.gui.examples.extension.extension.gui.extensionPanel import ExtensionPanel


def addToGUI():
    mainWindow.mainToolbar.addWidget(ExtensionPanel(viewController), 'Extension example')