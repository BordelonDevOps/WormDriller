"""
Integration utilities for connecting the desktop application with the FastAPI service.

This module provides utilities and helpers for seamless integration between
the PyQt6 desktop application and the FastAPI service.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
import time

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication

logger = logging.getLogger(__name__)


class APIConnectionManager(QObject):
    """Manages API connection and health monitoring."""
    
    connection_status_changed = pyqtSignal(bool)  # True if connected, False if disconnected
    api_error = pyqtSignal(str)  # Error message
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        """Initialize connection manager."""
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.is_connected = False
        self.last_check = None
        
        # Setup health check timer
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.check_health)
        self.health_timer.start(30000)  # Check every 30 seconds
        
        # Initial health check
        self.check_health()
    
    def check_health(self):
        """Check API health status."""
        self.health_worker = HealthCheckWorker(self.base_url)
        self.health_worker.health_result.connect(self.on_health_result)
        self.health_worker.start()
    
    def on_health_result(self, is_healthy: bool, response_time: float = None):
        """Handle health check result."""
        was_connected = self.is_connected
        self.is_connected = is_healthy
        self.last_check = datetime.now()
        
        if was_connected != is_healthy:
            self.connection_status_changed.emit(is_healthy)
            
            if is_healthy:
                logger.info(f"API connection established (response time: {response_time:.3f}s)")
            else:
                logger.warning("API connection lost")
                self.api_error.emit("Lost connection to API service")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            "base_url": self.base_url,
            "is_connected": self.is_connected,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "has_api_key": bool(self.api_key)
        }


class HealthCheckWorker(QThread):
    """Worker thread for health checks."""
    
    health_result = pyqtSignal(bool, float)  # is_healthy, response_time
    
    def __init__(self, base_url: str):
        """Initialize health check worker."""
        super().__init__()
        self.base_url = base_url
    
    def run(self):
        """Run health check."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            start_time = time.time()
            result = loop.run_until_complete(self._check_health())
            response_time = time.time() - start_time
            
            self.health_result.emit(result, response_time)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.health_result.emit(False, 0.0)
        finally:
            loop.close()
    
    async def _check_health(self) -> bool:
        """Perform async health check."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False


class ProgressDialog(QProgressDialog):
    """Enhanced progress dialog for API operations."""
    
    def __init__(self, title: str, message: str, parent=None):
        """Initialize progress dialog."""
        super().__init__(message, "Cancel", 0, 0, parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumDuration(500)  # Show after 500ms
        
        # Style the dialog
        self.setStyleSheet("""
            QProgressDialog {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)


class APIOperationManager:
    """Manages API operations with progress tracking and error handling."""
    
    def __init__(self, connection_manager: APIConnectionManager, parent_widget=None):
        """Initialize operation manager."""
        self.connection_manager = connection_manager
        self.parent_widget = parent_widget
        self.active_operations = {}
    
    def execute_operation(self, 
                         operation_name: str,
                         operation_func: Callable,
                         success_callback: Callable = None,
                         error_callback: Callable = None,
                         show_progress: bool = True,
                         progress_message: str = None) -> str:
        """
        Execute an API operation with progress tracking.
        
        Returns operation ID for tracking.
        """
        if not self.connection_manager.is_connected:
            error_msg = "No connection to API service"
            if error_callback:
                error_callback(error_msg)
            else:
                QMessageBox.critical(self.parent_widget, "Connection Error", error_msg)
            return None
        
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        # Create progress dialog if requested
        progress_dialog = None
        if show_progress:
            message = progress_message or f"Executing {operation_name}..."
            progress_dialog = ProgressDialog(operation_name.title(), message, self.parent_widget)
            progress_dialog.show()
        
        # Create and start worker
        worker = APIOperationWorker(
            operation_id=operation_id,
            operation_func=operation_func,
            api_client=APIClient(
                self.connection_manager.base_url,
                self.connection_manager.api_key
            )
        )
        
        # Connect signals
        worker.operation_finished.connect(
            lambda op_id, result: self._on_operation_finished(
                op_id, result, success_callback, progress_dialog
            )
        )
        worker.operation_error.connect(
            lambda op_id, error: self._on_operation_error(
                op_id, error, error_callback, progress_dialog
            )
        )
        
        # Track operation
        self.active_operations[operation_id] = {
            "worker": worker,
            "progress_dialog": progress_dialog,
            "start_time": time.time()
        }
        
        # Start operation
        worker.start()
        
        return operation_id
    
    def _on_operation_finished(self, operation_id: str, result: Any, 
                              success_callback: Callable, progress_dialog: ProgressDialog):
        """Handle operation completion."""
        if progress_dialog:
            progress_dialog.close()
        
        operation = self.active_operations.pop(operation_id, None)
        if operation:
            duration = time.time() - operation["start_time"]
            logger.info(f"Operation {operation_id} completed in {duration:.3f}s")
        
        if success_callback:
            success_callback(result)
    
    def _on_operation_error(self, operation_id: str, error: str,
                           error_callback: Callable, progress_dialog: ProgressDialog):
        """Handle operation error."""
        if progress_dialog:
            progress_dialog.close()
        
        operation = self.active_operations.pop(operation_id, None)
        if operation:
            duration = time.time() - operation["start_time"]
            logger.error(f"Operation {operation_id} failed after {duration:.3f}s: {error}")
        
        if error_callback:
            error_callback(error)
        else:
            QMessageBox.critical(self.parent_widget, "Operation Error", f"Operation failed: {error}")


class APIOperationWorker(QThread):
    """Worker thread for API operations."""
    
    operation_finished = pyqtSignal(str, object)  # operation_id, result
    operation_error = pyqtSignal(str, str)  # operation_id, error_message
    
    def __init__(self, operation_id: str, operation_func: Callable, api_client):
        """Initialize operation worker."""
        super().__init__()
        self.operation_id = operation_id
        self.operation_func = operation_func
        self.api_client = api_client
    
    def run(self):
        """Run the operation."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self.operation_func(self.api_client))
            self.operation_finished.emit(self.operation_id, result)
            
        except Exception as e:
            self.operation_error.emit(self.operation_id, str(e))
        finally:
            loop.close()


class APIClient:
    """Enhanced API client with comprehensive error handling."""
    
    def __init__(self, base_url: str, api_key: str = None):
        """Initialize API client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=self._get_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    async def calculate_wellpath(self, survey_data: List[Dict], method: str = "minimum_curvature",
                               unit_system: str = "imperial", reference_azimuth: float = 0.0) -> Dict:
        """Calculate wellpath using the enhanced API."""
        url = f"{self.base_url}/api/v1/calculations/wellpath"
        payload = {
            "survey_points": survey_data,
            "method": method,
            "unit_system": unit_system,
            "reference_azimuth": reference_azimuth
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")
    
    async def calculate_dogleg_severity(self, inc1: float, azi1: float, inc2: float, azi2: float,
                                      md_diff: float, unit_system: str = "imperial") -> Dict:
        """Calculate dogleg severity."""
        url = f"{self.base_url}/api/v1/calculations/dogleg-severity"
        payload = {
            "inc1": inc1,
            "azi1": azi1,
            "inc2": inc2,
            "azi2": azi2,
            "md_diff": md_diff,
            "unit_system": unit_system
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")
    
    async def project_wellpath(self, start_point: Dict, build_rate: float, turn_rate: float,
                              step_size: float, num_steps: int, unit_system: str = "imperial") -> Dict:
        """Project wellpath ahead."""
        url = f"{self.base_url}/api/v1/calculations/project-wellpath"
        payload = {
            "start_point": start_point,
            "build_rate": build_rate,
            "turn_rate": turn_rate,
            "step_size": step_size,
            "num_steps": num_steps,
            "unit_system": unit_system
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")
    
    async def validate_survey(self, survey_data: List[Dict]) -> Dict:
        """Validate survey data."""
        url = f"{self.base_url}/api/v1/calculations/validate-survey"
        payload = {"survey_points": survey_data}
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")
    
    async def predict_rop(self, drilling_params: Dict) -> Dict:
        """Predict ROP using ML model."""
        url = f"{self.base_url}/api/v1/predict-rop"
        
        async with self.session.post(url, json=drilling_params) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")
    
    async def upload_las_file(self, file_content: bytes, filename: str) -> Dict:
        """Upload and process LAS file."""
        url = f"{self.base_url}/api/v1/upload-las"
        
        data = aiohttp.FormData()
        data.add_field('file', file_content, filename=filename, content_type='application/octet-stream')
        
        async with self.session.post(url, data=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")
    
    async def get_calculation_methods(self) -> Dict:
        """Get available calculation methods."""
        url = f"{self.base_url}/api/v1/calculations/methods"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")


class DataSynchronizer:
    """Synchronizes data between desktop application and API service."""
    
    def __init__(self, api_client: APIClient):
        """Initialize data synchronizer."""
        self.api_client = api_client
        self.local_cache = {}
        self.sync_timestamps = {}
    
    async def sync_project_data(self, project_data: Dict) -> Dict:
        """Synchronize project data with the API."""
        # This would implement project data synchronization
        # For now, return the data as-is
        return project_data
    
    async def sync_well_data(self, well_data: Dict) -> Dict:
        """Synchronize well data with the API."""
        # This would implement well data synchronization
        return well_data
    
    async def sync_survey_data(self, survey_data: List[Dict]) -> List[Dict]:
        """Synchronize survey data with the API."""
        # This would implement survey data synchronization
        return survey_data
    
    def cache_data(self, key: str, data: Any):
        """Cache data locally."""
        self.local_cache[key] = data
        self.sync_timestamps[key] = datetime.now()
    
    def get_cached_data(self, key: str) -> Any:
        """Get cached data."""
        return self.local_cache.get(key)
    
    def is_cache_valid(self, key: str, max_age_seconds: int = 300) -> bool:
        """Check if cached data is still valid."""
        if key not in self.sync_timestamps:
            return False
        
        age = (datetime.now() - self.sync_timestamps[key]).total_seconds()
        return age < max_age_seconds

