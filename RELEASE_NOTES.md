# Release v1.0.0 - "First Stable Release"

## 🎉 What's New

### ✨ Features
- **Smart Fan Detection**: Automatically categorizes GPU, CPU, Chassis, and Other fans with intelligent labeling
- **Enhanced Metric Naming**: All metrics use `rigbeat_` prefix for better organization
- **Improved Fan Numbering**: Regex-based number extraction from sensor names (e.g., "GPU Fan #12" → `gpu_fan_12`)
- **Advanced Logging**: File logging, debug modes, and enhanced troubleshooting
- **Fan Testing Tool**: `test_fans.py` script for diagnosing fan detection issues
- **Mobile-Optimized Dashboard**: Grafana dashboard designed for iPad Pro and mobile viewing
- **Windows Service Support**: Complete service installation with `install_service.py`
- **Configuration Examples**: Prometheus config and alerting rules included

### 🐛 Bug Fixes
- Fixed CPU detection logic bug that caused AMD Ryzen CPUs to show as "Unknown"
- Improved fan detection with Prometheus-compliant label sanitization
- Added safety checks for missing WMI attributes
- Enhanced error handling for malformed sensor data
- Better hardware type detection with multiple pattern matching

### 📚 Documentation
- Comprehensive `FAN_SUPPORT.md` with troubleshooting guide
- Updated README with actual installation methods
- Enhanced Prometheus configuration examples
- Complete Grafana dashboard optimization guide
- Windows batch install script with validation

## 📦 Installation

### Quick Install (Windows) - Recommended

1. **Download** the latest release from GitHub
2. **Extract** to a folder
3. **Install LibreHardwareMonitor** from [releases](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
   - Run as Administrator
   - Enable WMI in Options (required!)
4. **Run** `install_script.bat` as Administrator
5. **Test** fan detection: `python test_fans.py`
6. **Start** the service: `net start Rigbeat`

### Manual Installation

```bash
# Clone or download the repository
git clone https://github.com/yourusername/rigbeat.git
cd rigbeat

# Install dependencies
pip install -r requirements.txt

# Test installation
python test_fans.py

# Run manually
python hardware_exporter.py --debug --logfile rigbeat.log
```

## 📊 Metrics Available

Visit `http://localhost:9182/metrics` to see:

- `rigbeat_cpu_temperature_celsius` - CPU temps per sensor
- `rigbeat_gpu_temperature_celsius` - GPU temperature
- `rigbeat_fan_speed_rpm{fan="X", type="Y"}` - All fan speeds with smart categorization
  - `type="gpu"`: Graphics card fans
  - `type="cpu"`: CPU/cooler fans  
  - `type="chassis"`: Case fans
  - `type="other"`: Pumps, unlabeled fans
- `rigbeat_cpu_load_percent` - CPU usage per core
- `rigbeat_gpu_load_percent` - GPU usage
- `rigbeat_memory_used_gb` - System RAM usage
- `rigbeat_system_info` - Hardware information

And more...

## 🎨 Grafana Dashboard

Import the included `grafana_dashboard.json` to get:
- 🌡️ Temperature gauges (color-coded with thresholds)
- 📈 Historical temperature and fan speed graphs
- 💨 Smart fan speed monitoring (all types: GPU/CPU/Chassis/Other)
- 📊 System load and memory indicators
- 📱 Mobile-optimized layout (works on iPad Pro without scrolling)
- 🚨 Ready-to-use alerting examples in comments

## 🔧 Requirements

- Windows 10/11
- Python 3.8+
- LibreHardwareMonitor
- Prometheus (optional, for storage)
- Grafana (optional, for dashboards)

## 🆕 Upgrade Instructions

### From Previous Versions

```bash
# Stop the service
net stop Rigbeat

# Backup your logs (optional)
copy "C:\ProgramData\Rigbeat\service.log" "C:\ProgramData\Rigbeat\service.log.backup"

# Download new release and run install script
# This will update files in C:\ProgramData\Rigbeat\

# Start the service
net start Rigbeat

# Verify with new fan detection
cd "C:\ProgramData\Rigbeat"
python test_fans.py
```

## ⚠️ Known Issues

- Some motherboards may not expose all sensors via WMI (this is hardware-dependent)
- Fans that don't match GPU/CPU/Chassis patterns are categorized as "other" type (this is normal)
- LibreHardwareMonitor must be running with WMI enabled before starting Rigbeat
- Service installation requires Administrator rights
- Prometheus-client and WMI dependencies are Windows-specific

## 🙏 Contributors

- @vegardhw - Initial release

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/vegardhw/rigbeat/blob/main/CHANGELOG.md) for detailed changes.

## 💬 Support

- 🐛 [Report bugs](https://github.com/vegardhw/rigbeat/issues)
- 💡 [Request features](https://github.com/vegardhw/rigbeat/issues)
- 💬 [Discussions](https://github.com/vegardhw/rigbeat/discussions)

---

**Assets:**
- `rigbeat-v1.0.0.zip` - Complete source code with all scripts
- `grafana_dashboard.json` - Mobile-optimized Grafana dashboard
- `prometheus_config.txt` - Example Prometheus configuration with alerts
- `install_script.bat` - Automated Windows installer
- `FAN_SUPPORT.md` - Comprehensive fan troubleshooting guide