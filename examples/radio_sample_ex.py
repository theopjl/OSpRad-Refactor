"""
Extended radiometric measurements for OSpRad
Demonstrates manual control over integration time, scans, and spectral data export

Mirrors JETI radio_sample_ex.py example structure and workflow.
"""

import sys
from pathlib import Path
import time
import numpy as np
from datetime import datetime

# Add parent directory to path for development mode
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

# Import OSpRad device
from devices.osprad_device import OSpRadDevice
from core.device_interface import MeasurementType

from examples.color_utils import calculate_chromaticity, calculate_cct, calculate_cri


class RadioExMeasurementApp:
    """Application for extended radiometric measurements with manual control"""
    
    def __init__(self):
        self.device = None
        self.last_result = None
        
    def initialize_device(self):
        """Initialize and open the OSpRad device"""
        print("\nSearching for OSpRad devices...")
        
        self.device = OSpRadDevice()
        
        try:
            if not self.device.connect():
                print(f"Connection failed: {self.device.get_error()}")
                return False
            
            print("Device opened successfully!")
            
            # Display device info
            caps = self.device.get_capabilities()
            print(f"\nDevice: {caps.device_name}")
            print(f"Model: {caps.model}")
            if caps.serial_number:
                print(f"Serial Number: {caps.serial_number}")
            
            # Display version info (no DLL version, but show capabilities)
            print(f"\nCapabilities:")
            print(f"  Wavelength range: {caps.wavelength_range[0]}-{caps.wavelength_range[1]} nm")
            print(f"  Pixels: {caps.pixel_count}")
            print(f"  Auto integration: {caps.supports_auto_integration}")
            
            return True
            
        except Exception as e:
            print(f"Error initializing device: {e}")
            return False
    
    def perform_measurement(
        self,
        integration_time: int = 0,
        min_scans: int = 3,
        max_scans: int = 50
    ):
        """
        Perform radiometric measurement with specified parameters
        
        Args:
            integration_time: Integration time in ms (0 = automatic)
            min_scans: Minimum number of scans to average
            max_scans: Maximum number of scans to average
        """
        print("\n" + "=" * 60)
        print("Performing radiometric measurement...")
        print(f"Parameters: int_time={integration_time}ms, scans={min_scans}-{max_scans}")
        print("=" * 60)
        
        try:
            # Configure measurement settings
            settings = {
                'integration_time': integration_time,
                'min_scans': min_scans,
                'max_scans': max_scans
            }
            
            if not self.device.configure(settings):
                print(f"Configuration failed: {self.device.get_error()}")
                return None
            
            print("Measuring", end="", flush=True)
            
            # Perform measurement
            result = self.device.measure(MeasurementType.RADIANCE)
            
            print(" Done!\n")
            
            if result is None:
                print(f"Measurement failed: {self.device.get_error()}")
                return None
            
            self.last_result = result
            
            # Display results
            results = self.display_results(380, 780)
            
            return results
            
        except Exception as e:
            print(f"Error during measurement: {e}")
            return None
    
    def display_results(self, wl_start: int = 380, wl_end: int = 780):
        """Display measurement results for specified wavelength range"""
        if self.last_result is None:
            print("No measurement data available!")
            return None
        
        result = self.last_result
        
        try:
            print("\n" + "-" * 60)
            print("MEASUREMENT RESULTS")
            print("-" * 60)
            
            # Radiometric value over specified range
            radiometric = 0.0
            for i, wl in enumerate(result.wavelengths):
                if wl_start <= wl <= wl_end:
                    if i < len(result.wavelengths) - 1:
                        dwl = result.wavelengths[i+1] - wl
                    else:
                        dwl = 1.0
                    radiometric += result.spectral_data[i] * dwl
            
            print(f"Radiometric value ({wl_start}-{wl_end}nm): {radiometric:.3E} W/(sr·m²)")
            
            # Photometric value
            print(f"Photometric value:                    {result.luminance:.3E} cd/m²")
            
            # Chromaticity
            x, y = calculate_chromaticity(result.wavelengths, result.spectral_data)
            print(f"\nCIE 1931 Chromaticity:")
            print(f"  x: {x:.4f}")
            print(f"  y: {y:.4f}")
            
            # CCT
            cct = calculate_cct(x, y)
            print(f"\nCorrelated Color Temperature: {cct:.1f} K")
            
            # CRI
            cri = calculate_cri(result.wavelengths, result.spectral_data, cct)
            print(f"\nColor Rendering Index (Ra): {cri[0]:.2f}")
            
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
            print(f"Error displaying results: {e}")
            return None
    
    def get_spectrum(self, wl_start: int = 380, wl_end: int = 780):
        """Get and display spectral radiance data"""
        if self.last_result is None:
            print("\nNo measurement data available!")
            print("Please perform a measurement first.")
            return None
        
        result = self.last_result
        
        print("\n" + "=" * 60)
        print(f"SPECTRAL RADIANCE ({wl_start}-{wl_end} nm)")
        print("=" * 60)
        
        # Extract spectrum in range
        spectrum = []
        wavelengths = []
        
        for i, wl in enumerate(result.wavelengths):
            if wl_start <= wl <= wl_end:
                wavelengths.append(wl)
                spectrum.append(result.spectral_data[i])
        
        spectrum = np.array(spectrum)
        wavelengths = np.array(wavelengths)
        
        print(f"Spectrum shape: ({len(spectrum)},)")
        print(f"Number of points: {len(spectrum)}")
        
        # Show first 10 points
        print(f"\nFirst 10 data points:")
        for i in range(min(10, len(spectrum))):
            print(f"  {wavelengths[i]:.1f} nm: {spectrum[i]:.3E} W/(sr·m²·nm)")
        
        if len(spectrum) > 10:
            print(f"  ... ({len(spectrum) - 10} more points)")
        
        # Ask if user wants to save
        save = input("\nSave spectrum to file? (y/n): ").strip().lower()
        if save == 'y':
            filename = input("Enter filename (default: spectrum.txt): ").strip()
            if not filename:
                filename = "spectrum.txt"
            
            # Create data array
            data = np.column_stack((wavelengths, spectrum))
            
            # Save with header
            header = (
                f"OSpRad Spectral Radiance Measurement\n"
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Integration time: {result.integration_time_ms} ms\n"
                f"Scans averaged: {result.num_scans}\n"
                f"Wavelength range: {wl_start}-{wl_end} nm\n"
                f"\nWavelength(nm)\tSpectralRadiance(W/sr/m²/nm)"
            )
            
            np.savetxt(filename, data, fmt='%.6e', delimiter='\t', header=header)
            print(f"\nSpectrum saved to: {filename}")
        
        return spectrum
    
    def run_interactive_measurement(self):
        """Run measurement with user-specified parameters"""
        print("\n" + "=" * 60)
        print("INTERACTIVE MEASUREMENT")
        print("=" * 60)
        
        try:
            # Get parameters from user
            print("\nEnter measurement parameters:")
            
            int_time_str = input("Integration time in ms (0 for automatic): ").strip()
            int_time = int(int_time_str) if int_time_str else 0
            
            min_scans_str = input("Minimum scans (default 3): ").strip()
            min_scans = int(min_scans_str) if min_scans_str else 3
            
            max_scans_str = input("Maximum scans (default 50): ").strip()
            max_scans = int(max_scans_str) if max_scans_str else 50
            
            # Perform measurement
            self.perform_measurement(int_time, min_scans, max_scans)
            
        except ValueError:
            print("\nInvalid input! Please enter numeric values.")
        except Exception as e:
            print(f"\nError: {e}")
    
    def run_menu(self):
        """Run the interactive menu"""
        while True:
            print("\n" + "=" * 60)
            print("OSPRAD RADIO EX MEASUREMENT - MAIN MENU")
            print("=" * 60)
            print("1) Default measurement (auto integration, 3-50 scans)")
            print("2) Interactive measurement (custom parameters)")
            print("3) Get spectral radiance")
            print("\n0) Exit")
            print("=" * 60)
            
            choice = input("\nYour choice: ").strip()
            
            try:
                if choice == '1':
                    self.perform_measurement()
                    input("\nPress Enter to continue...")
                
                elif choice == '2':
                    self.run_interactive_measurement()
                    input("\nPress Enter to continue...")
                
                elif choice == '3':
                    if self.last_result is None:
                        print("\nNo measurement data available!")
                        print("Please perform a measurement first.")
                    else:
                        wl_start_str = input("\nStart wavelength (default 380): ").strip()
                        wl_start = int(wl_start_str) if wl_start_str else 380
                        
                        wl_end_str = input("End wavelength (default 780): ").strip()
                        wl_end = int(wl_end_str) if wl_end_str else 780
                        
                        self.get_spectrum(wl_start, wl_end)
                    
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
                import traceback
                traceback.print_exc()
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
    print("OSpRad Extended Radiometric Measurement")
    print("Manual control over integration time and scans")
    print("=" * 60)
    
    app = RadioExMeasurementApp()
    
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
