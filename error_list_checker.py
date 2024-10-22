from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.core import QgsProject
from .error_list_checker_dialog import ErrorListCheckerDialog
import os
from qgis.PyQt.QtGui import QIcon  # Import QIcon to use for icons

class ErrorListChecker:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.dlg = ErrorListCheckerDialog(self.iface)
        self.menu = 'GMD Plugins'
        self.dialog = None
        self.action = None
        self.toolbar = None  # Initialize toolbar variable

    def initGui(self):
        # Load the icon for the action
        icon_path = os.path.join(self.plugin_dir, 'icon.png')  # Path to your icon
        self.action = QAction(QIcon(icon_path), "Error List Checker", self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        # Create or get the custom toolbar
        self.toolbar = self.iface.mainWindow().findChild(QToolBar, "GMDPlugins")
        if not self.toolbar:
            self.toolbar = self.iface.addToolBar("GMD Plugins")
            self.toolbar.setObjectName("GMDPlugins")

        # Add the action to the menu and the toolbar
        self.iface.addPluginToMenu(self.menu, self.action)
        self.toolbar.addAction(self.action)  # Add action to the custom toolbar

    def unload(self):
        self.iface.removePluginMenu(self.menu, self.action)
        self.toolbar.removeAction(self.action)  # Remove action from the toolbar

    def run(self):
        if not self.dialog:
            self.dialog = ErrorListCheckerDialog(self.iface)
        self.dialog.show()
