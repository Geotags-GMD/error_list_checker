# Error List Checker Plugin for QGIS

## Overview

The **Error List Checker** plugin allows users to validate geospatial data by checking for discrepancies in facility names and sector categories. It provides an intuitive interface for selecting layers, specifying validation criteria, and generating an error list for facilities that do not meet the required conditions.

## Features

- **Validation Criteria**: Automatically checks facility names against specified keywords in a selected JSON file.
- **Error Reporting**: Generates a detailed error list with facility geoid and remarks for discrepancies.
- **User-Friendly Interface**: Designed for easy navigation and quick access to features.

## Usage

1. Open QGIS and load your desired geospatial data layers.
2. Navigate to the **Plugins** menu and find **Error List Checker**.
3. Select a layer from the dropdown menu that ends with `_SF`.
4. Click on **Select JSON File** to load the validation criteria.
5. Click **Run Check** to validate the selected layer against the criteria.
6. The plugin will generate an error list, which will be displayed in a new layer on the map canvas.

## Error List Format

The generated error list will contain the following fields:

- **cbms_geoid**: The unique identifier for the facility.
- **remark**: A message describing the nature of the error or necessary action.

### Example Error List Entry

| cbms_geoid | remark                                                                          |
|------------|---------------------------------------------------------------------------------|
| 12345      | Invalid: Facility name or sector doesn't match the expected category.           |
| 67890      | Need to change category to 02_EDUCATION AND LITERACY.                          |

## License

This plugin is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Author

Philippine Statistics Authority | GMD
