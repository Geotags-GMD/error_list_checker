from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature
from qgis.PyQt.QtCore import QVariant, QSettings
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
        cbms_geoid_field = 'cbms_geoid'  # Updated to the correct field name
        fac_name_field = 'fac_name'  # Replace with actual facility name field
        sector_field = 'sector'  # Replace with actual sector field

        # Create a new temporary memory layer for storing the error list
        error_layer = QgsVectorLayer("Point?crs=EPSG:4326", "Error List", "memory")
        provider = error_layer.dataProvider()

        # Add fields for CBMS geoid and remark
        provider.addAttributes([
            QgsField("cbms_geoid", QVariant.String),
            QgsField("remark", QVariant.String)
        ])
        error_layer.updateFields()

        # New remark template with updated wording
        remark_template = "Invalid: Facility name or sector doesn't match the expected category. Please verify and update the category."

        # Iterate through features in the selected layer
        for feature in layer.getFeatures():
            fac_name_value = feature[fac_name_field]
            sector_value = feature[sector_field]
            cbms_geoid = feature[cbms_geoid_field]

            # Check against all validation criteria
            is_valid = False
            for category in validation_criteria['categories']:
                if (any(keyword in str(fac_name_value).lower() for keyword in category['keywords']) and
                        sector_value == category['sector']):
                    is_valid = True
                    break

            if not is_valid:
                # Create a new feature for the error list
                error_feature = QgsFeature()
                
                # Set the CBMS geoid and remark
                error_feature.setFields(error_layer.fields())
                error_feature.setAttribute("cbms_geoid", cbms_geoid)
                error_feature.setAttribute("remark", remark_template)

                # Optionally, add geometry if needed (e.g., point at feature's centroid)
                if feature.hasGeometry():
                    geom = feature.geometry().centroid()
                    error_feature.setGeometry(geom)

                # Add the feature to the error layer
                provider.addFeature(error_feature)

        # Add the error layer to the QGIS project
        QgsProject.instance().addMapLayer(error_layer)

        # Optional: Zoom to the error layer
        self.iface.mapCanvas().zoomToFullExtent()

        QMessageBox.information(self, "Success", "Error list layer created.")
