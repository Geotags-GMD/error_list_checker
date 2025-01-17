import os
import json
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QCheckBox, QFileDialog  # Add QFileDialog import
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature
from qgis.PyQt.QtCore import QVariant
from PyQt5.QtCore import QSettings  # Add this import

class ErrorListCheckerDialog(QDialog):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface  # Save iface for later use
        self.setWindowTitle('Error List Checker')
        self.setFixedWidth(300)  # Set the width of the dialog to 300 pixels

        # Create layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Load settings
        self.settings = QSettings("PSA", "Error List Checker")  # Change to your company/app name

        # Add checkbox for sector mismatch check
        self.sector_mismatch_check_box = QCheckBox('Check Sector Mismatch (Recommended)')
        self.sector_mismatch_check_box.setChecked(self.settings.value("sectorMismatchCheck", True, type=bool))  # Load saved state
        self.layout.addWidget(self.sector_mismatch_check_box)

        # Add checkbox for spelling check
        self.spelling_check_box = QCheckBox('Check Spelling')
        self.spelling_check_box.setChecked(self.settings.value("spellingCheck", False, type=bool))  # Load saved state
        self.layout.addWidget(self.spelling_check_box)

        # Run Button
        self.run_button = QPushButton('Run Check')
        self.run_button.clicked.connect(self.run_error_check)
        self.layout.addWidget(self.run_button)

        # Add version label at the bottom
        version_label = QLabel("GMD | Version: 1.4")
        self.layout.addWidget(version_label)

        # Load spelling corrections
        self.spelling_corrections = self.load_spelling_corrections()

    def closeEvent(self, event):
        # Save settings when the dialog is closed
        self.settings.setValue("sectorMismatchCheck", self.sector_mismatch_check_box.isChecked())
        self.settings.setValue("spellingCheck", self.spelling_check_box.isChecked())
        event.accept()  # Accept the event to close the dialog

    def run_error_check(self):
        # Get all vector layers from the current project
        layers = QgsProject.instance().mapLayers().values()
        found_layers = False  # Flag to check if any layers are found

        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and (layer.name().endswith('_SF') or layer.name().endswith('_GP')):
                found_layers = True  # Found at least one layer
                # Call the appropriate method based on the layer type
                if layer.name().endswith('_GP'):
                    self.run_error_check_gp(layer)
                elif layer.name().endswith('_SF'):
                    self.run_error_check_sf(layer)

        if not found_layers:
            QMessageBox.warning(self, "Warning", "No vector layers available for error checking.")

    # def run_error_check_sf(self, layer):
    #     # Define the path to the JSON file within the plugin folder
    #     plugin_path = os.path.dirname(__file__)
    #     json_file_path = os.path.join(plugin_path, "validation_criteria_sf.json")

    #     # Load validation criteria from the JSON file
    #     try:
    #         with open(json_file_path, 'r') as json_file:
    #             validation_criteria = json.load(json_file)
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", f"Failed to load JSON file: {e}")
    #         return

    #     # Define the attribute fields
    #     cbms_geoid_field = 'cbms_geoid'  # Field for geoid
    #     fac_name_field = 'fac_name'  # Facility name field
    #     sector_field = 'sector'  # Sector field

    #     # Create a new temporary memory layer for storing the error list
    #     error_layer = QgsVectorLayer("Point?crs=EPSG:4326", "SF Error List", "memory")
    #     provider = error_layer.dataProvider()

    #     # Add fields for CBMS geoid, recommended category, remark, and encountered errors
    #     provider.addAttributes([
    #         QgsField("cbms_geoid", QVariant.String),
    #         QgsField("suggested_sector", QVariant.String),
    #         QgsField("remark", QVariant.String),
    #         QgsField("encountered_errors", QVariant.String)  # Add the encountered_errors field
    #     ])
    #     error_layer.updateFields()

    #     error_count = 0  # Initialize error count
    #     encountered_errors = {}  # Dictionary to track errors for the same cbms_geoid

    #     # Iterate through features in the selected layer
    #     for feature in layer.getFeatures():
    #         # Convert QVariant to string and handle null values
    #         fac_name_value = feature[fac_name_field]
    #         if fac_name_value is None or not fac_name_value:
    #             continue

    #         # Convert QVariant to string
    #         fac_name_value = str(fac_name_value)

    #         sector_value = feature[sector_field]  # Sector from the layer
    #         cbms_geoid = feature[cbms_geoid_field]  # Geoid from the layer

    #         matched_sector = None  # Variable to store the recommended sector based on keywords
    #         keyword_matched = None  # Track which keyword caused the match

    #         # Initialize error message list
    #         error_messages = []

    #         # Check for spelling errors in the facility name only if the checkbox is checked
    #         if self.spelling_check_box.isChecked():
    #             words = str(fac_name_value).split()
    #             misspelled = []
    #             suggestions = []

    #             for word in words:
    #                 correction = self.check_word_spelling(word)
    #                 if correction:
    #                     misspelled.append(word)
    #                     suggestions.append(f"{word} → {correction}")
                  
            
    #             if misspelled:
    #                 error_msg = f"Spelling errors found: {', '.join(misspelled)}"
    #                 if suggestions:
    #                     error_msg += f". Suggestions: {'; '.join(suggestions)}"
    #                 error_messages.append(error_msg)
    #                 encountered_errors.setdefault(cbms_geoid, {}).setdefault('SPELLING ERROR', []).append(fac_name_value)

    #         # Check for sector mismatch only if the checkbox is checked
    #         if self.sector_mismatch_check_box.isChecked():
    #             # Check against all validation criteria for sector mismatch
    #             for category in validation_criteria['categories']:
    #                 for keyword in category['keywords']:
    #                     if keyword.lower() in str(fac_name_value).lower():
    #                         matched_sector = category['sector']
    #                         keyword_matched = keyword
    #                         break
    #                 if matched_sector:
    #                     break

    #             # If a match is found but the sector is incorrect, add sector mismatch to the error messages
    #             if matched_sector and matched_sector != sector_value:
    #                 error_messages.append(
    #                     f"Incorrect sector: '{sector_value}'. Recommended sector is '{matched_sector}' based on the keyword '{keyword_matched}'. Please verify and update the sector."
    #                 )
    #                 encountered_errors.setdefault(cbms_geoid, {}).setdefault('SECTOR MISMATCH', []).append(sector_value)

    #         # If there are any error messages, create a feature for the error list
    #         if error_messages:
    #             error_feature = QgsFeature()
    #             error_feature.setFields(error_layer.fields())
    #             error_feature.setAttribute("cbms_geoid", cbms_geoid)
    #             error_feature.setAttribute("suggested_sector", matched_sector if matched_sector else 'N/A')
    #             error_feature.setAttribute("remark", " ".join(error_messages))

    #             # Store the encountered errors as a string (no JSON)
    #             # encountered_errors_str = "\n".join([f"{key}: {', '.join(value)}" for key, value in encountered_errors.get(cbms_geoid, {}).items()])
    #             encountered_errors_str = "\n".join([f"{key}: {', '.join(str(v) for v in value)}" for key, value in encountered_errors.get(cbms_geoid, {}).items()])
    #             error_feature.setAttribute("encountered_errors", encountered_errors_str)  # Add as a plain string

    #             # Optionally, add geometry if needed
    #             if feature.hasGeometry():
    #                 geom = feature.geometry().centroid()
    #                 error_feature.setGeometry(geom)

    #             provider.addFeature(error_feature)
    #             error_count += 1  # Increment error count for combined errors

    #     # Add the error layer to the QGIS project
    #     QgsProject.instance().addMapLayer(error_layer)

    #     # Automatically apply QML styling from the built-in QML file
    #     qml_path = os.path.join(os.path.dirname(__file__), "error-list-style.qml")

    #     if os.path.exists(qml_path):
    #         error_layer.loadNamedStyle(qml_path)
    #         error_layer.triggerRepaint()
    #     else:
    #         QMessageBox.critical(self, "Error", "Failed to find the QML style file.")

    #     # Show the total count in the message box
    #     QMessageBox.information(self, "SF Errors", f"SF Errors detected: {error_count}. Please update the errors accordingly.")
    #     print("Encountered Errors:", encountered_errors)  # Debugging: check how errors are grouped


    def run_error_check_gp(self, layer):
        # Define the path to the JSON file within the plugin folder
        plugin_path = os.path.dirname(__file__)
        json_file_path = os.path.join(plugin_path, "validation_criteria_gp.json")

        # Load validation criteria from the JSON file
        try:
            with open(json_file_path, 'r') as json_file:
                validation_criteria = json.load(json_file)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON file: {e}")
            return

        # Define the attribute fields
        cbms_geoid_field = 'cbms_geoid'
        fac_name_field = 'gp_name'
        sector_field = 'sector'

        # Create a new temporary memory layer for storing the error list
        error_layer = QgsVectorLayer("Point?crs=EPSG:4326", "GP Error List", "memory")
        provider = error_layer.dataProvider()

        # Add fields for CBMS geoid, recommended category, remark, and encountered errors
        provider.addAttributes([
            QgsField("cbms_geoid", QVariant.String),
            QgsField("suggested_sector", QVariant.String),
            QgsField("remark", QVariant.String),
            QgsField("encountered_errors", QVariant.String)
        ])
        error_layer.updateFields()

        error_count = 0  # Initialize error count
        encountered_errors = {}  # Dictionary to track errors for the same cbms_geoid

        # Iterate through features in the selected layer
        for feature in layer.getFeatures():
            fac_name_value = feature[fac_name_field]
            if fac_name_value is None or not str(fac_name_value).strip():
                continue
            fac_name_value = str(fac_name_value).strip()

            sector_value = feature[sector_field]  # Sector from the layer
            cbms_geoid = feature[cbms_geoid_field]  # Geoid from the layer

            matched_sector = None
            keyword_matched = None
            error_messages = []

            # Check for spelling errors if enabled
            if self.spelling_check_box.isChecked():
                words = fac_name_value.split()
                misspelled = []
                suggestions = []

                for word in words:
                    correction = self.check_word_spelling(word)
                    if correction:
                        misspelled.append(word)
                        suggestions.append(f"{word} → {correction}")

                if misspelled:
                    error_msg = f"Spelling errors found: {', '.join(misspelled)}"
                    if suggestions:
                        error_msg += f". Suggestions: {'; '.join(suggestions)}"
                    error_messages.append(error_msg)
                    encountered_errors.setdefault(cbms_geoid, {}).setdefault('SPELLING ERROR', []).append(fac_name_value)

            # Check for sector mismatch if enabled
            if self.sector_mismatch_check_box.isChecked():
                words = fac_name_value.split()

                # Iterate over each word to match against validation keywords
                for word in words:
                    for category in validation_criteria['categories']:
                        for keyword in category['keywords']:
                            if keyword.lower() == word.lower():
                                matched_sector = category['sector']
                                keyword_matched = keyword
                                break
                        if matched_sector:
                            break
                    if matched_sector:
                        break

                # Add sector mismatch error if applicable
                if matched_sector and matched_sector != sector_value:
                    error_messages.append(
                        f"Incorrect sector: '{sector_value}'. Suggested sector is '{matched_sector}' based on the keyword '{keyword_matched}'. Please verify and update the sector."
                    )
                    encountered_errors.setdefault(cbms_geoid, {}).setdefault('MISMATCH', []).append(fac_name_value)

            # Create an error feature if errors are found
            if error_messages:
                error_feature = QgsFeature()
                error_feature.setFields(error_layer.fields())
                error_feature.setAttribute("cbms_geoid", cbms_geoid)
                error_feature.setAttribute("suggested_sector", matched_sector if matched_sector else 'N/A')
                error_feature.setAttribute("remark", " ".join(error_messages))

                # Format encountered errors as a string
                encountered_errors_str = "\n".join([f"{key}: {', '.join(str(v) for v in value)}" for key, value in encountered_errors.get(cbms_geoid, {}).items()])
                error_feature.setAttribute("encountered_errors", encountered_errors_str)

                # Set geometry if available
                if feature.hasGeometry():
                    geom = feature.geometry().centroid()
                    error_feature.setGeometry(geom)

                provider.addFeature(error_feature)
                error_count += 1

        # Add the error layer to the QGIS project
        QgsProject.instance().addMapLayer(error_layer)

        # Apply QML styling
        qml_path = os.path.join(plugin_path, "error-list-style.qml")
        if os.path.exists(qml_path):
            error_layer.loadNamedStyle(qml_path)
            error_layer.triggerRepaint()
        else:
            QMessageBox.critical(self, "Error", "Failed to find the QML style file.")

        # Show summary of detected errors
        QMessageBox.information(self, "GP Errors", f"GP Errors detected: {error_count}. Please update the errors accordingly.")
        print("Encountered Errors:", encountered_errors)  # Debugging output


    def run_error_check_sf(self, layer):
        # Define the path to the JSON file within the plugin folder
        plugin_path = os.path.dirname(__file__)
        json_file_path = os.path.join(plugin_path, "validation_criteria_sf.json")

        # Load validation criteria from the JSON file
        try:
            with open(json_file_path, 'r') as json_file:
                validation_criteria = json.load(json_file)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load JSON file: {e}")
            return

        # Define the attribute fields
        cbms_geoid_field = 'cbms_geoid'
        fac_name_field = 'fac_name'
        sector_field = 'sector'

        # Create a new temporary memory layer for storing the error list
        error_layer = QgsVectorLayer("Point?crs=EPSG:4326", "SF Error List", "memory")
        provider = error_layer.dataProvider()

        # Add fields for CBMS geoid, recommended category, remark, and encountered errors
        provider.addAttributes([
            QgsField("cbms_geoid", QVariant.String),
            QgsField("suggested_sector", QVariant.String),
            QgsField("remark", QVariant.String),
            QgsField("encountered_errors", QVariant.String)
        ])
        error_layer.updateFields()

        error_count = 0  # Initialize error count
        encountered_errors = {}  # Dictionary to track errors for the same cbms_geoid

        # Iterate through features in the selected layer
        for feature in layer.getFeatures():
            fac_name_value = feature[fac_name_field]
            if fac_name_value is None or not str(fac_name_value).strip():
                continue
            fac_name_value = str(fac_name_value).strip()

            sector_value = feature[sector_field]  # Sector from the layer
            cbms_geoid = feature[cbms_geoid_field]  # Geoid from the layer

            matched_sector = None
            keyword_matched = None
            error_messages = []

            # Check for spelling errors if enabled
            if self.spelling_check_box.isChecked():
                words = fac_name_value.split()
                misspelled = []
                suggestions = []

                for word in words:
                    correction = self.check_word_spelling(word)
                    if correction:
                        misspelled.append(word)
                        suggestions.append(f"{word} → {correction}")

                if misspelled:
                    error_msg = f"Spelling errors found: {', '.join(misspelled)}"
                    if suggestions:
                        error_msg += f". Suggestions: {'; '.join(suggestions)}"
                    error_messages.append(error_msg)
                    encountered_errors.setdefault(cbms_geoid, {}).setdefault('SPELLING ERROR', []).append(fac_name_value)

            # Check for sector mismatch if enabled
            if self.sector_mismatch_check_box.isChecked():
                words = fac_name_value.split()

                # Iterate over each word to match against validation keywords
                for word in words:
                    for category in validation_criteria['categories']:
                        for keyword in category['keywords']:
                            if keyword.lower() == word.lower():
                                matched_sector = category['sector']
                                keyword_matched = keyword
                                break
                        if matched_sector:
                            break
                    if matched_sector:
                        break

                # Add sector mismatch error if applicable
                if matched_sector and matched_sector != sector_value:
                    error_messages.append(
                        f"Incorrect sector: '{sector_value}'. Suggested sector is '{matched_sector}' based on the keyword '{keyword_matched}'. Please verify and update the sector."
                    )
                    encountered_errors.setdefault(cbms_geoid, {}).setdefault('MISMATCH', []).append(fac_name_value)

            # Create an error feature if errors are found
            if error_messages:
                error_feature = QgsFeature()
                error_feature.setFields(error_layer.fields())
                error_feature.setAttribute("cbms_geoid", cbms_geoid)
                error_feature.setAttribute("suggested_sector", matched_sector if matched_sector else 'N/A')
                error_feature.setAttribute("remark", " ".join(error_messages))

                # Format encountered errors as a string
                encountered_errors_str = "\n".join([f"{key}: {', '.join(str(v) for v in value)}" for key, value in encountered_errors.get(cbms_geoid, {}).items()])
                error_feature.setAttribute("encountered_errors", encountered_errors_str)

                # Set geometry if available
                if feature.hasGeometry():
                    geom = feature.geometry().centroid()
                    error_feature.setGeometry(geom)

                provider.addFeature(error_feature)
                error_count += 1

        # Add the error layer to the QGIS project
        QgsProject.instance().addMapLayer(error_layer)

        # Apply QML styling
        qml_path = os.path.join(plugin_path, "error-list-style.qml")
        if os.path.exists(qml_path):
            error_layer.loadNamedStyle(qml_path)
            error_layer.triggerRepaint()
        else:
            QMessageBox.critical(self, "Error", "Failed to find the QML style file.")

        # Show summary of detected errors
        QMessageBox.information(self, "SF Errors", f"SF Errors detected: {error_count}. Please update the errors accordingly.")
        print("Encountered Errors:", encountered_errors)  # Debugging output

    
   
    def load_spelling_corrections(self):
        try:
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(plugin_dir, 'spelling_dictionary.json'), 'r') as f:
                data = json.load(f)
                # Create a flat dictionary mapping each wrong spelling to correct word
                corrections = {}
                for item in data['corrections']:
                    for wrong_word in item['wrong']:
                        corrections[wrong_word.lower()] = item['correct']
                return corrections
        except:
            return {}

    def check_word_spelling(self, word):
        word_lower = word.lower()
        if word_lower in self.spelling_corrections:
            return self.spelling_corrections[word_lower]
        return None
