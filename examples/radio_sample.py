"""
Python version of RadioSample.c for OSpRad
Demonstrates basic radiometric measurements using OSpRad device

Mirrors JETI radio_sample.py example structure and workflow.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path for development mode
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

# Import OSpRad device
from devices.osprad_device import OSpRadDevice
from core.device_interface import MeasurementType

from examples.color_utils import calculate_chromaticity, calculate_cct, calculate_cri


class RadioMeasurementApp:
    """Application for performing radiometric measurements"""
    
    def __init__(self):
        self.device = None
        self.last_result = None
        
    def initialize_device(self):
        """Initialize and open the OSpRad device"""
        print("\nSearching for OSpRad devices...")
        
        self.device = OSpRadDevice()
        
        try:
            # OSpRad auto-detects single device on serial port
            # No get_num_devices() equivalent - device discovery is automatic
            if not self.device.connect():
                print(f"Connection failed: {self.device.get_error()}")
                print("\nTroubleshooting:")
                print("  - Check USB cable is connected")
                print("  - Verify serial port permissions")
                print("  - Ensure calibration_data.csv exists")
                return False
            
            print("Device opened successfully!")
            
            # Configure device with default settings
            self.device.configure({
                'integration_time': 0,  # Auto
                'min_scans': 3,
                'max_scans': 50
            })
            
            # Display device info
            caps = self.device.get_capabilities()
            print(f"\nDevice: {caps.device_name}")
            if caps.serial_number:
                print(f"Serial Number: {caps.serial_number}")
            print(f"Wavelength range: {caps.wavelength_range[0]}-{caps.wavelength_range[1]} nm")
            print(f"Pixels: {caps.pixel_count}")
            
            return True
            
        except Exception as e:
            print(f"Error initializing device: {e}")
            return False
    
    def perform_measurement(self):
        """Perform a complete radiometric measurement"""
        print("\n" + "=" * 60)
        print("Performing radiometric measurement...")
        print("=" * 60)
        
        try:
            # Configure for automatic integration time
            settings = {
                'integration_time': 0,  # 0 = automatic
                'min_scans': 3,
                'max_scans': 50
            }
            
            if not self.device.configure(settings):
                print(f"Configuration failed: {self.device.get_error()}")
                return None
            
            # Start measurement
            print("Starting measurement (automatic integration time)...")
            
            # OSpRad measure() is synchronous - includes waiting
            # Add simple progress indication
            print("Measuring", end="", flush=True)
            
            # Perform measurement
            result = self.device.measure(MeasurementType.RADIANCE)
            
            print(" Done!\n")
            
            if result is None:
                print(f"Measurement failed: {self.device.get_error()}")
                return None
            
            # Store for later retrieval
            self.last_result = result
            
            # Display all measurement results
            results = self.display_results()
            
            return results
            
        except Exception as e:
            print(f"Error during measurement: {e}")
            return None
    
    def display_results(self):
        """Display all measurement results"""
        if self.last_result is None:
            print("No measurement data available!")
            return None
        
        result = self.last_result
        
        try:
            print("\n" + "-" * 60)
            print("MEASUREMENT RESULTS")
            print("-" * 60)
            
            # Radiometric value (integrate over visible range)
            radiometric = 0.0
            for i, wl in enumerate(result.wavelengths):
                if 380 <= wl <= 780:
                    if i < len(result.wavelengths) - 1:
                        dwl = result.wavelengths[i+1] - wl
                    else:
                        dwl = 1.0
                    radiometric += result.spectral_data[i] * dwl
            
            print(f"Radiometric value:        {radiometric:.3E} W/(sr·m²)")
            
            # Photometric value (luminance)
            print(f"Photometric value:        {result.luminance:.3E} cd/m²")
            
            # Chromaticity coordinates
            x, y = calculate_chromaticity(result.wavelengths, result.spectral_data)
            print(f"\nCIE 1931 Chromaticity:")
            print(f"  x: {x:.4f}")
            print(f"  y: {y:.4f}")
            
            # Correlated Color Temperature
            cct = calculate_cct(x, y)
            print(f"\nCorrelated Color Temperature: {cct:.1f} K")
            
            # Color Rendering Index
            cri = calculate_cri(result.wavelengths, result.spectral_data, cct)
            print(f"\nColor Rendering Indices (CRI):")
            print(f"  Ra (General):  {cri[0]:.2f}")
            for i in range(1, 15):
                print(f"  R{i:2d}:           {cri[i]:.2f}")
            
            # Measurement metadata
            print(f"\nMeasurement Info:")
            print(f"  Integration time: {result.integration_time_ms} ms")
            print(f"  Scans averaged:   {result.num_scans}")
            print(f"  Saturation:       {result.saturation_level:.1f}%")
            
            print("-" * 60 + "\n")
            
            return {
                'radiometric': radiometric,
                'photometric': result.luminance,
                'chromaticity_x': x,
                'chromaticity_y': y,
                'cct': cct,
                'cri': cri
            }
            
        except Exception as e:
            print(f"Error reading results: {e}")
            return None
    
    def run_menu(self):
        """Run the interactive menu"""
        while True:
            print("\n" + "=" * 60)
            print("OSPRAD RADIO MEASUREMENT - MAIN MENU")
            print("=" * 60)
            print("1) Perform radiometric measurement")
            print("\n--- Single Operations ---")
            print("a) Start radiometric measurement")
            print("b) Get measurement status")
            print("c) Get radiometric value")
            print("d) Get photometric value")
            print("e) Get chromaticity coordinates x and y")
            print("f) Get correlated color temperature CCT")
            print("g) Get color rendering index CRI")
            print("\n0) Exit")
            print("=" * 60)
            
            choice = input("\nYour choice: ").strip().lower()
            
            try:
                if choice == '1':
                    self.perform_measurement()
                    input("\nPress Enter to continue...")
                
                elif choice == 'a':
                    print("\nStarting measurement...")
                    settings = {'integration_time': 0, 'min_scans': 3, 'max_scans': 50}
                    self.device.configure(settings)
                    result = self.device.measure(MeasurementType.RADIANCE)
                    if result:
                        self.last_result = result
                        print("Measurement complete!")
                    else:
                        print(f"Measurement failed: {self.device.get_error()}")
                    input("\nPress Enter to continue...")
                
                elif choice == 'b':
                    # OSpRad measurement is synchronous, no status to check
                    status = self.device.status.name
                    print(f"\nDevice status: {status}")
                    input("\nPress Enter to continue...")
                
                elif choice == 'c':
                    if self.last_result:
                        radiometric = sum(
                            self.last_result.spectral_data[i] * 
                            (self.last_result.wavelengths[i+1] - self.last_result.wavelengths[i] 
                             if i < len(self.last_result.wavelengths)-1 else 1.0)
                            for i, wl in enumerate(self.last_result.wavelengths) 
                            if 380 <= wl <= 780
                        )
                        print(f"\nRadiometric value: {radiometric:.3E} W/(sr·m²)")
                    else:
                        print("\nNo measurement data available!")
                    input("\nPress Enter to continue...")
                
                elif choice == 'd':
                    if self.last_result:
                        print(f"\nPhotometric value: {self.last_result.luminance:.3E} cd/m²")
                    else:
                        print("\nNo measurement data available!")
                    input("\nPress Enter to continue...")
                
                elif choice == 'e':
                    if self.last_result:
                        x, y = calculate_chromaticity(
                            self.last_result.wavelengths, 
                            self.last_result.spectral_data
                        )
                        print(f"\nChromaticity coordinates:")
                        print(f"  x: {x:.4f}")
                        print(f"  y: {y:.4f}")
                    else:
                        print("\nNo measurement data available!")
                    input("\nPress Enter to continue...")
                
                elif choice == 'f':
                    if self.last_result:
                        x, y = calculate_chromaticity(
                            self.last_result.wavelengths, 
                            self.last_result.spectral_data
                        )
                        cct = calculate_cct(x, y)
                        print(f"\nCorrelated Color Temperature: {cct:.1f} K")
                    else:
                        print("\nNo measurement data available!")
                    input("\nPress Enter to continue...")
                
                elif choice == 'g':
                    if self.last_result:
                        x, y = calculate_chromaticity(
                            self.last_result.wavelengths, 
                            self.last_result.spectral_data
                        )
                        cct = calculate_cct(x, y)
                        cri = calculate_cri(
                            self.last_result.wavelengths, 
                            self.last_result.spectral_data, 
                            cct
                        )
                        print(f"\nColor Rendering Index:")
                        print(f"  Ra (General): {cri[0]:.2f}")
                        for i in range(1, 15):
                            print(f"  R{i:2d}:          {cri[i]:.2f}")
                    else:
                        print("\nNo measurement data available!")
                    input("\nPress Enter to continue...")
                
                elif choice == '0':
                    print("\nExiting...")
                    break
                
                else:
                    print("\nInvalid choice! Please try again.")
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\nOperation interrupted!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                input("\nPress Enter to continue...")
    
    def cleanup(self):
        """Clean up resources"""
        if self.device is not None:
            try:
                self.device.disconnect()
                print("Device closed.")
            except Exception as e:
                print(f"Error closing device: {e}")


def main():
    """Main application entry point"""
    print("\n" + "=" * 60)
    print("OSpRad Radiometric Measurement Application")
    print("Based on JETI RadioSample.c")
    print("=" * 60)
    
    app = RadioMeasurementApp()
    
    try:
        if app.initialize_device():
            app.run_menu()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
