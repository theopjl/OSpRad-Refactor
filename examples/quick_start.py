"""
Quick start example for OSpRad Spectroradiometer
Demonstrates the simplest way to perform a measurement

Mirrors JETI quick_start.py example structure and workflow.
"""

import sys
from pathlib import Path

# Add parent directory to path for development mode
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

# Import OSpRad device and required types
from devices.osprad_device import OSpRadDevice
from core.device_interface import MeasurementType

# Import color utilities
from examples.color_utils import calculate_chromaticity, calculate_cct, calculate_cri


def quick_measurement():
    """Perform a quick radiometric measurement"""
    
    print("OSpRad Quick Start Example")
    print("=" * 60)
    
    device = None
    
    try:
        # Create device instance
        device = OSpRadDevice()
        
        # Connect to device
        print("\nConnecting to device...")
        if not device.connect():
            print(f"Connection failed: {device.get_error()}")
            print("\nPlease check:")
            print("  - OSpRad device is connected via USB")
            print("  - Serial port permissions are correct")
            print("  - calibration_data.csv is in project root")
            return
        
        print("Device connected successfully!")
        
        # Configure device with settings
        print("Configuring device...")
        device.configure({
            'integration_time': 0,  # Auto
            'min_scans': 1,
            'max_scans': 50
        })
        
        # Display device info
        caps = device.get_capabilities()
        if caps.serial_number:
            print(f"Device S/N: {caps.serial_number}")
        
        # Perform measurement with automatic settings
        print("\nPerforming measurement...")
        print("(Using automatic integration time)")
        
        result = device.measure(MeasurementType.RADIANCE)
        
        if result is None:
            print(f"Measurement failed: {device.get_error()}")
            return
        
        print("Measurement complete!")
        
        # Get results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)
        
        # Radiometric value (equivalent to get_radiometric_value)
        # Sum spectral radiance over wavelength range
        wl_start = 380
        wl_end = 780
        radiometric = 0.0
        for i, wl in enumerate(result.wavelengths):
            if wl_start <= wl <= wl_end:
                if i < len(result.wavelengths) - 1:
                    dwl = result.wavelengths[i+1] - wl
                else:
                    dwl = 1.0
                radiometric += result.spectral_data[i] * dwl
        
        print(f"Radiometric value: {radiometric:.3E} W/(sr·m²)")
        
        # Photometric value (luminance from result)
        print(f"Photometric value: {result.luminance:.3E} cd/m²")
        
        # Chromaticity coordinates
        x, y = calculate_chromaticity(result.wavelengths, result.spectral_data)
        print(f"Chromaticity x,y:  {x:.4f}, {y:.4f}")
        
        # Correlated Color Temperature
        cct = calculate_cct(x, y)
        print(f"CCT:               {cct:.1f} K")
        
        # Color Rendering Index
        cri = calculate_cri(result.wavelengths, result.spectral_data, cct)
        print(f"CRI (Ra):          {cri[0]:.2f}")
        
        print("=" * 60)
        
        # Display measurement metadata
        print(f"\nIntegration time:  {result.integration_time_ms} ms")
        print(f"Scans averaged:    {result.num_scans}")
        print(f"Saturation level:  {result.saturation_level:.1f}%")
        
        if result.saturation_level > 90:
            print("\nWARNING: High saturation detected!")
            print("Consider reducing integration time or light intensity.")
        
    except KeyboardInterrupt:
        print("\n\nMeasurement interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close device
        if device is not None:
            device.disconnect()
            print("\nDevice closed.")


if __name__ == "__main__":
    quick_measurement()
