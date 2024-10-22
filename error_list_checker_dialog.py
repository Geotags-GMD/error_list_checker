from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature
from qgis.PyQt.QtCore import QVariant, QSettings
from qgis.PyQt.QtGui import QColor  # Import QColor from QtGui
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

        # JSON File Selection
        self.button_json = QPushButton('Select JSON File')
        self.button_json.clicked.connect(self.select_json_file)
        self.layout.addWidget(self.button_json)
        self.label_json = QLabel('No JSON file selected')
        self.layout.addWidget(self.label_json)

        # Load saved JSON file path if it exists
        self.load_json_setting()

        # Run Button
        self.run_button = QPushButton('Run Check')
        self.run_button.clicked.connect(self.run_error_check)
        self.layout.addWidget(self.run_button)

        self.json_file_path = None

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
            print(f"Layer name: {layer.name()}, Layer type: {type(layer)}")  # Debugging output
            if isinstance(layer, QgsVectorLayer) and layer.name().endswith('_SF'):
                self.combo_layers.addItem(layer.name(), layer)
                found_layers = True  # Found at least one layer

        # Update the label if no layers were added
        if not found_layers:
            self.label_layer.setText("No vector layers available with '_SF' suffix.")
        else:
            self.label_layer.setText("Select a Layer:")

    def select_json_file(self):
        self.json_file_path, _ = QFileDialog.getOpenFileName(self, "Select JSON File", "", "JSON Files (*.json)")
        if self.json_file_path:
            self.label_json.setText(f'Selected: {self.json_file_path}')
            self.save_json_setting()  # Save the selected JSON file path

    def load_json_setting(self):
        settings = QSettings("PSA", "ErrorListChecker")
        saved_json_path = settings.value("json_file_path", "")
        if saved_json_path:
            self.json_file_path = saved_json_path
            self.label_json.setText(f'Selected: {self.json_file_path}')

    def save_json_setting(self):
        settings = QSettings("PSA", "ErrorListChecker")
        settings.setValue("json_file_path", self.json_file_path)

    def run_error_check(self):
        layer = self.combo_layers.currentData()
        if not self.json_file_path or not layer:
            QMessageBox.warning(self, "Warning", "Please select a layer and a JSON file.")
            return

        # Load validation criteria from the selected JSON file
        with open(self.json_file_path, 'r') as json_file:
            validation_criteria = json.load(json_file)

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
            QgsField("recommended_sector", QVariant.String),  # New category field for recommended sector
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
                        matched_sector = category['sector']  # Recommended sector from JSON
                        keyword_matched = keyword  # Save the matched keyword for remark
                        break  # Stop checking once a match is found
                if matched_sector:
                    break  # Stop if a matching sector is found

            # If a match is found but the sector is incorrect, update it and add to error list
            if matched_sector and matched_sector != sector_value:
                # Create a new feature for the error list
                error_feature = QgsFeature()

                # Set the CBMS geoid, the recommended category (sector from JSON), and the remark
                error_feature.setFields(error_layer.fields())
                error_feature.setAttribute("cbms_geoid", cbms_geoid)
                error_feature.setAttribute("recommended_sector", matched_sector)  # Recommended sector from JSON
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
        self.iface.mapCanvas().zoomToFullExtent()

        # Apply styling to make the points red
        symbol = error_layer.renderer().symbol()
        symbol.setColor(QColor("red"))  # Set color to red
        error_layer.triggerRepaint()  # Repaint the layer with the new style

        # Show the total count in the message box
        QMessageBox.information(self, "Errors", f"Errors detected: {error_count}. "
        "Please update the errors accordingly.")








   