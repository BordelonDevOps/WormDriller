"""
Reporting Module for Directional Driller Application

This module implements reporting functionality for directional drilling operations,
including daily drilling reports (DDR), survey reports, and BHA reports.
"""

import os
import json
import datetime
from typing import Dict, List, Optional, Union, Any
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt

from data_models import WellModel, SurveyModel, BHAModel, DrillingParamsModel
from visualization import VisualizationModule


class ReportGenerator:
    """
    Report generator for directional drilling operations.
    
    Provides methods for generating various reports, including daily drilling
    reports (DDR), survey reports, and BHA reports.
    """
    
    def __init__(self):
        """Initialize the report generator with default settings."""
        self.templates = {
            'ddr': 'templates/ddr_template.json',
            'survey': 'templates/survey_template.json',
            'bha': 'templates/bha_template.json'
        }
        self.visualization = VisualizationModule()
        self.report_dir = 'reports'
        
        # Create report directory if it doesn't exist
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_daily_report(self, well_model: WellModel, report_data: Dict[str, Any]) -> str:
        """
        Generate a Daily Drilling Report (DDR).
        
        Args:
            well_model: Well model containing well information
            report_data: Dictionary containing report data
            
        Returns:
            HTML content of the generated report
        """
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Daily Drilling Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Daily Drilling Report</h1>
            <p><strong>Date:</strong> {report_data['general']['date']}</p>
            <p><strong>Well:</strong> {report_data['general']['well_name']}</p>
            <p><strong>Operator:</strong> {report_data['general']['operator']}</p>
            <p><strong>Rig:</strong> {report_data['general']['rig_name']}</p>
            <p><strong>Report Number:</strong> {report_data['general']['report_number']}</p>
            <p><strong>Days Since Spud:</strong> {report_data['general']['days_since_spud']}</p>
            
            <h2>Current Status</h2>
            <table>
                <tr><th>Current Depth</th><td>{report_data['general']['current_depth']}</td></tr>
                <tr><th>Footage Today</th><td>{report_data['general']['footage_today']}</td></tr>
            </table>
            
            <h2>Operations</h2>
            <p>{report_data['operations']}</p>
            
            <h2>Drilling Parameters</h2>
            <table>
        """
        
        # Add drilling parameters
        for key, value in report_data['drilling_parameters'].items():
            html_content += f"<tr><td>{key}</td><td>{value}</td></tr>"
        
        html_content += """
            </table>
            
            <h2>Mud Properties</h2>
            <table>
        """
        
        # Add mud properties
        for key, value in report_data['mud_properties'].items():
            html_content += f"<tr><td>{key}</td><td>{value}</td></tr>"
        
        html_content += """
            </table>
            
            <h2>Surveys</h2>
            <table>
                <tr>
                    <th>MD</th>
                    <th>Inc</th>
                    <th>Azi</th>
                    <th>TVD</th>
                    <th>NS</th>
                    <th>EW</th>
                </tr>
        """
        
        # Add surveys
        for survey in report_data['surveys']:
            html_content += f"""
                <tr>
                    <td>{survey['md']}</td>
                    <td>{survey['inc']}°</td>
                    <td>{survey['azi']}°</td>
                    <td>{survey['tvd']}</td>
                    <td>{survey['ns']}</td>
                    <td>{survey['ew']}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>Comments</h2>
            <p>{}</p>
            
            <p><small>Generated on: {}</small></p>
        </body>
        </html>
        """.format(report_data['comments'], datetime.datetime.now().isoformat())
        
        return html_content
    
    def generate_survey_report(self, well_model: WellModel, survey_model: SurveyModel,
                              planned_survey: Optional[SurveyModel] = None,
                              output_format: str = 'pdf') -> str:
        """
        Generate a Survey Report.
        
        Args:
            well_model: Well model containing well information
            survey_model: Survey model containing survey data
            planned_survey: Optional planned survey model for comparison
            output_format: Output format ('pdf', 'html', or 'json')
            
        Returns:
            Path to the generated report file or HTML content if output_format is 'html'
        """
        # Create report data structure
        report_data = {
            'report_type': 'Survey Report',
            'report_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'well_info': well_model.to_dict(),
            'surveys': [s.to_dict() for s in survey_model.surveys],
            'generation_time': datetime.datetime.now().isoformat()
        }
        
        # Add planned survey data if available
        if planned_survey and planned_survey.surveys:
            report_data['planned_surveys'] = [s.to_dict() for s in planned_survey.surveys]
        
        # Generate report based on format
        if output_format.lower() == 'json':
            return self._generate_json_report(report_data, 'survey')
        elif output_format.lower() == 'html':
            # For HTML format, return the content directly instead of the file path
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{report_data['report_type']}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                </style>
            </head>
            <body>
                <h1>{report_data['report_type']}</h1>
                <p><strong>Date:</strong> {report_data['report_date']}</p>
                <p><strong>Well:</strong> {report_data['well_info']['name']}</p>
                <p><strong>Operator:</strong> {report_data['well_info']['operator']}</p>
            """
            
            # Add survey-specific content
            html_content += self._generate_survey_html_content(report_data)
            
            # Close HTML
            html_content += f"""
                <p><small>Generated on: {report_data['generation_time']}</small></p>
            </body>
            </html>
            """
            
            return html_content
        else:  # Default to PDF
            return self._generate_pdf_report(report_data, 'survey', survey_model, planned_survey)
    
    def generate_bha_report(self, well_model: WellModel, bha_model: BHAModel,
                           output_format: str = 'html') -> str:
        """
        Generate a BHA Report.
        
        Args:
            well_model: Well model containing well information
            bha_model: BHA model containing BHA information
            output_format: Output format ('pdf', 'html', or 'json')
            
        Returns:
            HTML content of the generated report
        """
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BHA Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>BHA Report</h1>
            <p><strong>Well:</strong> {well_model.name}</p>
            <p><strong>Operator:</strong> {well_model.operator}</p>
            <p><strong>BHA Name:</strong> {bha_model.name}</p>
            
            <h2>BHA Components</h2>
            <table>
                <tr>
                    <th>Position</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Length</th>
                    <th>OD</th>
                    <th>ID</th>
                    <th>Weight</th>
                </tr>
        """
        
        # Add BHA components
        for component in bha_model.components:
            html_content += f"""
                <tr>
                    <td>{component.position}</td>
                    <td>{component.name}</td>
                    <td>{component.type}</td>
                    <td>{component.length}</td>
                    <td>{component.od}</td>
                    <td>{component.id}</td>
                    <td>{component.weight}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>BHA Summary</h2>
            <table>
        """
        
        # Calculate BHA summary
        total_length = sum(c.length for c in bha_model.components)
        total_weight = sum(c.weight for c in bha_model.components)
        
        html_content += f"""
                <tr><th>Total Length</th><td>{total_length} {'m' if bha_model.unit_system == 'metric' else 'ft'}</td></tr>
                <tr><th>Total Weight</th><td>{total_weight} {'kg' if bha_model.unit_system == 'metric' else 'lbs'}</td></tr>
            </table>
            
            <p><small>Generated on: {datetime.datetime.now().isoformat()}</small></p>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_wellpath_report(self, well_model: WellModel, survey_model: SurveyModel) -> str:
        """
        Generate a Wellpath Report.
        
        Args:
            well_model: Well model containing well information
            survey_model: Survey model containing survey data
            
        Returns:
            HTML content of the generated report
        """
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wellpath Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Wellpath Report</h1>
            <p><strong>Well:</strong> {well_model.name}</p>
            <p><strong>Operator:</strong> {well_model.operator}</p>
            
            <h2>Wellpath Data</h2>
            <table>
                <tr>
                    <th>MD</th>
                    <th>Inc</th>
                    <th>Azi</th>
                    <th>TVD</th>
                    <th>Northing</th>
                    <th>Easting</th>
                    <th>DLS</th>
                </tr>
        """
        
        # Add survey points
        for survey in survey_model.surveys:
            html_content += f"""
                <tr>
                    <td>{survey.md}</td>
                    <td>{survey.inc}°</td>
                    <td>{survey.azi}°</td>
                    <td>{survey.tvd}</td>
                    <td>{survey.northing}</td>
                    <td>{survey.easting}</td>
                    <td>{survey.dls}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>Wellpath Summary</h2>
            <table>
        """
        
        # Calculate wellpath summary
        if survey_model.surveys:
            last_survey = survey_model.surveys[-1]
            total_md = last_survey.md
            total_tvd = last_survey.tvd
            final_inc = last_survey.inc
            final_azi = last_survey.azi
            
            html_content += f"""
                <tr><th>Total Measured Depth</th><td>{total_md} {'m' if survey_model.unit_system == 'metric' else 'ft'}</td></tr>
                <tr><th>Total True Vertical Depth</th><td>{total_tvd} {'m' if survey_model.unit_system == 'metric' else 'ft'}</td></tr>
                <tr><th>Final Inclination</th><td>{final_inc}°</td></tr>
                <tr><th>Final Azimuth</th><td>{final_azi}°</td></tr>
            """
        
        html_content += """
            </table>
            
            <p><small>Generated on: {}</small></p>
        </body>
        </html>
        """.format(datetime.datetime.now().isoformat())
        
        return html_content
    
    def generate_trajectory_analysis(self, well_model: WellModel, survey_model: SurveyModel) -> str:
        """
        Generate a Trajectory Analysis Report.
        
        Args:
            well_model: Well model containing well information
            survey_model: Survey model containing survey data
            
        Returns:
            HTML content of the generated report
        """
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trajectory Analysis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Trajectory Analysis</h1>
            <p><strong>Well:</strong> {well_model.name}</p>
            <p><strong>Operator:</strong> {well_model.operator}</p>
            
            <h2>Dogleg Severity Analysis</h2>
            <table>
                <tr>
                    <th>MD</th>
                    <th>Inc</th>
                    <th>Azi</th>
                    <th>Dogleg</th>
                    <th>DLS</th>
                </tr>
        """
        
        # Add survey points (skip first point as it has no dogleg)
        for survey in survey_model.surveys[1:]:
            html_content += f"""
                <tr>
                    <td>{survey.md}</td>
                    <td>{survey.inc}°</td>
                    <td>{survey.azi}°</td>
                    <td>{survey.dogleg}°</td>
                    <td>{survey.dls}°/{'30m' if survey_model.unit_system == 'metric' else '100ft'}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>Build and Turn Rates</h2>
            <table>
                <tr>
                    <th>MD Interval</th>
                    <th>Build Rate</th>
                    <th>Turn Rate</th>
                </tr>
        """
        
        # Calculate build and turn rates
        for i in range(1, len(survey_model.surveys)):
            prev = survey_model.surveys[i-1]
            curr = survey_model.surveys[i]
            
            md_interval = f"{prev.md} - {curr.md}"
            md_change = curr.md - prev.md
            
            if md_change > 0:
                build_rate = (curr.inc - prev.inc) / md_change * (100 if survey_model.unit_system == 'imperial' else 30)
                
                # Handle azimuth wrap-around
                azi_change = curr.azi - prev.azi
                if azi_change > 180:
                    azi_change -= 360
                elif azi_change < -180:
                    azi_change += 360
                
                turn_rate = azi_change / md_change * (100 if survey_model.unit_system == 'imperial' else 30)
                
                html_content += f"""
                    <tr>
                        <td>{md_interval}</td>
                        <td>{build_rate:.2f}°/{'30m' if survey_model.unit_system == 'metric' else '100ft'}</td>
                        <td>{turn_rate:.2f}°/{'30m' if survey_model.unit_system == 'metric' else '100ft'}</td>
                    </tr>
                """
        
        html_content += """
            </table>
            
            <p><small>Generated on: {}</small></p>
        </body>
        </html>
        """.format(datetime.datetime.now().isoformat())
        
        return html_content
    
    def generate_final_well_report(self, well_model: WellModel, survey_model: SurveyModel, bha_model: BHAModel) -> str:
        """
        Generate a Final Well Report.
        
        Args:
            well_model: Well model containing well information
            survey_model: Survey model containing survey data
            bha_model: BHA model containing BHA information
            
        Returns:
            HTML content of the generated report
        """
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Final Well Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>Final Well Report</h1>
            <h2>Well Information</h2>
            <table>
                <tr><th>Well Name</th><td>{well_model.name}</td></tr>
                <tr><th>Operator</th><td>{well_model.operator}</td></tr>
                <tr><th>Rig Name</th><td>{well_model.rig_name}</td></tr>
            """
        
        if well_model.location:
            html_content += f"""
                <tr><th>Latitude</th><td>{well_model.location.get('latitude', 'N/A')}</td></tr>
                <tr><th>Longitude</th><td>{well_model.location.get('longitude', 'N/A')}</td></tr>
            """
        
        html_content += """
            </table>
            
            <h2>Final Wellbore Data</h2>
        """
        
        if survey_model.surveys:
            last_survey = survey_model.surveys[-1]
            html_content += f"""
            <table>
                <tr><th>Total Measured Depth</th><td>{last_survey.md} {'m' if survey_model.unit_system == 'metric' else 'ft'}</td></tr>
                <tr><th>Total True Vertical Depth</th><td>{last_survey.tvd} {'m' if survey_model.unit_system == 'metric' else 'ft'}</td></tr>
                <tr><th>Final Inclination</th><td>{last_survey.inc}°</td></tr>
                <tr><th>Final Azimuth</th><td>{last_survey.azi}°</td></tr>
                <tr><th>Final Northing</th><td>{last_survey.northing} {'m' if survey_model.unit_system == 'metric' else 'ft'}</td></tr>
                <tr><th>Final Easting</th><td>{last_survey.easting} {'m' if survey_model.unit_system == 'metric' else 'ft'}</td></tr>
            </table>
            """
        
        html_content += """
            <h2>Final BHA Information</h2>
        """
        
        if bha_model.components:
            html_content += f"""
            <h3>{bha_model.name}</h3>
            <table>
                <tr>
                    <th>Position</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Length</th>
                    <th>OD</th>
                </tr>
            """
            
            for component in bha_model.components:
                html_content += f"""
                <tr>
                    <td>{component.position}</td>
                    <td>{component.name}</td>
                    <td>{component.type}</td>
                    <td>{component.length}</td>
                    <td>{component.od}</td>
                </tr>
                """
            
            html_content += "</table>"
        
        html_content += """
            <p><small>Generated on: {}</small></p>
        </body>
        </html>
        """.format(datetime.datetime.now().isoformat())
        
        return html_content
    
    def export_to_pdf(self, html_content: str, output_path: str) -> str:
        """
        Export HTML content to PDF.
        
        Args:
            html_content: HTML content to export
            output_path: Path to save the PDF file
            
        Returns:
            Path to the generated PDF file
        """
        try:
            # Create a simple PDF with FPDF as a fallback
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "", 12)
            
            # Add a simplified version of the HTML content
            pdf.multi_cell(0, 10, "PDF Export (simplified version)")
            pdf.ln(10)
            
            # Strip HTML tags for basic text
            import re
            text_content = re.sub('<[^<]+?>', ' ', html_content)
            text_content = re.sub('\\s+', ' ', text_content).strip()
            
            # Add first 500 chars of content
            pdf.multi_cell(0, 10, text_content[:500] + "...")
            
            # Save PDF
            pdf.output(output_path)
            return output_path
        except Exception as e:
            print(f"Error generating PDF: {e}")
            # If PDF generation fails, save as HTML instead
            html_path = output_path.replace('.pdf', '.html')
            with open(html_path, 'w') as f:
                f.write(html_content)
            return html_path
    
    def export_survey_to_csv(self, survey_model: SurveyModel, output_path: str) -> str:
        """
        Export survey data to CSV.
        
        Args:
            survey_model: Survey model containing survey data
            output_path: Path to save the CSV file
            
        Returns:
            Path to the generated CSV file
        """
        # Create DataFrame from survey data
        survey_data = []
        for survey in survey_model.surveys:
            survey_data.append({
                'MD': survey.md,
                'Inc': survey.inc,
                'Azi': survey.azi,
                'TVD': survey.tvd,
                'Northing': survey.northing,
                'Easting': survey.easting,
                'Dogleg': survey.dogleg,
                'DLS': survey.dls
            })
        
        df = pd.DataFrame(survey_data)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        return output_path
    
    def export_bha_to_csv(self, bha_model: BHAModel, output_path: str) -> str:
        """
        Export BHA data to CSV.
        
        Args:
            bha_model: BHA model containing BHA information
            output_path: Path to save the CSV file
            
        Returns:
            Path to the generated CSV file
        """
        # Create DataFrame from BHA data
        bha_data = []
        for component in bha_model.components:
            bha_data.append({
                'Name': component.name,
                'Type': component.type,
                'Length': component.length,
                'OD': component.od,
                'ID': component.id,
                'Weight': component.weight,
                'Position': component.position
            })
        
        df = pd.DataFrame(bha_data)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        return output_path
    
    def _generate_json_report(self, report_data: Dict[str, Any], report_type: str) -> str:
        """
        Generate a JSON report.
        
        Args:
            report_data: Report data dictionary
            report_type: Report type ('ddr', 'survey', or 'bha')
            
        Returns:
            Path to the generated JSON file
        """
        # Create filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_{timestamp}.json"
        filepath = os.path.join(self.report_dir, filename)
        
        # Write JSON file
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=4)
        
        return filepath
    
    def _generate_html_report(self, report_data: Dict[str, Any], report_type: str) -> str:
        """
        Generate an HTML report.
        
        Args:
            report_data: Report data dictionary
            report_type: Report type ('ddr', 'survey', or 'bha')
            
        Returns:
            Path to the generated HTML file
        """
        # Create filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_{timestamp}.html"
        filepath = os.path.join(self.report_dir, filename)
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report_data['report_type']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>{report_data['report_type']}</h1>
            <p><strong>Date:</strong> {report_data['report_date']}</p>
            <p><strong>Well:</strong> {report_data['well_info']['name']}</p>
            <p><strong>Operator:</strong> {report_data['well_info']['operator']}</p>
        """
        
        # Add report-specific content
        if report_type == 'ddr':
            html_content += self._generate_ddr_html_content(report_data)
        elif report_type == 'survey':
            html_content += self._generate_survey_html_content(report_data)
        elif report_type == 'bha':
            html_content += self._generate_bha_html_content(report_data)
        
        # Close HTML
        html_content += f"""
            <p><small>Generated on: {report_data['generation_time']}</small></p>
        </body>
        </html>
        """
        
        # Write HTML file
        with open(filepath, 'w') as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_ddr_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content specific to DDR."""
        html_content = ""
        
        # Add current depth information
        if 'current_depth' in report_data:
            depth = report_data['current_depth']
            html_content += f"""
            <h2>Current Depth</h2>
            <table>
                <tr><th>Measured Depth</th><td>{depth['md']}</td></tr>
                <tr><th>True Vertical Depth</th><td>{depth['tvd']}</td></tr>
                <tr><th>Inclination</th><td>{depth['inc']}°</td></tr>
                <tr><th>Azimuth</th><td>{depth['azi']}°</td></tr>
            </table>
            """
        
        # Add personnel information
        if 'personnel' in report_data:
            html_content += """
            <h2>Personnel</h2>
            <table>
                <tr><th>Role</th><th>Name</th></tr>
            """
            for role, name in report_data['personnel'].items():
                html_content += f"<tr><td>{role}</td><td>{name}</td></tr>"
            html_content += "</table>"
        
        # Add activities
        if 'activities' in report_data:
            html_content += """
            <h2>Activities</h2>
            <table>
                <tr><th>Time</th><th>Activity</th><th>Details</th></tr>
            """
            for activity in report_data['activities']:
                html_content += f"<tr><td>{activity.get('time', '')}</td><td>{activity.get('activity', '')}</td><td>{activity.get('details', '')}</td></tr>"
            html_content += "</table>"
        
        # Add drilling parameters
        if 'drilling_params' in report_data:
            params = report_data['drilling_params']
            html_content += """
            <h2>Drilling Parameters</h2>
            <table>
            """
            for key, value in params.items():
                if key not in ['md', 'timestamp', 'additional_params']:
                    html_content += f"<tr><td>{key}</td><td>{value}</td></tr>"
            html_content += "</table>"
        
        # Add comments
        if 'comments' in report_data and report_data['comments']:
            html_content += f"""
            <h2>Comments</h2>
            <p>{report_data['comments']}</p>
            """
        
        return html_content
    
    def _generate_survey_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content specific to Survey Report."""
        html_content = ""
        
        # Add survey data
        if 'surveys' in report_data:
            html_content += """
            <h2>Survey Data</h2>
            <table>
                <tr>
                    <th>MD</th>
                    <th>Inc</th>
                    <th>Azi</th>
                    <th>TVD</th>
                    <th>Northing</th>
                    <th>Easting</th>
                    <th>DLS</th>
                </tr>
            """
            for survey in report_data['surveys']:
                html_content += f"""
                <tr>
                    <td>{survey['md']}</td>
                    <td>{survey['inc']}°</td>
                    <td>{survey['azi']}°</td>
                    <td>{survey['tvd']}</td>
                    <td>{survey['northing']}</td>
                    <td>{survey['easting']}</td>
                    <td>{survey['dls']}</td>
                </tr>
                """
            html_content += "</table>"
        
        return html_content
    
    def _generate_bha_html_content(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content specific to BHA Report."""
        html_content = ""
        
        # Add BHA information
        if 'bha_info' in report_data:
            bha_info = report_data['bha_info']
            html_content += f"""
            <h2>BHA Information</h2>
            <p><strong>Name:</strong> {bha_info['name']}</p>
            """
            
            # Add components
            if 'components' in bha_info:
                html_content += """
                <h3>Components</h3>
                <table>
                    <tr>
                        <th>Position</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Length</th>
                        <th>OD</th>
                        <th>ID</th>
                        <th>Weight</th>
                    </tr>
                """
                for component in bha_info['components']:
                    html_content += f"""
                    <tr>
                        <td>{component['position']}</td>
                        <td>{component['name']}</td>
                        <td>{component['type']}</td>
                        <td>{component['length']}</td>
                        <td>{component['od']}</td>
                        <td>{component['id']}</td>
                        <td>{component['weight']}</td>
                    </tr>
                    """
                html_content += "</table>"
        
        return html_content
    
    def _generate_pdf_report(self, report_data: Dict[str, Any], report_type: str,
                            survey_model: Optional[SurveyModel] = None,
                            planned_survey: Optional[SurveyModel] = None) -> str:
        """
        Generate a PDF report.
        
        Args:
            report_data: Report data dictionary
            report_type: Report type ('ddr', 'survey', or 'bha')
            survey_model: Optional survey model for visualizations
            planned_survey: Optional planned survey model for comparison
            
        Returns:
            Path to the generated PDF file
        """
        # Create filename
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{report_type}_{timestamp}.pdf"
        filepath = os.path.join(self.report_dir, filename)
        
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font("Arial", "B", 16)
        
        # Add title
        pdf.cell(0, 10, report_data['report_type'], 0, 1, "C")
        pdf.ln(5)
        
        # Add well information
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Well Information", 0, 1)
        
        pdf.set_font("Arial", "", 10)
        pdf.cell(40, 10, "Well Name:", 0, 0)
        pdf.cell(0, 10, report_data['well_info']['name'], 0, 1)
        
        pdf.cell(40, 10, "Operator:", 0, 0)
        pdf.cell(0, 10, report_data['well_info']['operator'], 0, 1)
        
        pdf.cell(40, 10, "Report Date:", 0, 0)
        pdf.cell(0, 10, report_data['report_date'], 0, 1)
        
        pdf.ln(5)
        
        # Add report-specific content
        if report_type == 'ddr':
            self._add_ddr_to_pdf(pdf, report_data)
        elif report_type == 'survey':
            self._add_survey_to_pdf(pdf, report_data)
        elif report_type == 'bha':
            self._add_bha_to_pdf(pdf, report_data)
        
        # Add visualizations if survey model is provided
        if survey_model and (report_type == 'survey' or report_type == 'ddr'):
            self._add_visualizations_to_pdf(pdf, survey_model, planned_survey)
        
        # Save PDF
        pdf.output(filepath)
        
        return filepath
    
    def _add_ddr_to_pdf(self, pdf: FPDF, report_data: Dict[str, Any]) -> None:
        """Add DDR content to PDF."""
        # Add current depth information
        if 'current_depth' in report_data:
            depth = report_data['current_depth']
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Current Depth", 0, 1)
            
            pdf.set_font("Arial", "", 10)
            pdf.cell(40, 10, "Measured Depth:", 0, 0)
            pdf.cell(0, 10, str(depth['md']), 0, 1)
            
            pdf.cell(40, 10, "True Vertical Depth:", 0, 0)
            pdf.cell(0, 10, str(depth['tvd']), 0, 1)
            
            pdf.cell(40, 10, "Inclination:", 0, 0)
            pdf.cell(0, 10, f"{depth['inc']}°", 0, 1)
            
            pdf.cell(40, 10, "Azimuth:", 0, 0)
            pdf.cell(0, 10, f"{depth['azi']}°", 0, 1)
            
            pdf.ln(5)
        
        # Add personnel information
        if 'personnel' in report_data:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Personnel", 0, 1)
            
            pdf.set_font("Arial", "", 10)
            for role, name in report_data['personnel'].items():
                pdf.cell(40, 10, f"{role}:", 0, 0)
                pdf.cell(0, 10, name, 0, 1)
            
            pdf.ln(5)
        
        # Add activities
        if 'activities' in report_data:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Activities", 0, 1)
            
            pdf.set_font("Arial", "", 10)
            for activity in report_data['activities']:
                pdf.cell(30, 10, activity.get('time', ''), 0, 0)
                pdf.cell(40, 10, activity.get('activity', ''), 0, 0)
                pdf.multi_cell(0, 10, activity.get('details', ''))
            
            pdf.ln(5)
        
        # Add drilling parameters
        if 'drilling_params' in report_data:
            params = report_data['drilling_params']
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Drilling Parameters", 0, 1)
            
            pdf.set_font("Arial", "", 10)
            for key, value in params.items():
                if key not in ['md', 'timestamp', 'additional_params']:
                    pdf.cell(40, 10, f"{key}:", 0, 0)
                    pdf.cell(0, 10, str(value), 0, 1)
            
            pdf.ln(5)
        
        # Add comments
        if 'comments' in report_data and report_data['comments']:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Comments", 0, 1)
            
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(0, 10, report_data['comments'])
            
            pdf.ln(5)
    
    def _add_survey_to_pdf(self, pdf: FPDF, report_data: Dict[str, Any]) -> None:
        """Add survey content to PDF."""
        # Add survey data
        if 'surveys' in report_data:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Survey Data", 0, 1)
            
            # Add table header
            pdf.set_font("Arial", "B", 10)
            pdf.cell(20, 10, "MD", 1, 0, "C")
            pdf.cell(20, 10, "Inc", 1, 0, "C")
            pdf.cell(20, 10, "Azi", 1, 0, "C")
            pdf.cell(20, 10, "TVD", 1, 0, "C")
            pdf.cell(25, 10, "Northing", 1, 0, "C")
            pdf.cell(25, 10, "Easting", 1, 0, "C")
            pdf.cell(20, 10, "DLS", 1, 1, "C")
            
            # Add table rows
            pdf.set_font("Arial", "", 10)
            for survey in report_data['surveys']:
                pdf.cell(20, 10, str(survey['md']), 1, 0, "C")
                pdf.cell(20, 10, f"{survey['inc']}°", 1, 0, "C")
                pdf.cell(20, 10, f"{survey['azi']}°", 1, 0, "C")
                pdf.cell(20, 10, str(survey['tvd']), 1, 0, "C")
                pdf.cell(25, 10, str(survey['northing']), 1, 0, "C")
                pdf.cell(25, 10, str(survey['easting']), 1, 0, "C")
                pdf.cell(20, 10, str(survey['dls']), 1, 1, "C")
            
            pdf.ln(5)
    
    def _add_bha_to_pdf(self, pdf: FPDF, report_data: Dict[str, Any]) -> None:
        """Add BHA content to PDF."""
        # Add BHA information
        if 'bha_info' in report_data:
            bha_info = report_data['bha_info']
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "BHA Information", 0, 1)
            
            pdf.set_font("Arial", "", 10)
            pdf.cell(40, 10, "Name:", 0, 0)
            pdf.cell(0, 10, bha_info['name'], 0, 1)
            
            # Add components
            if 'components' in bha_info:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Components", 0, 1)
                
                # Add table header
                pdf.set_font("Arial", "B", 10)
                pdf.cell(20, 10, "Position", 1, 0, "C")
                pdf.cell(40, 10, "Name", 1, 0, "C")
                pdf.cell(30, 10, "Type", 1, 0, "C")
                pdf.cell(20, 10, "Length", 1, 0, "C")
                pdf.cell(20, 10, "OD", 1, 0, "C")
                pdf.cell(20, 10, "ID", 1, 0, "C")
                pdf.cell(20, 10, "Weight", 1, 1, "C")
                
                # Add table rows
                pdf.set_font("Arial", "", 10)
                for component in bha_info['components']:
                    pdf.cell(20, 10, str(component['position']), 1, 0, "C")
                    pdf.cell(40, 10, component['name'], 1, 0, "C")
                    pdf.cell(30, 10, component['type'], 1, 0, "C")
                    pdf.cell(20, 10, str(component['length']), 1, 0, "C")
                    pdf.cell(20, 10, str(component['od']), 1, 0, "C")
                    pdf.cell(20, 10, str(component['id']), 1, 0, "C")
                    pdf.cell(20, 10, str(component['weight']), 1, 1, "C")
                
                pdf.ln(5)
    
    def _add_visualizations_to_pdf(self, pdf: FPDF, survey_model: SurveyModel,
                                  planned_survey: Optional[SurveyModel] = None) -> None:
        """Add visualizations to PDF."""
        # Create temporary directory for charts
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Generate charts
            charts = self.visualization.generate_report_charts(
                survey_model,
                temp_dir,
                planned_survey=planned_survey
            )
            
            # Add charts to PDF
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Visualizations", 0, 1)
            
            # Add each chart
            for chart_type, chart_path in charts.items():
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 10, chart_type.replace('_', ' ').title(), 0, 1)
                
                # Add image
                pdf.image(chart_path, x=10, w=190)
                pdf.ln(5)
        finally:
            # Clean up temporary directory
            import shutil
            shutil.rmtree(temp_dir)
