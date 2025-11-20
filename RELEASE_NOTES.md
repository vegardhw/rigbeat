# Release v0.1.1

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

### 🎯 User Experience Improvements
- **Intuitive File Naming**: Renamed installation files for better clarity
  - `install_script.bat` → `Install-Rigbeat.bat` (clear primary installer)
  - `install.ps1` → `Install-Rigbeat.ps1` (modern PowerShell installer)
  - `install_service.py` → `service-manager.py` (dedicated service management)
- **Modern PowerShell Installer**: Enhanced with winget Python installation, colored output, and progress bars
- **Optimized Update Interval**: Changed default from 2 seconds to 15 seconds for better efficiency and Prometheus alignment
- **Professional Documentation**: Migrated from single README to comprehensive VitePress documentation site

### 📚 Documentation & Developer Experience
- **VitePress Documentation Site**: Modern, mobile-optimized documentation with search functionality and Mermaid diagram support
- **Structured Fan Documentation**: Split comprehensive fan support into logical sections (detection, troubleshooting, API reference)
- **Interactive Architecture Diagrams**: Mermaid diagrams showing data flow from hardware to dashboards
- **Comprehensive Troubleshooting**: Dedicated sections for fan issues, service problems, and common solutions
- **GitHub Pages Integration**: Automated documentation deployment with professional presentation

### ⚡ Performance & Architecture
- **Efficient Update Intervals**: Default 15-second polling aligns with Prometheus scrape intervals (configurable down to 2s for gaming)
- **Reduced Resource Usage**: Eliminated unnecessary CPU cycles from over-frequent polling
- **Better Prometheus Integration**: Aligned client and scrape intervals for optimal data collection
- **Winget Python Installation**: Automatic Python dependency management via Windows Package Manager

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

### Documentation Architecture
- **Fan Detection Guide**: Comprehensive explanation of smart categorization
- **Prometheus & Grafana Integration**: Complete setup and query examples
- **Troubleshooting Guides**: Separate sections for common issues vs fan-specific problems
- **API Reference**: Detailed metrics documentation with examples
- **Interactive Diagrams**: Mermaid-powered architecture visualization

### Enhanced ReliabilityInstallation
- Simplified installation workflow with intuitive file naming
- Modern PowerShell installer with automatic dependency management
- Clear separation between installation (`Install-Rigbeat.*`) and service management (`service-manager.py`)
- Enhanced error messages and user guidance throughout installation process

### Documentation Architecture
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
python service-manager.py remove

# Update files (download new release)
# Copy new files to C:\ProgramData\Rigbeat\

# Install updated service
python service-manager.py install

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

### Performance Improvements
- **Optimized Polling**: 15-second default interval reduces CPU usage by ~87% compared to 2-second polling
- **Configurable for Gaming**: Use `--interval 2` for real-time monitoring during gaming sessions
- **Prometheus Alignment**: Eliminates waste from updates between scrapes
- **PowerShell Character Encoding**: Fixed bullet point issues in Windows PowerShell execution

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

# Release v0.1.0 - Initial Release

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
4. **Run** `Install-Rigbeat.bat` as Administrator (improved installer with modern PowerShell backend)
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
- `rigbeat-v0.1.1.zip` - Complete source code with intuitive file naming
- `grafana_dashboard.json` - Mobile-optimized Grafana dashboard
- `prometheus_config.yml` - Example Prometheus configuration with alerts
- `Install-Rigbeat.bat` - Modern Windows installer with PowerShell backend
- `Install-Rigbeat.ps1` - Enhanced PowerShell installer with winget support
- `service-manager.py` - Dedicated service management tool
- **Documentation**: [https://vegardhw.github.io/rigbeat/](https://vegardhw.github.io/rigbeat/) - Comprehensive VitePress documentation site