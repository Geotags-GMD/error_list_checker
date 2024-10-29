from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature
from qgis.PyQt.QtCore import QVariant, QSettings
from qgis.PyQt.QtGui import QColor
import os
import json

class ErrorListCheckerDialog(QDialog):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface  # Save iface for later use
        self.setWindowTitle('Error List Checker')
        self.setFixedWidth(300)  # Set the width of the dialog to 300 pixels

        # Create layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Layer Selection
        self.label_layer = QLabel('Select a Layer:')
        self.layout.addWidget(self.label_layer)
        self.combo_layers = QComboBox()
        self.layout.addWidget(self.combo_layers)

        # Run Button
        self.run_button = QPushButton('Run Check')
        self.run_button.clicked.connect(self.run_error_check)
        self.layout.addWidget(self.run_button)

        # Add version label at the bottom
        version_label = QLabel("GMD | Version: 1.1")
        self.layout.addWidget(version_label)

    def showEvent(self, event):
        """Override the showEvent to refresh the layer list each time the dialog is shown."""
        self.populate_layers()
        super().showEvent(event)  # Call the base class implementation

    def populate_layers(self):
        # Clear previous items
        self.combo_layers.clear()
        
        # Get all vector layers from the current project
        layers = QgsProject.instance().mapLayers().values()
        found_layers = False  # Flag to check if any layers are found
        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and layer.name().endswith('_SF'):
                self.combo_layers.addItem(layer.name(), layer)
                found_layers = True  # Found at least one layer

        # Update the label if no layers were added
        if not found_layers:
            self.label_layer.setText("No vector layers available")
        else:
            self.label_layer.setText("Select a Layer:")

    def run_error_check(self):
        layer = self.combo_layers.currentData()
        if not layer:
            QMessageBox.warning(self, "Warning", "Please select a layer.")
            return

        # Define the path to the JSON file within the plugin folder
        plugin_path = os.path.dirname(__file__)
        json_file_path = os.path.join(plugin_path, "validation_criteria.json")

        # Load validation criteria from the JSON file
        try:
            with open(json_file_path, 'r') as json_file:
                validation_criteria = json.load(json_file)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON file: {e}")
            return

        # Define the attribute fields
        cbms_geoid_field = 'cbms_geoid'  # Field for geoid
        fac_name_field = 'fac_name'  # Replace with actual facility name field
        sector_field = 'sector'  # Replace with actual sector field

        # Create a new temporary memory layer for storing the error list
        error_layer = QgsVectorLayer("Point?crs=EPSG:4326", "Error List", "memory")
        provider = error_layer.dataProvider()

        # Add fields for CBMS geoid, recommended category, and remark
        provider.addAttributes([
            QgsField("cbms_geoid", QVariant.String),
            QgsField("recommended_sector", QVariant.String),
            QgsField("remark", QVariant.String)
        ])
        error_layer.updateFields()

        error_count = 0  # Initialize error count

        # Iterate through features in the selected layer
        for feature in layer.getFeatures():
            fac_name_value = feature[fac_name_field]  # Facility name from the layer
            sector_value = feature[sector_field]  # Sector from the layer
            cbms_geoid = feature[cbms_geoid_field]  # Geoid from the layer

            matched_sector = None  # Variable to store the recommended sector based on keywords
            keyword_matched = None  # Track which keyword caused the match

            # Check against all validation criteria
            for category in validation_criteria['categories']:
                for keyword in category['keywords']:
                    if keyword.lower() in str(fac_name_value).lower():
                        matched_sector = category['sector']
                        keyword_matched = keyword
                        break
                if matched_sector:
                    break

            # If a match is found but the sector is incorrect, update it and add to error list
            if matched_sector and matched_sector != sector_value:
                # Create a new feature for the error list
                error_feature = QgsFeature()

                # Set the CBMS geoid, the recommended category (sector from JSON), and the remark
                error_feature.setFields(error_layer.fields())
                error_feature.setAttribute("cbms_geoid", cbms_geoid)
                error_feature.setAttribute("recommended_sector", matched_sector)
                error_feature.setAttribute(
                    "remark", 
                    f"Incorrect sector: '{sector_value}'. Recommended sector is '{matched_sector}' based on the keyword '{keyword_matched}'. Please verify and update the sector."
                )

                # Optionally, add geometry if needed (e.g., point at feature's centroid)
                if feature.hasGeometry():
                    geom = feature.geometry().centroid()
                    error_feature.setGeometry(geom)

                # Add the feature to the error layer
                provider.addFeature(error_feature)
                error_count += 1  # Increment the error count

        # Add the error layer to the QGIS project
        QgsProject.instance().addMapLayer(error_layer)

        # Optional: Zoom to the error layer
        self.iface.mapCanvas().setExtent(error_layer.extent())
        self.iface.mapCanvas().refresh()

        # Automatically apply QML styling from the built-in QML file
        qml_path = os.path.join(os.path.dirname(__file__), "error-list-style.qml")

        # Check if the QML file exists and apply it
        if os.path.exists(qml_path):
            error_layer.loadNamedStyle(qml_path)
            error_layer.triggerRepaint()
        else:
            QMessageBox.critical(self, "Error", "Failed to find the QML style file.")

        # Show the total count in the message box
        QMessageBox.information(self, "Errors", f"Errors detected: {error_count}. Please update the errors accordingly.")
