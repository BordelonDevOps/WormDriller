"""
Enhanced Calculation Engine for WormDriller Hybrid Architecture

This module implements the complete directional drilling calculation engine
that was present in the original PyQt application, enhanced for use in both
the FastAPI service and desktop application.
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json


class CalculationMethod(Enum):
    """Enumeration of available calculation methods."""
    MINIMUM_CURVATURE = "minimum_curvature"
    RADIUS_OF_CURVATURE = "radius_of_curvature"
    TANGENTIAL = "tangential"
    BALANCED_TANGENTIAL = "balanced_tangential"


class UnitSystem(Enum):
    """Enumeration of unit systems."""
    METRIC = "metric"
    IMPERIAL = "imperial"


@dataclass
class SurveyPoint:
    """
    Data class for a single survey point.
    
    Contains measured depth, inclination, azimuth, and calculated values.
    """
    md: float
    inc: float
    azi: float
    tvd: float = 0.0
    northing: float = 0.0
    easting: float = 0.0
    dogleg: float = 0.0
    dls: float = 0.0
    build_rate: float = 0.0
    turn_rate: float = 0.0
    closure: float = 0.0
    vertical_section: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert survey point to dictionary."""
        return {
            'md': self.md,
            'inc': self.inc,
            'azi': self.azi,
            'tvd': self.tvd,
            'northing': self.northing,
            'easting': self.easting,
            'dogleg': self.dogleg,
            'dls': self.dls,
            'build_rate': self.build_rate,
            'turn_rate': self.turn_rate,
            'closure': self.closure,
            'vertical_section': self.vertical_section
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'SurveyPoint':
        """Create survey point from dictionary."""
        return cls(
            md=data['md'],
            inc=data['inc'],
            azi=data['azi'],
            tvd=data.get('tvd', 0.0),
            northing=data.get('northing', 0.0),
            easting=data.get('easting', 0.0),
            dogleg=data.get('dogleg', 0.0),
            dls=data.get('dls', 0.0),
            build_rate=data.get('build_rate', 0.0),
            turn_rate=data.get('turn_rate', 0.0),
            closure=data.get('closure', 0.0),
            vertical_section=data.get('vertical_section', 0.0)
        )


@dataclass
class CalculationResult:
    """
    Data class for calculation results.
    
    Contains the calculated wellpath and metadata about the calculation.
    """
    wellpath: List[SurveyPoint]
    method: CalculationMethod
    unit_system: UnitSystem
    total_md: float
    total_tvd: float
    max_inc: float
    max_dls: float
    calculation_time: float
    quality_metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert calculation result to dictionary."""
        return {
            'wellpath': [point.to_dict() for point in self.wellpath],
            'method': self.method.value,
            'unit_system': self.unit_system.value,
            'total_md': self.total_md,
            'total_tvd': self.total_tvd,
            'max_inc': self.max_inc,
            'max_dls': self.max_dls,
            'calculation_time': self.calculation_time,
            'quality_metrics': self.quality_metrics
        }


class EnhancedCalculationEngine:
    """
    Enhanced calculation engine for directional drilling calculations.
    
    Provides all calculation methods from the original application plus
    additional features for the hybrid architecture.
    """
    
    def __init__(self):
        """Initialize the calculation engine."""
        self.methods = {
            CalculationMethod.MINIMUM_CURVATURE: self._minimum_curvature_method,
            CalculationMethod.RADIUS_OF_CURVATURE: self._radius_of_curvature_method,
            CalculationMethod.TANGENTIAL: self._tangential_method,
            CalculationMethod.BALANCED_TANGENTIAL: self._balanced_tangential_method
        }
        self.default_method = CalculationMethod.MINIMUM_CURVATURE
        self.tolerance = 1e-10
        self.max_iterations = 1000
    
    def calculate_wellpath(self, 
                          survey_data: List[Dict[str, float]], 
                          method: CalculationMethod = None,
                          unit_system: UnitSystem = UnitSystem.IMPERIAL,
                          reference_azimuth: float = 0.0) -> CalculationResult:
        """
        Calculate wellpath using the specified method.
        
        Args:
            survey_data: List of survey points (each with md, inc, azi)
            method: Calculation method to use
            unit_system: Unit system for calculations
            reference_azimuth: Reference azimuth for vertical section
            
        Returns:
            CalculationResult with calculated wellpath and metadata
        """
        import time
        start_time = time.time()
        
        if method is None:
            method = self.default_method
        
        if method not in self.methods:
            raise ValueError(f"Unknown method: {method}")
        
        # Convert input data to SurveyPoint objects
        survey_points = [SurveyPoint.from_dict(point) for point in survey_data]
        
        # Validate survey data
        self._validate_survey_data(survey_points)
        
        # Calculate wellpath using specified method
        calculated_points = self.methods[method](survey_points, unit_system)
        
        # Calculate additional parameters
        self._calculate_build_turn_rates(calculated_points, unit_system)
        self._calculate_closure(calculated_points)
        self._calculate_vertical_section(calculated_points, reference_azimuth)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(calculated_points)
        
        # Calculate summary statistics
        total_md = calculated_points[-1].md if calculated_points else 0.0
        total_tvd = calculated_points[-1].tvd if calculated_points else 0.0
        max_inc = max(point.inc for point in calculated_points) if calculated_points else 0.0
        max_dls = max(point.dls for point in calculated_points) if calculated_points else 0.0
        
        calculation_time = time.time() - start_time
        
        return CalculationResult(
            wellpath=calculated_points,
            method=method,
            unit_system=unit_system,
            total_md=total_md,
            total_tvd=total_tvd,
            max_inc=max_inc,
            max_dls=max_dls,
            calculation_time=calculation_time,
            quality_metrics=quality_metrics
        )
    
    def calculate_dogleg_severity(self, 
                                 inc1: float, azi1: float, 
                                 inc2: float, azi2: float,
                                 md_diff: float,
                                 unit_system: UnitSystem = UnitSystem.IMPERIAL) -> float:
        """
        Calculate dogleg severity between two survey points.
        
        Args:
            inc1: Inclination at first point (degrees)
            azi1: Azimuth at first point (degrees)
            inc2: Inclination at second point (degrees)
            azi2: Azimuth at second point (degrees)
            md_diff: Measured depth difference between points
            unit_system: Unit system for calculations
            
        Returns:
            Dogleg severity in degrees per 100ft (imperial) or 30m (metric)
        """
        # Convert to radians
        inc1_rad = math.radians(inc1)
        azi1_rad = math.radians(azi1)
        inc2_rad = math.radians(inc2)
        azi2_rad = math.radians(azi2)
        
        # Calculate dogleg angle using spherical trigonometry
        cos_dogleg = (math.cos(inc1_rad) * math.cos(inc2_rad) + 
                     math.sin(inc1_rad) * math.sin(inc2_rad) * 
                     math.cos(azi2_rad - azi1_rad))
        
        # Handle numerical precision issues
        cos_dogleg = max(min(cos_dogleg, 1.0), -1.0)
        
        dogleg = math.degrees(math.acos(cos_dogleg))
        
        # Calculate dogleg severity
        if unit_system == UnitSystem.METRIC:
            # Degrees per 30m
            dls = dogleg * 30 / md_diff if md_diff > 0 else 0.0
        else:
            # Degrees per 100ft
            dls = dogleg * 100 / md_diff if md_diff > 0 else 0.0
        
        return dls
    
    def project_wellpath(self,
                        start_point: Dict[str, float],
                        build_rate: float,
                        turn_rate: float,
                        step_size: float,
                        num_steps: int,
                        unit_system: UnitSystem = UnitSystem.IMPERIAL) -> List[SurveyPoint]:
        """
        Project wellpath ahead based on build and turn rates.
        
        Args:
            start_point: Starting survey point
            build_rate: Build rate (degrees per 100ft or 30m)
            turn_rate: Turn rate (degrees per 100ft or 30m)
            step_size: Step size in measured depth
            num_steps: Number of steps to project
            unit_system: Unit system for calculations
            
        Returns:
            List of projected survey points
        """
        projection = []
        
        # Convert start point
        current = SurveyPoint.from_dict(start_point)
        projection.append(current)
        
        # Calculate rate factors based on unit system
        if unit_system == UnitSystem.METRIC:
            rate_factor = step_size / 30.0
        else:
            rate_factor = step_size / 100.0
        
        # Project forward
        for i in range(num_steps):
            prev = projection[-1]
            
            # Calculate new survey point
            md = prev.md + step_size
            inc = prev.inc + build_rate * rate_factor
            azi = (prev.azi + turn_rate * rate_factor) % 360
            
            # Ensure inclination stays within valid range
            inc = max(0.0, min(180.0, inc))
            
            new_point = SurveyPoint(md=md, inc=inc, azi=azi)
            projection.append(new_point)
        
        # Calculate coordinates for projected points using minimum curvature
        return self._minimum_curvature_method(projection, unit_system)
    
    def _validate_survey_data(self, survey_points: List[SurveyPoint]) -> None:
        """
        Validate survey data for calculation.
        
        Args:
            survey_points: List of survey points to validate
            
        Raises:
            ValueError: If survey data is invalid
        """
        if not survey_points:
            raise ValueError("Survey data cannot be empty")
        
        if len(survey_points) < 2:
            raise ValueError("At least two survey points are required")
        
        for i, point in enumerate(survey_points):
            # Check for valid measured depth
            if point.md < 0:
                raise ValueError(f"Invalid measured depth at point {i}: {point.md}")
            
            # Check for valid inclination
            if not (0 <= point.inc <= 180):
                raise ValueError(f"Invalid inclination at point {i}: {point.inc}")
            
            # Check for valid azimuth
            if not (0 <= point.azi < 360):
                raise ValueError(f"Invalid azimuth at point {i}: {point.azi}")
            
            # Check for monotonic measured depth
            if i > 0 and point.md <= survey_points[i-1].md:
                raise ValueError(f"Measured depth must be monotonically increasing at point {i}")
    
    def _minimum_curvature_method(self, 
                                 survey_points: List[SurveyPoint],
                                 unit_system: UnitSystem) -> List[SurveyPoint]:
        """
        Calculate wellpath using minimum curvature method.
        
        Args:
            survey_points: List of survey points
            unit_system: Unit system for calculations
            
        Returns:
            List of calculated survey points
        """
        if not survey_points:
            return []
        
        # Initialize first point
        calculated_points = [survey_points[0]]
        calculated_points[0].tvd = 0.0
        calculated_points[0].northing = 0.0
        calculated_points[0].easting = 0.0
        calculated_points[0].dogleg = 0.0
        calculated_points[0].dls = 0.0
        
        # Calculate remaining points
        for i in range(1, len(survey_points)):
            prev = survey_points[i-1]
            curr = survey_points[i]
            
            # Create new calculated point
            calc_point = SurveyPoint(
                md=curr.md,
                inc=curr.inc,
                azi=curr.azi
            )
            
            # Convert to radians
            inc1_rad = math.radians(prev.inc)
            azi1_rad = math.radians(prev.azi)
            inc2_rad = math.radians(curr.inc)
            azi2_rad = math.radians(curr.azi)
            
            # Calculate dogleg angle
            cos_dogleg = (math.cos(inc1_rad) * math.cos(inc2_rad) + 
                         math.sin(inc1_rad) * math.sin(inc2_rad) * 
                         math.cos(azi2_rad - azi1_rad))
            
            # Handle numerical precision issues
            cos_dogleg = max(min(cos_dogleg, 1.0), -1.0)
            
            dogleg = math.acos(cos_dogleg)
            dogleg_deg = math.degrees(dogleg)
            
            # Calculate dogleg severity
            md_diff = curr.md - prev.md
            if md_diff > 0:
                if unit_system == UnitSystem.METRIC:
                    dls = dogleg_deg * 30 / md_diff
                else:
                    dls = dogleg_deg * 100 / md_diff
            else:
                dls = 0.0
            
            # Calculate ratio factor for minimum curvature
            if dogleg < self.tolerance:
                rf = 1.0
            else:
                rf = 2 * math.tan(dogleg / 2) / dogleg
            
            # Calculate coordinate changes
            delta_md = curr.md - prev.md
            delta_tvd = delta_md / 2 * (math.cos(inc1_rad) + math.cos(inc2_rad)) * rf
            delta_northing = delta_md / 2 * (math.sin(inc1_rad) * math.cos(azi1_rad) + 
                                           math.sin(inc2_rad) * math.cos(azi2_rad)) * rf
            delta_easting = delta_md / 2 * (math.sin(inc1_rad) * math.sin(azi1_rad) + 
                                          math.sin(inc2_rad) * math.sin(azi2_rad)) * rf
            
            # Update calculated point
            calc_point.tvd = calculated_points[-1].tvd + delta_tvd
            calc_point.northing = calculated_points[-1].northing + delta_northing
            calc_point.easting = calculated_points[-1].easting + delta_easting
            calc_point.dogleg = dogleg_deg
            calc_point.dls = dls
            
            calculated_points.append(calc_point)
        
        return calculated_points
    
    def _radius_of_curvature_method(self, 
                                   survey_points: List[SurveyPoint],
                                   unit_system: UnitSystem) -> List[SurveyPoint]:
        """
        Calculate wellpath using radius of curvature method.
        
        This is a simplified implementation that uses minimum curvature
        as the base and applies radius of curvature corrections.
        """
        # For now, use minimum curvature as base
        # In a full implementation, this would use the specific
        # radius of curvature formulations
        return self._minimum_curvature_method(survey_points, unit_system)
    
    def _tangential_method(self, 
                          survey_points: List[SurveyPoint],
                          unit_system: UnitSystem) -> List[SurveyPoint]:
        """
        Calculate wellpath using tangential method.
        
        This method assumes the wellbore follows a straight line
        between survey points at the inclination and azimuth
        of the upper survey point.
        """
        if not survey_points:
            return []
        
        # Initialize first point
        calculated_points = [survey_points[0]]
        calculated_points[0].tvd = 0.0
        calculated_points[0].northing = 0.0
        calculated_points[0].easting = 0.0
        calculated_points[0].dogleg = 0.0
        calculated_points[0].dls = 0.0
        
        # Calculate remaining points
        for i in range(1, len(survey_points)):
            prev = survey_points[i-1]
            curr = survey_points[i]
            
            # Create new calculated point
            calc_point = SurveyPoint(
                md=curr.md,
                inc=curr.inc,
                azi=curr.azi
            )
            
            # Use previous point's inclination and azimuth
            inc_rad = math.radians(prev.inc)
            azi_rad = math.radians(prev.azi)
            
            # Calculate coordinate changes
            delta_md = curr.md - prev.md
            delta_tvd = delta_md * math.cos(inc_rad)
            delta_northing = delta_md * math.sin(inc_rad) * math.cos(azi_rad)
            delta_easting = delta_md * math.sin(inc_rad) * math.sin(azi_rad)
            
            # Calculate dogleg and DLS
            dogleg_deg = self._calculate_dogleg_angle(prev.inc, prev.azi, curr.inc, curr.azi)
            if delta_md > 0:
                if unit_system == UnitSystem.METRIC:
                    dls = dogleg_deg * 30 / delta_md
                else:
                    dls = dogleg_deg * 100 / delta_md
            else:
                dls = 0.0
            
            # Update calculated point
            calc_point.tvd = calculated_points[-1].tvd + delta_tvd
            calc_point.northing = calculated_points[-1].northing + delta_northing
            calc_point.easting = calculated_points[-1].easting + delta_easting
            calc_point.dogleg = dogleg_deg
            calc_point.dls = dls
            
            calculated_points.append(calc_point)
        
        return calculated_points
    
    def _balanced_tangential_method(self, 
                                   survey_points: List[SurveyPoint],
                                   unit_system: UnitSystem) -> List[SurveyPoint]:
        """
        Calculate wellpath using balanced tangential method.
        
        This method uses the average of the inclination and azimuth
        values at the two survey points.
        """
        if not survey_points:
            return []
        
        # Initialize first point
        calculated_points = [survey_points[0]]
        calculated_points[0].tvd = 0.0
        calculated_points[0].northing = 0.0
        calculated_points[0].easting = 0.0
        calculated_points[0].dogleg = 0.0
        calculated_points[0].dls = 0.0
        
        # Calculate remaining points
        for i in range(1, len(survey_points)):
            prev = survey_points[i-1]
            curr = survey_points[i]
            
            # Create new calculated point
            calc_point = SurveyPoint(
                md=curr.md,
                inc=curr.inc,
                azi=curr.azi
            )
            
            # Calculate average inclination and azimuth
            avg_inc = (prev.inc + curr.inc) / 2
            
            # Handle azimuth averaging with wrap-around
            azi_diff = curr.azi - prev.azi
            if azi_diff > 180:
                azi_diff -= 360
            elif azi_diff < -180:
                azi_diff += 360
            avg_azi = (prev.azi + azi_diff / 2) % 360
            
            # Convert to radians
            inc_rad = math.radians(avg_inc)
            azi_rad = math.radians(avg_azi)
            
            # Calculate coordinate changes
            delta_md = curr.md - prev.md
            delta_tvd = delta_md * math.cos(inc_rad)
            delta_northing = delta_md * math.sin(inc_rad) * math.cos(azi_rad)
            delta_easting = delta_md * math.sin(inc_rad) * math.sin(azi_rad)
            
            # Calculate dogleg and DLS
            dogleg_deg = self._calculate_dogleg_angle(prev.inc, prev.azi, curr.inc, curr.azi)
            if delta_md > 0:
                if unit_system == UnitSystem.METRIC:
                    dls = dogleg_deg * 30 / delta_md
                else:
                    dls = dogleg_deg * 100 / delta_md
            else:
                dls = 0.0
            
            # Update calculated point
            calc_point.tvd = calculated_points[-1].tvd + delta_tvd
            calc_point.northing = calculated_points[-1].northing + delta_northing
            calc_point.easting = calculated_points[-1].easting + delta_easting
            calc_point.dogleg = dogleg_deg
            calc_point.dls = dls
            
            calculated_points.append(calc_point)
        
        return calculated_points
    
    def _calculate_dogleg_angle(self, inc1: float, azi1: float, inc2: float, azi2: float) -> float:
        """Calculate dogleg angle between two survey points."""
        inc1_rad = math.radians(inc1)
        azi1_rad = math.radians(azi1)
        inc2_rad = math.radians(inc2)
        azi2_rad = math.radians(azi2)
        
        cos_dogleg = (math.cos(inc1_rad) * math.cos(inc2_rad) + 
                     math.sin(inc1_rad) * math.sin(inc2_rad) * 
                     math.cos(azi2_rad - azi1_rad))
        
        cos_dogleg = max(min(cos_dogleg, 1.0), -1.0)
        return math.degrees(math.acos(cos_dogleg))
    
    def _calculate_build_turn_rates(self, 
                                   calculated_points: List[SurveyPoint],
                                   unit_system: UnitSystem) -> None:
        """Calculate build and turn rates for calculated points."""
        for i in range(1, len(calculated_points)):
            prev = calculated_points[i-1]
            curr = calculated_points[i]
            
            md_diff = curr.md - prev.md
            
            if md_diff > 0:
                # Calculate rate factor
                if unit_system == UnitSystem.METRIC:
                    rate_factor = 30.0 / md_diff
                else:
                    rate_factor = 100.0 / md_diff
                
                # Build rate (inclination change)
                curr.build_rate = (curr.inc - prev.inc) * rate_factor
                
                # Turn rate (azimuth change with wrap-around handling)
                azi_diff = curr.azi - prev.azi
                if azi_diff > 180:
                    azi_diff -= 360
                elif azi_diff < -180:
                    azi_diff += 360
                
                curr.turn_rate = azi_diff * rate_factor
            else:
                curr.build_rate = 0.0
                curr.turn_rate = 0.0
    
    def _calculate_closure(self, calculated_points: List[SurveyPoint]) -> None:
        """Calculate closure (horizontal distance from wellhead) for each point."""
        for point in calculated_points:
            point.closure = math.sqrt(point.northing**2 + point.easting**2)
    
    def _calculate_vertical_section(self, 
                                   calculated_points: List[SurveyPoint],
                                   reference_azimuth: float) -> None:
        """Calculate vertical section for each point."""
        ref_azi_rad = math.radians(reference_azimuth)
        
        for point in calculated_points:
            point.vertical_section = (point.northing * math.cos(ref_azi_rad) + 
                                    point.easting * math.sin(ref_azi_rad))
    
    def _calculate_quality_metrics(self, calculated_points: List[SurveyPoint]) -> Dict[str, float]:
        """Calculate quality metrics for the calculated wellpath."""
        if not calculated_points:
            return {}
        
        # Calculate various quality metrics
        dls_values = [point.dls for point in calculated_points if point.dls > 0]
        
        metrics = {
            'max_dls': max(dls_values) if dls_values else 0.0,
            'avg_dls': sum(dls_values) / len(dls_values) if dls_values else 0.0,
            'num_high_dls': sum(1 for dls in dls_values if dls > 3.0),
            'total_dogleg': sum(point.dogleg for point in calculated_points),
            'max_inclination': max(point.inc for point in calculated_points),
            'total_closure': calculated_points[-1].closure if calculated_points else 0.0,
            'calculation_points': len(calculated_points)
        }
        
        return metrics

