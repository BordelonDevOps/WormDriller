"""
Data Models for Directional Driller Application

This module defines the data models for the directional drilling application,
including well information, survey data, BHA components, and drilling parameters.
"""

import json
import os
import uuid
import datetime
from typing import Dict, List, Optional, Union, Any


class WellModel:
    """
    Model for well information.
    
    Stores basic information about a well, including name, operator,
    location, and other metadata.
    """
    
    def __init__(self, name: str, operator: str, 
                location: Optional[Dict[str, float]] = None,
                rig_name: Optional[str] = None,
                metadata: Optional[Dict[str, Any]] = None,
                well_id: Optional[str] = None):
        """
        Initialize a well model.
        
        Args:
            name: Well name
            operator: Operator name
            location: Dictionary with latitude and longitude
            rig_name: Rig name
            metadata: Additional metadata
            well_id: Unique identifier (generated if not provided)
        """
        self.name = name
        self.operator = operator
        self.location = location or {}
        self.rig_name = rig_name or ""
        self.metadata = metadata or {}
        self.well_id = well_id or str(uuid.uuid4())
        self.creation_date = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert well model to dictionary."""
        return {
            'name': self.name,
            'operator': self.operator,
            'location': self.location,
            'rig_name': self.rig_name,
            'metadata': self.metadata,
            'well_id': self.well_id,
            'creation_date': self.creation_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WellModel':
        """Create well model from dictionary."""
        return cls(
            name=data['name'],
            operator=data['operator'],
            location=data.get('location', {}),
            rig_name=data.get('rig_name', ""),
            metadata=data.get('metadata', {}),
            well_id=data.get('well_id')
        )
    
    def save_to_file(self, filepath: str) -> None:
        """Save well model to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'WellModel':
        """Load well model from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class SurveyPoint:
    """
    Model for a single survey point.
    
    Stores measured depth, inclination, azimuth, and calculated values
    such as TVD, northing, easting, dogleg, and dogleg severity.
    """
    
    def __init__(self, md: float, inc: float, azi: float,
                tvd: float = 0.0, northing: float = 0.0, easting: float = 0.0,
                dogleg: float = 0.0, dls: float = 0.0):
        """
        Initialize a survey point.
        
        Args:
            md: Measured depth
            inc: Inclination (degrees)
            azi: Azimuth (degrees)
            tvd: True vertical depth (calculated)
            northing: Northing coordinate (calculated)
            easting: Easting coordinate (calculated)
            dogleg: Dogleg angle (calculated)
            dls: Dogleg severity (calculated)
        """
        self.md = md
        self.inc = inc
        self.azi = azi
        self.tvd = tvd
        self.northing = northing
        self.easting = easting
        self.dogleg = dogleg
        self.dls = dls
    
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
            'dls': self.dls
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
            dls=data.get('dls', 0.0)
        )


class SurveyModel:
    """
    Model for survey data.
    
    Stores a collection of survey points for a well, along with
    metadata such as the well ID and unit system.
    """
    
    def __init__(self, well_id: str, unit_system: str = 'metric'):
        """
        Initialize a survey model.
        
        Args:
            well_id: Well identifier
            unit_system: Unit system ('metric' or 'imperial')
        """
        self.well_id = well_id
        self.unit_system = unit_system
        self.surveys: List[SurveyPoint] = []
        self.creation_date = datetime.datetime.now().isoformat()
    
    def add_survey(self, survey: SurveyPoint) -> None:
        """Add a survey point to the model."""
        self.surveys.append(survey)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert survey model to dictionary."""
        return {
            'well_id': self.well_id,
            'unit_system': self.unit_system,
            'surveys': [s.to_dict() for s in self.surveys],
            'creation_date': self.creation_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SurveyModel':
        """Create survey model from dictionary."""
        model = cls(
            well_id=data['well_id'],
            unit_system=data.get('unit_system', 'metric')
        )
        for survey_data in data.get('surveys', []):
            model.add_survey(SurveyPoint.from_dict(survey_data))
        return model
    
    def save_to_file(self, filepath: str) -> None:
        """Save survey model to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'SurveyModel':
        """Load survey model from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class BHAComponent:
    """
    Model for a BHA component.
    
    Stores information about a bottom hole assembly component,
    including name, type, dimensions, and position.
    """
    
    def __init__(self, name: str, type: str, length: float, od: float, id: float,
                weight: float, position: float):
        """
        Initialize a BHA component.
        
        Args:
            name: Component name
            type: Component type (bit, motor, MWD, etc.)
            length: Component length
            od: Outside diameter
            id: Inside diameter
            weight: Component weight
            position: Position from bit (0 = bit)
        """
        self.name = name
        self.type = type
        self.length = length
        self.od = od
        self.id = id
        self.weight = weight
        self.position = position
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert BHA component to dictionary."""
        return {
            'name': self.name,
            'type': self.type,
            'length': self.length,
            'od': self.od,
            'id': self.id,
            'weight': self.weight,
            'position': self.position
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BHAComponent':
        """Create BHA component from dictionary."""
        return cls(
            name=data['name'],
            type=data['type'],
            length=data['length'],
            od=data['od'],
            id=data['id'],
            weight=data['weight'],
            position=data['position']
        )


class BHAModel:
    """
    Model for BHA data.
    
    Stores a collection of BHA components for a well, along with
    metadata such as the well ID, BHA name, and unit system.
    """
    
    def __init__(self, well_id: str, name: str, unit_system: str = 'metric',
                bha_id: Optional[str] = None):
        """
        Initialize a BHA model.
        
        Args:
            well_id: Well identifier
            name: BHA name
            unit_system: Unit system ('metric' or 'imperial')
            bha_id: Unique identifier (generated if not provided)
        """
        self.well_id = well_id
        self.name = name
        self.unit_system = unit_system
        self.bha_id = bha_id or str(uuid.uuid4())
        self.components: List[BHAComponent] = []
        self.creation_date = datetime.datetime.now().isoformat()
    
    def add_component(self, component: BHAComponent) -> None:
        """Add a component to the BHA."""
        self.components.append(component)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert BHA model to dictionary."""
        return {
            'well_id': self.well_id,
            'name': self.name,
            'unit_system': self.unit_system,
            'bha_id': self.bha_id,
            'components': [c.to_dict() for c in self.components],
            'creation_date': self.creation_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BHAModel':
        """Create BHA model from dictionary."""
        model = cls(
            well_id=data['well_id'],
            name=data['name'],
            unit_system=data.get('unit_system', 'metric'),
            bha_id=data.get('bha_id')
        )
        for component_data in data.get('components', []):
            model.add_component(BHAComponent.from_dict(component_data))
        return model
    
    def save_to_file(self, filepath: str) -> None:
        """Save BHA model to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'BHAModel':
        """Load BHA model from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class DrillingParamsModel:
    """
    Model for drilling parameters.
    
    Stores a collection of drilling parameters for a well, including
    weight on bit, RPM, flow rate, standpipe pressure, torque, and ROP.
    """
    
    def __init__(self, well_id: str, unit_system: str = 'metric'):
        """
        Initialize a drilling parameters model.
        
        Args:
            well_id: Well identifier
            unit_system: Unit system ('metric' or 'imperial')
        """
        self.well_id = well_id
        self.unit_system = unit_system
        self.params: List[Dict[str, Any]] = []
        self.creation_date = datetime.datetime.now().isoformat()
    
    def add_params(self, md: float, wob: float, rpm: float, flow_rate: float,
                  spp: float, torque: float, rop: float,
                  additional_params: Optional[Dict[str, Any]] = None) -> None:
        """
        Add drilling parameters at a specific measured depth.
        
        Args:
            md: Measured depth
            wob: Weight on bit
            rpm: Rotations per minute
            flow_rate: Flow rate
            spp: Standpipe pressure
            torque: Torque
            rop: Rate of penetration
            additional_params: Additional parameters
        """
        params = {
            'md': md,
            'wob': wob,
            'rpm': rpm,
            'flow_rate': flow_rate,
            'spp': spp,
            'torque': torque,
            'rop': rop,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        if additional_params:
            params['additional_params'] = additional_params
        
        self.params.append(params)
    
    def get_latest_parameters(self) -> Optional[Dict[str, Any]]:
        """Get the latest drilling parameters."""
        if not self.params:
            return None
        
        # Sort by timestamp and return the latest
        return sorted(self.params, key=lambda p: p['timestamp'])[-1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert drilling parameters model to dictionary."""
        return {
            'well_id': self.well_id,
            'unit_system': self.unit_system,
            'params': self.params,
            'creation_date': self.creation_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DrillingParamsModel':
        """Create drilling parameters model from dictionary."""
        model = cls(
            well_id=data['well_id'],
            unit_system=data.get('unit_system', 'metric')
        )
        model.params = data.get('params', [])
        return model
    
    def save_to_file(self, filepath: str) -> None:
        """Save drilling parameters model to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'DrillingParamsModel':
        """Load drilling parameters model from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
