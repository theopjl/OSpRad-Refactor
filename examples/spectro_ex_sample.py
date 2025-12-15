"""
Spectroscopic measurements for OSpRad
Demonstrates irradiance (spectroscopic) measurements vs radiance

Mirrors JETI spectro_ex_sample.py example structure and workflow.
Note: OSpRad uses the same device class for both radiance and irradiance,
      differing only in measurement type.
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

from examples.color_utils import calculate_chromaticity, calculate_cct


class SpectroExMeasurementApp:
    """Application for spectroscopic (irradiance) measurements"""
    
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
            
            # Display pixel count (equivalent to JETI's pixel info)
            print(f"\nPixel count: {caps.pixel_count}")
            print(f"Wavelength range: {caps.wavelength_range[0]}-{caps.wavelength_range[1]} nm")
            
            return True
            
        except Exception as e:
            print(f"Error initializing device: {e}")
            return False
    
    def perform_irradiance_measurement(
        self,
        integration_time: int = 0,
        min_scans: int = 3,
        max_scans: int = 50
    ):
        """
        Perform irradiance (spectroscopic) measurement
        
        Args:
            integration_time: Integration time in ms (0 = automatic)
            min_scans: Minimum number of scans to average
            max_scans: Maximum number of scans to average
        """
        print("\n" + "=" * 60)
        print("Performing IRRADIANCE measurement...")
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
            
            # Perform IRRADIANCE measurement (key difference from radio examples)
            result = self.device.measure(MeasurementType.IRRADIANCE)
            
            print(" Done!\n")
            
            if result is None:
                print(f"Measurement failed: {self.device.get_error()}")
                return None
            
            self.last_result = result
            
            # Display spectrum info
            self.display_spectrum_info()
            
            return result
            
        except Exception as e:
            print(f"Error during measurement: {e}")
            return None
    
    def display_spectrum_info(self):
        """Display spectrum statistics and information"""
        if self.last_result is None:
            print("No measurement data available!")
            return
        
        result = self.last_result
        spectrum = np.array(result.spectral_data)
        wavelengths = np.array(result.wavelengths)
        
        print("\n" + "-" * 60)
        print("IRRADIANCE SPECTRUM INFO")
        print("-" * 60)
        
        print(f"Number of points: {len(spectrum)}")
        print(f"Wavelength range: {wavelengths[0]:.1f} - {wavelengths[-1]:.1f} nm")
        
        # Statistics
        print(f"\nSpectrum Statistics:")
        print(f"  Min value:  {np.min(spectrum):.3E} W/(m²·nm)")
        print(f"  Max value:  {np.max(spectrum):.3E} W/(m²·nm)")
        print(f"  Mean value: {np.mean(spectrum):.3E} W/(m²·nm)")
        print(f"  Std dev:    {np.std(spectrum):.3E} W/(m²·nm)")
        
        # Total irradiance (illuminance)
        print(f"\nTotal Illuminance: {result.illuminance:.3E} lux")
        
        # Measurement metadata
        print(f"\nMeasurement Info:")
        print(f"  Integration time: {result.integration_time_ms} ms")
        print(f"  Scans averaged:   {result.num_scans}")
        print(f"  Saturation:       {result.saturation_level:.1f}%")
        
        print("-" * 60 + "\n")
    
    def get_wavelength_spectrum(
        self,
        wl_start: int = 380,
        wl_end: int = 780,
        step: float = 5.0
    ):
        """
        Get irradiance spectrum at specified wavelength range and step
        
        Note: Unlike JETI which can specify step during retrieval,
              OSpRad returns full resolution - we resample here
        """
        if self.last_result is None:
            print("\nNo measurement data available!")
            print("Please perform a measurement first.")
            return None
        
        result = self.last_result
        
        print("\n" + "=" * 60)
        print(f"IRRADIANCE SPECTRUM ({wl_start}-{wl_end} nm, step={step} nm)")
        print("=" * 60)
        
        # Resample spectrum at specified step
        target_wavelengths = np.arange(wl_start, wl_end + step, step)
        resampled_spectrum = np.interp(
            target_wavelengths,
            result.wavelengths,
            result.spectral_data
        )
        
        print(f"Number of points: {len(resampled_spectrum)}")
        
        # Show first 10 points
        print(f"\nFirst 10 data points:")
        for i in range(min(10, len(resampled_spectrum))):
            print(f"  {target_wavelengths[i]:.1f} nm: {resampled_spectrum[i]:.3E} W/(m²·nm)")
        
        if len(resampled_spectrum) > 10:
            print(f"  ... ({len(resampled_spectrum) - 10} more points)")
        
        return resampled_spectrum
    
    def get_pixel_spectrum(self):
        """Get raw pixel spectrum (full resolution)"""
        if self.last_result is None:
            print("\nNo measurement data available!")
            print("Please perform a measurement first.")
            return None
        
        result = self.last_result
        pixel_spectrum = np.array(result.spectral_data)
        
        print("\n" + "=" * 60)
        print("RAW PIXEL SPECTRUM")
        print("=" * 60)
        
        print(f"Number of pixels: {len(pixel_spectrum)}")
        print(f"Data type: {pixel_spectrum.dtype}")
        
        print(f"\nPixel Spectrum Statistics:")
        print(f"  Min value:  {np.min(pixel_spectrum):.3E}")
        print(f"  Max value:  {np.max(pixel_spectrum):.3E}")
        print(f"  Mean value: {np.mean(pixel_spectrum):.3E}")
        print(f"  Std dev:    {np.std(pixel_spectrum):.3E}")
        
        # Show first 10 pixels
        print(f"\nFirst 10 pixels:")
        for i in range(min(10, len(pixel_spectrum))):
            wl = result.wavelengths[i] if i < len(result.wavelengths) else 0
            print(f"  Pixel {i:3d} ({wl:.1f} nm): {pixel_spectrum[i]:.3E}")
        
        if len(pixel_spectrum) > 10:
            print(f"  ... ({len(pixel_spectrum) - 10} more pixels)")
        
        # Raw counts are also available
        if hasattr(result, 'raw_counts') and result.raw_counts:
            print(f"\nRaw counts available: {len(result.raw_counts)} values")
            print(f"First raw count: {result.raw_counts[0]:.0f}")
        
        return pixel_spectrum
    
    def run_interactive_measurement(self):
        """Run measurement with user-specified parameters"""
        print("\n" + "=" * 60)
        print("INTERACTIVE IRRADIANCE MEASUREMENT")
        print("=" * 60)
        
        try:
            print("\nEnter measurement parameters:")
            
            int_time_str = input("Integration time in ms (0 for automatic, default 0): ").strip()
            int_time = int(int_time_str) if int_time_str else 0
            
            min_scans_str = input("Minimum scans (default 3): ").strip()
            min_scans = int(min_scans_str) if min_scans_str else 3
            
            max_scans_str = input("Maximum scans (default 50): ").strip()
            max_scans = int(max_scans_str) if max_scans_str else 50
            
            # Perform measurement
            self.perform_irradiance_measurement(int_time, min_scans, max_scans)
            
        except ValueError:
            print("\nInvalid input! Please enter numeric values.")
        except Exception as e:
            print(f"\nError: {e}")
    
    def run_menu(self):
        """Run the interactive menu"""
        while True:
            print("\n" + "=" * 60)
            print("OSPRAD SPECTRO EX - MAIN MENU")
            print("=" * 60)
            print("1) Default irradiance measurement (auto, 3-50 scans)")
            print("2) Interactive measurement (custom parameters)")
            print("\n--- Single Operations ---")
            print("a) Start irradiance measurement")
            print("b) Get device status")
            print("c) Get irradiance spectrum (wavelength-based)")
            print("d) Get irradiance spectrum (pixel-based)")
            print("\n0) Exit")
            print("=" * 60)
            
            choice = input("\nYour choice: ").strip().lower()
            
            try:
                if choice == '1':
                    self.perform_irradiance_measurement()
                    input("\nPress Enter to continue...")
                
                elif choice == '2':
                    self.run_interactive_measurement()
                    input("\nPress Enter to continue...")
                
                elif choice == 'a':
                    print("\nStarting irradiance measurement...")
                    self.perform_irradiance_measurement()
                    input("\nPress Enter to continue...")
                
                elif choice == 'b':
                    status = self.device.status.name if self.device else "DISCONNECTED"
                    print(f"\nDevice status: {status}")
                    
                    if self.last_result:
                        print("\nLast measurement:")
                        print(f"  Timestamp: {self.last_result.timestamp}")
                        print(f"  Type: {self.last_result.measurement_type}")
                    
                    input("\nPress Enter to continue...")
                
                elif choice == 'c':
                    if self.last_result is None:
                        print("\nNo measurement data available!")
                        print("Please perform a measurement first.")
                    else:
                        wl_start_str = input("\nStart wavelength (default 380): ").strip()
                        wl_start = int(wl_start_str) if wl_start_str else 380
                        
                        wl_end_str = input("End wavelength (default 780): ").strip()
                        wl_end = int(wl_end_str) if wl_end_str else 780
                        
                        step_str = input("Step size in nm (default 5.0): ").strip()
                        step = float(step_str) if step_str else 5.0
                        
                        self.get_wavelength_spectrum(wl_start, wl_end, step)
                    
                    input("\nPress Enter to continue...")
                
                elif choice == 'd':
                    self.get_pixel_spectrum()
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
    print("OSpRad Spectroscopic (Irradiance) Measurement")
    print("Demonstrates irradiance vs radiance measurements")
    print("=" * 60)
    
    app = SpectroExMeasurementApp()
    
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
