"""
Calculation Engine for Directional Driller Application

This module implements the calculation engine for directional drilling calculations,
including minimum curvature method, dogleg severity, and other directional drilling
calculations.
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any

class CalculationEngine:
    """
    Calculation engine for directional drilling calculations.
    
    Provides methods for calculating wellbore trajectory, dogleg severity,
    and other directional drilling calculations.
    """
    
    def __init__(self):
        """Initialize the calculation engine with default settings."""
        self.methods = {
            'minimum_curvature': self._minimum_curvature_method,
            'radius_of_curvature': self._radius_of_curvature_method,
            'tangential': self._tangential_method,
            'balanced_tangential': self._balanced_tangential_method
        }
        self.default_method = 'minimum_curvature'
    
    def calculate_wellpath(self, survey_data: List[Dict[str, float]], 
                          method: str = None) -> List[Dict[str, float]]:
        """
        Calculate wellpath using the specified method.
        
        Args:
            survey_data: List of survey points (each with md, inc, azi)
            method: Calculation method to use (default: minimum_curvature)
            
        Returns:
            List of wellpath points with calculated TVD, northing, easting, etc.
        """
        if method is None:
            method = self.default_method
        
        if method not in self.methods:
            raise ValueError(f"Unknown method: {method}")
        
        return self.methods[method](survey_data)
    
    def calculate_dogleg_severity(self, inc1: float, azi1: float, 
                                 inc2: float, azi2: float,
                                 md_diff: float = 100.0,
                                 unit_system: str = 'imperial') -> float:
        """
        Calculate dogleg severity between two survey points.
        
        Args:
            inc1: Inclination at first point (degrees)
            azi1: Azimuth at first point (degrees)
            inc2: Inclination at second point (degrees)
            azi2: Azimuth at second point (degrees)
            md_diff: Measured depth difference between points
            unit_system: Unit system ('metric' or 'imperial')
            
        Returns:
            Dogleg severity in degrees per 100ft (imperial) or 30m (metric)
        """
        # Convert to radians
        inc1_rad = math.radians(inc1)
        azi1_rad = math.radians(azi1)
        inc2_rad = math.radians(inc2)
        azi2_rad = math.radians(azi2)
        
        # Calculate dogleg angle
        cos_dogleg = (math.cos(inc1_rad) * math.cos(inc2_rad) + 
                     math.sin(inc1_rad) * math.sin(inc2_rad) * 
                     math.cos(azi2_rad - azi1_rad))
        
        # Handle numerical precision issues
        cos_dogleg = max(min(cos_dogleg, 1.0), -1.0)
        
        dogleg = math.degrees(math.acos(cos_dogleg))
        
        # Calculate dogleg severity
        if unit_system.lower() == 'metric':
            # Degrees per 30m
            dls = dogleg * 30 / md_diff
        else:
            # Degrees per 100ft
            dls = dogleg * 100 / md_diff
        
        return dls
    
    def calculate_build_turn_rates(self, survey_data: List[Dict[str, float]]) -> Tuple[List[float], List[float]]:
        """
        Calculate build and turn rates between survey points.
        
        Args:
            survey_data: List of survey points (each with md, inc, azi)
            
        Returns:
            Tuple of (build_rates, turn_rates) lists
        """
        build_rates = []
        turn_rates = []
        
        for i in range(1, len(survey_data)):
            prev = survey_data[i-1]
            curr = survey_data[i]
            
            md_diff = curr['md'] - prev['md']
            
            if md_diff > 0:
                # Build rate (degrees per 100ft)
                build_rate = (curr['inc'] - prev['inc']) / md_diff * 100
                
                # Turn rate (degrees per 100ft)
                # Handle azimuth wrap-around
                azi_diff = curr['azi'] - prev['azi']
                if azi_diff > 180:
                    azi_diff -= 360
                elif azi_diff < -180:
                    azi_diff += 360
                
                turn_rate = azi_diff / md_diff * 100
                
                build_rates.append(build_rate)
                turn_rates.append(turn_rate)
            else:
                # If MD difference is zero, use zero rates
                build_rates.append(0)
                turn_rates.append(0)
        
        return build_rates, turn_rates
    
    def calculate_closure(self, wellpath: List[Dict[str, float]]) -> List[float]:
        """
        Calculate closure (horizontal distance from wellhead) for each survey point.
        
        Args:
            wellpath: List of wellpath points with northing and easting
            
        Returns:
            List of closure values
        """
        closure = []
        
        for point in wellpath:
            # Calculate closure as sqrt(northing^2 + easting^2)
            closure_val = math.sqrt(point['northing']**2 + point['easting']**2)
            closure.append(closure_val)
        
        return closure
    
    def calculate_vertical_section(self, survey_data: List[Dict[str, float]], 
                                  reference_azimuth: float = 0.0) -> List[float]:
        """
        Calculate vertical section for each survey point.
        
        Args:
            survey_data: List of survey points with northing and easting
            reference_azimuth: Reference azimuth for vertical section (degrees)
            
        Returns:
            List of vertical section values
        """
        vertical_section = []
        ref_azi_rad = math.radians(reference_azimuth)
        
        for point in survey_data:
            # If point doesn't have northing/easting, use zeros
            northing = point.get('northing', 0)
            easting = point.get('easting', 0)
            
            # Calculate vertical section
            vs = northing * math.cos(ref_azi_rad) + easting * math.sin(ref_azi_rad)
            vertical_section.append(vs)
        
        return vertical_section
    
    def calculate_toolface(self, inc: float, azi: float, 
                          toolface_gravity: float, toolface_magnetic: float) -> Tuple[float, float]:
        """
        Calculate gravity and magnetic toolface angles.
        
        Args:
            inc: Hole inclination (degrees)
            azi: Hole azimuth (degrees)
            toolface_gravity: Gravity toolface reading (degrees)
            toolface_magnetic: Magnetic toolface reading (degrees)
            
        Returns:
            Tuple of (gravity_toolface, magnetic_toolface) in degrees
        """
        # Convert to radians
        inc_rad = math.radians(inc)
        azi_rad = math.radians(azi)
        toolface_gravity_rad = math.radians(toolface_gravity)
        toolface_magnetic_rad = math.radians(toolface_magnetic)
        
        # Calculate gravity toolface
        if inc < 3.0:
            # Near vertical, gravity toolface is undefined
            gravity_toolface = 0.0
        else:
            gravity_toolface = toolface_gravity
        
        # Calculate magnetic toolface
        magnetic_toolface = (toolface_magnetic + azi) % 360
        
        return gravity_toolface, magnetic_toolface
    
    def project_well(self, md_start: float, inc_start: float, azi_start: float,
                    build_rate: float, turn_rate: float, step: float, 
                    num_steps: int) -> List[Dict[str, float]]:
        """
        Project well ahead based on current position and build/turn rates.
        
        Args:
            md_start: Starting measured depth
            inc_start: Starting inclination (degrees)
            azi_start: Starting azimuth (degrees)
            build_rate: Build rate (degrees per 100ft)
            turn_rate: Turn rate (degrees per 100ft)
            step: Step size in measured depth
            num_steps: Number of steps to project
            
        Returns:
            List of projected survey points
        """
        projection = []
        
        # Add starting point
        projection.append({
            'md': md_start,
            'inc': inc_start,
            'azi': azi_start
        })
        
        # Project forward
        for i in range(num_steps):
            prev = projection[-1]
            
            # Calculate new MD
            md = prev['md'] + step
            
            # Calculate new inclination
            inc = prev['inc'] + build_rate * step / 100
            
            # Calculate new azimuth
            azi = (prev['azi'] + turn_rate * step / 100) % 360
            
            # Add new point
            projection.append({
                'md': md,
                'inc': inc,
                'azi': azi
            })
        
        # Calculate coordinates for projected points
        return self._minimum_curvature_method(projection)
    
    def _minimum_curvature_method(self, survey_data: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Calculate wellpath using minimum curvature method.
        
        Args:
            survey_data: List of survey points (each with md, inc, azi)
            
        Returns:
            List of wellpath points with calculated TVD, northing, easting, etc.
        """
        if not survey_data:
            return []
        
        # Initialize wellpath with first point
        wellpath = [{
            'md': survey_data[0]['md'],
            'inc': survey_data[0]['inc'],
            'azi': survey_data[0]['azi'],
            'tvd': 0.0,
            'northing': 0.0,
            'easting': 0.0,
            'dogleg': 0.0,
            'dls': 0.0
        }]
        
        # Calculate remaining points
        for i in range(1, len(survey_data)):
            prev = survey_data[i-1]
            curr = survey_data[i]
            
            # Extract values
            md1 = prev['md']
            inc1 = prev['inc']
            azi1 = prev['azi']
            md2 = curr['md']
            inc2 = curr['inc']
            azi2 = curr['azi']
            
            # Convert to radians
            inc1_rad = math.radians(inc1)
            azi1_rad = math.radians(azi1)
            inc2_rad = math.radians(inc2)
            azi2_rad = math.radians(azi2)
            
            # Calculate dogleg angle
            cos_dogleg = (math.cos(inc1_rad) * math.cos(inc2_rad) + 
                         math.sin(inc1_rad) * math.sin(inc2_rad) * 
                         math.cos(azi2_rad - azi1_rad))
            
            # Handle numerical precision issues
            cos_dogleg = max(min(cos_dogleg, 1.0), -1.0)
            
            dogleg = math.acos(cos_dogleg)
            dogleg_deg = math.degrees(dogleg)
            
            # Calculate dogleg severity (degrees per 100ft)
            md_diff = md2 - md1
            if md_diff > 0:
                dls = dogleg_deg * 100 / md_diff
            else:
                dls = 0.0
            
            # Calculate ratio factor
            if dogleg < 0.0001:  # Near zero dogleg
                rf = 1.0
            else:
                rf = 2 * math.tan(dogleg / 2) / dogleg
            
            # Calculate TVD, northing, easting
            delta_md = md2 - md1
            delta_tvd = delta_md / 2 * (math.cos(inc1_rad) + math.cos(inc2_rad)) * rf
            delta_northing = delta_md / 2 * (math.sin(inc1_rad) * math.cos(azi1_rad) + 
                                           math.sin(inc2_rad) * math.cos(azi2_rad)) * rf
            delta_easting = delta_md / 2 * (math.sin(inc1_rad) * math.sin(azi1_rad) + 
                                          math.sin(inc2_rad) * math.sin(azi2_rad)) * rf
            
            # Add to previous values
            tvd = wellpath[-1]['tvd'] + delta_tvd
            northing = wellpath[-1]['northing'] + delta_northing
            easting = wellpath[-1]['easting'] + delta_easting
            
            # Add to wellpath
            wellpath.append({
                'md': md2,
                'inc': inc2,
                'azi': azi2,
                'tvd': tvd,
                'northing': northing,
                'easting': easting,
                'dogleg': dogleg_deg,
                'dls': dls
            })
        
        return wellpath
    
    def _radius_of_curvature_method(self, survey_data: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Calculate wellpath using radius of curvature method.
        
        Args:
            survey_data: List of survey points (each with md, inc, azi)
            
        Returns:
            List of wellpath points with calculated TVD, northing, easting, etc.
        """
        # Similar implementation to minimum curvature but with different formulas
        # For now, we'll use minimum curvature as a fallback
        return self._minimum_curvature_method(survey_data)
    
    def _tangential_method(self, survey_data: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Calculate wellpath using tangential method.
        
        Args:
            survey_data: List of survey points (each with md, inc, azi)
            
        Returns:
            List of wellpath points with calculated TVD, northing, easting, etc.
        """
        # Similar implementation to minimum curvature but with different formulas
        # For now, we'll use minimum curvature as a fallback
        return self._minimum_curvature_method(survey_data)
    
    def _balanced_tangential_method(self, survey_data: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Calculate wellpath using balanced tangential method.
        
        Args:
            survey_data: List of survey points (each with md, inc, azi)
            
        Returns:
            List of wellpath points with calculated TVD, northing, easting, etc.
        """
        # Similar implementation to minimum curvature but with different formulas
        # For now, we'll use minimum curvature as a fallback
        return self._minimum_curvature_method(survey_data)
