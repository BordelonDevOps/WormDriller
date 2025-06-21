"""
Enhanced Desktop Application for WormDriller Hybrid Architecture

This module implements the main desktop application using PyQt6 that provides
the complete user interface and workflow management while integrating with
the FastAPI service for calculations and ML operations.
"""

import sys
import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import traceback

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox, QAction, QMenu, QToolBar,
    QStatusBar, QSplitter, QFrame, QComboBox, QLineEdit, QFormLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QProgressBar, QTreeWidget, QTreeWidgetItem, QTabBar, QScrollArea,
    QGridLayout, QSlider, QDial, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import (
    Qt, QSize, QThread, pyqtSignal, QTimer, QSettings, QStandardPaths,
    QUrl, QPropertyAnimation, QEasingCurve, QRect
)
from PyQt6.QtGui import (
    QIcon, QFont, QPixmap, QPainter, QPen, QBrush, QColor, QAction,
    QKeySequence, QShortcut, QPalette
)

# Matplotlib integration
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# Data models
from enhanced_data_models import (
    WellModel, SurveyModel, SurveyPointModel, BHAModel, BHAComponent,
    DrillingParameters, ProjectModel, UnitSystem, WellType, ComponentType
)


class APIClient:
    """Client for communicating with the FastAPI service."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        """Initialize API client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
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
        """Calculate wellpath using the API."""
        url = f"{self.base_url}/api/v1/calculations/wellpath"
        payload = {
            "survey_points": survey_data,
            "method": method,
            "unit_system": unit_system,
            "reference_azimuth": reference_azimuth
        }
        
        async with self.session.post(url, json=payload, headers=self._get_headers()) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")
    
    async def predict_rop(self, drilling_params: Dict) -> Dict:
        """Predict ROP using the ML model."""
        url = f"{self.base_url}/api/v1/predict-rop"
        
        async with self.session.post(url, json=drilling_params, headers=self._get_headers()) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")
    
    async def validate_survey(self, survey_data: List[Dict]) -> Dict:
        """Validate survey data."""
        url = f"{self.base_url}/api/v1/calculations/validate-survey"
        payload = {"survey_points": survey_data}
        
        async with self.session.post(url, json=payload, headers=self._get_headers()) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")


class CalculationWorker(QThread):
    """Worker thread for API calculations."""
    
    calculation_finished = pyqtSignal(dict)
    calculation_error = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    
    def __init__(self, api_client: APIClient, operation: str, **kwargs):
        """Initialize calculation worker."""
        super().__init__()
        self.api_client = api_client
        self.operation = operation
        self.kwargs = kwargs
        
    def run(self):
        """Run the calculation in a separate thread."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async operation
            result = loop.run_until_complete(self._execute_operation())
            
            self.calculation_finished.emit(result)
            
        except Exception as e:
            self.calculation_error.emit(str(e))
        finally:
            loop.close()
    
    async def _execute_operation(self):
        """Execute the specific operation."""
        async with self.api_client:
            if self.operation == "calculate_wellpath":
                return await self.api_client.calculate_wellpath(**self.kwargs)
            elif self.operation == "predict_rop":
                return await self.api_client.predict_rop(**self.kwargs)
            elif self.operation == "validate_survey":
                return await self.api_client.validate_survey(**self.kwargs)
            else:
                raise ValueError(f"Unknown operation: {self.operation}")


class ModernPlotWidget(QWidget):
    """Modern plotting widget with enhanced visualization capabilities."""
    
    def __init__(self, parent=None):
        """Initialize plot widget."""
        super().__init__(parent)
        self.setup_ui()
        self.current_data = None
        
    def setup_ui(self):
        """Setup the plot widget UI."""
        layout = QVBoxLayout(self)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Add widgets to layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Set modern styling
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
        """)
    
    def plot_trajectory_2d(self, wellpath_data: List[Dict], view_type: str = "plan"):
        """Plot 2D trajectory."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not wellpath_data:
            ax.text(0.5, 0.5, 'No data to display', ha='center', va='center', transform=ax.transAxes)
            self.canvas.draw()
            return
        
        # Extract coordinates
        md = [point['md'] for point in wellpath_data]
        tvd = [point['tvd'] for point in wellpath_data]
        northing = [point['northing'] for point in wellpath_data]
        easting = [point['easting'] for point in wellpath_data]
        
        if view_type == "plan":
            ax.plot(easting, northing, 'b-', linewidth=2, marker='o', markersize=4)
            ax.set_xlabel('Easting (ft)')
            ax.set_ylabel('Northing (ft)')
            ax.set_title('Wellbore Trajectory - Plan View')
            ax.set_aspect('equal')
        elif view_type == "vertical":
            ax.plot(md, tvd, 'r-', linewidth=2, marker='o', markersize=4)
            ax.set_xlabel('Measured Depth (ft)')
            ax.set_ylabel('True Vertical Depth (ft)')
            ax.set_title('Wellbore Trajectory - Vertical Section')
            ax.invert_yaxis()
        
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self.canvas.draw()
        
        self.current_data = wellpath_data
    
    def plot_trajectory_3d(self, wellpath_data: List[Dict]):
        """Plot 3D trajectory."""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        
        if not wellpath_data:
            ax.text(0.5, 0.5, 0.5, 'No data to display', ha='center', va='center')
            self.canvas.draw()
            return
        
        # Extract coordinates
        northing = [point['northing'] for point in wellpath_data]
        easting = [point['easting'] for point in wellpath_data]
        tvd = [point['tvd'] for point in wellpath_data]
        
        ax.plot(easting, northing, tvd, 'b-', linewidth=2, marker='o', markersize=4)
        ax.set_xlabel('Easting (ft)')
        ax.set_ylabel('Northing (ft)')
        ax.set_zlabel('TVD (ft)')
        ax.set_title('Wellbore Trajectory - 3D View')
        ax.invert_zaxis()
        
        self.figure.tight_layout()
        self.canvas.draw()
        
        self.current_data = wellpath_data
    
    def plot_dogleg_severity(self, wellpath_data: List[Dict]):
        """Plot dogleg severity."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not wellpath_data:
            ax.text(0.5, 0.5, 'No data to display', ha='center', va='center', transform=ax.transAxes)
            self.canvas.draw()
            return
        
        # Extract data
        md = [point['md'] for point in wellpath_data if point.get('dls', 0) > 0]
        dls = [point['dls'] for point in wellpath_data if point.get('dls', 0) > 0]
        
        if md and dls:
            ax.plot(md, dls, 'orange', linewidth=2, marker='o', markersize=4)
            ax.axhline(y=3.0, color='red', linestyle='--', alpha=0.7, label='High DLS (3°/100ft)')
            ax.set_xlabel('Measured Depth (ft)')
            ax.set_ylabel('Dogleg Severity (°/100ft)')
            ax.set_title('Dogleg Severity vs Measured Depth')
            ax.grid(True, alpha=0.3)
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'No dogleg data available', ha='center', va='center', transform=ax.transAxes)
        
        self.figure.tight_layout()
        self.canvas.draw()


class SurveyDataWidget(QWidget):
    """Widget for managing survey data."""
    
    data_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize survey data widget."""
        super().__init__(parent)
        self.survey_data = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the survey data UI."""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.add_point_btn = QPushButton("Add Point")
        self.add_point_btn.clicked.connect(self.add_survey_point)
        
        self.delete_point_btn = QPushButton("Delete Point")
        self.delete_point_btn.clicked.connect(self.delete_survey_point)
        
        self.import_btn = QPushButton("Import LAS")
        self.import_btn.clicked.connect(self.import_las_file)
        
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.clicked.connect(self.export_csv)
        
        toolbar_layout.addWidget(self.add_point_btn)
        toolbar_layout.addWidget(self.delete_point_btn)
        toolbar_layout.addWidget(self.import_btn)
        toolbar_layout.addWidget(self.export_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Survey table
        self.survey_table = QTableWidget()
        self.survey_table.setColumnCount(8)
        self.survey_table.setHorizontalHeaderLabels([
            "MD", "Inc", "Azi", "TVD", "Northing", "Easting", "Dogleg", "DLS"
        ])
        
        # Make table editable for MD, Inc, Azi columns
        self.survey_table.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.survey_table)
        
        # Status label
        self.status_label = QLabel("No survey data")
        layout.addWidget(self.status_label)
        
    def add_survey_point(self):
        """Add a new survey point."""
        row = self.survey_table.rowCount()
        self.survey_table.insertRow(row)
        
        # Set default values
        md = row * 100.0 if row > 0 else 0.0
        self.survey_table.setItem(row, 0, QTableWidgetItem(str(md)))
        self.survey_table.setItem(row, 1, QTableWidgetItem("0.0"))
        self.survey_table.setItem(row, 2, QTableWidgetItem("0.0"))
        
        # Set calculated columns as read-only
        for col in range(3, 8):
            item = QTableWidgetItem("0.0")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.survey_table.setItem(row, col, item)
        
        self.update_status()
        
    def delete_survey_point(self):
        """Delete selected survey point."""
        current_row = self.survey_table.currentRow()
        if current_row >= 0:
            self.survey_table.removeRow(current_row)
            self.update_status()
            self.data_changed.emit()
    
    def import_las_file(self):
        """Import survey data from LAS file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import LAS File", "", "LAS Files (*.las);;All Files (*)"
        )
        
        if file_path:
            try:
                # This would integrate with the LAS processor
                QMessageBox.information(self, "Import", f"LAS import functionality would be implemented here for: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import LAS file: {str(e)}")
    
    def export_csv(self):
        """Export survey data to CSV."""
        if self.survey_table.rowCount() == 0:
            QMessageBox.warning(self, "Export", "No data to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    headers = []
                    for col in range(self.survey_table.columnCount()):
                        headers.append(self.survey_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(self.survey_table.rowCount()):
                        row_data = []
                        for col in range(self.survey_table.columnCount()):
                            item = self.survey_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "Export", f"Data exported to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def on_item_changed(self, item):
        """Handle item changes in the table."""
        if item.column() < 3:  # Only for editable columns (MD, Inc, Azi)
            self.data_changed.emit()
    
    def get_survey_data(self) -> List[Dict]:
        """Get survey data from the table."""
        data = []
        for row in range(self.survey_table.rowCount()):
            try:
                md_item = self.survey_table.item(row, 0)
                inc_item = self.survey_table.item(row, 1)
                azi_item = self.survey_table.item(row, 2)
                
                if md_item and inc_item and azi_item:
                    point = {
                        "md": float(md_item.text()),
                        "inc": float(inc_item.text()),
                        "azi": float(azi_item.text())
                    }
                    data.append(point)
            except ValueError:
                continue  # Skip invalid rows
        
        return data
    
    def set_calculated_data(self, wellpath_data: List[Dict]):
        """Set calculated data in the table."""
        for i, point in enumerate(wellpath_data):
            if i < self.survey_table.rowCount():
                # Update calculated columns
                self.survey_table.item(i, 3).setText(f"{point.get('tvd', 0):.2f}")
                self.survey_table.item(i, 4).setText(f"{point.get('northing', 0):.2f}")
                self.survey_table.item(i, 5).setText(f"{point.get('easting', 0):.2f}")
                self.survey_table.item(i, 6).setText(f"{point.get('dogleg', 0):.2f}")
                self.survey_table.item(i, 7).setText(f"{point.get('dls', 0):.2f}")
    
    def update_status(self):
        """Update status label."""
        count = self.survey_table.rowCount()
        self.status_label.setText(f"Survey points: {count}")


class WellInfoWidget(QWidget):
    """Widget for managing well information."""
    
    def __init__(self, parent=None):
        """Initialize well info widget."""
        super().__init__(parent)
        self.well_data = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the well info UI."""
        layout = QFormLayout(self)
        
        # Well basic information
        self.well_name_edit = QLineEdit()
        self.operator_edit = QLineEdit()
        self.field_edit = QLineEdit()
        self.rig_name_edit = QLineEdit()
        
        # Well type and status
        self.well_type_combo = QComboBox()
        self.well_type_combo.addItems(["vertical", "directional", "horizontal", "multilateral"])
        
        self.well_status_combo = QComboBox()
        self.well_status_combo.addItems(["planned", "drilling", "completed", "suspended", "abandoned"])
        
        # Unit system
        self.unit_system_combo = QComboBox()
        self.unit_system_combo.addItems(["imperial", "metric"])
        
        # Target depth
        self.target_depth_spin = QDoubleSpinBox()
        self.target_depth_spin.setRange(0, 50000)
        self.target_depth_spin.setSuffix(" ft")
        
        # Location
        self.latitude_spin = QDoubleSpinBox()
        self.latitude_spin.setRange(-90, 90)
        self.latitude_spin.setDecimals(6)
        
        self.longitude_spin = QDoubleSpinBox()
        self.longitude_spin.setRange(-180, 180)
        self.longitude_spin.setDecimals(6)
        
        # Add fields to form
        layout.addRow("Well Name:", self.well_name_edit)
        layout.addRow("Operator:", self.operator_edit)
        layout.addRow("Field:", self.field_edit)
        layout.addRow("Rig Name:", self.rig_name_edit)
        layout.addRow("Well Type:", self.well_type_combo)
        layout.addRow("Status:", self.well_status_combo)
        layout.addRow("Unit System:", self.unit_system_combo)
        layout.addRow("Target Depth:", self.target_depth_spin)
        layout.addRow("Latitude:", self.latitude_spin)
        layout.addRow("Longitude:", self.longitude_spin)
        
    def get_well_data(self) -> Dict:
        """Get well data from the form."""
        return {
            "name": self.well_name_edit.text(),
            "operator": self.operator_edit.text(),
            "field": self.field_edit.text(),
            "rig_name": self.rig_name_edit.text(),
            "well_type": self.well_type_combo.currentText(),
            "status": self.well_status_combo.currentText(),
            "unit_system": self.unit_system_combo.currentText(),
            "target_depth": self.target_depth_spin.value(),
            "location": {
                "latitude": self.latitude_spin.value(),
                "longitude": self.longitude_spin.value()
            }
        }
    
    def set_well_data(self, well_data: Dict):
        """Set well data in the form."""
        self.well_data = well_data
        
        self.well_name_edit.setText(well_data.get("name", ""))
        self.operator_edit.setText(well_data.get("operator", ""))
        self.field_edit.setText(well_data.get("field", ""))
        self.rig_name_edit.setText(well_data.get("rig_name", ""))
        
        well_type = well_data.get("well_type", "directional")
        index = self.well_type_combo.findText(well_type)
        if index >= 0:
            self.well_type_combo.setCurrentIndex(index)
        
        status = well_data.get("status", "planned")
        index = self.well_status_combo.findText(status)
        if index >= 0:
            self.well_status_combo.setCurrentIndex(index)
        
        unit_system = well_data.get("unit_system", "imperial")
        index = self.unit_system_combo.findText(unit_system)
        if index >= 0:
            self.unit_system_combo.setCurrentIndex(index)
        
        self.target_depth_spin.setValue(well_data.get("target_depth", 0))
        
        location = well_data.get("location", {})
        self.latitude_spin.setValue(location.get("latitude", 0))
        self.longitude_spin.setValue(location.get("longitude", 0))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.api_client = APIClient()
        self.current_project = None
        self.current_well = None
        self.settings = QSettings("WormDriller", "HybridApp")
        
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("WormDriller - Hybrid Desktop Application")
        self.setMinimumSize(1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Well info and controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Main work area
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 1100])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Apply modern styling
        self.apply_modern_styling()
        
    def create_left_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Well information group
        well_group = QGroupBox("Well Information")
        well_layout = QVBoxLayout(well_group)
        
        self.well_info_widget = WellInfoWidget()
        well_layout.addWidget(self.well_info_widget)
        
        layout.addWidget(well_group)
        
        # Calculation controls group
        calc_group = QGroupBox("Calculations")
        calc_layout = QVBoxLayout(calc_group)
        
        # Method selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "minimum_curvature", "radius_of_curvature", 
            "tangential", "balanced_tangential"
        ])
        method_layout.addWidget(self.method_combo)
        calc_layout.addLayout(method_layout)
        
        # Calculate button
        self.calculate_btn = QPushButton("Calculate Wellpath")
        self.calculate_btn.clicked.connect(self.calculate_wellpath)
        calc_layout.addWidget(self.calculate_btn)
        
        # Validate button
        self.validate_btn = QPushButton("Validate Survey")
        self.validate_btn.clicked.connect(self.validate_survey)
        calc_layout.addWidget(self.validate_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        calc_layout.addWidget(self.progress_bar)
        
        layout.addWidget(calc_group)
        
        # ROP Prediction group
        rop_group = QGroupBox("ROP Prediction")
        rop_layout = QVBoxLayout(rop_group)
        
        self.predict_rop_btn = QPushButton("Predict ROP")
        self.predict_rop_btn.clicked.connect(self.predict_rop)
        rop_layout.addWidget(self.predict_rop_btn)
        
        layout.addWidget(rop_group)
        
        layout.addStretch()
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        """Create the right main work panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create tab widget for main content
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Survey data tab
        self.survey_widget = SurveyDataWidget()
        self.survey_widget.data_changed.connect(self.on_survey_data_changed)
        self.tab_widget.addTab(self.survey_widget, "Survey Data")
        
        # 2D Visualization tab
        self.plot_2d_widget = ModernPlotWidget()
        self.tab_widget.addTab(self.plot_2d_widget, "2D Visualization")
        
        # 3D Visualization tab
        self.plot_3d_widget = ModernPlotWidget()
        self.tab_widget.addTab(self.plot_3d_widget, "3D Visualization")
        
        # Dogleg Severity tab
        self.plot_dls_widget = ModernPlotWidget()
        self.tab_widget.addTab(self.plot_dls_widget, "Dogleg Severity")
        
        return panel
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Project", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create the application toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        
        # Add actions to toolbar
        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_project)
        toolbar.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_project)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        calc_action = QAction("Calculate", self)
        calc_action.triggered.connect(self.calculate_wellpath)
        toolbar.addAction(calc_action)
    
    def apply_modern_styling(self):
        """Apply modern styling to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
            }
            
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
    
    def setup_connections(self):
        """Setup signal connections."""
        pass
    
    def load_settings(self):
        """Load application settings."""
        # Restore window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Restore API settings
        api_url = self.settings.value("api_url", "http://localhost:8000")
        api_key = self.settings.value("api_key", "")
        
        self.api_client = APIClient(api_url, api_key)
    
    def save_settings(self):
        """Save application settings."""
        self.settings.setValue("geometry", self.saveGeometry())
    
    def closeEvent(self, event):
        """Handle application close event."""
        self.save_settings()
        event.accept()
    
    def new_project(self):
        """Create a new project."""
        # Clear current data
        self.current_project = None
        self.current_well = None
        
        # Reset UI
        self.well_info_widget.set_well_data({})
        self.survey_widget.survey_table.setRowCount(0)
        
        self.status_bar.showMessage("New project created")
    
    def open_project(self):
        """Open an existing project."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    project_data = json.load(f)
                
                self.current_project = project_data
                
                # Load well data if available
                if "wells" in project_data and project_data["wells"]:
                    well_data = project_data["wells"][0]  # Load first well
                    self.well_info_widget.set_well_data(well_data)
                    
                    # Load survey data if available
                    if "survey_data" in well_data:
                        self.load_survey_data(well_data["survey_data"])
                
                self.status_bar.showMessage(f"Project loaded: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load project: {str(e)}")
    
    def save_project(self):
        """Save the current project."""
        if not self.current_project:
            self.current_project = {"wells": []}
        
        # Get current well data
        well_data = self.well_info_widget.get_well_data()
        well_data["survey_data"] = self.survey_widget.get_survey_data()
        
        # Update project
        if not self.current_project.get("wells"):
            self.current_project["wells"] = [well_data]
        else:
            self.current_project["wells"][0] = well_data
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.current_project, f, indent=2, default=str)
                
                self.status_bar.showMessage(f"Project saved: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save project: {str(e)}")
    
    def load_survey_data(self, survey_data: List[Dict]):
        """Load survey data into the table."""
        self.survey_widget.survey_table.setRowCount(len(survey_data))
        
        for i, point in enumerate(survey_data):
            self.survey_widget.survey_table.setItem(i, 0, QTableWidgetItem(str(point.get("md", 0))))
            self.survey_widget.survey_table.setItem(i, 1, QTableWidgetItem(str(point.get("inc", 0))))
            self.survey_widget.survey_table.setItem(i, 2, QTableWidgetItem(str(point.get("azi", 0))))
            
            # Set calculated columns as read-only
            for col in range(3, 8):
                item = QTableWidgetItem("0.0")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.survey_widget.survey_table.setItem(i, col, item)
        
        self.survey_widget.update_status()
    
    def on_survey_data_changed(self):
        """Handle survey data changes."""
        # Clear calculated data when survey data changes
        for row in range(self.survey_widget.survey_table.rowCount()):
            for col in range(3, 8):
                item = self.survey_widget.survey_table.item(row, col)
                if item:
                    item.setText("0.0")
    
    def calculate_wellpath(self):
        """Calculate wellpath using the API."""
        survey_data = self.survey_widget.get_survey_data()
        
        if len(survey_data) < 2:
            QMessageBox.warning(self, "Warning", "At least 2 survey points are required")
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.calculate_btn.setEnabled(False)
        
        # Start calculation in worker thread
        self.calc_worker = CalculationWorker(
            self.api_client,
            "calculate_wellpath",
            survey_data=survey_data,
            method=self.method_combo.currentText(),
            unit_system=self.well_info_widget.unit_system_combo.currentText()
        )
        
        self.calc_worker.calculation_finished.connect(self.on_calculation_finished)
        self.calc_worker.calculation_error.connect(self.on_calculation_error)
        self.calc_worker.start()
    
    def on_calculation_finished(self, result: Dict):
        """Handle calculation completion."""
        self.progress_bar.setVisible(False)
        self.calculate_btn.setEnabled(True)
        
        if result.get("success"):
            wellpath_data = result["data"]["wellpath"]
            
            # Update survey table with calculated data
            self.survey_widget.set_calculated_data(wellpath_data)
            
            # Update visualizations
            self.plot_2d_widget.plot_trajectory_2d(wellpath_data, "plan")
            self.plot_3d_widget.plot_trajectory_3d(wellpath_data)
            self.plot_dls_widget.plot_dogleg_severity(wellpath_data)
            
            # Show summary
            calc_time = result.get("calculation_time", 0)
            self.status_bar.showMessage(f"Calculation completed in {calc_time:.3f}s")
            
        else:
            QMessageBox.critical(self, "Calculation Error", result.get("message", "Unknown error"))
    
    def on_calculation_error(self, error_msg: str):
        """Handle calculation error."""
        self.progress_bar.setVisible(False)
        self.calculate_btn.setEnabled(True)
        
        QMessageBox.critical(self, "Calculation Error", f"Calculation failed: {error_msg}")
    
    def validate_survey(self):
        """Validate survey data."""
        survey_data = self.survey_widget.get_survey_data()
        
        if len(survey_data) < 2:
            QMessageBox.warning(self, "Warning", "At least 2 survey points are required")
            return
        
        # Start validation in worker thread
        self.validate_worker = CalculationWorker(
            self.api_client,
            "validate_survey",
            survey_data=survey_data
        )
        
        self.validate_worker.calculation_finished.connect(self.on_validation_finished)
        self.validate_worker.calculation_error.connect(self.on_validation_error)
        self.validate_worker.start()
    
    def on_validation_finished(self, result: Dict):
        """Handle validation completion."""
        if result.get("success"):
            data = result["data"]
            if data.get("valid"):
                msg = f"Survey data is valid!\n\n"
                msg += f"Points: {data['num_points']}\n"
                msg += f"MD Range: {data['md_range']:.1f}\n"
                msg += f"Inc Range: {data['inc_range']:.1f}°\n"
                
                warnings = data.get("warnings", [])
                if warnings:
                    msg += f"\nWarnings:\n" + "\n".join(f"• {w}" for w in warnings)
                
                QMessageBox.information(self, "Validation Result", msg)
            else:
                QMessageBox.critical(self, "Validation Error", f"Survey data is invalid: {data.get('error', 'Unknown error')}")
        else:
            QMessageBox.critical(self, "Validation Error", result.get("message", "Unknown error"))
    
    def on_validation_error(self, error_msg: str):
        """Handle validation error."""
        QMessageBox.critical(self, "Validation Error", f"Validation failed: {error_msg}")
    
    def predict_rop(self):
        """Predict ROP using ML model."""
        # This would collect drilling parameters and call the ROP prediction API
        QMessageBox.information(self, "ROP Prediction", "ROP prediction functionality would be implemented here")
    
    def show_settings(self):
        """Show settings dialog."""
        QMessageBox.information(self, "Settings", "Settings dialog would be implemented here")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About WormDriller", 
                         "WormDriller Hybrid Desktop Application\n\n"
                         "A comprehensive directional drilling application\n"
                         "combining desktop GUI with cloud-based calculations\n"
                         "and machine learning capabilities.\n\n"
                         "Version 2.0.0\n"
                         "© 2025 WormDriller Team")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("WormDriller")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("WormDriller")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

