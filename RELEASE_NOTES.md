# Release v0.1.1 - "Robustness & Documentation Update"

## 🔧 Bug Fixes & Improvements

### ⚙️ Service Reliability
- **Fixed Windows Service COM Initialization**: Resolved "OLE error 0x8004100e" by adding proper `pythoncom.CoInitialize()` calls
- **Graceful Hardware Monitor Handling**: Service no longer crashes when LibreHardwareMonitor is unavailable
- **Demo Mode**: Service runs successfully on VMs and test systems without hardware monitoring
- **Enhanced Error Logging**: Better error messages and troubleshooting information in service logs

### 🔧 CPU Detection Improvements
- **Enhanced CPU Detection**: Added comprehensive support for Intel CPUs alongside existing AMD support
- **Future-Proof Patterns**: Detection now covers Intel Core, Xeon, AMD Ryzen, Threadripper, EPYC series
- **Robust Fallbacks**: Multiple detection patterns ensure compatibility with various hardware configurations

### 📚 Documentation & Developer Experience
- **VitePress Documentation Site**: Modern, mobile-optimized documentation with search functionality
- **Comprehensive Guides**: Installation, troubleshooting, configuration, and development documentation
- **GitHub Pages Integration**: Automated documentation deployment
- **Improved README**: Clean landing page with clear value proposition

### 🔍 Testing & Development
- **VM Compatibility**: Can now test service deployment on virtual machines without errors
- **Improved Error Handling**: Hardware detection failures are logged as warnings instead of fatal errors
- **Better Service Lifecycle**: Proper COM cleanup and status reporting throughout service lifecycle
- **Enhanced Debugging**: Service logs show clear distinction between demo mode and hardware monitoring mode

## 🆕 What's New

### Demo Mode Features
- Service starts successfully without LibreHardwareMonitor
- Prometheus endpoint remains functional at `http://localhost:9182/metrics`
- Shows demo system information ("Demo CPU", "Demo GPU", "Demo Board")
- Automatic detection when real hardware monitoring becomes available
- Perfect for CI/CD testing and service deployment validation

### Enhanced Reliability
- **Zero-downtime testing**: Test service deployment without requiring actual hardware
- **Better error recovery**: Service handles hardware disconnect/reconnect gracefully
- **Improved diagnostics**: Clear logs indicate whether running in demo or hardware mode
- **Service robustness**: Handles COM initialization failures and WMI connection issues

## 🔄 Upgrade Instructions

### From v0.1.0

```bash
# Stop the service
net stop Rigbeat

# Remove old service
python service_manager.py remove

# Update files (download new release)
# Copy new files to C:\ProgramData\Rigbeat\

# Install updated service
python service_manager.py install

# Start service
net start Rigbeat

# Verify service status
net query Rigbeat

# Check logs for demo/hardware mode
type "C:\ProgramData\Rigbeat\service.log"
```

## ⚙️ Technical Details

### Fixed Issues
- **COM Error 0x8004100e**: Added `pythoncom.CoInitialize()` before WMI operations
- **Service Crash on Missing LHM**: Hardware monitor failures now handled gracefully
- **Duplicate Prometheus Metrics**: Resolved registry collision between service and exporter
- **WMI Connection in Service Context**: Proper initialization for Windows service environment

### Code Improvements
- Added `self.connected` flag to track hardware monitor state
- Improved error handling in `get_sensors()` and `get_system_info()` methods
- Enhanced service logging with mode detection (demo vs hardware)
- Better separation of concerns between hardware access and service lifecycle

## 📊 Metrics in Demo Mode

When running in demo mode, the service exposes:
- `rigbeat_system_info{cpu="Demo CPU", gpu="Demo GPU", motherboard="Demo Board"}`
- Prometheus endpoint remains functional for testing scrape configuration
- No sensor metrics are collected (expected behavior)
- Service health can be monitored via Prometheus

## ✅ Validation

To test the improvements:

1. **VM Testing**: Install on a VM without LibreHardwareMonitor
2. **Service Status**: Verify service starts without errors
3. **Demo Mode**: Check logs show "Demo mode" messages
4. **Metrics Endpoint**: Confirm `http://localhost:9182/metrics` responds
5. **Hardware Mode**: Install LibreHardwareMonitor to switch to full monitoring

## 🎯 Roadmap to v1.0.0

Planned features for the v1.0.0 major release:

### 🔮 Upcoming Features
- **System Tray Application**: GUI for service management and quick status
- **Enhanced Dashboard**: Additional panels and customization options
- **Alert Templates**: Pre-configured alerting rules for common scenarios
- **Multi-PC Support**: Centralized monitoring for multiple systems
- **Performance Optimizations**: Reduced resource usage and faster startup

### 📈 Stability Goals
- **Extensive Hardware Testing**: Validation across diverse hardware configurations
- **Production Hardening**: Enhanced error recovery and edge case handling
- **Documentation Completion**: Full guides for all features and use cases
- **Community Feedback**: Integration of user suggestions and bug reports

---

# Release v0.1.0 - "Initial Release"

## 🎉 What's New

### ✨ Features
- **Smart Fan Detection**: Automatically categorizes GPU, CPU, Chassis, and Other fans with intelligent labeling
- **Enhanced Metric Naming**: All metrics use `rigbeat_` prefix for better organization
- **Improved Fan Numbering**: Regex-based number extraction from sensor names (e.g., "GPU Fan #12" → `gpu_fan_12`)
- **Advanced Logging**: File logging, debug modes, and enhanced troubleshooting
- **Fan Testing Tool**: `test_fans.py` script for diagnosing fan detection issues
- **Mobile-Optimized Dashboard**: Grafana dashboard designed for iPad Pro and mobile viewing
- **Windows Service Support**: Complete service installation with `service_manager.py`
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
4. **Run** `Install-Rigbeat.bat` as Administrator
5. **Test** fan detection: `python test_fans.py`
6. **Start** the service: `net start Rigbeat`

### Manual Installation

```bash
# Clone or download the repository
git clone https://github.com/vegardhw/rigbeat.git
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
  - `type="cpu"`: CPU/cooler fan
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
- LibreHardwareMonitor must be running with WMI enabled for full hardware monitoring (demo mode available without it)
- Service installation requires Administrator rights
- Prometheus-client and WMI dependencies are Windows-specific
- Demo mode only provides basic system info - no actual sensor metrics (by design)
- Service switches to demo mode if LibreHardwareMonitor stops while service is running

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
- `Install-Rigbeat.bat` - Automated Windows installer
- `FAN_SUPPORT.md` - Comprehensive fan troubleshooting guide