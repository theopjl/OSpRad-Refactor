# OSpRad Examples

This directory contains example scripts for the OSpRad (Open Source Spectroradiometer) device, structured to mirror the JETI SDK examples for consistency and familiarity.

## Overview

The examples demonstrate various aspects of spectroradiometer usage, from simple quick-start measurements to advanced spectral analysis. They are organized by complexity and use case:

- **quick_start.py** - Minimal code for first-time users
- **radio_sample.py** - Basic radiometric measurements with interactive menu
- **radio_sample_ex.py** - Extended radiometric with manual control
- **spectro_ex_sample.py** - Irradiance (spectroscopic) measurements  
- **advanced_example.py** - Professional analysis with data export
- **sync_sample.py** - Placeholder for sync features (limited on OSpRad)

## Quick Start

### Prerequisites

- Python 3.7 or higher
- OSpRad hardware connected via USB
- Calibration file (`calibration_data.csv`) in project root
- Required packages: `numpy`, `pyserial`

### Running Examples

From the project root directory:

```bash
# Quick measurement
python examples/quick_start.py

# Interactive radiometric measurements
python examples/radio_sample.py

# Extended control with data export
python examples/radio_sample_ex.py

# Irradiance measurements
python examples/spectro_ex_sample.py

# Advanced analysis and export
python examples/advanced_example.py
```

## Example Descriptions

### quick_start.py

**Purpose**: Simplest measurement workflow for beginners

**Key Features**:
- Auto-connection to device
- Single measurement with automatic settings
- Display of key results (luminance, chromaticity, CCT, CRI)
- ~100 lines of code

**Output**:
```
OSpRad Quick Start Example
============================================================

Connecting to device...
Device connected successfully!
Device S/N: 1

Performing measurement...
Measurement complete!

============================================================
RESULTS
============================================================
Radiometric value: 1.234E+00 W/(sr·m²)
Photometric value: 5.678E+02 cd/m²
Chromaticity x,y:  0.3127, 0.3290
CCT:               6504.2 K
CRI (Ra):          95.23
============================================================
```

---

### radio_sample.py

**Purpose**: Basic radiometric measurements with interactive menu

**Key Features**:
- Interactive menu system
- Individual API method testing
- Full CRI array display (Ra + R1-R14)
- Device info display

**Usage**:
```bash
python examples/radio_sample.py
```

**Menu Options**:
1. Perform full measurement
2. Individual operations (measure, get status, get results)
3. Access individual color metrics

---

### radio_sample_ex.py

**Purpose**: Extended control over measurement parameters

**Key Features**:
- Manual integration time setting
- Configurable scan averaging (min/max scans)
- Spectral data export to file
- Interactive parameter input
- Data export in text format

**Usage**:
```bash
python examples/radio_sample_ex.py
```

**Example Workflow**:
1. Choose default or interactive measurement
2. Specify integration time (0 = auto)
3. Set scan range (e.g., 3-50 scans)
4. View results and optionally export spectrum

---

### spectro_ex_sample.py

**Purpose**: Irradiance (spectroscopic) measurements

**Key Features**:
- Irradiance vs radiance measurements
- Pixel-level spectrum access
- Wavelength-based resampling
- Spectrum statistics display

**Note**: OSpRad uses the same device class for both measurement types (radiance/irradiance), unlike JETI which has separate JetiRadio and JetiSpectroEx classes.

**Usage**:
```bash
python examples/spectro_ex_sample.py
```

---

### advanced_example.py

**Purpose**: Professional spectral analysis and data export

**Key Features**:
- Comprehensive spectral analysis (peak, FWHM, centroid)
- Multiple export formats (TXT, CSV)
- Metadata inclusion in exports
- Spectrum comparison functionality
- Statistical analysis

**Usage**:
```bash
python examples/advanced_example.py
```

**Analysis Outputs**:
- Basic statistics (min, max, mean, std dev)
- Peak detection and wavelength
- Centroid wavelength
- FWHM (Full Width at Half Maximum)
- Color measurements (chromaticity, CCT)
- Measurement metadata

**Export Formats**:
- Text file with header metadata
- CSV with embedded analysis results

---

### sync_sample.py

**Purpose**: Demonstrates sync API structure (limited functionality)

**Note**: ⚠️ OSpRad does not have hardware synchronization like JETI devices. This example shows the API structure for compatibility but actual sync features are not available.

**Alternatives for AC Light Measurement**:
1. Increase scan averaging (10-50 scans)
2. Set integration time to match AC frequency (e.g., 20ms for 50Hz)
3. Post-process multiple rapid measurements

---

## Utilities

### color_utils.py

Helper functions for color calculations:

- `calculate_chromaticity(wavelengths, spectral_data)` → (x, y)
- `calculate_cct(x, y)` → CCT in Kelvin
- `calculate_cri(wavelengths, spectral_data, cct)` → [Ra, R1...R14]
- `spectrum_to_rgb(wavelengths, spectral_data)` → (R, G, B)

**Note**: CRI calculation is simplified. For production use, consider specialized colorimetry libraries.

---

## Testing Without Hardware

All examples can be tested without hardware using the mock device:

```bash
# Run unit tests
pytest tests/test_examples.py -v

# Or use the mock device directly
python -c "
from tests.mock_device import MockOSpRadDevice, MeasurementType
device = MockOSpRadDevice()
device.connect()
result = device.measure(MeasurementType.RADIANCE)
print(f'Luminance: {result.luminance:.2e} cd/m²')
"
```

---

## API Mapping: JETI → OSpRad

| JETI SDK | OSpRad Equivalent | Notes |
|----------|-------------------|-------|
| `JetiRadio()` | `OSpRadDevice()` | Single device class |
| `JetiRadioEx()` | `OSpRadDevice()` | Same device, configure() for settings |
| `JetiSpectroEx()` | `OSpRadDevice()` | Same device, different MeasurementType |
| `get_num_devices()` | N/A | Auto-detects single device |
| `open_device(idx)` | `connect()` | Returns bool |
| `close_device()` | `disconnect()` | |
| `measure(time, avg, step)` | `configure() + measure(type)` | Two-step process |
| `get_measure_status()` | `device.status` | Synchronous measurement |
| `get_radiometric_value()` | `result.luminance` + spectrum integration | |
| `get_photometric_value()` | `result.luminance` or `illuminance` | Depends on type |
| `get_chromaticity_xy()` | `calculate_chromaticity()` | Helper function |
| `get_cct()` | `calculate_cct()` | Helper function |
| `get_cri()` | `calculate_cri()` | Helper function |
| `get_spectral_radiance()` | `result.spectral_data` | Direct access |

---

## Common Patterns

### Device Lifecycle

```python
from osprad_device import OSpRadDevice, MeasurementType

# Create and connect
device = OSpRadDevice()
if not device.connect():
    print(f"Error: {device.get_error()}")
    return

# Configure
device.configure({
    'integration_time': 0,  # Auto
    'min_scans': 3,
    'max_scans': 50
})

# Measure
result = device.measure(MeasurementType.RADIANCE)

# Access results
print(f"Luminance: {result.luminance:.2e} cd/m²")
print(f"Scans: {result.num_scans}")

# Cleanup
device.disconnect()
```

### Error Handling

```python
try:
    result = device.measure(MeasurementType.RADIANCE)
    if result is None:
        print(f"Measurement failed: {device.get_error()}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    device.disconnect()
```

### Data Export

```python
import numpy as np
from datetime import datetime

# Prepare data
data = np.column_stack((result.wavelengths, result.spectral_data))

# Save with metadata
header = f"OSpRad Measurement\nDate: {datetime.now()}\n"
np.savetxt('spectrum.txt', data, fmt='%.6e', header=header)
```

---

## Troubleshooting

### Connection Issues

**Problem**: "Connection failed: No serial ports found"

**Solutions**:
- Check USB cable connection
- On Linux: `sudo chmod 666 /dev/ttyUSB0` (or add user to dialout group)
- On Windows: Check Device Manager for COM port
- Verify OSpRad is powered on

---

### Calibration Issues

**Problem**: "Calibration not found for unit #X"

**Solutions**:
- Ensure `calibration_data.csv` is in project root
- Verify unit number in calibration file matches device
- Check CSV format (no extra commas, correct column count)

---

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'osprad_device'`

**Solutions**:
- Run examples from project root: `python examples/quick_start.py`
- Or add to PYTHONPATH: `export PYTHONPATH=/path/to/project:$PYTHONPATH`
- Check that `osprad_device.py` is in project root

---

## Contributing

When adding new examples:

1. Follow existing naming conventions (`*_sample.py`)
2. Include docstring with purpose and key features
3. Add progress indicators for long operations
4. Handle errors gracefully with informative messages
5. Include cleanup in `finally` blocks
6. Add corresponding tests in `tests/test_examples.py`

---

## License

These examples are provided as educational material for the OSpRad project. See project root for license information.

---

## Acknowledgments

Examples are structured to mirror the JETI SDK example suite for consistency and ease of learning. The spectral analysis and export patterns are adapted from professional spectroradiometry best practices.

---

**For questions or issues, please refer to the main project README or open an issue on GitHub.**
