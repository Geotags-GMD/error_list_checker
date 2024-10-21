from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject
from .error_list_checker_dialog import ErrorListCheckerDialog
import os

class ErrorListChecker:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.dialog = None  # Initialize dialog variable
        self.action = None

    def initGui(self):
        self.action = QAction("Error List Checker", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        if self.dialog is None:  # Create dialog instance if not already created
            self.dialog = ErrorListCheckerDialog(self.iface)  # Pass iface to the dialog
        self.dialog.show()  # Show the dialog
