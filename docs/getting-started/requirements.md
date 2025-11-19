# Requirements

Rigbeat is designed for Windows systems and requires specific components to access hardware sensors.

## System Requirements

### Operating System
- **Windows 10** (version 1903 or later)
- **Windows 11** (all versions)
- **Windows Server 2019/2022** (for server monitoring)

### Hardware Architecture
- **64-bit (x64)** - Required
- **32-bit (x86)** - Not supported

### Python Version
- **Python 3.8** - Minimum supported
- **Python 3.9** - Recommended
- **Python 3.10** - Recommended  
- **Python 3.11** - Supported
- **Python 3.12** - Supported

::: tip Python Installation
Download Python from [python.org](https://python.org/downloads/) and ensure "Add to PATH" is checked during installation.
:::

## Hardware Requirements

### Supported CPUs
- **Intel**: Core series, Xeon, most modern Intel processors
- **AMD**: Ryzen, Threadripper, EPYC, FX series
- **Others**: Most x64 processors with temperature sensors

### Supported GPUs  
- **NVIDIA**: GeForce, RTX, GTX, Quadro, Tesla series
- **AMD**: Radeon RX, Radeon Pro, FirePro series
- **Intel**: Arc series (limited support)

### Motherboard Compatibility
- **Modern chipsets**: Most motherboards from 2015+
- **Sensor support**: Requires temperature/fan sensors accessible via WMI
- **BIOS settings**: Some sensors may need to be enabled in BIOS

## Software Dependencies

### Core Dependencies
These are automatically installed via `pip install -r requirements.txt`:

```txt
prometheus-client>=0.19.0    # Prometheus metrics
wmi>=1.5.1                   # Windows Management Instrumentation
pywin32>=306                 # Windows API access
```

### LibreHardwareMonitor
**Required** - Provides hardware sensor access:
- **Version**: 0.9.0 or later
- **Download**: [GitHub Releases](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
- **Requirements**: Must run as Administrator with WMI enabled

::: warning Critical Requirement
LibreHardwareMonitor is essential for hardware monitoring. Without it, Rigbeat runs in demo mode only.
:::

## Permissions

### Administrator Rights
Required for:
- Installing Windows service
- Accessing hardware sensors via WMI
- Running LibreHardwareMonitor
- Installing to `C:\ProgramData\Rigbeat\`

### Windows Service Account
The service runs under:
- **Account**: Local System
- **Privileges**: Full system access for hardware monitoring
- **Network**: Local network access only (for Prometheus endpoint)

## Network Requirements

### Ports
- **9182** (default) - Prometheus metrics endpoint
- **Configurable** - Can be changed via `--port` argument

### Firewall
- **Inbound**: Allow port 9182 for Prometheus scraping
- **Outbound**: No external connections required
- **Local**: Service communicates with LibreHardwareMonitor via WMI

## Optional Components

### Prometheus
For metrics storage and querying:
- **Version**: 2.0 or later
- **Configuration**: Scrape interval 2-10 seconds recommended
- **Storage**: Local or remote Prometheus instance

### Grafana
For dashboards and visualization:
- **Version**: 8.0 or later  
- **Plugins**: No additional plugins required
- **Dashboard**: Import provided `grafana_dashboard.json`

### Docker (Optional)
For containerized Prometheus/Grafana:
- **Docker Desktop**: For Windows
- **Docker Compose**: Included setup available

## Performance Impact

### System Resources
- **RAM**: ~30-50MB typical usage
- **CPU**: <1% on modern systems
- **Disk**: Minimal (logs only)
- **Network**: <1KB/s metrics traffic

### Gaming Performance
- **No measurable impact** on gaming FPS
- **Non-blocking**: Monitoring runs independently  
- **Low priority**: Service runs at normal priority

## Compatibility Notes

### Virtualization
- **VMware**: Demo mode only (no hardware sensors)
- **VirtualBox**: Demo mode only  
- **Hyper-V**: Demo mode only
- **Physical hardware**: Full functionality

### Remote Desktop
- **RDP**: Service continues running when disconnected
- **Monitoring**: Works normally during remote sessions
- **LibreHardwareMonitor**: Must be running on physical machine

### Dual Boot
- **Linux**: No impact when booting Linux
- **Multiple Windows**: Each installation needs separate setup
- **Shared storage**: Logs/config are Windows-specific

::: tip Next Steps
Ready to install? Continue to [Installation →](/getting-started/installation)
:::