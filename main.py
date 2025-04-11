"""
Main application module for Directional Driller Application

This module implements the main application class and entry point for the
directional drilling application.
"""

import sys
import os
from typing import Dict, List, Optional, Union, Any

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QLabel, QPushButton, QFileDialog, QMessageBox, QAction, QMenu, QToolBar
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from data_models import WellModel, SurveyModel, BHAModel, DrillingParamsModel
from calculation_engine import CalculationEngine
from visualization import VisualizationModule
from reporting import ReportGenerator
from data_management import DataManagementModule

# Import UI modules
from ui.main_window import MainWindow


class DirectionalDrillerApp:
    """
    Main application class for the Directional Driller Application.
    
    This class initializes and manages the application components and provides
    the entry point for the application.
    """
    
    def __init__(self):
        """Initialize the application."""
        self.app = QApplication(sys.argv)
        self.modules = {}
        self.initialize()
    
    def initialize(self):
        """Initialize application modules."""
        # Initialize core modules
        self.modules['data_management'] = DataManagementModule()
        self.modules['calculation_engine'] = CalculationEngine()
        self.modules['visualization'] = VisualizationModule()
        self.modules['reporting'] = ReportGenerator()
        
        # Initialize UI
        self.main_window = MainWindow(self.modules)
    
    def run(self):
        """Run the application."""
        self.main_window.show()
        return self.app.exec_()


def main():
    """Application entry point."""
    # Create application directories if they don't exist
    os.makedirs("projects", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Create and run application
    app = DirectionalDrillerApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
