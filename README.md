# OSpRad Spectral GUI - Refactored Implementation

A modular, extensible Python application for spectral measurements using the OSpRad (Open Source Spectroradiometer) and other spectral devices. This project is a complete refactor of the original OSpRad Python code with improved architecture, enhanced readability, and a modern GUI framework designed for research and education.

---

## Background and Motivation

This project builds upon the excellent work done by the **OSpRad project** (https://github.com/troscianko/OSpRad), an open-source spectroradiometer designed for accessible and accurate light measurement in research and fieldwork.

The original OSpRad Python application provided essential functionality for radiance and irradiance measurements, but was designed as a monolithic application. This refactor reimagines the codebase with modern software engineering practices to make it more maintainable, extensible, and suitable for broader educational and research applications.

---

## Refactor Summary

### What Changed

This implementation represents a ground-up architectural refactor with the following key improvements:

**Modular Architecture**
- Separated device communication, calibration logic, and GUI into distinct, reusable modules
- Introduced abstract device interface (`SpectralDevice`) enabling support for multiple device types
- Clean separation of concerns between hardware I/O, data processing, and presentation layers

**Code Quality & Maintainability**
- Type hints throughout for better IDE support and error detection
- Comprehensive docstrings for all public methods and classes
- Eliminated code duplication through proper class hierarchies
- Structured constants and configuration in dedicated sections
- Improved error handling with clear status reporting

**Enhanced Usability**
- Modern tkinter-based GUI with real-time plotting
- Settings panel with dynamic controls based on device capabilities
- Better visual feedback during measurements
- Export functionality for data preservation
- Responsive layout suitable for various screen sizes

**Extensibility**
- Plugin-style device architecture - add new devices by implementing `SpectralDevice` interface
- Easy to extend with new measurement types or analysis features
- Platform-agnostic design (supports both desktop and Android via conditional imports)

### Goals Achieved

✅ **Simpler, more readable code** - Logical module organization, clear naming conventions  
✅ **Easier maintenance and testing** - Isolated components, reduced coupling  
✅ **Modular UI/UX design** - Pluggable GUI components, reusable widgets  
✅ **Open-source and device-agnostic** - Abstract interfaces enable multi-device support  
✅ **Research & education ready** - Well-documented, examples included, suitable for teaching

---

## Features

### Current Capabilities

- **Measurement Types**: Radiance and Irradiance spectral measurements
- **Wavelength Range**: 350-850 nm (288 pixels)
- **Auto-integration**: Automatic exposure time adjustment for optimal signal
- **Scan Averaging**: Configurable min/max scan counts (1-50 scans)
- **Calibration Management**: CSV-based calibration loading with validation
- **Platform Support**: Windows, macOS, Linux, and Android (via USB4A)
- **Real-time Plotting**: Live spectral data visualization with matplotlib
- **Data Export**: Save measurements with metadata for post-processing
- **CIE Photometry**: Automatic luminance/illuminance calculation from spectral data

### Device Capabilities (OSpRad)

- **Connection**: USB serial (115200 baud) with auto-detection
- **Integration Time**: 0-10,000 ms (0 = automatic)
- **Scan Averaging**: Adaptive averaging based on signal stability
- **Linearity Correction**: Built-in correction for sensor non-linearity
- **Wavelength Calibration**: Polynomial wavelength mapping per unit
- **Sensitivity Calibration**: Per-pixel radiance and irradiance sensitivity

---

## Quick Start

### Prerequisites

- Python 3.7 or higher
- OSpRad hardware with calibration file (`calibration_data.csv`)
- Serial port access (may require admin/sudo on some systems)

### Installation

1. **Clone or download this repository**
   ```bash
   git clone <your-repo-url>
   cd diy
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Required packages:
   - `pyserial` - Serial port communication
   - `matplotlib` - Data visualization
   - `numpy` - Numerical operations (via matplotlib)
   - `usb4a` and `usbserial4a` (Android only)

3. **Place calibration file**
   
   Copy your `calibration_data.csv` to the project root directory (same level as `main.py`)

4. **Run the application**
   ```bash
   python spectral_gui/main.py
   ```
   
   Or with device selection:
   ```bash
   python spectral_gui/main.py --device osprad
   ```

### First Measurement

1. Connect your OSpRad device via USB
2. Launch the application - it will auto-detect the serial port
3. Click "Connect" to establish communication
4. Adjust settings (integration time, scan averaging) if needed
5. Click "Measure Radiance" or "Measure Irradiance"
6. View real-time spectral plot and photometric values

---

## Usage

### Basic Programmatic Usage

```python
from spectral_gui.devices import OSpRadDevice
from spectral_gui.core.device_interface import MeasurementType

# Initialize device with calibration file
device = OSpRadDevice(calibration_file="calibration_data.csv")

# Connect to hardware
if device.connect():
    print(f"Connected: {device.get_capabilities().device_name}")
    
    # Configure measurement settings
    device.configure({
        'integration_time': 0,      # Auto-integration
        'min_scans': 3,
        'max_scans': 50
    })
    
    # Perform radiance measurement
    result = device.measure(MeasurementType.RADIANCE)
    
    if result:
        print(f"Luminance: {result.luminance:.2f} cd/m²")
        print(f"Integration time: {result.integration_time_ms} ms")
        print(f"Scans averaged: {result.num_scans}")
        print(f"Wavelengths: {len(result.wavelengths)} pixels")
        
        # Access spectral data
        for wl, intensity in zip(result.wavelengths, result.spectral_data):
            print(f"{wl:.1f} nm: {intensity:.6e} W/(sr·m²·nm)")
    
    device.disconnect()
else:
    print("Connection failed:", device.get_error())
```

### GUI Application

Run the complete GUI application:

```bash
python spectral_gui/main.py
```

The GUI provides:
- **Connection panel** - Connect/disconnect with status indicators
- **Settings panel** - Dynamic controls for device-specific parameters
- **Measurement buttons** - Trigger radiance or irradiance measurements
- **Live plotting** - Real-time spectral distribution visualization
- **Results display** - Photometric values, metadata, saturation warnings
- **Export options** - Save data in CSV or JSON formats

---

## File Map / Key Modules

```
diy/
├── spectral_gui/
│   ├── __init__.py                   # Package initialization, exports
│   ├── main.py                       # Application entry point, CLI args
│   │
│   ├── core/                         # Core abstractions
│   │   ├── device_interface.py       # SpectralDevice ABC, enums, dataclasses
│   │   └── measurement_result.py     # MeasurementResult, MeasurementUnit
│   │
│   ├── devices/                      # Device implementations
│   │   ├── device_template.py        # Template for adding new devices
│   │   └── osprad_device.py          # OSpRad device adapter ⭐
│   │
│   └── gui/                          # GUI components
│       ├── main_window.py            # Main application window
│       └── plot_window.py            # Spectral plotting widget
│
├── calibration_data.csv              # Device calibration data (required)
├── README.md                         # This file
└── requirements.txt                  # Python dependencies
```

### Key Files

- **[osprad_device.py](spectral_gui/devices/osprad_device.py)** - Complete OSpRad implementation
  - `OSpRadCalibration` class - Loads and validates calibration, computes wavelengths and CIE Y
  - `OSpRadDevice` class - Implements `SpectralDevice` interface, handles serial communication
  - Platform detection for Android vs. desktop serial libraries
  
- **[device_interface.py](spectral_gui/core/device_interface.py)** - Abstract base class
  - Defines contract all devices must implement (`connect`, `measure`, `configure`, etc.)
  - Enums for measurement types, device status
  - Dataclasses for capabilities and settings definitions
  
- **[main_window.py](spectral_gui/gui/main_window.py)** - GUI controller
  - Orchestrates device communication and UI updates
  - Builds dynamic settings panel from device capabilities
  - Handles measurement workflows and error display

---

## Calibration

### Calibration File Format

The OSpRad requires a CSV calibration file (`calibration_data.csv`) with the following structure:

```csv
<unit_number>,wavCoef,<coef0>,<coef1>,<coef2>,<coef3>,<coef4>,<coef5>
<unit_number>,radSens,<sens_0>,<sens_1>,...,<sens_287>
<unit_number>,irrSens,<sens_0>,<sens_1>,...,<sens_287>
<unit_number>,linCoefs,<coef0>,<coef1>
```

- **wavCoef**: Polynomial coefficients for wavelength calculation (6 coefficients)
- **radSens**: Radiance sensitivity per pixel (288 values, W/(sr·m²·nm) per count)
- **irrSens**: Irradiance sensitivity per pixel (288 values, W/(m²·nm) per count)
- **linCoefs**: Linearity correction coefficients (2 values)

### Loading Behavior

1. **Auto-detection**: On first measurement, device reads unit number from hardware response
2. **Dynamic loading**: `OSpRadCalibration.load_for_unit()` searches CSV for matching unit number
3. **Validation**: Verifies all required arrays have correct lengths (288 pixels, 6 wavCoef, etc.)
4. **Derived values**: Automatically computes:
   - Wavelength array from polynomial coefficients
   - Wavelength bin widths for integration
   - CIE photopic response curve (Y values) for luminance calculation

### File Placement

Place `calibration_data.csv` in:
- **Project root** (next to `spectral_gui/`) for default behavior
- **Custom location** by passing `calibration_file="path/to/file.csv"` to `OSpRadDevice()`

---

## Development

### Adding a New Device

1. Create a new file in `spectral_gui/devices/` (e.g., `mydevice.py`)
2. Subclass `SpectralDevice` from `core.device_interface`
3. Implement required methods: `connect()`, `disconnect()`, `measure()`, `get_capabilities()`, `configure()`
4. Register device in `spectral_gui/__init__.py`
5. Use `device_template.py` as a reference

### Running Tests

```bash
# Run with mock device (no hardware required)
python spectral_gui/main.py --device mock

# Test connection only
python -c "from spectral_gui.devices import OSpRadDevice; d = OSpRadDevice(); print('OK' if d.connect() else 'FAIL')"
```

### Code Style

- **PEP 8** compliant
- Type hints for all public APIs
- Docstrings in Google style
- Maximum line length: 100 characters
- Use descriptive variable names

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## License and Contribution

### License

This refactored implementation is released under the **MIT License** (or specify your chosen license). See `LICENSE` file for details.

The original OSpRad hardware and firmware remain under their original license terms. Please respect the original project's licensing when using OSpRad hardware or firmware.

### How to Contribute

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes with clear messages
4. Push to your fork and submit a pull request
5. Ensure code passes style checks and includes tests where applicable

---

## Acknowledgments

This project is built upon the foundational work of the **OSpRad (Open Source Spectroradiometer)** project:

🔗 **Original Repository**: https://github.com/troscianko/OSpRad

### Credits

- **Original OSpRad Project**: Thomas Troscianko and contributors
  - Hardware design and firmware
  - Calibration methodology
  - Original Python measurement algorithms
  - CIE photometric response calculations
  - Linearity correction algorithms

### What We Borrowed

From the original OSpRad Python implementation, this refactor incorporated and adapted:
- **Spectral calibration algorithms** - Polynomial wavelength mapping and sensitivity corrections
- **Serial communication protocol** - Command structure for measurement requests
- **Photometric calculations** - CIE luminance/illuminance integration using photopic response
- **Linearity correction** - Sensor non-linearity compensation formulas

All borrowed algorithms have been refactored for clarity, modularity, and type safety while preserving scientific accuracy.

---

## Contact / Further Resources

### Project Resources

- **Original OSpRad**: https://github.com/troscianko/OSpRad
- **OSpRad Documentation**: See original repo for hardware assembly and firmware
- **Calibration Services**: Contact OSpRad project maintainers

### Support

For issues, feature requests, or questions about this refactored implementation:
- Open an issue on this repository
- For hardware or calibration questions, refer to the original OSpRad project

### Related Projects

- **Original OSpRad Firmware**: Arduino-based firmware for the hardware
- **OSpRad Hardware**: Open-source spectroradiometer design files

---

**Built for researchers, educators, and spectroscopy enthusiasts** 🔬✨

*Making spectral measurements accessible, maintainable, and extensible.*
