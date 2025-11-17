# Release v1.0.0 - "First Stable Release"

## 🎉 What's New

### ✨ Features
- **Enhanced Fan Detection**: Now properly categorizes GPU, CPU, and Chassis fans (CHA1-4)
- **Real-time Monitoring**: 2-second update interval for near-instant metrics
- **Beautiful Grafana Dashboard**: Pre-configured with temperature gauges and fan speed panels
- **Windows Service Support**: Auto-start on boot with `--install-service`

### 🐛 Bug Fixes
- Fixed issue where chassis fans weren't properly detected
- Improved WMI connection error handling
- Better logging for troubleshooting

### 📚 Documentation
- Added comprehensive setup guide
- Created fan detection reference
- VS Code development documentation

## 📦 Installation

### Quick Install (Windows)

1. **Download** `rigbeat-1.0.0-portable.zip`
2. **Extract** to a folder
3. **Install LibreHardwareMonitor** from [releases](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
4. **Run** `install.bat` as Administrator
5. **Start** the service: `net start rigbeat`

### Install via pip

```bash
pip install rigbeat
rigbeat --port 9182
```

### From Source

```bash
git clone https://github.com/vegardhw/rigbeat.git
cd rigbeat
pip install -r requirements.txt
python hardware_exporter.py
```

## 📊 Metrics Available

Visit `http://localhost:9182/metrics` to see:

- `cpu_temperature_celsius` - CPU temps per core
- `gpu_temperature_celsius` - GPU temperature
- `fan_speed_rpm{type="gpu|cpu|chassis"}` - All fan speeds
- `cpu_load_percent` - CPU usage
- `gpu_load_percent` - GPU usage
- And more...

## 🎨 Grafana Dashboard

Import the included `grafana-dashboard.json` to get:
- 🌡️ Temperature gauges (color-coded)
- 📈 Historical graphs
- 💨 Fan speed monitoring
- 📊 System load indicators

## 🔧 Requirements

- Windows 10/11
- Python 3.8+
- LibreHardwareMonitor
- Prometheus (optional, for storage)
- Grafana (optional, for dashboards)

## 🆕 Upgrade Instructions

### From v0.x.x

```bash
# Stop the service
net stop rigbeat

# Update
pip install --upgrade rigbeat

# Restart
net start rigbeat
```

## ⚠️ Known Issues

- Some older motherboards may not expose all fan sensors
- GPU fans on AMD cards may show as "other" type (working on fix)
- Windows Service installer requires Administrator rights

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
- `rigbeat-1.0.0.whl` - Python package
- `rigbeat-1.0.0.tar.gz` - Source distribution
- `rigbeat-1.0.0-portable.zip` - Portable version (no install needed)