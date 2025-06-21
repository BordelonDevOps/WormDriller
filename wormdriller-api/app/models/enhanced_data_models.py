"""
Enhanced data models for the hybrid WormDriller architecture.

This module provides comprehensive data models that support both the
FastAPI service and desktop application components.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid
import json


class UnitSystem(str, Enum):
    """Unit system enumeration."""
    METRIC = "metric"
    IMPERIAL = "imperial"


class WellType(str, Enum):
    """Well type enumeration."""
    VERTICAL = "vertical"
    DIRECTIONAL = "directional"
    HORIZONTAL = "horizontal"
    MULTILATERAL = "multilateral"


class WellStatus(str, Enum):
    """Well status enumeration."""
    PLANNED = "planned"
    DRILLING = "drilling"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    ABANDONED = "abandoned"


class ComponentType(str, Enum):
    """BHA component type enumeration."""
    BIT = "bit"
    MOTOR = "motor"
    MWD = "mwd"
    LWD = "lwd"
    STABILIZER = "stabilizer"
    DRILL_COLLAR = "drill_collar"
    HEAVY_WEIGHT_DRILL_PIPE = "hwdp"
    DRILL_PIPE = "drill_pipe"
    CROSSOVER = "crossover"
    OTHER = "other"


class Location(BaseModel):
    """Geographic location model."""
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude in decimal degrees")
    elevation: Optional[float] = Field(None, description="Elevation above sea level")
    coordinate_system: Optional[str] = Field("WGS84", description="Coordinate system")
    utm_zone: Optional[str] = Field(None, description="UTM zone if applicable")
    
    class Config:
        schema_extra = {
            "example": {
                "latitude": 29.7604,
                "longitude": -95.3698,
                "elevation": 50.0,
                "coordinate_system": "WGS84"
            }
        }


class WellModel(BaseModel):
    """Comprehensive well information model."""
    well_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique well identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Well name")
    operator: str = Field(..., min_length=1, max_length=100, description="Operating company")
    field: Optional[str] = Field(None, max_length=100, description="Field name")
    location: Optional[Location] = Field(None, description="Well location")
    rig_name: Optional[str] = Field(None, max_length=100, description="Rig name")
    well_type: WellType = Field(WellType.DIRECTIONAL, description="Type of well")
    status: WellStatus = Field(WellStatus.PLANNED, description="Current well status")
    unit_system: UnitSystem = Field(UnitSystem.IMPERIAL, description="Unit system")
    
    # Drilling parameters
    target_depth: Optional[float] = Field(None, gt=0, description="Target total depth")
    surface_casing_depth: Optional[float] = Field(None, gt=0, description="Surface casing depth")
    intermediate_casing_depth: Optional[float] = Field(None, gt=0, description="Intermediate casing depth")
    production_casing_depth: Optional[float] = Field(None, gt=0, description="Production casing depth")
    
    # Metadata
    spud_date: Optional[datetime] = Field(None, description="Spud date")
    completion_date: Optional[datetime] = Field(None, description="Completion date")
    created_date: datetime = Field(default_factory=datetime.now, description="Record creation date")
    updated_date: datetime = Field(default_factory=datetime.now, description="Last update date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Well-001",
                "operator": "ABC Energy",
                "field": "Eagle Ford",
                "location": {
                    "latitude": 29.7604,
                    "longitude": -95.3698,
                    "elevation": 50.0
                },
                "rig_name": "Rig-42",
                "well_type": "directional",
                "target_depth": 15000.0
            }
        }


class SurveyPointModel(BaseModel):
    """Enhanced survey point model."""
    md: float = Field(..., ge=0, description="Measured depth")
    inc: float = Field(..., ge=0, le=180, description="Inclination in degrees")
    azi: float = Field(..., ge=0, lt=360, description="Azimuth in degrees")
    
    # Calculated values
    tvd: Optional[float] = Field(None, description="True vertical depth")
    northing: Optional[float] = Field(None, description="Northing coordinate")
    easting: Optional[float] = Field(None, description="Easting coordinate")
    dogleg: Optional[float] = Field(None, ge=0, description="Dogleg angle in degrees")
    dls: Optional[float] = Field(None, ge=0, description="Dogleg severity")
    build_rate: Optional[float] = Field(None, description="Build rate")
    turn_rate: Optional[float] = Field(None, description="Turn rate")
    closure: Optional[float] = Field(None, ge=0, description="Closure distance")
    vertical_section: Optional[float] = Field(None, description="Vertical section")
    
    # Quality and metadata
    survey_date: Optional[datetime] = Field(None, description="Survey measurement date")
    survey_method: Optional[str] = Field(None, description="Survey measurement method")
    quality_code: Optional[str] = Field(None, description="Data quality code")
    comments: Optional[str] = Field(None, description="Survey comments")
    
    @validator('azi')
    def normalize_azimuth(cls, v):
        """Normalize azimuth to 0-360 range."""
        return v % 360
    
    class Config:
        schema_extra = {
            "example": {
                "md": 5000.0,
                "inc": 45.5,
                "azi": 135.2,
                "tvd": 3535.5,
                "northing": 1250.3,
                "easting": 1250.3,
                "dogleg": 2.5,
                "dls": 1.8
            }
        }


class SurveyModel(BaseModel):
    """Comprehensive survey data model."""
    survey_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique survey identifier")
    well_id: str = Field(..., description="Associated well identifier")
    survey_name: Optional[str] = Field(None, description="Survey name or identifier")
    survey_points: List[SurveyPointModel] = Field(default_factory=list, description="Survey points")
    
    # Calculation parameters
    calculation_method: Optional[str] = Field("minimum_curvature", description="Calculation method used")
    reference_azimuth: Optional[float] = Field(0.0, description="Reference azimuth for vertical section")
    magnetic_declination: Optional[float] = Field(0.0, description="Magnetic declination correction")
    
    # Quality metrics
    data_quality_score: Optional[float] = Field(None, ge=0, le=100, description="Overall data quality score")
    completeness_score: Optional[float] = Field(None, ge=0, le=100, description="Data completeness score")
    
    # Metadata
    created_date: datetime = Field(default_factory=datetime.now, description="Survey creation date")
    updated_date: datetime = Field(default_factory=datetime.now, description="Last update date")
    created_by: Optional[str] = Field(None, description="Survey creator")
    comments: Optional[str] = Field(None, description="Survey comments")
    
    @validator('survey_points')
    def validate_survey_points(cls, v):
        """Validate survey points for monotonic MD."""
        if len(v) < 2:
            return v
        
        for i in range(1, len(v)):
            if v[i].md <= v[i-1].md:
                raise ValueError(f"Measured depth must be monotonically increasing at point {i}")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "well_id": "well-123",
                "survey_name": "Final Survey",
                "calculation_method": "minimum_curvature",
                "survey_points": [
                    {"md": 0, "inc": 0, "azi": 0},
                    {"md": 1000, "inc": 2, "azi": 45},
                    {"md": 5000, "inc": 45, "azi": 135}
                ]
            }
        }


class BHAComponent(BaseModel):
    """BHA component model."""
    component_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Component identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Component name")
    component_type: ComponentType = Field(..., description="Component type")
    manufacturer: Optional[str] = Field(None, max_length=100, description="Manufacturer")
    model: Optional[str] = Field(None, max_length=100, description="Model number")
    
    # Physical properties
    length: float = Field(..., gt=0, description="Component length")
    outer_diameter: float = Field(..., gt=0, description="Outer diameter")
    inner_diameter: Optional[float] = Field(None, gt=0, description="Inner diameter")
    weight: Optional[float] = Field(None, gt=0, description="Component weight")
    
    # Position in BHA
    position_from_bit: float = Field(..., ge=0, description="Distance from bit")
    
    # Performance characteristics
    max_wob: Optional[float] = Field(None, gt=0, description="Maximum weight on bit")
    max_torque: Optional[float] = Field(None, gt=0, description="Maximum torque")
    max_flow_rate: Optional[float] = Field(None, gt=0, description="Maximum flow rate")
    
    # Metadata
    serial_number: Optional[str] = Field(None, description="Serial number")
    comments: Optional[str] = Field(None, description="Component comments")
    
    @validator('inner_diameter')
    def validate_inner_diameter(cls, v, values):
        """Validate that inner diameter is less than outer diameter."""
        if v is not None and 'outer_diameter' in values and v >= values['outer_diameter']:
            raise ValueError("Inner diameter must be less than outer diameter")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "8.5in PDC Bit",
                "component_type": "bit",
                "manufacturer": "Smith Bits",
                "length": 1.2,
                "outer_diameter": 8.5,
                "position_from_bit": 0.0
            }
        }


class BHAModel(BaseModel):
    """Bottom Hole Assembly model."""
    bha_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="BHA identifier")
    well_id: str = Field(..., description="Associated well identifier")
    bha_name: str = Field(..., min_length=1, max_length=100, description="BHA name")
    components: List[BHAComponent] = Field(default_factory=list, description="BHA components")
    
    # BHA characteristics
    total_length: Optional[float] = Field(None, ge=0, description="Total BHA length")
    total_weight: Optional[float] = Field(None, ge=0, description="Total BHA weight")
    
    # Operational parameters
    recommended_wob: Optional[float] = Field(None, gt=0, description="Recommended weight on bit")
    recommended_rpm: Optional[float] = Field(None, gt=0, description="Recommended RPM")
    recommended_flow_rate: Optional[float] = Field(None, gt=0, description="Recommended flow rate")
    
    # Metadata
    created_date: datetime = Field(default_factory=datetime.now, description="BHA creation date")
    updated_date: datetime = Field(default_factory=datetime.now, description="Last update date")
    created_by: Optional[str] = Field(None, description="BHA creator")
    comments: Optional[str] = Field(None, description="BHA comments")
    
    @validator('components')
    def sort_components_by_position(cls, v):
        """Sort components by position from bit."""
        return sorted(v, key=lambda x: x.position_from_bit)
    
    def calculate_totals(self):
        """Calculate total length and weight."""
        if self.components:
            self.total_length = sum(comp.length for comp in self.components)
            self.total_weight = sum(comp.weight for comp in self.components if comp.weight)
    
    class Config:
        schema_extra = {
            "example": {
                "well_id": "well-123",
                "bha_name": "BHA Run #1",
                "components": [
                    {
                        "name": "8.5in PDC Bit",
                        "component_type": "bit",
                        "length": 1.2,
                        "outer_diameter": 8.5,
                        "position_from_bit": 0.0
                    }
                ]
            }
        }


class DrillingParameters(BaseModel):
    """Real-time drilling parameters model."""
    timestamp: datetime = Field(default_factory=datetime.now, description="Measurement timestamp")
    md: float = Field(..., ge=0, description="Measured depth")
    
    # Primary drilling parameters
    wob: Optional[float] = Field(None, ge=0, description="Weight on bit")
    torque: Optional[float] = Field(None, ge=0, description="Surface torque")
    rpm: Optional[float] = Field(None, ge=0, description="Rotary speed")
    flow_rate: Optional[float] = Field(None, ge=0, description="Flow rate")
    spp: Optional[float] = Field(None, ge=0, description="Standpipe pressure")
    rop: Optional[float] = Field(None, ge=0, description="Rate of penetration")
    
    # Additional parameters
    hookload: Optional[float] = Field(None, ge=0, description="Hookload")
    block_height: Optional[float] = Field(None, description="Block height")
    pump_pressure: Optional[float] = Field(None, ge=0, description="Pump pressure")
    
    # Formation evaluation
    gamma_ray: Optional[float] = Field(None, ge=0, description="Gamma ray reading")
    resistivity: Optional[float] = Field(None, ge=0, description="Resistivity")
    
    # Quality indicators
    data_quality: Optional[str] = Field(None, description="Data quality indicator")
    comments: Optional[str] = Field(None, description="Parameter comments")
    
    class Config:
        schema_extra = {
            "example": {
                "md": 5000.0,
                "wob": 25000.0,
                "torque": 8500.0,
                "rpm": 120.0,
                "flow_rate": 450.0,
                "spp": 2800.0,
                "rop": 45.5
            }
        }


class ProjectModel(BaseModel):
    """Project model for managing multiple wells."""
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Project identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    operator: str = Field(..., min_length=1, max_length=100, description="Operating company")
    field: Optional[str] = Field(None, max_length=100, description="Field name")
    
    # Project settings
    default_unit_system: UnitSystem = Field(UnitSystem.IMPERIAL, description="Default unit system")
    default_calculation_method: Optional[str] = Field("minimum_curvature", description="Default calculation method")
    
    # Wells in project
    well_ids: List[str] = Field(default_factory=list, description="List of well IDs in project")
    
    # Metadata
    created_date: datetime = Field(default_factory=datetime.now, description="Project creation date")
    updated_date: datetime = Field(default_factory=datetime.now, description="Last update date")
    created_by: Optional[str] = Field(None, description="Project creator")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Eagle Ford Development",
                "description": "Multi-well development project",
                "operator": "ABC Energy",
                "field": "Eagle Ford",
                "default_unit_system": "imperial"
            }
        }


class CalculationQualityMetrics(BaseModel):
    """Quality metrics for calculations."""
    max_dls: float = Field(..., description="Maximum dogleg severity")
    avg_dls: float = Field(..., description="Average dogleg severity")
    num_high_dls: int = Field(..., description="Number of high DLS points")
    total_dogleg: float = Field(..., description="Total dogleg angle")
    max_inclination: float = Field(..., description="Maximum inclination")
    total_closure: float = Field(..., description="Total closure distance")
    calculation_points: int = Field(..., description="Number of calculation points")
    
    # Data quality indicators
    data_completeness: Optional[float] = Field(None, ge=0, le=100, description="Data completeness percentage")
    calculation_convergence: Optional[float] = Field(None, ge=0, le=100, description="Calculation convergence score")
    
    class Config:
        schema_extra = {
            "example": {
                "max_dls": 3.5,
                "avg_dls": 1.2,
                "num_high_dls": 2,
                "total_dogleg": 45.8,
                "max_inclination": 89.5,
                "total_closure": 2500.0,
                "calculation_points": 25
            }
        }

