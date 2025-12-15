"""
Advanced spectral analysis for OSpRad
Professional spectral analysis with numpy operations and data export

Mirrors JETI advanced_example.py example structure and workflow.
"""

import sys
from pathlib import Path
import time
import numpy as np
from datetime import datetime
import os

# Add parent directory to path for development mode
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

# Import OSpRad device
from devices.osprad_device import OSpRadDevice
from core.device_interface import MeasurementType

from examples.color_utils import calculate_chromaticity, calculate_cct, calculate_cri


class SpectralAnalyzer:
    """
    Professional spectral analysis tool for OSpRad measurements.
    
    Provides comprehensive analysis, comparison, and export functionality.
    """
    
    def __init__(self):
        self.device = None
        self.spectrum_data = None
        self.wavelengths = None
        self.measurement_result = None
        
    def connect(self, calibration_file: str = "calibration_data.csv"):
        """
        Connect to OSpRad device
        
        Args:
            calibration_file: Path to calibration data file
        """
        print("Connecting to OSpRad device...")
        
        self.device = OSpRadDevice(calibration_file=calibration_file)
        
        if not self.device.connect():
            raise RuntimeError(f"Connection failed: {self.device.get_error()}")
        
        print("Device connected successfully!")
        
        # Display device info
        caps = self.device.get_capabilities()
        print(f"\nDevice: {caps.device_name}")
        print(f"Model: {caps.model}")
        if caps.serial_number:
            print(f"Serial Number: {caps.serial_number}")
        
        return True
    
    def measure_spectrum(
        self,
        wl_start: int = 380,
        wl_end: int = 780,
        integration_time: int = 0,
        min_scans: int = 3,
        max_scans: int = 50,
        measurement_type: MeasurementType = MeasurementType.RADIANCE
    ):
        """
        Perform spectral measurement with specified parameters
        
        Args:
            wl_start: Start wavelength (nm)
            wl_end: End wavelength (nm)
            integration_time: Integration time in ms (0 = auto)
            min_scans: Minimum scans to average
            max_scans: Maximum scans to average
            measurement_type: RADIANCE or IRRADIANCE
            
        Returns:
            Spectral data array
        """
        if self.device is None:
            raise RuntimeError("Device not connected")
        
        print("\n" + "=" * 60)
        print(f"Measuring {measurement_type.name} spectrum...")
        print(f"Range: {wl_start}-{wl_end} nm")
        print(f"Integration: {'AUTO' if integration_time == 0 else f'{integration_time} ms'}")
        print(f"Scans: {min_scans}-{max_scans}")
        print("=" * 60)
        
        # Configure settings
        settings = {
            'integration_time': integration_time,
            'min_scans': min_scans,
            'max_scans': max_scans
        }
        
        if not self.device.configure(settings):
            raise RuntimeError(f"Configuration failed: {self.device.get_error()}")
        
        # Perform measurement with progress indication
        print("\nMeasuring", end="", flush=True)
        
        result = self.device.measure(measurement_type)
        
        print(" Done!\n")
        
        if result is None:
            raise RuntimeError(f"Measurement failed: {self.device.get_error()}")
        
        # Store full result
        self.measurement_result = result
        
        # Extract spectrum in specified range
        spectrum = []
        wavelengths = []
        
        for i, wl in enumerate(result.wavelengths):
            if wl_start <= wl <= wl_end:
                wavelengths.append(wl)
                spectrum.append(result.spectral_data[i])
        
        self.spectrum_data = np.array(spectrum)
        self.wavelengths = np.array(wavelengths)
        
        print(f"Captured {len(self.spectrum_data)} spectral points")
        
        return self.spectrum_data
    
    def analyze_spectrum(self):
        """
        Perform comprehensive spectral analysis
        
        Returns:
            Dictionary of analysis results
        """
        if self.spectrum_data is None:
            print("No spectrum data available!")
            return None
        
        print("\n" + "=" * 60)
        print("SPECTRAL ANALYSIS")
        print("=" * 60)
        
        # Basic statistics
        print("\nBasic Statistics:")
        print(f"  Min value:     {np.min(self.spectrum_data):.3E}")
        print(f"  Max value:     {np.max(self.spectrum_data):.3E}")
        print(f"  Mean value:    {np.mean(self.spectrum_data):.3E}")
        print(f"  Std deviation: {np.std(self.spectrum_data):.3E}")
        print(f"  Total power:   {np.sum(self.spectrum_data):.3E}")
        
        # Peak detection
        peak_idx = np.argmax(self.spectrum_data)
        peak_wavelength = self.wavelengths[peak_idx]
        peak_value = self.spectrum_data[peak_idx]
        
        print(f"\nPeak Detection:")
        print(f"  Peak wavelength: {peak_wavelength:.1f} nm")
        print(f"  Peak value:      {peak_value:.3E}")
        
        # Centroid wavelength (weighted average)
        total_intensity = np.sum(self.spectrum_data)
        if total_intensity > 0:
            centroid = np.sum(self.wavelengths * self.spectrum_data) / total_intensity
            print(f"  Centroid:        {centroid:.1f} nm")
        else:
            centroid = 0
        
        # FWHM (Full Width at Half Maximum)
        half_max = peak_value / 2
        above_half = self.spectrum_data >= half_max
        
        if np.any(above_half):
            indices = np.where(above_half)[0]
            fwhm = self.wavelengths[indices[-1]] - self.wavelengths[indices[0]]
            print(f"  FWHM:            {fwhm:.1f} nm")
        else:
            fwhm = 0
        
        # Color measurements (if radiance)
        if self.measurement_result and self.measurement_result.measurement_type == 'radiance':
            print("\nColor Measurements:")
            
            # Use full spectrum for color calculations
            full_wl = self.measurement_result.wavelengths
            full_spec = self.measurement_result.spectral_data
            
            x, y = calculate_chromaticity(full_wl, full_spec)
            print(f"  Chromaticity x:  {x:.4f}")
            print(f"  Chromaticity y:  {y:.4f}")
            
            cct = calculate_cct(x, y)
            print(f"  CCT:             {cct:.1f} K")
            
            print(f"  Luminance:       {self.measurement_result.luminance:.3E} cd/m²")
        
        # Measurement metadata
        if self.measurement_result:
            print(f"\nMeasurement Info:")
            print(f"  Integration time: {self.measurement_result.integration_time_ms} ms")
            print(f"  Scans averaged:   {self.measurement_result.num_scans}")
            print(f"  Saturation:       {self.measurement_result.saturation_level:.1f}%")
        
        print("=" * 60 + "\n")
        
        # Return analysis results
        analysis = {
            'min': float(np.min(self.spectrum_data)),
            'max': float(np.max(self.spectrum_data)),
            'mean': float(np.mean(self.spectrum_data)),
            'std': float(np.std(self.spectrum_data)),
            'total_power': float(np.sum(self.spectrum_data)),
            'peak_wavelength': float(peak_wavelength),
            'peak_value': float(peak_value),
            'centroid': float(centroid),
            'fwhm': float(fwhm)
        }
        
        if self.measurement_result and self.measurement_result.measurement_type == 'radiance':
            full_wl = self.measurement_result.wavelengths
            full_spec = self.measurement_result.spectral_data
            x, y = calculate_chromaticity(full_wl, full_spec)
            cct = calculate_cct(x, y)
            
            analysis.update({
                'chromaticity_x': float(x),
                'chromaticity_y': float(y),
                'cct': float(cct),
                'luminance': float(self.measurement_result.luminance)
            })
        
        return analysis
    
    def export_data(self, filename: str = None, metadata: dict = None):
        """
        Export spectral data to text file with metadata
        
        Args:
            filename: Output filename (auto-generated if None)
            metadata: Additional metadata dictionary
        """
        if self.spectrum_data is None:
            print("No spectrum data to export!")
            return
        
        # Auto-generate filename with timestamp
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"osprad_spectrum_{timestamp}.txt"
        
        print(f"\nExporting data to: {filename}")
        
        # Build header
        header_lines = [
            "OSpRad Spectral Measurement Data",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Wavelength range: {self.wavelengths[0]:.1f}-{self.wavelengths[-1]:.1f} nm",
            f"Number of points: {len(self.spectrum_data)}"
        ]
        
        if self.measurement_result:
            header_lines.append("")
            header_lines.append("Measurement parameters:")
            header_lines.append(f"  Type: {self.measurement_result.measurement_type}")
            header_lines.append(f"  Integration time: {self.measurement_result.integration_time_ms} ms")
            header_lines.append(f"  Scans averaged: {self.measurement_result.num_scans}")
            header_lines.append(f"  Saturation: {self.measurement_result.saturation_level:.1f}%")
            
            if self.measurement_result.device_serial:
                header_lines.append(f"  Device S/N: {self.measurement_result.device_serial}")
        
        if metadata:
            header_lines.append("")
            header_lines.append("Additional metadata:")
            for key, value in metadata.items():
                header_lines.append(f"  {key}: {value}")
        
        # Data format description
        unit = "W/(sr·m²·nm)" if (self.measurement_result and 
                                    self.measurement_result.measurement_type == 'radiance') else "W/(m²·nm)"
        header_lines.append("")
        header_lines.append(f"Data format: Wavelength(nm)  SpectralIntensity({unit})")
        
        header = '\n'.join(header_lines)
        
        # Combine wavelengths and spectral data
        data = np.column_stack((self.wavelengths, self.spectrum_data))
        
        # Save with header
        np.savetxt(filename, data, fmt='%.6e', delimiter='\t', header=header, comments='# ')
        
        file_size = os.path.getsize(filename)
        print(f"Export complete! File size: {file_size} bytes")
    
    def export_csv(self, filename: str = None, include_analysis: bool = True):
        """
        Export spectral data in CSV format
        
        Args:
            filename: Output filename (auto-generated if None)
            include_analysis: Include analysis results in header
        """
        if self.spectrum_data is None:
            print("No spectrum data to export!")
            return
        
        # Auto-generate filename
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"osprad_spectrum_{timestamp}.csv"
        
        print(f"\nExporting CSV to: {filename}")
        
        with open(filename, 'w') as f:
            # Header
            f.write("# OSpRad Spectral Measurement Data\n")
            f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            if self.measurement_result:
                f.write(f"# Type: {self.measurement_result.measurement_type}\n")
                f.write(f"# Integration_time_ms: {self.measurement_result.integration_time_ms}\n")
                f.write(f"# Scans_averaged: {self.measurement_result.num_scans}\n")
            
            # Analysis section
            if include_analysis:
                analysis = self.analyze_spectrum()
                if analysis:
                    f.write("#\n# Analysis Results:\n")
                    for key, value in analysis.items():
                        f.write(f"# {key}: {value}\n")
            
            f.write("#\n")
            
            # Column headers
            unit = "W_sr_m2_nm" if (self.measurement_result and 
                                     self.measurement_result.measurement_type == 'radiance') else "W_m2_nm"
            f.write(f"Wavelength_nm,SpectralIntensity_{unit}\n")
            
            # Data rows
            for wl, val in zip(self.wavelengths, self.spectrum_data):
                f.write(f"{wl:.6e},{val:.6e}\n")
        
        file_size = os.path.getsize(filename)
        print(f"CSV export complete! File size: {file_size} bytes")
    
    def compare_spectra(
        self,
        other_spectrum: np.ndarray,
        label1: str = "Current",
        label2: str = "Reference"
    ):
        """
        Compare current spectrum with another spectrum
        
        Args:
            other_spectrum: Reference spectrum array (same length)
            label1: Label for current spectrum
            label2: Label for reference spectrum
        """
        if self.spectrum_data is None:
            print("No spectrum data available!")
            return
        
        if len(self.spectrum_data) != len(other_spectrum):
            print("Error: Spectra must have the same length!")
            return
        
        print("\n" + "=" * 60)
        print("SPECTRUM COMPARISON")
        print("=" * 60)
        
        # Correlation coefficient
        correlation = np.corrcoef(self.spectrum_data, other_spectrum)[0, 1]
        print(f"\nCorrelation coefficient: {correlation:.4f}")
        
        # RMS difference
        rms_diff = np.sqrt(np.mean((self.spectrum_data - other_spectrum)**2))
        print(f"RMS difference:          {rms_diff:.3E}")
        
        # Relative difference
        # Avoid division by zero
        rel_diff = np.abs(self.spectrum_data - other_spectrum) / (np.abs(other_spectrum) + 1e-10)
        mean_rel_diff = np.mean(rel_diff) * 100
        max_rel_diff = np.max(rel_diff) * 100
        
        print(f"Mean relative diff:      {mean_rel_diff:.2f}%")
        print(f"Max relative diff:       {max_rel_diff:.2f}%")
        
        # Peak comparison
        peak1_idx = np.argmax(self.spectrum_data)
        peak2_idx = np.argmax(other_spectrum)
        
        peak1_wl = self.wavelengths[peak1_idx]
        peak2_wl = self.wavelengths[peak2_idx]
        peak_shift = peak1_wl - peak2_wl
        
        print(f"\nPeak Comparison:")
        print(f"  {label1} peak: {peak1_wl:.1f} nm")
        print(f"  {label2} peak: {peak2_wl:.1f} nm")
        print(f"  Peak shift:    {peak_shift:.1f} nm")
        
        print("=" * 60 + "\n")
    
    def disconnect(self):
        """Disconnect from device"""
        if self.device is not None:
            self.device.disconnect()
            print("Device disconnected.")


def main():
    """Main application demonstrating advanced analysis"""
    print("\n" + "=" * 60)
    print("OSpRad Advanced Spectral Analysis")
    print("Professional analysis and export tools")
    print("=" * 60)
    
    analyzer = SpectralAnalyzer()
    
    try:
        # Connect to device
        analyzer.connect()
        
        # Measure spectrum
        print("\nPerforming measurement...")
        spectrum = analyzer.measure_spectrum(
            wl_start=380,
            wl_end=780,
            integration_time=0,  # Auto
            min_scans=3,
            max_scans=50,
            measurement_type=MeasurementType.RADIANCE
        )
        
        # Analyze
        analysis = analyzer.analyze_spectrum()
        
        # Export data
        print("\n--- Data Export ---")
        
        # Text format
        analyzer.export_data(
            metadata={
                'Operator': 'Auto',
                'Location': 'Lab',
                'Notes': 'Advanced example measurement'
            }
        )
        
        # CSV format
        analyzer.export_csv(include_analysis=True)
        
        # Optional: Compare with reference (example)
        # reference_spectrum = np.loadtxt('reference.txt', usecols=1)
        # analyzer.compare_spectra(reference_spectrum, "Current", "Reference")
        
        print("\n" + "=" * 60)
        print("Analysis complete!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nOperation interrupted by user!")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        analyzer.disconnect()


if __name__ == "__main__":
    main()
