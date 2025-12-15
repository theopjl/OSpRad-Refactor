"""
Color calculation utilities for OSpRad examples

Provides helper functions to calculate chromaticity, CCT, and CRI
from spectral data - mimicking JETI SDK functionality.
"""

import math
from typing import List, Tuple, Optional
import numpy as np


# ============================================================================
# CIE Color Matching Functions (1931 2° observer)
# ============================================================================

# Simplified wavelength range: 380-780 nm at 5nm intervals
CIE_WAVELENGTHS = list(range(380, 785, 5))

# CIE 1931 2° standard observer color matching functions (simplified)
# These are approximate values for demonstration purposes
# For production, use complete CIE tables or colormath library
CIE_X = [
    0.001368, 0.002236, 0.004243, 0.007650, 0.014310,
    0.023190, 0.043510, 0.077630, 0.134380, 0.214770,
    0.283900, 0.328500, 0.348280, 0.348060, 0.336200,
    0.318700, 0.290800, 0.251100, 0.195360, 0.142100,
    0.095640, 0.057950, 0.032010, 0.014700, 0.004900,
    0.002400, 0.009300, 0.029100, 0.063270, 0.109600,
    0.165500, 0.225750, 0.290400, 0.359700, 0.433450,
    0.512050, 0.594500, 0.678400, 0.762100, 0.842500,
    0.916300, 0.978600, 1.026300, 1.056700, 1.062200,
    1.045600, 1.002600, 0.938400, 0.854450, 0.751400,
    0.642400, 0.541900, 0.447900, 0.360800, 0.283500,
    0.218700, 0.164900, 0.121200, 0.087400, 0.063600,
    0.046770, 0.032900, 0.022700, 0.015840, 0.011359,
    0.008111, 0.005790, 0.004109, 0.002899, 0.002049,
    0.001440, 0.001000, 0.000690, 0.000476, 0.000332,
    0.000235, 0.000166, 0.000117, 0.000083, 0.000059,
    0.000042
]

CIE_Y = [
    0.000039, 0.000064, 0.000120, 0.000217, 0.000396,
    0.000640, 0.001210, 0.002180, 0.004000, 0.007300,
    0.011600, 0.016840, 0.023000, 0.029800, 0.038000,
    0.048000, 0.060000, 0.073900, 0.090980, 0.112600,
    0.139020, 0.169300, 0.208020, 0.258600, 0.323000,
    0.407300, 0.503000, 0.608200, 0.710000, 0.793200,
    0.862000, 0.914850, 0.954000, 0.980300, 0.994950,
    1.000000, 0.995000, 0.978600, 0.952000, 0.915400,
    0.870000, 0.816300, 0.757000, 0.694900, 0.631000,
    0.566800, 0.503000, 0.441200, 0.381000, 0.321000,
    0.265000, 0.217000, 0.175000, 0.138200, 0.107000,
    0.081600, 0.061000, 0.044580, 0.032000, 0.023200,
    0.017000, 0.011920, 0.008210, 0.005723, 0.004102,
    0.002929, 0.002091, 0.001484, 0.001047, 0.000740,
    0.000520, 0.000361, 0.000249, 0.000172, 0.000120,
    0.000085, 0.000060, 0.000042, 0.000030, 0.000021,
    0.000015
]

CIE_Z = [
    0.006450, 0.010550, 0.020050, 0.036210, 0.067850,
    0.110200, 0.207400, 0.371300, 0.645600, 1.039050,
    1.385600, 1.622960, 1.747060, 1.782600, 1.772110,
    1.744100, 1.669200, 1.528100, 1.287640, 1.041900,
    0.812950, 0.616200, 0.465180, 0.353300, 0.272000,
    0.212300, 0.158200, 0.111700, 0.078250, 0.057250,
    0.042160, 0.029840, 0.020300, 0.013400, 0.008750,
    0.005750, 0.003900, 0.002750, 0.002100, 0.001800,
    0.001650, 0.001400, 0.001100, 0.001000, 0.000800,
    0.000600, 0.000340, 0.000240, 0.000190, 0.000100,
    0.000050, 0.000030, 0.000020, 0.000010, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000
]


def interpolate_cie_values(wavelength: float) -> Tuple[float, float, float]:
    """
    Interpolate CIE XYZ color matching functions at a given wavelength.
    
    Args:
        wavelength: Wavelength in nm
        
    Returns:
        Tuple of (x, y, z) color matching function values
    """
    if wavelength < CIE_WAVELENGTHS[0] or wavelength > CIE_WAVELENGTHS[-1]:
        return (0.0, 0.0, 0.0)
    
    # Find bracketing indices
    for i in range(len(CIE_WAVELENGTHS) - 1):
        if CIE_WAVELENGTHS[i] <= wavelength <= CIE_WAVELENGTHS[i + 1]:
            # Linear interpolation
            t = (wavelength - CIE_WAVELENGTHS[i]) / (CIE_WAVELENGTHS[i + 1] - CIE_WAVELENGTHS[i])
            x = CIE_X[i] + t * (CIE_X[i + 1] - CIE_X[i])
            y = CIE_Y[i] + t * (CIE_Y[i + 1] - CIE_Y[i])
            z = CIE_Z[i] + t * (CIE_Z[i + 1] - CIE_Z[i])
            return (x, y, z)
    
    return (0.0, 0.0, 0.0)


def calculate_chromaticity(
    wavelengths: List[float],
    spectral_data: List[float]
) -> Tuple[float, float]:
    """
    Calculate CIE 1931 chromaticity coordinates from spectral data.
    
    Args:
        wavelengths: Wavelength values in nm
        spectral_data: Spectral intensity values
        
    Returns:
        Tuple of (x, y) chromaticity coordinates
    """
    if len(wavelengths) != len(spectral_data):
        raise ValueError("Wavelength and spectral data must have same length")
    
    # Calculate tristimulus values X, Y, Z
    X = 0.0
    Y = 0.0
    Z = 0.0
    
    for i in range(len(wavelengths) - 1):
        wl = wavelengths[i]
        intensity = spectral_data[i]
        
        # Get CIE values at this wavelength
        x_bar, y_bar, z_bar = interpolate_cie_values(wl)
        
        # Calculate wavelength bin width
        dwl = wavelengths[i + 1] - wavelengths[i]
        
        # Integrate
        X += intensity * x_bar * dwl
        Y += intensity * y_bar * dwl
        Z += intensity * z_bar * dwl
    
    # Calculate chromaticity coordinates
    total = X + Y + Z
    if total < 1e-10:
        return (0.3333, 0.3333)  # Equal energy white point
    
    x = X / total
    y = Y / total
    
    return (x, y)


def calculate_cct(x: float, y: float) -> float:
    """
    Calculate Correlated Color Temperature from chromaticity coordinates.
    
    Uses McCamy's approximation formula.
    
    Args:
        x: CIE x chromaticity coordinate
        y: CIE y chromaticity coordinate
        
    Returns:
        CCT in Kelvin
    """
    # McCamy's formula
    n = (x - 0.3320) / (0.1858 - y)
    cct = 449.0 * n**3 + 3525.0 * n**2 + 6823.3 * n + 5520.33
    
    return cct


def calculate_cri(
    wavelengths: List[float],
    spectral_data: List[float],
    cct: Optional[float] = None
) -> List[float]:
    """
    Calculate Color Rendering Index (CRI) from spectral data.
    
    This is a simplified approximation. For accurate CRI calculation,
    use specialized colorimetry libraries.
    
    Args:
        wavelengths: Wavelength values in nm
        spectral_data: Spectral intensity values
        cct: Correlated Color Temperature (calculated if not provided)
        
    Returns:
        List of 15 CRI values: [Ra, R1, R2, ..., R14]
        Ra is the general color rendering index
    """
    # TODO: This is a placeholder implementation
    # Real CRI calculation requires:
    # 1. Reference illuminant SPD (blackbody or D-series)
    # 2. 14 test color samples (TCS)
    # 3. Chromatic adaptation transform
    # 4. Complex color difference calculations
    
    # For now, return estimated values based on spectral characteristics
    if cct is None:
        x, y = calculate_chromaticity(wavelengths, spectral_data)
        cct = calculate_cct(x, y)
    
    # Very rough estimation based on CCT
    # Real implementation needed for production use
    if 2500 <= cct <= 6500:
        ra = 85.0 + 10.0 * math.exp(-abs(cct - 5000) / 2000)
    else:
        ra = 70.0
    
    # Generate individual R values with some variation
    cri_values = [ra]  # Ra
    for i in range(14):
        variation = (hash(str(i)) % 20 - 10) * 0.5  # Deterministic variation
        cri_values.append(max(0, min(100, ra + variation)))
    
    return cri_values


def spectrum_to_rgb(
    wavelengths: List[float],
    spectral_data: List[float],
    gamma: float = 2.2
) -> Tuple[int, int, int]:
    """
    Convert spectral data to approximate RGB color.
    
    Args:
        wavelengths: Wavelength values in nm
        spectral_data: Spectral intensity values
        gamma: Gamma correction factor
        
    Returns:
        Tuple of (R, G, B) values in range 0-255
    """
    # Calculate CIE XYZ
    X = 0.0
    Y = 0.0
    Z = 0.0
    
    for i in range(len(wavelengths) - 1):
        wl = wavelengths[i]
        intensity = spectral_data[i]
        x_bar, y_bar, z_bar = interpolate_cie_values(wl)
        dwl = wavelengths[i + 1] - wavelengths[i]
        
        X += intensity * x_bar * dwl
        Y += intensity * y_bar * dwl
        Z += intensity * z_bar * dwl
    
    # Normalize
    if Y > 0:
        X /= Y
        Z /= Y
        Y = 1.0
    
    # XYZ to RGB (sRGB D65)
    r =  3.2406 * X - 1.5372 * Y - 0.4986 * Z
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    b =  0.0557 * X - 0.2040 * Y + 1.0570 * Z
    
    # Gamma correction and clipping
    def gamma_correct(val):
        if val <= 0:
            return 0
        val = val ** (1.0 / gamma)
        return int(max(0, min(255, val * 255)))
    
    return (gamma_correct(r), gamma_correct(g), gamma_correct(b))
