# WormDriller

<div align="center">
  <img src="promotional/images/logo.png" alt="WormDriller Logo" width="200"/>
  <br>
  <h3>The Complete Solution for Directional Drilling Professionals</h3>
  
  ![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
  ![PyQt5](https://img.shields.io/badge/PyQt-5.15+-green.svg)
  ![License](https://img.shields.io/badge/License-MIT-yellow.svg)
  ![Status](https://img.shields.io/badge/Status-Beta-orange.svg)
</div>

## 📋 Overview

WormDriller is a comprehensive software solution designed specifically for directional drilling professionals. Built by industry experts, this powerful application combines advanced mathematical models with an intuitive interface to help you plan, monitor, and report on directional drilling operations with unprecedented efficiency and accuracy.

<div align="center">
  <img src="promotional/images/3d_viz.png" alt="3D Wellbore Visualization" width="600"/>
</div>

## ✨ Key Features

### 🎯 Precise Trajectory Calculations
- Industry-standard Minimum Curvature Method
- Real-time dogleg severity analysis
- Advanced anti-collision detection
- Build and turn rate optimization

<div align="center">
  <img src="promotional/images/trajectory_calc.png" alt="Trajectory Calculations" width="600"/>
</div>

### 📊 Powerful Visualization Tools
- Interactive 2D wellbore trajectory plots
- Immersive 3D wellbore visualization
- Inclination and azimuth analysis graphs
- Comparative planned vs. actual trajectory views

### 🔧 Comprehensive BHA Management
- Detailed BHA component configuration
- Performance analysis and optimization
- Historical BHA tracking and comparison
- Component stress and wear prediction

<div align="center">
  <img src="promotional/images/bha.png" alt="BHA Management" width="600"/>
</div>

### 📝 Professional Reporting System
- Customizable Daily Drilling Reports (DDR)
- Detailed survey reports with visualizations
- Comprehensive BHA reports
- Multiple export formats (HTML, PDF, CSV)

<div align="center">
  <img src="promotional/images/reporting.png" alt="Reporting System" width="600"/>
</div>

### 💾 Robust Data Management
- Secure project and well organization
- CSV import/export capabilities
- Historical data tracking and analysis
- Automated data backup and recovery

<div align="center">
  <img src="promotional/images/dashboard.png" alt="Project Dashboard" width="600"/>
</div>

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- 4GB RAM (minimum)
- 500MB disk space

### Quick Start
1. Clone this repository:
   ```bash
   git clone https://github.com/BordelonDevOps/WormDriller.git
   cd WormDriller
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## 📖 Documentation

Comprehensive documentation is available in the [docs](docs/) directory:

- [User Guide](docs/user_guide.md) - Complete guide to using the application
- [Mathematical Models](docs/math_models.md) - Details on implemented calculations
- [API Reference](docs/api_reference.md) - For developers extending the application
- [FAQ](docs/faq.md) - Frequently asked questions

## 🧪 Development

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/BordelonDevOps/WormDriller.git
   cd WormDriller
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Running Tests

```bash
python -m unittest discover tests
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- Email: info@wormdriller.com
- Website: www.wormdriller.com

## 🙏 Acknowledgments

- Special thanks to all the directional drilling professionals who provided valuable input
- [NumPy](https://numpy.org/) for numerical computations
- [Matplotlib](https://matplotlib.org/) for visualization capabilities
- [Pandas](https://pandas.pydata.org/) for data manipulation
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for the user interface
