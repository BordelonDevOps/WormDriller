"""
Visualization Module for Directional Driller Application

This module implements visualization functions for directional drilling data,
including wellbore trajectory plots, cross-sections, and data visualizations.
"""

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict, List, Tuple, Union, Optional, Any
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import pandas as pd

from data_models import SurveyModel, SurveyPoint, WellModel, BHAModel


class VisualizationModule:
    """
    Visualization module for directional drilling data.
    
    Provides methods for generating various visualizations of directional
    drilling data, including wellbore trajectory plots, cross-sections,
    and data visualizations.
    """
    
    def __init__(self):
        """Initialize the visualization module with default settings."""
        self.default_figsize = (10, 8)
        self.default_dpi = 100
        self.color_palette = {
            'planned': 'blue',
            'actual': 'red',
            'projection': 'green',
            'target': 'purple',
            'background': '#f5f5f5',
            'grid': '#cccccc'
        }
        self.plot_styles = {
            'planned': {'linestyle': '--', 'linewidth': 2, 'marker': 'o', 'markersize': 4},
            'actual': {'linestyle': '-', 'linewidth': 2, 'marker': 'o', 'markersize': 4},
            'projection': {'linestyle': ':', 'linewidth': 2, 'marker': None}
        }
    
    def plot_trajectory_2d(self, survey_model: SurveyModel, 
                          planned_survey: Optional[SurveyModel] = None,
                          view: str = 'plan', 
                          figsize: Optional[Tuple[int, int]] = None,
                          show_grid: bool = True,
                          show_labels: bool = True,
                          show_legend: bool = True) -> Figure:
        """
        Generate a 2D plot of the wellbore trajectory.
        
        Args:
            survey_model: Survey model containing actual survey data
            planned_survey: Optional survey model containing planned survey data
            view: View type ('plan', 'vs_md', 'vs_tvd', 'ns_ew')
            figsize: Figure size (width, height) in inches
            show_grid: Whether to show grid lines
            show_labels: Whether to show axis labels
            show_legend: Whether to show legend
            
        Returns:
            Matplotlib Figure object
        """
        if figsize is None:
            figsize = self.default_figsize
        
        fig, ax = plt.subplots(figsize=figsize, dpi=self.default_dpi)
        ax.set_facecolor(self.color_palette['background'])
        
        # Extract data from survey model
        if not survey_model.surveys:
            return fig
        
        md = [s.md for s in survey_model.surveys]
        tvd = [s.tvd for s in survey_model.surveys]
        northing = [s.northing for s in survey_model.surveys]
        easting = [s.easting for s in survey_model.surveys]
        
        # Plot based on view type
        if view == 'plan':
            # Plan view (North vs East)
            ax.plot(easting, northing, color=self.color_palette['actual'],
                   **self.plot_styles['actual'], label='Actual')
            
            if planned_survey and planned_survey.surveys:
                planned_easting = [s.easting for s in planned_survey.surveys]
                planned_northing = [s.northing for s in planned_survey.surveys]
                ax.plot(planned_easting, planned_northing, color=self.color_palette['planned'],
                       **self.plot_styles['planned'], label='Planned')
            
            ax.set_xlabel('Easting (m)' if survey_model.unit_system == 'metric' else 'Easting (ft)')
            ax.set_ylabel('Northing (m)' if survey_model.unit_system == 'metric' else 'Northing (ft)')
            ax.set_title('Wellbore Trajectory - Plan View')
            
            # Equal aspect ratio for plan view
            ax.set_aspect('equal')
            
        elif view == 'vs_md':
            # Vertical section vs measured depth
            ax.plot(md, tvd, color=self.color_palette['actual'],
                   **self.plot_styles['actual'], label='Actual')
            
            if planned_survey and planned_survey.surveys:
                planned_md = [s.md for s in planned_survey.surveys]
                planned_tvd = [s.tvd for s in planned_survey.surveys]
                ax.plot(planned_md, planned_tvd, color=self.color_palette['planned'],
                       **self.plot_styles['planned'], label='Planned')
            
            ax.set_xlabel('Measured Depth (m)' if survey_model.unit_system == 'metric' else 'Measured Depth (ft)')
            ax.set_ylabel('True Vertical Depth (m)' if survey_model.unit_system == 'metric' else 'True Vertical Depth (ft)')
            ax.set_title('Wellbore Trajectory - Vertical Section vs MD')
            
            # Invert y-axis for depth
            ax.invert_yaxis()
            
        elif view == 'vs_tvd':
            # Vertical section vs true vertical depth
            # Calculate vertical section (projection along azimuth)
            if not survey_model.surveys:
                return fig
            
            # Use the azimuth of the last survey point for vertical section calculation
            last_azi_rad = np.radians(survey_model.surveys[-1].azi)
            vs = [n * np.cos(last_azi_rad) + e * np.sin(last_azi_rad) 
                 for n, e in zip(northing, easting)]
            
            ax.plot(vs, tvd, color=self.color_palette['actual'],
                   **self.plot_styles['actual'], label='Actual')
            
            if planned_survey and planned_survey.surveys:
                planned_northing = [s.northing for s in planned_survey.surveys]
                planned_easting = [s.easting for s in planned_survey.surveys]
                planned_tvd = [s.tvd for s in planned_survey.surveys]
                
                planned_vs = [n * np.cos(last_azi_rad) + e * np.sin(last_azi_rad) 
                             for n, e in zip(planned_northing, planned_easting)]
                
                ax.plot(planned_vs, planned_tvd, color=self.color_palette['planned'],
                       **self.plot_styles['planned'], label='Planned')
            
            ax.set_xlabel('Vertical Section (m)' if survey_model.unit_system == 'metric' else 'Vertical Section (ft)')
            ax.set_ylabel('True Vertical Depth (m)' if survey_model.unit_system == 'metric' else 'True Vertical Depth (ft)')
            ax.set_title('Wellbore Trajectory - Vertical Section vs TVD')
            
            # Invert y-axis for depth
            ax.invert_yaxis()
            
        elif view == 'ns_ew':
            # North-South vs East-West
            ax.plot(northing, easting, color=self.color_palette['actual'],
                   **self.plot_styles['actual'], label='Actual')
            
            if planned_survey and planned_survey.surveys:
                planned_northing = [s.northing for s in planned_survey.surveys]
                planned_easting = [s.easting for s in planned_survey.surveys]
                ax.plot(planned_northing, planned_easting, color=self.color_palette['planned'],
                       **self.plot_styles['planned'], label='Planned')
            
            ax.set_xlabel('Northing (m)' if survey_model.unit_system == 'metric' else 'Northing (ft)')
            ax.set_ylabel('Easting (m)' if survey_model.unit_system == 'metric' else 'Easting (ft)')
            ax.set_title('Wellbore Trajectory - NS vs EW')
            
            # Equal aspect ratio
            ax.set_aspect('equal')
        
        # Add grid if requested
        if show_grid:
            ax.grid(True, linestyle='--', alpha=0.7, color=self.color_palette['grid'])
        
        # Add legend if requested
        if show_legend:
            ax.legend()
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    def plot_trajectory_3d(self, survey_model: SurveyModel,
                          planned_survey: Optional[SurveyModel] = None,
                          figsize: Optional[Tuple[int, int]] = None,
                          show_grid: bool = True,
                          show_labels: bool = True,
                          show_legend: bool = True) -> Figure:
        """
        Generate a 3D plot of the wellbore trajectory.
        
        Args:
            survey_model: Survey model containing actual survey data
            planned_survey: Optional survey model containing planned survey data
            figsize: Figure size (width, height) in inches
            show_grid: Whether to show grid lines
            show_labels: Whether to show axis labels
            show_legend: Whether to show legend
            
        Returns:
            Matplotlib Figure object
        """
        if figsize is None:
            figsize = self.default_figsize
        
        fig = plt.figure(figsize=figsize, dpi=self.default_dpi)
        ax = fig.add_subplot(111, projection='3d')
        
        # Extract data from survey model
        if not survey_model.surveys:
            return fig
        
        northing = [s.northing for s in survey_model.surveys]
        easting = [s.easting for s in survey_model.surveys]
        tvd = [s.tvd for s in survey_model.surveys]
        
        # Plot actual trajectory
        ax.plot(easting, northing, tvd, color=self.color_palette['actual'],
               **self.plot_styles['actual'], label='Actual')
        
        # Plot planned trajectory if provided
        if planned_survey and planned_survey.surveys:
            planned_northing = [s.northing for s in planned_survey.surveys]
            planned_easting = [s.easting for s in planned_survey.surveys]
            planned_tvd = [s.tvd for s in planned_survey.surveys]
            
            ax.plot(planned_easting, planned_northing, planned_tvd, 
                   color=self.color_palette['planned'],
                   **self.plot_styles['planned'], label='Planned')
        
        # Set labels if requested
        if show_labels:
            ax.set_xlabel('Easting (m)' if survey_model.unit_system == 'metric' else 'Easting (ft)')
            ax.set_ylabel('Northing (m)' if survey_model.unit_system == 'metric' else 'Northing (ft)')
            ax.set_zlabel('TVD (m)' if survey_model.unit_system == 'metric' else 'TVD (ft)')
            ax.set_title('Wellbore Trajectory - 3D View')
        
        # Invert z-axis for depth
        ax.invert_zaxis()
        
        # Add legend if requested
        if show_legend:
            ax.legend()
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    def plot_dogleg_severity(self, survey_model: SurveyModel,
                            figsize: Optional[Tuple[int, int]] = None,
                            show_grid: bool = True,
                            show_labels: bool = True) -> Figure:
        """
        Generate a plot of dogleg severity vs measured depth.
        
        Args:
            survey_model: Survey model containing survey data
            figsize: Figure size (width, height) in inches
            show_grid: Whether to show grid lines
            show_labels: Whether to show axis labels
            
        Returns:
            Matplotlib Figure object
        """
        if figsize is None:
            figsize = self.default_figsize
        
        fig, ax = plt.subplots(figsize=figsize, dpi=self.default_dpi)
        ax.set_facecolor(self.color_palette['background'])
        
        # Extract data from survey model
        if not survey_model.surveys or len(survey_model.surveys) < 2:
            return fig
        
        md = [s.md for s in survey_model.surveys[1:]]  # Skip first point (no dogleg)
        dls = [s.dls for s in survey_model.surveys[1:]]  # Skip first point (no dogleg)
        
        # Plot dogleg severity
        ax.plot(md, dls, color='orange', linewidth=2, marker='o', markersize=4)
        
        # Set labels if requested
        if show_labels:
            ax.set_xlabel('Measured Depth (m)' if survey_model.unit_system == 'metric' else 'Measured Depth (ft)')
            ax.set_ylabel('Dogleg Severity (°/30m)' if survey_model.unit_system == 'metric' else 'Dogleg Severity (°/100ft)')
            ax.set_title('Dogleg Severity vs Measured Depth')
        
        # Add grid if requested
        if show_grid:
            ax.grid(True, linestyle='--', alpha=0.7, color=self.color_palette['grid'])
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    def plot_inclination_azimuth(self, survey_model: SurveyModel,
                                figsize: Optional[Tuple[int, int]] = None,
                                show_grid: bool = True,
                                show_labels: bool = True) -> Figure:
        """
        Generate plots of inclination and azimuth vs measured depth.
        
        Args:
            survey_model: Survey model containing survey data
            figsize: Figure size (width, height) in inches
            show_grid: Whether to show grid lines
            show_labels: Whether to show axis labels
            
        Returns:
            Matplotlib Figure object
        """
        if figsize is None:
            figsize = (self.default_figsize[0], self.default_figsize[1] * 1.5)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, dpi=self.default_dpi)
        ax1.set_facecolor(self.color_palette['background'])
        ax2.set_facecolor(self.color_palette['background'])
        
        # Extract data from survey model
        if not survey_model.surveys:
            return fig
        
        md = [s.md for s in survey_model.surveys]
        inc = [s.inc for s in survey_model.surveys]
        azi = [s.azi for s in survey_model.surveys]
        
        # Plot inclination
        ax1.plot(md, inc, color='blue', linewidth=2, marker='o', markersize=4)
        
        # Plot azimuth
        ax2.plot(md, azi, color='red', linewidth=2, marker='o', markersize=4)
        
        # Set labels if requested
        if show_labels:
            ax1.set_xlabel('Measured Depth (m)' if survey_model.unit_system == 'metric' else 'Measured Depth (ft)')
            ax1.set_ylabel('Inclination (°)')
            ax1.set_title('Inclination vs Measured Depth')
            
            ax2.set_xlabel('Measured Depth (m)' if survey_model.unit_system == 'metric' else 'Measured Depth (ft)')
            ax2.set_ylabel('Azimuth (°)')
            ax2.set_title('Azimuth vs Measured Depth')
        
        # Add grid if requested
        if show_grid:
            ax1.grid(True, linestyle='--', alpha=0.7, color=self.color_palette['grid'])
            ax2.grid(True, linestyle='--', alpha=0.7, color=self.color_palette['grid'])
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    def plot_drilling_parameters(self, drilling_params: List[Dict[str, Any]],
                                params_to_plot: List[str],
                                figsize: Optional[Tuple[int, int]] = None,
                                show_grid: bool = True,
                                show_labels: bool = True) -> Figure:
        """
        Generate plots of drilling parameters vs measured depth.
        
        Args:
            drilling_params: List of drilling parameter dictionaries
            params_to_plot: List of parameter names to plot
            figsize: Figure size (width, height) in inches
            show_grid: Whether to show grid lines
            show_labels: Whether to show axis labels
            
        Returns:
            Matplotlib Figure object
        """
        if figsize is None:
            figsize = (self.default_figsize[0], self.default_figsize[1] * len(params_to_plot) / 2)
        
        # Create DataFrame from drilling parameters
        df = pd.DataFrame(drilling_params)
        
        # Check if measured depth is available
        if 'md' not in df.columns:
            return plt.figure(figsize=figsize, dpi=self.default_dpi)
        
        # Filter parameters to plot
        params_available = [p for p in params_to_plot if p in df.columns]
        
        if not params_available:
            return plt.figure(figsize=figsize, dpi=self.default_dpi)
        
        # Create subplots
        fig, axes = plt.subplots(len(params_available), 1, figsize=figsize, dpi=self.default_dpi)
        
        # Handle case with only one parameter
        if len(params_available) == 1:
            axes = [axes]
        
        # Plot each parameter
        for i, param in enumerate(params_available):
            ax = axes[i]
            ax.set_facecolor(self.color_palette['background'])
            
            # Plot parameter vs measured depth
            ax.plot(df['md'], df[param], linewidth=2, marker='o', markersize=4)
            
            # Set labels if requested
            if show_labels:
                ax.set_xlabel('Measured Depth')
                ax.set_ylabel(param)
                ax.set_title(f'{param} vs Measured Depth')
            
            # Add grid if requested
            if show_grid:
                ax.grid(True, linestyle='--', alpha=0.7, color=self.color_palette['grid'])
        
        # Adjust layout
        plt.tight_layout()
        
        return fig
    
    def save_figure(self, fig: Figure, filepath: str, dpi: Optional[int] = None) -> None:
        """
        Save a figure to a file.
        
        Args:
            fig: Matplotlib Figure object
            filepath: Path to save the figure
            dpi: Resolution in dots per inch
        """
        if dpi is None:
            dpi = self.default_dpi
        
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
    
    def generate_report_charts(self, survey_model: SurveyModel,
                              output_dir: str,
                              planned_survey: Optional[SurveyModel] = None,
                              prefix: str = 'chart_') -> Dict[str, str]:
        """
        Generate and save a set of charts for reporting.
        
        Args:
            survey_model: Survey model containing actual survey data
            output_dir: Directory to save the charts
            planned_survey: Optional survey model containing planned survey data
            prefix: Prefix for chart filenames
            
        Returns:
            Dictionary mapping chart types to file paths
        """
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate and save charts
        charts = {}
        
        # Plan view
        fig_plan = self.plot_trajectory_2d(survey_model, planned_survey, view='plan')
        plan_path = os.path.join(output_dir, f'{prefix}plan_view.png')
        self.save_figure(fig_plan, plan_path)
        charts['plan_view'] = plan_path
        plt.close(fig_plan)
        
        # Vertical section vs MD
        fig_vs_md = self.plot_trajectory_2d(survey_model, planned_survey, view='vs_md')
        vs_md_path = os.path.join(output_dir, f'{prefix}vs_md.png')
        self.save_figure(fig_vs_md, vs_md_path)
        charts['vs_md'] = vs_md_path
        plt.close(fig_vs_md)
        
        # Vertical section vs TVD
        fig_vs_tvd = self.plot_trajectory_2d(survey_model, planned_survey, view='vs_tvd')
        vs_tvd_path = os.path.join(output_dir, f'{prefix}vs_tvd.png')
        self.save_figure(fig_vs_tvd, vs_tvd_path)
        charts['vs_tvd'] = vs_tvd_path
        plt.close(fig_vs_tvd)
        
        # 3D view
        fig_3d = self.plot_trajectory_3d(survey_model, planned_survey)
        view_3d_path = os.path.join(output_dir, f'{prefix}3d_view.png')
        self.save_figure(fig_3d, view_3d_path)
        charts['3d_view'] = view_3d_path
        plt.close(fig_3d)
        
        # Dogleg severity
        fig_dls = self.plot_dogleg_severity(survey_model)
        dls_path = os.path.join(output_dir, f'{prefix}dogleg_severity.png')
        self.save_figure(fig_dls, dls_path)
        charts['dogleg_severity'] = dls_path
        plt.close(fig_dls)
        
        # Inclination and azimuth
        fig_inc_azi = self.plot_inclination_azimuth(survey_model)
        inc_azi_path = os.path.join(output_dir, f'{prefix}inc_azi.png')
        self.save_figure(fig_inc_azi, inc_azi_path)
        charts['inc_azi'] = inc_azi_path
        plt.close(fig_inc_azi)
        
        return charts
