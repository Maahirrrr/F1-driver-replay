# 🏎️ F1 Driver Tracker - Live Animation System

A real-time visualization tool for Formula 1 driver positions on track using FastF1 telemetry data. This project provides an interactive animation system that displays driver movements, speeds, gaps, and race statistics with a sleek dark-themed interface.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![FastF1](https://img.shields.io/badge/FastF1-3.0+-red.svg)

## 📋 Features

- **Real-time Driver Tracking**: Visualize up to 10 drivers simultaneously on the track
- **Ghost Mode**: Compare the top 2 fastest drivers head-to-head with live gap calculations
- **Interactive Controls**:
  - Play/Pause animation
  - Progress slider for manual timeline control
  - Reset to beginning
  - Switch between Full Grid and Ghost Mode
- **Performance Metrics**:
  - Live speed display
  - Lap time comparisons
  - Distance-based gap calculations in Ghost Mode
- **High FPS Animation**: Optimized for smooth 90 FPS playback
- **Persistent Data Caching**: FastF1 cache system for quick reloads

## 🎯 Demo

The system displays:
- Driver positions as colored dots on the track map
- Real-time speed and timing information
- Interactive legend with driver names
- Progress bar showing race completion percentage
- Lap time leaderboard

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Maahirrrr/F1-driver-replay.git
cd F1-driver-replay
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python f1_driver_tracker.py
```

## 📦 Dependencies

- **fastf1** (>=3.0.0): Official F1 telemetry data API
- **matplotlib** (>=3.5.0): Plotting and animation
- **numpy** (>=1.21.0): Numerical computations
- **pandas** (>=1.3.0): Data manipulation

## 🎮 Usage

### Basic Configuration

Edit the configuration parameters in `f1_driver_tracker.py`:

```python
YEAR = 2023          # Season year
RACE = 'Monaco'      # Race name
SESSION = 'Q'        # Session type: 'R' (Race), 'Q' (Qualifying), 'FP1', 'FP2', 'FP3'
NUM_DRIVERS = 10     # Number of drivers to track (1-20)
FPS = 90             # Animation frames per second
```

### Controls

- **Ghost Mode Button**: Toggle between Full Grid (all drivers) and Ghost Mode (top 2 drivers)
- **Pause/Play Button**: Pause or resume the animation
- **Reset Button**: Return to the start of the session
- **Progress Slider**: Manually scrub through the timeline

### Available Sessions

- `'R'` - Race
- `'Q'` - Qualifying
- `'FP1'`, `'FP2'`, `'FP3'` - Free Practice Sessions
- `'S'` - Sprint Race (where applicable)

## 🏗️ Project Structure

```
f1-driver-replay/
│
├── f1_driver_tracker.py    # Main application file
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── LICENSE                # MIT License
├── .gitignore            # Git ignore rules
└── cache/                # FastF1 data cache (auto-created)
```

## 🔧 Technical Details

### Data Processing

- **Session Loading**: Fetches telemetry data using FastF1 API
- **Lap Selection**: Identifies fastest lap for each driver
- **Synchronization**: Interpolates all drivers to a common timeline
- **Pre-computation**: Calculates cumulative distances for performance optimization

### Performance Optimizations

- Pre-calculated cumulative distances for gap calculations
- Efficient numpy interpolation
- Optimized frame updates with blit=False for stability
- Persistent caching system to avoid re-downloading data

### Gap Calculation (Ghost Mode)

The system calculates real-time gaps using:
- Distance differential between drivers
- Average speed conversion (km/h to m/s)
- Dynamic updates at each frame

## 📊 Example Races

Try these interesting sessions:

```python
# Monaco 2023 Qualifying
YEAR = 2023
RACE = 'Monaco'
SESSION = 'Q'

# Silverstone 2023 Race
YEAR = 2023
RACE = 'Silverstone'
SESSION = 'R'

# Spa 2023 Qualifying
YEAR = 2023
RACE = 'Spa'
SESSION = 'Q'
```

## 🐛 Troubleshooting

### Cache Issues

If you encounter data loading problems:
```bash
# Delete the cache folder
rm -rf cache/
```

### Memory Issues

For longer sessions or many drivers:
- Reduce `NUM_DRIVERS`
- Lower `FPS` to 60 or 30
- Close other applications

### Missing Data

Some sessions may not have complete telemetry data. Try:
- Different sessions from the same race weekend
- More recent races (better data quality)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastF1** - For providing the excellent F1 data API
- **Formula 1®** - For the incredible sport and data
- **The F1 community** - For inspiration and support

## 📧 Contact

**Maahir Kadia** - AI/ML Student | [LinkedIn](https://linkedin.com/in/maahir-kadia) | [GitHub](https://github.com/Maahirrrr)

Project Link: [https://github.com/Maahirrrr/F1-driver-replay](https://github.com/Maahirrrr/F1-driver-replay)

---

⭐ **If you found this project helpful, please consider giving it a star!**

---

*Note: This project is for educational purposes. All F1 data is provided by FastF1 and is subject to their terms of use.*
