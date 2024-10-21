from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject
from .error_list_checker_dialog import ErrorListCheckerDialog
import os
from qgis.PyQt.QtGui import QIcon  # Import QIcon to use for icons

class ErrorListChecker:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.dlg = ErrorListCheckerDialog(self.iface)
        self.dialog = None
        self.action = None

    def initGui(self):
        # Load the icon for the action
        icon_path = os.path.join(self.plugin_dir, 'icon.png')  # Path to your icon
        self.action = QAction(QIcon(icon_path), "Error List Checker", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        if not self.dialog:
            self.dialog = ErrorListCheckerDialog(self.iface)
        self.dialog.show()
