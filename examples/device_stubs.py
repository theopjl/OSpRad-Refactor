"""
Adapter to make osprad_device.py importable from examples

This module handles the import complications since osprad_device.py
uses relative imports but is located in the project root.

For actual usage, osprad_device.py should be placed in a proper package structure.
"""

# Note: The actual osprad_device.py imports from ..core.device_interface
# which doesn't exist yet. For the examples to run, you need to either:
#
# 1. Create the full package structure with core/ modules
# 2. Modify osprad_device.py to use absolute imports
# 3. Use these mock/stub classes for testing

# Temporary stubs for running examples without full package
class DeviceStatus:
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    MEASURING = "MEASURING"
    ERROR = "ERROR"


class MeasurementType:
    RADIANCE = "radiance"
    IRRADIANCE = "irradiance"


class MeasurementUnit:
    WATTS_PER_SR_SQM_NM = "W/(sr·m²·nm)"
    WATTS_PER_SQM_NM = "W/(m²·nm)"
    CD_PER_SQM = "cd/m²"
    LUX = "lux"


class SettingDefinition:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.display_name = kwargs.get('display_name', '')
        self.setting_type = kwargs.get('setting_type', 'int')
        self.default_value = kwargs.get('default_value', 0)
        self.min_value = kwargs.get('min_value', 0)
        self.max_value = kwargs.get('max_value', 100)
        self.unit = kwargs.get('unit', '')
        self.tooltip = kwargs.get('tooltip', '')


class MeasurementResult:
    """Measurement result container"""
    
    def __init__(self, **kwargs):
        self.wavelengths = kwargs.get('wavelengths', [])
        self.spectral_data = kwargs.get('spectral_data', [])
        self.measurement_type = kwargs.get('measurement_type', 'radiance')
        self.timestamp = kwargs.get('timestamp', None)
        self.luminance = kwargs.get('luminance', 0.0)
        self.illuminance = kwargs.get('illuminance', 0.0)
        self.integration_time_ms = kwargs.get('integration_time_ms', 0)
        self.num_scans = kwargs.get('num_scans', 1)
        self.saturation_level = kwargs.get('saturation_level', 0.0)
        self.raw_counts = kwargs.get('raw_counts', [])
        self.device_name = kwargs.get('device_name', '')
        self.device_serial = kwargs.get('device_serial', '')
        self.device_info = kwargs.get('device_info', {})
        self.spectral_unit = kwargs.get('spectral_unit', MeasurementUnit.WATTS_PER_SR_SQM_NM)
        self.luminance_unit = kwargs.get('luminance_unit', MeasurementUnit.CD_PER_SQM)


class DeviceCapabilities:
    """Device capabilities container"""
    
    def __init__(self, **kwargs):
        self.device_name = kwargs.get('device_name', 'OSpRad')
        self.device_type = kwargs.get('device_type', 'Spectroradiometer')
        self.manufacturer = kwargs.get('manufacturer', 'Open Source')
        self.model = kwargs.get('model', 'OSpRad v1')
        self.serial_number = kwargs.get('serial_number', '')
        self.measurement_types = kwargs.get('measurement_types', [])
        self.wavelength_range = kwargs.get('wavelength_range', (350, 850))
        self.pixel_count = kwargs.get('pixel_count', 288)
        self.settings = kwargs.get('settings', [])
        self.supports_auto_integration = kwargs.get('supports_auto_integration', True)
        self.supports_dark_correction = kwargs.get('supports_dark_correction', False)
        self.supports_continuous_mode = kwargs.get('supports_continuous_mode', False)


class SpectralDevice:
    """Base spectral device interface (stub)"""
    
    def __init__(self):
        self.status = DeviceStatus.DISCONNECTED
        self.error_message = ""
    
    def connect(self) -> bool:
        raise NotImplementedError
    
    def disconnect(self) -> None:
        raise NotImplementedError
    
    def is_connected(self) -> bool:
        raise NotImplementedError
    
    def get_capabilities(self) -> DeviceCapabilities:
        raise NotImplementedError
    
    def configure(self, settings: dict) -> bool:
        raise NotImplementedError
    
    def measure(self, measurement_type) -> Optional[MeasurementResult]:
        raise NotImplementedError
    
    def get_current_settings(self) -> dict:
        raise NotImplementedError
    
    def get_error(self) -> str:
        return self.error_message
    
    def set_error(self, message: str):
        self.error_message = message
        self.status = DeviceStatus.ERROR


# TODO: Import actual OSpRadDevice when package structure is complete
# For now, the mock device from tests can be used for validation

__all__ = [
    'DeviceStatus',
    'MeasurementType',
    'MeasurementUnit',
    'MeasurementResult',
    'DeviceCapabilities',
    'SpectralDevice',
    'SettingDefinition',
]
