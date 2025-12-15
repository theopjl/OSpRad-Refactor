"""
Core package for spectral device interfaces
"""

from .device_interface import (
    SpectralDevice,
    DeviceCapabilities,
    DeviceStatus,
    MeasurementType,
    SettingDefinition
)
from .measurement_result import MeasurementResult, MeasurementUnit

__all__ = [
    'SpectralDevice',
    'DeviceCapabilities',
    'DeviceStatus',
    'MeasurementType',
    'SettingDefinition',
    'MeasurementResult',
    'MeasurementUnit',
]
