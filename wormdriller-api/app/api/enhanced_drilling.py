"""
Enhanced API endpoints for directional drilling calculations.

This module provides comprehensive REST API endpoints for all directional
drilling calculations, integrating the enhanced calculation engine with
the FastAPI service.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import time
import logging

from ..models.enhanced_calculation_engine import (
    EnhancedCalculationEngine, 
    CalculationMethod, 
    UnitSystem,
    SurveyPoint,
    CalculationResult
)
from ..models.enhanced_data_models import (
    WellModel, SurveyModel, SurveyPointModel, BHAModel, BHAComponent,
    DrillingParameters, ProjectModel, UnitSystem, WellType, ComponentType
)
from ..core.auth import get_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/calculations", tags=["calculations"])

# Initialize calculation engine
calc_engine = EnhancedCalculationEngine()


class SurveyPointRequest(BaseModel):
    """Request model for survey point data."""
    md: float = Field(..., ge=0, description="Measured depth")
    inc: float = Field(..., ge=0, le=180, description="Inclination in degrees")
    azi: float = Field(..., ge=0, lt=360, description="Azimuth in degrees")


class WellpathCalculationRequest(BaseModel):
    """Request model for wellpath calculation."""
    survey_points: List[SurveyPointRequest] = Field(..., min_items=2)
    method: Optional[str] = Field("minimum_curvature", description="Calculation method")
    unit_system: Optional[str] = Field("imperial", description="Unit system")
    reference_azimuth: Optional[float] = Field(0.0, ge=0, lt=360, description="Reference azimuth for vertical section")
    
    @validator('method')
    def validate_method(cls, v):
        valid_methods = [method.value for method in CalculationMethod]
        if v not in valid_methods:
            raise ValueError(f"Method must be one of: {valid_methods}")
        return v
    
    @validator('unit_system')
    def validate_unit_system(cls, v):
        valid_systems = [system.value for system in UnitSystem]
        if v not in valid_systems:
            raise ValueError(f"Unit system must be one of: {valid_systems}")
        return v


class DoglegseverityRequest(BaseModel):
    """Request model for dogleg severity calculation."""
    inc1: float = Field(..., ge=0, le=180, description="First inclination in degrees")
    azi1: float = Field(..., ge=0, lt=360, description="First azimuth in degrees")
    inc2: float = Field(..., ge=0, le=180, description="Second inclination in degrees")
    azi2: float = Field(..., ge=0, lt=360, description="Second azimuth in degrees")
    md_diff: float = Field(..., gt=0, description="Measured depth difference")
    unit_system: Optional[str] = Field("imperial", description="Unit system")
    
    @validator('unit_system')
    def validate_unit_system(cls, v):
        valid_systems = [system.value for system in UnitSystem]
        if v not in valid_systems:
            raise ValueError(f"Unit system must be one of: {valid_systems}")
        return v


class WellProjectionRequest(BaseModel):
    """Request model for well projection."""
    start_point: SurveyPointRequest
    build_rate: float = Field(..., description="Build rate in degrees per 100ft or 30m")
    turn_rate: float = Field(..., description="Turn rate in degrees per 100ft or 30m")
    step_size: float = Field(..., gt=0, description="Step size in measured depth")
    num_steps: int = Field(..., gt=0, le=1000, description="Number of steps to project")
    unit_system: Optional[str] = Field("imperial", description="Unit system")
    
    @validator('unit_system')
    def validate_unit_system(cls, v):
        valid_systems = [system.value for system in UnitSystem]
        if v not in valid_systems:
            raise ValueError(f"Unit system must be one of: {valid_systems}")
        return v


class CalculationResponse(BaseModel):
    """Response model for calculation results."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    calculation_time: Optional[float] = None


@router.post("/wellpath", response_model=CalculationResponse)
async def calculate_wellpath(
    request: WellpathCalculationRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Calculate wellbore trajectory using specified method.
    
    This endpoint performs complete wellpath calculations including:
    - TVD, northing, easting coordinates
    - Dogleg severity and build/turn rates
    - Closure and vertical section
    - Quality metrics and validation
    """
    try:
        logger.info(f"Calculating wellpath with {len(request.survey_points)} points using {request.method}")
        
        # Convert request to calculation engine format
        survey_data = [point.dict() for point in request.survey_points]
        method = CalculationMethod(request.method)
        unit_system = UnitSystem(request.unit_system)
        
        # Perform calculation
        result = calc_engine.calculate_wellpath(
            survey_data=survey_data,
            method=method,
            unit_system=unit_system,
            reference_azimuth=request.reference_azimuth
        )
        
        logger.info(f"Wellpath calculation completed in {result.calculation_time:.3f}s")
        
        return CalculationResponse(
            success=True,
            data=result.to_dict(),
            message=f"Wellpath calculated successfully using {method.value}",
            calculation_time=result.calculation_time
        )
        
    except ValueError as e:
        logger.error(f"Validation error in wellpath calculation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in wellpath calculation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal calculation error")


@router.post("/dogleg-severity", response_model=CalculationResponse)
async def calculate_dogleg_severity(
    request: DoglegseverityRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Calculate dogleg severity between two survey points.
    
    Returns the dogleg severity in degrees per 100ft (imperial) 
    or degrees per 30m (metric).
    """
    try:
        start_time = time.time()
        
        unit_system = UnitSystem(request.unit_system)
        
        dls = calc_engine.calculate_dogleg_severity(
            inc1=request.inc1,
            azi1=request.azi1,
            inc2=request.inc2,
            azi2=request.azi2,
            md_diff=request.md_diff,
            unit_system=unit_system
        )
        
        calculation_time = time.time() - start_time
        
        unit_label = "°/30m" if unit_system == UnitSystem.METRIC else "°/100ft"
        
        return CalculationResponse(
            success=True,
            data={
                "dogleg_severity": dls,
                "unit": unit_label,
                "inc1": request.inc1,
                "azi1": request.azi1,
                "inc2": request.inc2,
                "azi2": request.azi2,
                "md_diff": request.md_diff
            },
            message=f"Dogleg severity calculated: {dls:.2f} {unit_label}",
            calculation_time=calculation_time
        )
        
    except ValueError as e:
        logger.error(f"Validation error in dogleg calculation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in dogleg calculation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal calculation error")


@router.post("/project-wellpath", response_model=CalculationResponse)
async def project_wellpath(
    request: WellProjectionRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Project wellpath ahead based on build and turn rates.
    
    This endpoint projects the wellbore trajectory forward from a starting
    point using specified build and turn rates.
    """
    try:
        start_time = time.time()
        
        unit_system = UnitSystem(request.unit_system)
        start_point = request.start_point.dict()
        
        projected_points = calc_engine.project_wellpath(
            start_point=start_point,
            build_rate=request.build_rate,
            turn_rate=request.turn_rate,
            step_size=request.step_size,
            num_steps=request.num_steps,
            unit_system=unit_system
        )
        
        calculation_time = time.time() - start_time
        
        # Convert to response format
        projection_data = [point.to_dict() for point in projected_points]
        
        return CalculationResponse(
            success=True,
            data={
                "projected_points": projection_data,
                "start_point": start_point,
                "build_rate": request.build_rate,
                "turn_rate": request.turn_rate,
                "step_size": request.step_size,
                "num_steps": request.num_steps,
                "unit_system": unit_system.value,
                "total_projected_md": projected_points[-1].md - projected_points[0].md if projected_points else 0
            },
            message=f"Wellpath projected {request.num_steps} steps successfully",
            calculation_time=calculation_time
        )
        
    except ValueError as e:
        logger.error(f"Validation error in wellpath projection: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in wellpath projection: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal calculation error")


@router.get("/methods", response_model=CalculationResponse)
async def get_calculation_methods():
    """
    Get available calculation methods and unit systems.
    
    Returns information about supported calculation methods,
    unit systems, and their descriptions.
    """
    try:
        methods_info = {
            "calculation_methods": [
                {
                    "value": method.value,
                    "name": method.value.replace("_", " ").title(),
                    "description": _get_method_description(method)
                }
                for method in CalculationMethod
            ],
            "unit_systems": [
                {
                    "value": system.value,
                    "name": system.value.title(),
                    "description": _get_unit_system_description(system)
                }
                for system in UnitSystem
            ],
            "default_method": calc_engine.default_method.value,
            "tolerance": calc_engine.tolerance,
            "max_iterations": calc_engine.max_iterations
        }
        
        return CalculationResponse(
            success=True,
            data=methods_info,
            message="Calculation methods retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving calculation methods: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate-survey", response_model=CalculationResponse)
async def validate_survey_data(
    request: WellpathCalculationRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Validate survey data without performing calculations.
    
    This endpoint validates survey data for completeness, consistency,
    and physical feasibility without performing the actual calculations.
    """
    try:
        start_time = time.time()
        
        # Convert request to survey points
        survey_data = [point.dict() for point in request.survey_points]
        survey_points = [SurveyPoint.from_dict(point) for point in survey_data]
        
        # Validate survey data
        calc_engine._validate_survey_data(survey_points)
        
        # Calculate basic statistics
        md_range = survey_points[-1].md - survey_points[0].md if len(survey_points) > 1 else 0
        inc_range = max(point.inc for point in survey_points) - min(point.inc for point in survey_points)
        azi_range = _calculate_azimuth_range(survey_points)
        
        # Check for potential issues
        warnings = []
        if any(abs(survey_points[i].md - survey_points[i-1].md) < 1.0 for i in range(1, len(survey_points))):
            warnings.append("Some survey points are very close together (< 1 unit)")
        
        if inc_range > 90:
            warnings.append("Large inclination changes detected")
        
        calculation_time = time.time() - start_time
        
        return CalculationResponse(
            success=True,
            data={
                "valid": True,
                "num_points": len(survey_points),
                "md_range": md_range,
                "inc_range": inc_range,
                "azi_range": azi_range,
                "warnings": warnings,
                "statistics": {
                    "start_md": survey_points[0].md,
                    "end_md": survey_points[-1].md,
                    "min_inc": min(point.inc for point in survey_points),
                    "max_inc": max(point.inc for point in survey_points),
                    "min_azi": min(point.azi for point in survey_points),
                    "max_azi": max(point.azi for point in survey_points)
                }
            },
            message="Survey data validation completed successfully",
            calculation_time=calculation_time
        )
        
    except ValueError as e:
        return CalculationResponse(
            success=False,
            data={"valid": False, "error": str(e)},
            message=f"Survey data validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in survey validation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal validation error")


def _get_method_description(method: CalculationMethod) -> str:
    """Get description for calculation method."""
    descriptions = {
        CalculationMethod.MINIMUM_CURVATURE: "Industry standard method providing highest accuracy",
        CalculationMethod.RADIUS_OF_CURVATURE: "Alternative method using radius of curvature assumptions",
        CalculationMethod.TANGENTIAL: "Simple method using upper survey point angles",
        CalculationMethod.BALANCED_TANGENTIAL: "Improved tangential method using averaged angles"
    }
    return descriptions.get(method, "No description available")


def _get_unit_system_description(system: UnitSystem) -> str:
    """Get description for unit system."""
    descriptions = {
        UnitSystem.IMPERIAL: "Feet and degrees per 100ft for dogleg severity",
        UnitSystem.METRIC: "Meters and degrees per 30m for dogleg severity"
    }
    return descriptions.get(system, "No description available")


def _calculate_azimuth_range(survey_points: List[SurveyPoint]) -> float:
    """Calculate azimuth range handling wrap-around."""
    if len(survey_points) < 2:
        return 0.0
    
    azimuths = [point.azi for point in survey_points]
    
    # Handle azimuth wrap-around by finding the minimum range
    min_range = 360.0
    for offset in range(0, 360, 30):  # Check different offset points
        adjusted_azimuths = [(azi + offset) % 360 for azi in azimuths]
        range_val = max(adjusted_azimuths) - min(adjusted_azimuths)
        min_range = min(min_range, range_val)
    
    return min_range

