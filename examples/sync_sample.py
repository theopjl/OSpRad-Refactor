"""
Synchronized measurement placeholder for OSpRad

NOTE: OSpRad does not have built-in flicker detection or synchronized
measurement capabilities like JETI devices. This file is provided for
API completeness but functionality is limited.

For AC flicker measurements with OSpRad, consider:
1. Manual external triggering
2. Post-processing multiple rapid measurements
3. Custom firmware modifications

This example demonstrates what WOULD be possible if sync features existed.
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

from examples.color_utils import calculate_chromaticity, calculate_cct


class SyncMeasurementApp:
    """
    Synchronized measurement application (placeholder for OSpRad)
    
    This demonstrates the structure of JETI's sync_sample.py but with
    OSpRad limitations noted.
    """
    
    def __init__(self):
        self.device = None
        self.last_result = None
        
    def initialize_device(self):
        """Initialize and open the OSpRad device"""
        print("\nSearching for OSpRad devices...")
        print("\nWARNING: OSpRad does not have built-in flicker detection.")
        print("This example demonstrates the API structure only.\n")
        
        self.device = OSpRadDevice()
        
        try:
            if not self.device.connect():
                print(f"Connection failed: {self.device.get_error()}")
                return False
            
            print("Device connected successfully!")
            
            caps = self.device.get_capabilities()
            print(f"\nDevice: {caps.device_name}")
            if caps.serial_number:
                print(f"Serial Number: {caps.serial_number}")
            
            return True
            
        except Exception as e:
            print(f"Error initializing device: {e}")
            return False
    
    def get_flicker_frequency(self) -> float:
        """
        Placeholder: Get flicker frequency (not supported on OSpRad)
        
        Returns:
            Flicker frequency in Hz (always returns 0.0)
        """
        # TODO: OSpRad does not have flicker detection hardware
        # Would require:
        # 1. Very high speed sampling
        # 2. FFT analysis of temporal variations
        # 3. Custom firmware modifications
        
        print("\nFlicker detection not available on OSpRad.")
        print("For AC light sources, consider:")
        print("  - Manual frequency specification (50/60 Hz)")
        print("  - External trigger synchronization")
        print("  - Multiple rapid measurements")
        
        return 0.0
    
    def set_sync_mode(self, enable: bool):
        """
        Placeholder: Enable/disable sync mode (not supported on OSpRad)
        
        Args:
            enable: True to enable sync mode, False to disable
        """
        # TODO: OSpRad does not have hardware sync mode
        print(f"\nSync mode {'enable' if enable else 'disable'} requested")
        print("NOT IMPLEMENTED: OSpRad lacks hardware sync capability")
        
        # Could potentially implement via:
        # - Software gating of measurements
        # - External hardware trigger input
        # - Firmware modifications
    
    def set_sync_frequency(self, frequency: float):
        """
        Placeholder: Set sync frequency (not supported on OSpRad)
        
        Args:
            frequency: Sync frequency in Hz
        """
        print(f"\nSync frequency set to: {frequency:.2f} Hz")
        print("NOT IMPLEMENTED: OSpRad lacks hardware sync capability")
    
    def get_sync_frequency(self) -> float:
        """
        Placeholder: Get current sync frequency
        
        Returns:
            Sync frequency in Hz (always returns 0.0)
        """
        return 0.0
    
    def perform_sync_measurement(self):
        """
        Perform a "synchronized" measurement (fallback to normal measurement)
        
        Since OSpRad doesn't support sync, this performs a standard measurement
        but documents what WOULD happen with sync support.
        """
        print("\n" + "=" * 60)
        print("SYNCHRONIZED MEASUREMENT (SIMULATED)")
        print("=" * 60)
        
        # In JETI, we would:
        # 1. Detect flicker frequency
        # 2. Enable sync mode
        # 3. Set sync frequency
        # 4. Perform measurement synchronized to AC cycle
        # 5. Disable sync mode
        
        print("\nWhat WOULD happen with sync support:")
        print("1. Auto-detect flicker frequency from light source")
        print("2. Enable hardware synchronization")
        print("3. Trigger measurements at specific phase of AC cycle")
        print("4. Average over integer number of cycles")
        print("5. Eliminate flicker artifacts")
        
        print("\nActual behavior:")
        print("Performing STANDARD (non-sync) measurement...")
        
        try:
            # Configure for standard measurement
            settings = {
                'integration_time': 0,
                'min_scans': 10,  # More scans to average out flicker
                'max_scans': 50
            }
            
            if not self.device.configure(settings):
                print(f"Configuration failed: {self.device.get_error()}")
                return None
            
            print("\nMeasuring (averaging multiple scans to reduce flicker)...")
            result = self.device.measure(MeasurementType.RADIANCE)
            
            if result is None:
                print(f"Measurement failed: {self.device.get_error()}")
                return None
            
            self.last_result = result
            
            # Display results
            print("\n" + "-" * 60)
            print("RESULTS")
            print("-" * 60)
            
            print(f"Luminance: {result.luminance:.3E} cd/m²")
            
            x, y = calculate_chromaticity(result.wavelengths, result.spectral_data)
            print(f"Chromaticity: ({x:.4f}, {y:.4f})")
            
            cct = calculate_cct(x, y)
            print(f"CCT: {cct:.1f} K")
            
            print(f"\nMeasurement Info:")
            print(f"  Integration time: {result.integration_time_ms} ms")
            print(f"  Scans averaged:   {result.num_scans}")
            
            print("\nNOTE: Flicker effects may still be present!")
            print("For best results with AC lighting:")
            print("  - Use integration time = multiple of 1/frequency")
            print("  - Average many scans (>10)")
            print("  - Consider DC reference measurements")
            
            print("-" * 60)
            
            return result
            
        except Exception as e:
            print(f"Error during measurement: {e}")
            return None
    
    def display_sync_info(self):
        """Display sync mode information"""
        print("\n" + "=" * 60)
        print("SYNC MODE INFORMATION")
        print("=" * 60)
        
        print("\nOSpRad Synchronization Status:")
        print("  Hardware sync:     NOT SUPPORTED")
        print("  Flicker detection: NOT SUPPORTED")
        print("  Sync frequency:    N/A")
        print("  Sync mode active:  No")
        
        print("\nAlternatives for AC light measurement:")
        print("  1. Increase scan averaging (10-50 scans)")
        print("  2. Set integration time to match AC frequency:")
        print("     - 50 Hz: 20 ms, 40 ms, 60 ms, etc.")
        print("     - 60 Hz: 16.67 ms, 33.33 ms, 50 ms, etc.")
        print("  3. Post-process multiple rapid measurements")
        print("  4. Use external hardware trigger (requires mods)")
        
        print("=" * 60)
    
    def run_menu(self):
        """Run the interactive menu"""
        while True:
            print("\n" + "=" * 60)
            print("OSPRAD SYNC MEASUREMENT - MAIN MENU (LIMITED)")
            print("=" * 60)
            print("1) Perform 'synchronized' measurement (simulated)")
            print("2) Display sync info")
            print("3) Get flicker frequency (not supported)")
            print("4) Set sync parameters (not supported)")
            print("\n0) Exit")
            print("=" * 60)
            
            choice = input("\nYour choice: ").strip()
            
            try:
                if choice == '1':
                    self.perform_sync_measurement()
                    input("\nPress Enter to continue...")
                
                elif choice == '2':
                    self.display_sync_info()
                    input("\nPress Enter to continue...")
                
                elif choice == '3':
                    freq = self.get_flicker_frequency()
                    print(f"\nFlicker frequency: {freq:.2f} Hz")
                    input("\nPress Enter to continue...")
                
                elif choice == '4':
                    print("\nEnter sync frequency (for documentation only):")
                    freq_str = input("Frequency in Hz (50 or 60): ").strip()
                    try:
                        freq = float(freq_str)
                        self.set_sync_frequency(freq)
                        
                        # Calculate appropriate integration time
                        period_ms = 1000.0 / freq
                        print(f"\nFor {freq} Hz AC:")
                        print(f"  Period: {period_ms:.2f} ms")
                        print(f"  Recommended integration times:")
                        for i in range(1, 4):
                            print(f"    {i * period_ms:.2f} ms ({i} cycles)")
                    except ValueError:
                        print("Invalid frequency!")
                    
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
                # Ensure any hypothetical sync mode is disabled
                # (no-op for OSpRad)
                self.device.disconnect()
                print("Device closed.")
            except Exception as e:
                print(f"Error closing device: {e}")


def main():
    """Main application entry point"""
    print("\n" + "=" * 60)
    print("OSpRad Synchronized Measurement (LIMITED FUNCTIONALITY)")
    print("=" * 60)
    print("\nWARNING: OSpRad does not support hardware synchronization!")
    print("This example demonstrates API structure for compatibility.")
    print("Actual sync features require JETI or similar devices.")
    print("=" * 60)
    
    app = SyncMeasurementApp()
    
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
