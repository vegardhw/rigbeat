# Installation

Get Rigbeat up and running on your Windows system in just a few minutes.

## Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.8+**
- **Administrator rights** (required for hardware sensor access)

## Quick Install (Recommended)

### 1. Download Rigbeat

Get the latest release from GitHub:

::: tip Download Options
- **[Latest Release](https://github.com/vegardhw/rigbeat/releases)** (recommended)
- **Clone**: `git clone https://github.com/vegardhw/rigbeat.git`
:::

### 2. Install LibreHardwareMonitor

LibreHardwareMonitor provides access to your hardware sensors via HTTP API or WMI.

1. **Download** from [LibreHardwareMonitor Releases](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
2. **Extract** the ZIP file
3. **Run** `LibreHardwareMonitor.exe` as Administrator
4. **Enable HTTP Server** (recommended for best performance):
   - Go to Options → Web Server
   - Check "Enable Web Server" ✅ (port 8085)
5. **Fallback**: Enable WMI if HTTP not preferred: Options → Check "WMI" ✅
6. **Optional**: Enable "Run On Windows Startup" for automatic startup

::: tip Performance Recommendation
**HTTP Server** provides ~90% better performance than WMI. Enable it in Options → Web Server for optimal Rigbeat performance.
:::

::: warning Firewall Configuration
If using Prometheus on a different machine, configure Windows Firewall:
```powershell
netsh advfirewall firewall add rule name="Rigbeat" dir=in action=allow protocol=TCP localport=9182
```
:::

### 3. Run Installation Script

Right-click `Install-Rigbeat.bat` and select **"Run as Administrator"**

The script will:
- ✅ Install Python dependencies
- ✅ Set up Windows service
- ✅ Copy files to `C:\ProgramData\Rigbeat\`
- ✅ Test fan detection
- ✅ Start the service

### 4. Verify Installation

Open your browser and visit: **http://localhost:9182/metrics**

You should see Prometheus metrics like:
```prometheus
rigbeat_cpu_temperature_celsius{sensor="CPU Package"} 45.0
rigbeat_gpu_temperature_celsius{gpu="NVIDIA GeForce RTX 4080"} 52.0
rigbeat_fan_speed_rpm{fan="gpu_fan_1", type="gpu"} 1850.0
```

## Manual Installation

If you prefer manual setup or want more control:

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test Fan Detection

```bash
python test_fans.py
```

This will show you what fans and sensors are detected on your system.

### 3. Run the Exporter

```bash
# Simple run (HTTP API automatically detected)
python hardware_exporter.py

# With debug logging to see connection method
python hardware_exporter.py --debug --logfile rigbeat.log

# Custom port and interval
python hardware_exporter.py --port 9183 --interval 5

# Custom LibreHardwareMonitor HTTP API location
python hardware_exporter.py --http-host 192.168.1.100 --http-port 8085
```

**Debug Output Examples:**
```
🚀 Connected to LibreHardwareMonitor HTTP API at http://localhost:8085
✅ Performance optimized mode enabled (HTTP API)
```
or
```
⚠️ Connected via WMI fallback (higher CPU usage)  
💡 Enable LibreHardwareMonitor HTTP server for better performance
```

### 4. Install as Windows Service

```bash
# Install service
python service_manager.py install

# Start service
net start Rigbeat

# Check status
net query Rigbeat
```

## Service Features

The Windows service provides:

- **🛡️ Robust Startup**: Starts successfully even without LibreHardwareMonitor
- **☁️ Demo Mode**: Runs on VMs/test systems for deployment validation
- **🔧 Proper COM Initialization**: Fixed WMI access issues in service context
- **📝 Enhanced Logging**: Logs to `C:\ProgramData\Rigbeat\service.log`
- **🔄 Auto-Detection**: Switches to full monitoring when hardware becomes available

## What's Next?

- **[First Run →](/getting-started/first-run)** - Test your installation
- **[Grafana Setup →](/guide/grafana)** - Create beautiful dashboards
- **[Prometheus Config →](/guide/prometheus)** - Set up metrics collection

## Troubleshooting

If you encounter issues during installation:

- **Service won't start**: Check [Service Troubleshooting](/troubleshooting/service)
- **No fans detected**: See [Fan Detection Guide](/troubleshooting/fans)
- **Demo mode only**: Ensure LibreHardwareMonitor is running with WMI enabled