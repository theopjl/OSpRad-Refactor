"""
Measurement result data structure

Contains spectral data and metadata from measurements.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class MeasurementUnit(Enum):
    """Units for measurement values"""
    WATTS_PER_SR_SQM_NM = "W/(sr·m²·nm)"
    WATTS_PER_SQM_NM = "W/(m²·nm)"
    CD_PER_SQM = "cd/m²"
    LUX = "lux"


class MeasurementResult:
    """
    Container for spectral measurement results.
    
    Holds spectral data, calculated values, and metadata from a measurement.
    """
    
    def __init__(
        self,
        wavelengths: List[float],
        spectral_data: List[float],
        measurement_type: str,
        timestamp: datetime,
        luminance: float = 0.0,
        illuminance: float = 0.0,
        integration_time_ms: int = 0,
        num_scans: int = 1,
        saturation_level: float = 0.0,
        raw_counts: Optional[List[float]] = None,
        device_name: str = "",
        device_serial: str = "",
        device_info: Optional[Dict[str, Any]] = None,
        spectral_unit: MeasurementUnit = MeasurementUnit.WATTS_PER_SR_SQM_NM,
        luminance_unit: MeasurementUnit = MeasurementUnit.CD_PER_SQM
    ):
        """
        Initialize measurement result.
        
        Args:
            wavelengths: List of wavelength values in nm
            spectral_data: List of spectral intensity values
            measurement_type: Type of measurement ("radiance" or "irradiance")
            timestamp: Time of measurement
            luminance: Calculated luminance (cd/m²) for radiance measurements
            illuminance: Calculated illuminance (lux) for irradiance measurements
            integration_time_ms: Integration time used in milliseconds
            num_scans: Number of scans averaged
            saturation_level: Percentage of pixels saturated
            raw_counts: Raw detector counts (optional)
            device_name: Name of the device
            device_serial: Serial number of the device
            device_info: Additional device-specific information
            spectral_unit: Unit for spectral data
            luminance_unit: Unit for luminance/illuminance
        """
        self.wavelengths = wavelengths
        self.spectral_data = spectral_data
        self.measurement_type = measurement_type
        self.timestamp = timestamp
        self.luminance = luminance
        self.illuminance = illuminance
        self.integration_time_ms = integration_time_ms
        self.num_scans = num_scans
        self.saturation_level = saturation_level
        self.raw_counts = raw_counts if raw_counts is not None else []
        self.device_name = device_name
        self.device_serial = device_serial
        self.device_info = device_info if device_info is not None else {}
        self.spectral_unit = spectral_unit
        self.luminance_unit = luminance_unit
    
    def __repr__(self):
        return (
            f"MeasurementResult("
            f"type={self.measurement_type}, "
            f"points={len(self.wavelengths)}, "
            f"luminance={self.luminance:.2e}, "
            f"timestamp={self.timestamp})"
        )
