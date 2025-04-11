"""
Data Management Module for Directional Driller Application

This module implements data management functionality for the directional drilling application,
including project management, data import/export, and database operations.
"""

import os
import json
import sqlite3
import datetime
import shutil
from typing import Dict, List, Optional, Union, Any, Tuple
import pandas as pd
import csv

from data_models import WellModel, SurveyModel, BHAModel, DrillingParamsModel, SurveyPoint


class DataManagementModule:
    """
    Data management module for directional drilling application.
    
    Provides methods for managing projects, importing and exporting data,
    and performing database operations.
    """
    
    def __init__(self, base_dir: str = "projects"):
        """
        Initialize the data management module.
        
        Args:
            base_dir: Base directory for project storage
        """
        self.base_dir = base_dir
        self.current_project = None
        self.current_well = None
        self.current_survey_model = None
        self.current_bha_model = None
        self.current_drilling_params = None
        
        # Create base directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
    
    def create_project(self, project_name: str) -> str:
        """
        Create a new project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to the project directory
        """
        # Create project directory
        project_dir = os.path.join(self.base_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Create subdirectories
        os.makedirs(os.path.join(project_dir, "wells"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "surveys"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "bha"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "drilling_params"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "reports"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "exports"), exist_ok=True)
        
        # Create project metadata
        metadata = {
            "name": project_name,
            "creation_date": datetime.datetime.now().isoformat(),
            "last_modified": datetime.datetime.now().isoformat(),
            "wells": []
        }
        
        # Save metadata
        with open(os.path.join(project_dir, "project.json"), "w") as f:
            json.dump(metadata, f, indent=4)
        
        # Set as current project
        self.current_project = project_dir
        
        return project_dir
    
    def open_project(self, project_name: str) -> str:
        """
        Open an existing project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to the project directory
        """
        # Check if project exists
        project_dir = os.path.join(self.base_dir, project_name)
        if not os.path.exists(project_dir):
            raise FileNotFoundError(f"Project '{project_name}' not found")
        
        # Check if project metadata exists
        metadata_path = os.path.join(project_dir, "project.json")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Project metadata not found for '{project_name}'")
        
        # Load project metadata
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        # Update last modified date
        metadata["last_modified"] = datetime.datetime.now().isoformat()
        
        # Save updated metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)
        
        # Set as current project
        self.current_project = project_dir
        
        # Reset current models
        self.current_well = None
        self.current_survey_model = None
        self.current_bha_model = None
        self.current_drilling_params = None
        
        return project_dir
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all available projects.
        
        Returns:
            List of project metadata dictionaries
        """
        projects = []
        
        # Check if base directory exists
        if not os.path.exists(self.base_dir):
            return projects
        
        # Iterate through directories in base directory
        for item in os.listdir(self.base_dir):
            project_dir = os.path.join(self.base_dir, item)
            if os.path.isdir(project_dir):
                # Check if project metadata exists
                metadata_path = os.path.join(project_dir, "project.json")
                if os.path.exists(metadata_path):
                    # Load project metadata
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                    
                    projects.append(metadata)
        
        return projects
    
    def create_well(self, name: str, operator: str, location: Dict[str, Any] = None,
                   rig_name: str = "", metadata: Dict[str, Any] = None) -> WellModel:
        """
        Create a new well.
        
        Args:
            name: Well name
            operator: Operator name
            location: Location information
            rig_name: Rig name
            metadata: Additional metadata
            
        Returns:
            Well model
        """
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Create well model
        well = WellModel(
            name=name,
            operator=operator,
            location=location or {},
            rig_name=rig_name,
            metadata=metadata or {}
        )
        
        # Save well model
        well_dir = os.path.join(self.current_project, "wells")
        well_path = os.path.join(well_dir, f"{well.well_id}.json")
        well.save_to_file(well_path)
        
        # Update project metadata
        metadata_path = os.path.join(self.current_project, "project.json")
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        # Add well to metadata if not already present
        if well.well_id not in metadata["wells"]:
            metadata["wells"].append(well.well_id)
        
        # Update last modified date
        metadata["last_modified"] = datetime.datetime.now().isoformat()
        
        # Save updated metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)
        
        # Set as current well
        self.current_well = well
        
        return well
    
    def open_well(self, well_id: str) -> WellModel:
        """
        Open an existing well.
        
        Args:
            well_id: Well ID
            
        Returns:
            Well model
        """
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Check if well exists
        well_dir = os.path.join(self.current_project, "wells")
        well_path = os.path.join(well_dir, f"{well_id}.json")
        if not os.path.exists(well_path):
            raise FileNotFoundError(f"Well '{well_id}' not found")
        
        # Load well model
        well = WellModel.load_from_file(well_path)
        
        # Set as current well
        self.current_well = well
        
        return well
    
    def list_wells(self) -> List[WellModel]:
        """
        List all wells in the current project.
        
        Returns:
            List of well models
        """
        wells = []
        
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Check if wells directory exists
        well_dir = os.path.join(self.current_project, "wells")
        if not os.path.exists(well_dir):
            return wells
        
        # Iterate through well files
        for item in os.listdir(well_dir):
            if item.endswith(".json"):
                well_path = os.path.join(well_dir, item)
                well = WellModel.load_from_file(well_path)
                wells.append(well)
        
        return wells
    
    def create_survey_model(self, well_id: str, unit_system: str = "metric") -> SurveyModel:
        """
        Create a new survey model.
        
        Args:
            well_id: Well ID
            unit_system: Unit system ("metric" or "imperial")
            
        Returns:
            Survey model
        """
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Create survey model
        survey_model = SurveyModel(
            well_id=well_id,
            unit_system=unit_system
        )
        
        # Set as current survey model
        self.current_survey_model = survey_model
        
        return survey_model
    
    def save_survey_model(self, survey_model: SurveyModel, name: str = "surveys") -> str:
        """
        Save a survey model.
        
        Args:
            survey_model: Survey model
            name: Name for the survey file
            
        Returns:
            Path to the saved survey file
        """
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Save survey model
        survey_dir = os.path.join(self.current_project, "surveys")
        survey_path = os.path.join(survey_dir, f"{name}_{survey_model.well_id}.json")
        survey_model.save_to_file(survey_path)
        
        return survey_path
    
    def load_survey_model(self, filepath: str) -> SurveyModel:
        """
        Load a survey model.
        
        Args:
            filepath: Path to the survey file
            
        Returns:
            Survey model
        """
        # Check if file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Survey file '{filepath}' not found")
        
        # Load survey model
        survey_model = SurveyModel.load_from_file(filepath)
        
        # Set as current survey model
        self.current_survey_model = survey_model
        
        return survey_model
    
    def list_survey_models(self, well_id: Optional[str] = None) -> List[str]:
        """
        List all survey models in the current project.
        
        Args:
            well_id: Optional well ID to filter by
            
        Returns:
            List of survey file paths
        """
        surveys = []
        
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Check if surveys directory exists
        survey_dir = os.path.join(self.current_project, "surveys")
        if not os.path.exists(survey_dir):
            return surveys
        
        # Iterate through survey files
        for item in os.listdir(survey_dir):
            if item.endswith(".json"):
                # Filter by well ID if provided
                if well_id and well_id not in item:
                    continue
                
                survey_path = os.path.join(survey_dir, item)
                surveys.append(survey_path)
        
        return surveys
    
    def create_bha_model(self, well_id: str, name: str, unit_system: str = "metric") -> BHAModel:
        """
        Create a new BHA model.
        
        Args:
            well_id: Well ID
            name: BHA name
            unit_system: Unit system ("metric" or "imperial")
            
        Returns:
            BHA model
        """
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Create BHA model
        bha_model = BHAModel(
            well_id=well_id,
            name=name,
            unit_system=unit_system
        )
        
        # Set as current BHA model
        self.current_bha_model = bha_model
        
        return bha_model
    
    def save_bha_model(self, bha_model: BHAModel) -> str:
        """
        Save a BHA model.
        
        Args:
            bha_model: BHA model
            
        Returns:
            Path to the saved BHA file
        """
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Save BHA model
        bha_dir = os.path.join(self.current_project, "bha")
        bha_path = os.path.join(bha_dir, f"{bha_model.bha_id}.json")
        bha_model.save_to_file(bha_path)
        
        return bha_path
    
    def load_bha_model(self, filepath: str) -> BHAModel:
        """
        Load a BHA model.
        
        Args:
            filepath: Path to the BHA file
            
        Returns:
            BHA model
        """
        # Check if file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"BHA file '{filepath}' not found")
        
        # Load BHA model
        bha_model = BHAModel.load_from_file(filepath)
        
        # Set as current BHA model
        self.current_bha_model = bha_model
        
        return bha_model
    
    def list_bha_models(self, well_id: Optional[str] = None) -> List[str]:
        """
        List all BHA models in the current project.
        
        Args:
            well_id: Optional well ID to filter by
            
        Returns:
            List of BHA file paths
        """
        bhas = []
        
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Check if BHA directory exists
        bha_dir = os.path.join(self.current_project, "bha")
        if not os.path.exists(bha_dir):
            return bhas
        
        # Iterate through BHA files
        for item in os.listdir(bha_dir):
            if item.endswith(".json"):
                bha_path = os.path.join(bha_dir, item)
                
                # Filter by well ID if provided
                if well_id:
                    try:
                        bha_model = BHAModel.load_from_file(bha_path)
                        if bha_model.well_id != well_id:
                            continue
                    except:
                        continue
                
                bhas.append(bha_path)
        
        return bhas
    
    def create_drilling_params_model(self, well_id: str, unit_system: str = "metric") -> DrillingParamsModel:
        """
        Create a new drilling parameters model.
        
        Args:
            well_id: Well ID
            unit_system: Unit system ("metric" or "imperial")
            
        Returns:
            Drilling parameters model
        """
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Create drilling parameters model
        drilling_params = DrillingParamsModel(
            well_id=well_id,
            unit_system=unit_system
        )
        
        # Set as current drilling parameters model
        self.current_drilling_params = drilling_params
        
        return drilling_params
    
    def save_drilling_params_model(self, drilling_params: DrillingParamsModel) -> str:
        """
        Save a drilling parameters model.
        
        Args:
            drilling_params: Drilling parameters model
            
        Returns:
            Path to the saved drilling parameters file
        """
        # Check if project is open
        if not self.current_project:
            raise ValueError("No project is currently open")
        
        # Save drilling parameters model
        params_dir = os.path.join(self.current_project, "drilling_params")
        params_path = os.path.join(params_dir, f"params_{drilling_params.well_id}.json")
        drilling_params.save_to_file(params_path)
        
        return params_path
    
    def load_drilling_params_model(self, filepath: str) -> DrillingParamsModel:
        """
        Load a drilling parameters model.
        
        Args:
            filepath: Path to the drilling parameters file
            
        Returns:
            Drilling parameters model
        """
        # Check if file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Drilling parameters file '{filepath}' not found")
        
        # Load drilling parameters model
        drilling_params = DrillingParamsModel.load_from_file(filepath)
        
        # Set as current drilling parameters model
        self.current_drilling_params = drilling_params
        
        return drilling_params
    
    def import_survey_from_csv(self, filepath: str, well_id: str, 
                              unit_system: str = "metric") -> SurveyModel:
        """
        Import survey data from a CSV file.
        
        Args:
            filepath: Path to the CSV file
            well_id: Well ID
            unit_system: Unit system ("metric" or "imperial")
            
        Returns:
            Survey model
        """
        # Check if file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV file '{filepath}' not found")
        
        # Create survey model
        survey_model = SurveyModel(
            well_id=well_id,
            unit_system=unit_system
        )
        
        # Read CSV file
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check for required fields
                if 'md' not in row or 'inc' not in row or 'azi' not in row:
                    continue
                
                # Create survey point
                survey = SurveyPoint(
                    md=float(row['md']),
                    inc=float(row['inc']),
                    azi=float(row['azi']),
                    tvd=float(row.get('tvd', 0.0)),
                    northing=float(row.get('northing', 0.0)),
                    easting=float(row.get('easting', 0.0)),
                    dogleg=float(row.get('dogleg', 0.0)),
                    dls=float(row.get('dls', 0.0))
                )
                
                # Add survey point to model
                survey_model.add_survey(survey)
        
        # Set as current survey model
        self.current_survey_model = survey_model
        
        return survey_model
    
    def export_survey_to_csv(self, survey_model: SurveyModel, filepath: str) -> str:
        """
        Export survey data to a CSV file.
        
        Args:
            survey_model: Survey model
            filepath: Path to the CSV file
            
        Returns:
            Path to the exported CSV file
        """
        # Check if survey model has data
        if not survey_model.surveys:
            raise ValueError("Survey model has no data to export")
        
        # Create CSV file
        with open(filepath, 'w', newline='') as f:
            fieldnames = ['md', 'inc', 'azi', 'tvd', 'northing', 'easting', 'dogleg', 'dls']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write survey data
            for survey in survey_model.surveys:
                writer.writerow({
                    'md': survey.md,
                    'inc': survey.inc,
                    'azi': survey.azi,
                    'tvd': survey.tvd,
                    'northing': survey.northing,
                    'easting': survey.easting,
                    'dogleg': survey.dogleg,
                    'dls': survey.dls
                })
        
        return filepath
    
    def backup_project(self, project_name: str, backup_dir: str) -> str:
        """
        Create a backup of a project.
        
        Args:
            project_name: Name of the project
            backup_dir: Directory to store the backup
            
        Returns:
            Path to the backup file
        """
        # Check if project exists
        project_dir = os.path.join(self.base_dir, project_name)
        if not os.path.exists(project_dir):
            raise FileNotFoundError(f"Project '{project_name}' not found")
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{project_name}_backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create zip archive
        shutil.make_archive(
            os.path.splitext(backup_path)[0],  # Remove .zip extension
            'zip',
            self.base_dir,
            project_name
        )
        
        return backup_path
    
    def restore_project_from_backup(self, backup_path: str) -> str:
        """
        Restore a project from a backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            Path to the restored project directory
        """
        # Check if backup file exists
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file '{backup_path}' not found")
        
        # Create temporary directory for extraction
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        # Extract backup
        import zipfile
        with zipfile.ZipFile(backup_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find project directory in extracted files
        extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
        if not extracted_dirs:
            raise ValueError("No project found in backup file")
        
        project_name = extracted_dirs[0]
        extracted_project_dir = os.path.join(temp_dir, project_name)
        
        # Check if project already exists
        target_project_dir = os.path.join(self.base_dir, project_name)
        if os.path.exists(target_project_dir):
            # Create a backup of the existing project
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.base_dir, f"{project_name}_old_{timestamp}")
            shutil.move(target_project_dir, backup_dir)
        
        # Copy extracted project to projects directory
        shutil.copytree(extracted_project_dir, target_project_dir)
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return target_project_dir
