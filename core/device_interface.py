"""
Core device interface definitions for spectral devices

Provides abstract base classes and enums for device implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum


class DeviceStatus(Enum):
    """Device connection and operation status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    MEASURING = "measuring"
    ERROR = "error"


class MeasurementType(Enum):
    """Types of spectral measurements"""
    RADIANCE = "radiance"
    IRRADIANCE = "irradiance"


class SettingDefinition:
    """Definition of a device setting/parameter"""
    
    def __init__(
        self,
        name: str,
        display_name: str,
        setting_type: str,
        default_value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        unit: str = "",
        tooltip: str = ""
    ):
        self.name = name
        self.display_name = display_name
        self.setting_type = setting_type
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
        self.tooltip = tooltip


class DeviceCapabilities:
    """Device capability information"""
    
    def __init__(
        self,
        device_name: str,
        device_type: str,
        manufacturer: str,
        model: str,
        serial_number: str,
        measurement_types: List[MeasurementType],
        wavelength_range: tuple,
        pixel_count: int,
        settings: List[SettingDefinition],
        supports_auto_integration: bool = False,
        supports_dark_correction: bool = False,
        supports_continuous_mode: bool = False
    ):
        self.device_name = device_name
        self.device_type = device_type
        self.manufacturer = manufacturer
        self.model = model
        self.serial_number = serial_number
        self.measurement_types = measurement_types
        self.wavelength_range = wavelength_range
        self.pixel_count = pixel_count
        self.settings = settings
        self.supports_auto_integration = supports_auto_integration
        self.supports_dark_correction = supports_dark_correction
        self.supports_continuous_mode = supports_continuous_mode


class SpectralDevice(ABC):
    """
    Abstract base class for spectral measurement devices.
    
    All spectroradiometer implementations should inherit from this class
    and implement the required methods.
    """
    
    def __init__(self):
        self.status = DeviceStatus.DISCONNECTED
        self.error_message = ""
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the device.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the device"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if device is connected.
        
        Returns:
            True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> DeviceCapabilities:
        """
        Get device capabilities and information.
        
        Returns:
            DeviceCapabilities object
        """
        pass
    
    @abstractmethod
    def configure(self, settings: Dict[str, Any]) -> bool:
        """
        Apply settings to the device.
        
        Args:
            settings: Dictionary of setting name -> value
            
        Returns:
            True if configuration successful, False otherwise
        """
        pass
    
    @abstractmethod
    def measure(self, measurement_type: MeasurementType):
        """
        Perform a measurement.
        
        Args:
            measurement_type: Type of measurement (RADIANCE or IRRADIANCE)
            
        Returns:
            MeasurementResult object or None on failure
        """
        pass
    
    @abstractmethod
    def get_current_settings(self) -> Dict[str, Any]:
        """
        Get current device settings.
        
        Returns:
            Dictionary of current settings
        """
        pass
    
    def get_error(self) -> str:
        """
        Get last error message.
        
        Returns:
            Error message string
        """
        return self.error_message
    
    def set_error(self, message: str):
        """
        Set error message and status.
        
        Args:
            message: Error message
        """
        self.error_message = message
        self.status = DeviceStatus.ERROR
