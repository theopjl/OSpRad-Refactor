#
#  OSpRad Device Adapter
#
#  Implements SpectralDevice interface for the Open Source Spectroradiometer
#

import time
import os
import math
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..core.device_interface import (
    SpectralDevice, DeviceCapabilities, DeviceStatus, 
    MeasurementType, SettingDefinition
)
from ..core.measurement_result import MeasurementResult, MeasurementUnit


# ============================================================================
# CONSTANTS
# ============================================================================

SENSOR_PIXELS = 288
SERIAL_BAUD_RATE = 115200

MIN_SCANS = 1
MAX_SCANS = 50
DEFAULT_MIN_SCANS = 3
DEFAULT_MAX_SCANS = 50

LUMINANCE_CONSTANT = 683
CIE_Y_COEFFICIENTS = [0.821, 568.8, 46.9, 40.5, 0.286, 530.9, 16.3, 31.1]

CALIBRATION_FILE = "calibration_data.csv"


# ============================================================================
# Platform-specific imports
# ============================================================================

def is_android() -> bool:
    return any(key.startswith('ANDROID_') for key in os.environ)

if is_android():
    from usb4a import usb
    from usbserial4a import serial4a
else:
    import serial
    import serial.tools.list_ports


# ============================================================================
# Calibration Data Handler
# ============================================================================

class OSpRadCalibration:
    """Manages OSpRad calibration data"""
    
    def __init__(self):
        self.unit_number: int = 0
        self.wav_coef: List[float] = []
        self.rad_sens: List[float] = []
        self.irr_sens: List[float] = []
        self.lin_coefs: List[float] = []
        self.wavelength: List[float] = []
        self.wavelength_bins: List[float] = []
        self.ciey: List[float] = []
        self.is_loaded: bool = False
    
    def load_for_unit(self, unit_number: int, filename: str = CALIBRATION_FILE) -> bool:
        """Load calibration data from CSV file"""
        self.unit_number = unit_number
        
        try:
            with open(filename, 'r') as file:
                for line in file:
                    row = line.strip().split(',')
                    
                    try:
                        row_unit = int(row[0])
                    except (ValueError, IndexError):
                        continue
                    
                    if row_unit != unit_number:
                        continue
                    
                    # Filter out empty strings
                    if row[1] == "wavCoef":
                        self.wav_coef = [float(x) for x in row[2:] if x.strip()]
                    elif row[1] == "radSens":
                        self.rad_sens = [float(x) for x in row[2:] if x.strip()]
                    elif row[1] == "irrSens":
                        self.irr_sens = [float(x) for x in row[2:] if x.strip()]
                    elif row[1] == "linCoefs":
                        self.lin_coefs = [float(x) for x in row[2:] if x.strip()]
            
            if not self._validate():
                return False
            
            self._calculate_derived_values()
            self.is_loaded = True
            return True
            
        except FileNotFoundError:
            print(f"Calibration file not found: {filename}")
            return False
        except Exception as e:
            print(f"Error loading calibration: {e}")
            return False
    
    def _validate(self) -> bool:
        """Validate calibration data"""
        if len(self.wav_coef) < 6:
            return False
        if len(self.rad_sens) != SENSOR_PIXELS:
            return False
        if len(self.irr_sens) != SENSOR_PIXELS:
            return False
        if len(self.lin_coefs) < 2:
            return False
        return True
    
    def _calculate_derived_values(self):
        """Calculate wavelengths and CIE Y values"""
        # Calculate wavelengths
        self.wavelength = []
        for i in range(SENSOR_PIXELS):
            wl = sum(float(self.wav_coef[j]) * (i ** j) for j in range(min(6, len(self.wav_coef))))
            self.wavelength.append(wl)
        
        # Calculate wavelength bins
        self.wavelength_bins = []
        for i in range(SENSOR_PIXELS - 1):
            self.wavelength_bins.append(self.wavelength[i + 1] - self.wavelength[i])
        self.wavelength_bins.append(self.wavelength_bins[-1])
        
        # Calculate CIE Y
        coef = CIE_Y_COEFFICIENTS
        self.ciey = []
        for wl in self.wavelength:
            if wl < coef[1]:
                y1 = coef[0] * math.exp(-0.5 * ((wl - coef[1]) / coef[2]) ** 2)
            else:
                y1 = coef[0] * math.exp(-0.5 * ((wl - coef[1]) / coef[3]) ** 2)
            
            if wl < coef[5]:
                y2 = coef[4] * math.exp(-0.5 * ((wl - coef[5]) / coef[6]) ** 2)
            else:
                y2 = coef[4] * math.exp(-0.5 * ((wl - coef[5]) / coef[7]) ** 2)
            
            self.ciey.append(y1 + y2)


# ============================================================================
# OSpRad Device
# ============================================================================

class OSpRadDevice(SpectralDevice):
    """
    OSpRad (Open Source Spectroradiometer) device adapter.
    
    Implements the SpectralDevice interface for OSpRad hardware.
    """
    
    def __init__(self, calibration_file: str = CALIBRATION_FILE):
        super().__init__()
        
        self.calibration_file = calibration_file
        self.ser = None
        self.calibration = OSpRadCalibration()
        
        # Current settings
        self.integration_time = 0  # 0 = auto
        self.min_scans = DEFAULT_MIN_SCANS
        self.max_scans = DEFAULT_MAX_SCANS
        
        # Track sent settings to avoid unnecessary communication
        self._sent_int_time = None
        self._sent_min_scans = None
        self._sent_max_scans = None
    
    # =========================================================================
    # SpectralDevice Interface Implementation
    # =========================================================================
    
    def connect(self) -> bool:
        """Connect to OSpRad device"""
        try:
            self.status = DeviceStatus.CONNECTING
            
            if is_android():
                self.ser = self._connect_android()
            else:
                self.ser = self._connect_desktop()
            
            time.sleep(1)  # Allow connection to stabilize
            
            self.status = DeviceStatus.CONNECTED
            return True
            
        except Exception as e:
            self.set_error(f"Connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from device"""
        try:
            if self.ser:
                self.ser.close()
                self.ser = None
        except:
            pass
        
        self.status = DeviceStatus.DISCONNECTED
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.ser is not None and self.status == DeviceStatus.CONNECTED
    
    def get_capabilities(self) -> DeviceCapabilities:
        """Return OSpRad capabilities"""
        return DeviceCapabilities(
            device_name="OSpRad Spectroradiometer",
            device_type="Spectroradiometer",
            manufacturer="Open Source",
            model="OSpRad v1",
            serial_number=str(self.calibration.unit_number) if self.calibration.is_loaded else "",
            
            measurement_types=[MeasurementType.RADIANCE, MeasurementType.IRRADIANCE],
            wavelength_range=(350, 850),
            pixel_count=SENSOR_PIXELS,
            
            settings=[
                SettingDefinition(
                    name="integration_time",
                    display_name="Integration Time",
                    setting_type="int",
                    default_value=0,
                    min_value=0,
                    max_value=10000,
                    unit="ms",
                    tooltip="0 = automatic integration time"
                ),
                SettingDefinition(
                    name="min_scans",
                    display_name="Minimum Scans",
                    setting_type="int",
                    default_value=DEFAULT_MIN_SCANS,
                    min_value=MIN_SCANS,
                    max_value=MAX_SCANS,
                    tooltip="Minimum number of scans to average"
                ),
                SettingDefinition(
                    name="max_scans",
                    display_name="Maximum Scans",
                    setting_type="int",
                    default_value=DEFAULT_MAX_SCANS,
                    min_value=MIN_SCANS,
                    max_value=MAX_SCANS,
                    tooltip="Maximum number of scans to average"
                ),
            ],
            
            supports_auto_integration=True,
            supports_dark_correction=False,
            supports_continuous_mode=False,
        )
    
    def configure(self, settings: Dict[str, Any]) -> bool:
        """Apply settings to device"""
        try:
            if 'integration_time' in settings:
                new_time = int(settings['integration_time'])
                if new_time != self._sent_int_time:
                    self._send_command(f't{new_time}')
                    self._sent_int_time = new_time
                    self.integration_time = new_time
            
            if 'min_scans' in settings:
                new_min = max(MIN_SCANS, min(MAX_SCANS, int(settings['min_scans'])))
                if new_min != self._sent_min_scans:
                    self._send_command(f'n{new_min}')
                    self._sent_min_scans = new_min
                    self.min_scans = new_min
            
            if 'max_scans' in settings:
                new_max = max(MIN_SCANS, min(MAX_SCANS, int(settings['max_scans'])))
                if new_max != self._sent_max_scans:
                    self._send_command(f'a{new_max}')
                    self._sent_max_scans = new_max
                    self.max_scans = new_max
            
            return True
            
        except Exception as e:
            self.set_error(f"Configure failed: {e}")
            return False
    
    def measure(self, measurement_type: MeasurementType) -> Optional[MeasurementResult]:
        """Perform measurement"""
        print("Measuring with osprad")
        if not self.is_connected():
            self.set_error("Device not connected")
            return None
        
        self.status = DeviceStatus.MEASURING
        
        try:
            # Send measurement command
            cmd = 'r' if measurement_type == MeasurementType.RADIANCE else 'i'
            raw_data = self._request_measurement(cmd)
            
            if raw_data is None:
                self.set_error("No data received")
                return None
            
            # Parse metadata
            if len(raw_data) < 5 + SENSOR_PIXELS:
                self.set_error("Incomplete data")
                return None
            
            unit_number = int(raw_data[0])
            n_scans = int(raw_data[2])
            actual_int_time = int(raw_data[3])
            saturated = float(raw_data[4])
            raw_counts = raw_data[5:]
            
            # Load calibration if needed
            if not self.calibration.is_loaded:
                if not self.calibration.load_for_unit(unit_number, self.calibration_file):
                    self.set_error(f"Calibration not found for unit #{unit_number}")
                    return None
            
            # Validate length
            if len(raw_counts) != SENSOR_PIXELS:
                self.set_error("Spectrum length mismatch")
                return None
            
            # Calculate calibrated spectrum
            spectral_data, luminance = self._calculate_spectrum(raw_counts, actual_int_time, cmd)
            
            # Create result
            result = MeasurementResult(
                wavelengths=self.calibration.wavelength,
                spectral_data=spectral_data,
                measurement_type=measurement_type.value,
                timestamp=datetime.now(),
                luminance=luminance if cmd == 'r' else 0,
                illuminance=luminance if cmd == 'i' else 0,
                integration_time_ms=actual_int_time,
                num_scans=n_scans,
                saturation_level=saturated,
                raw_counts=raw_counts,
                device_name="OSpRad",
                device_serial=str(unit_number),
                device_info={
                    'unit_number': unit_number,
                    'saturated_pixels': saturated,
                },
                spectral_unit=MeasurementUnit.WATTS_PER_SR_SQM_NM if cmd == 'r' else MeasurementUnit.WATTS_PER_SQM_NM,
                luminance_unit=MeasurementUnit.CD_PER_SQM if cmd == 'r' else MeasurementUnit.LUX,
            )
            
            self.status = DeviceStatus.CONNECTED
            return result
            
        except Exception as e:
            self.set_error(f"Measurement failed: {e}")
            self.status = DeviceStatus.ERROR
            return None
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings"""
        return {
            'integration_time': self.integration_time,
            'min_scans': self.min_scans,
            'max_scans': self.max_scans,
        }
    
    # =========================================================================
    # Private Methods
    # =========================================================================
    
    def _connect_android(self):
        """Connect via USB on Android"""
        usb_device_list = usb.get_usb_device_list()
        device_name_list = [device.getDeviceName() for device in usb_device_list]
        
        if not device_name_list:
            raise RuntimeError("No USB devices found")
        
        serial_name = device_name_list[0]
        device_name = usb.get_usb_device(serial_name)
        
        while not usb.has_usb_permission(device_name):
            usb.request_usb_permission(device_name)
            time.sleep(1)
        
        return serial4a.get_serial_port(serial_name, SERIAL_BAUD_RATE, 8, 'N', 1, timeout=1)
    
    def _connect_desktop(self):
        """Connect via serial port on desktop"""
        ports = serial.tools.list_ports.comports()
        com_list = [p.device for p in ports]
        
        if not com_list:
            raise RuntimeError("No serial ports found")
        
        print(f"Available ports: {com_list}")
        return serial.Serial(com_list[0], SERIAL_BAUD_RATE)
    
    def _send_command(self, command: str) -> bool:
        """Send command and wait for acknowledgment"""
        try:
            self.ser.write(str.encode(command))
            self.ser.readline()  # Wait for ack
            return True
        except Exception as e:
            print(f"Command error: {e}")
            return False
    
    def _request_measurement(self, cmd: str) -> Optional[List[float]]:
        """Request and read measurement data"""
        try:
            print(f"Sending measurement command: {cmd}")
            self.ser.write(str.encode(cmd))
            
            output = " "
            while output != "":
                output = self.ser.readline()
                if output != b'':
                    values = output.split(b',')
                    try:
                        return [float(v) for v in values]
                    except ValueError as e:
                        print(f"Parse error: {output}")
                        return None
            
            return None
            
        except Exception as e:
            print(f"Measurement error: {e}")
            return None
    
    def _calculate_spectrum(
        self, 
        raw_counts: List[float], 
        int_time: int, 
        measurement_type: str
    ) -> tuple:
        """Calculate calibrated spectrum and luminance"""
        spectral_data = [0.0] * len(raw_counts)
        luminance = 0.0
        
        cal = self.calibration
        sensitivity = cal.irr_sens if measurement_type == 'i' else cal.rad_sens
        
        for i in range(len(raw_counts)):
            if float(sensitivity[i]) <= 0:
                continue
            
            # Linearity correction
            if raw_counts[i] > 0:
                lin_mult = float(cal.lin_coefs[0]) * math.log(
                    (raw_counts[i] + 1) * float(cal.lin_coefs[1])
                )
            else:
                lin_mult = -1 * float(cal.lin_coefs[0]) * math.log(
                    (-raw_counts[i] + 1) * float(cal.lin_coefs[1])
                )
            
            # Convert to physical units
            spectral_data[i] = (raw_counts[i] / lin_mult) / (
                float(sensitivity[i]) * int_time * cal.wavelength_bins[i]
            )
            
            # Accumulate luminance
            luminance += spectral_data[i] * cal.wavelength_bins[i] * cal.ciey[i]
        
        luminance *= LUMINANCE_CONSTANT
        
        return spectral_data, luminance
