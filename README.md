# 🖥️ Rigbeat

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Prometheus](https://img.shields.io/badge/Prometheus-compatible-orange.svg)](https://prometheus.io/)

A lightweight Prometheus exporter for Windows that monitors PC hardware metrics in real-time. Perfect for gaming PCs, workstations, and anyone who wants beautiful Grafana dashboards showing CPU/GPU temperatures, fan speeds, and system loads.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Dashboard+Preview+Coming+Soon)

## ✨ Features

- 🌡️ **CPU Temperature** - Per-core temperature monitoring
- 🎮 **GPU Metrics** - Temperature, load, memory usage, clock speeds (NVIDIA/AMD)
- 💨 **Smart Fan Detection** - Auto-categorizes GPU, CPU, Chassis, and other fans
- 📊 **System Load** - CPU/GPU utilization per core
- ⚡ **Clock Speeds** - Real-time CPU/GPU frequencies
- 📝 **Enhanced Logging** - File logging and debug modes
- 🔧 **Fan Testing** - Built-in fan detection diagnostics
- 🎯 **Low Overhead** - <50MB RAM, minimal CPU usage
- 📱 **Mobile Friendly** - Optimized for tablets and phones
- 🔄 **Auto-refresh** - 1-5 second update intervals
- 📈 **Historical Data** - Track trends, identify thermal issues

## 🚀 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.8 or higher
- Administrator rights (for sensor access)
- Prometheus & Grafana (or use Docker setup below)

### Installation

#### Option 1: Quick Install Script (Recommended)

1. **Download Rigbeat**
   ```bash
   # Download the latest release from:
   # https://github.com/vegardhw/rigbeat/releases
   # Or clone: git clone https://github.com/vegardhw/rigbeat.git
   ```

2. **Install LibreHardwareMonitor** (provides sensor access)
   ```bash
   # Download from: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
   # Extract and run LibreHardwareMonitor.exe as Administrator
   # Enable: Options → "WMI" (required!)
   # Enable: Options → "Run On Windows Startup" (optional)
   ```

3. **Run install script**
   ```bash
   # Right-click install_script.bat → "Run as Administrator"
   # This will:
   # - Install Python dependencies
   # - Set up Windows service
   # - Copy files to C:\ProgramData\Rigbeat\
   ```

#### Option 2: Manual Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test fan detection** (recommended)
   ```bash
   python test_fans.py
   ```

3. **Run the exporter**
   ```bash
   # Simple run
   python hardware_exporter.py

   # With debug logging
   python hardware_exporter.py --debug

   # Save logs to file
   python hardware_exporter.py --logfile rigbeat.log

   # Custom port and interval
   python hardware_exporter.py --port 9183 --interval 5
   ```

4. **Verify it's working**
   ```bash
   # Visit in browser
   http://localhost:9182/metrics
   
   # You should see Prometheus metrics like:
   # rigbeat_cpu_temperature_celsius{sensor="CPU Package"} 45.0
   # rigbeat_gpu_temperature_celsius{gpu="NVIDIA GeForce RTX 4080"} 52.0
   # rigbeat_fan_speed_rpm{fan="gpu_fan_1", type="gpu"} 1850.0
   # rigbeat_fan_speed_rpm{fan="cpu_fan", type="cpu"} 1450.0
   # rigbeat_fan_speed_rpm{fan="chassis_fan_1", type="chassis"} 1200.0
   ```

### Install as Windows Service

The install script automatically sets this up, but you can also do it manually:

```bash
# Install service (from the Rigbeat directory)
cd "C:\ProgramData\Rigbeat"
python install_service.py install

# Start service
net start Rigbeat

# Stop service
net stop Rigbeat

# Remove service
python install_service.py remove
```

## 📊 Grafana Dashboard Setup

### Option 1: Import from Grafana.com

1. Open Grafana → Dashboards → Import
2. Enter Dashboard ID: `[TBD - will be published]`
3. Select your Prometheus datasource
4. Click Import

### Option 2: Import JSON file

1. Copy `grafana-dashboard.json` from this repo
2. Grafana → Dashboards → Import → Upload JSON file
3. Select your Prometheus datasource

### Option 3: Manual Setup

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'rigbeat-hardware'
    scrape_interval: 2s
    static_configs:
      - targets: ['localhost:9182']
        labels:
          instance: 'gaming-pc'
          environment: 'home'
          service: 'rigbeat'
```

Restart Prometheus and the metrics will be available in Grafana.

## 🐋 Docker Setup (Bonus)

If you don't have Prometheus/Grafana yet, use this Docker Compose setup:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

volumes:
  prometheus-data:
  grafana-data:
```

Start with: `docker-compose up -d`

Access Grafana at http://localhost:3000 (admin/admin)

## 📝 Available Metrics

| Metric | Description | Labels |
|--------|-------------|--------|
| `rigbeat_cpu_temperature_celsius` | CPU temperature | `sensor` |
| `rigbeat_cpu_load_percent` | CPU load per core | `core` |
| `rigbeat_cpu_clock_mhz` | CPU clock speed | `core` |
| `rigbeat_gpu_temperature_celsius` | GPU temperature | `gpu` |
| `rigbeat_gpu_load_percent` | GPU load | `gpu`, `type` |
| `rigbeat_gpu_memory_used_mb` | GPU memory usage | `gpu` |
| `rigbeat_gpu_clock_mhz` | GPU clock speed | `gpu`, `type` |
| `rigbeat_fan_speed_rpm` | Fan speed with smart categorization | `fan`, `type` |
| `rigbeat_memory_used_gb` | System RAM used | - |
| `rigbeat_memory_available_gb` | System RAM available | - |
| `rigbeat_system_info` | System information | `cpu`, `gpu`, `motherboard` |

### Fan Types
- `type="gpu"`: Graphics card fans (e.g., `gpu_fan_1`, `gpu_fan_2`)
- `type="cpu"`: CPU/cooler fans (e.g., `cpu_fan`, `cpu_fan_1`)
- `type="chassis"`: Case fans (e.g., `chassis_fan_1`, `chassis_fan_2`)
- `type="other"`: Pumps, custom fans (e.g., `pump_fan`, `fan_2`)

## 🔧 Configuration

### Command Line Options

```bash
python hardware_exporter.py --help

Options:
  --port PORT           Port to expose metrics (default: 9182)
  --interval INTERVAL   Update interval in seconds (default: 2)
  --logfile PATH        Save logs to file (e.g., --logfile rigbeat.log)
  --debug               Enable debug logging
```

### Testing and Diagnostics

```bash
# Test fan detection (shows all detected fans)
python test_fans.py

# Run with debug output
python hardware_exporter.py --debug

# Save detailed logs for troubleshooting
python hardware_exporter.py --debug --logfile debug.log
```

## 🎨 Dashboard Features

- **Temperature Gauges**: Color-coded (green/yellow/red) CPU/GPU temps
- **Time Series Graphs**: Historical temp data for last 15m/1h/24h
- **Fan Speed Monitoring**: Real-time RPM for all fans
- **Load Indicators**: CPU/GPU utilization percentages
- **Memory Stats**: RAM usage tracking
- **Mobile Optimized**: Responsive design for phones/tablets

## 🤔 Troubleshooting

### "Failed to connect to LibreHardwareMonitor WMI"

- Make sure LibreHardwareMonitor is running
- Run LibreHardwareMonitor as Administrator
- Check: Options → Enable WMI is checked
- Restart LibreHardwareMonitor after enabling WMI

### No sensors/fans showing up

- Run `python test_fans.py` to see what's detected
- Check LibreHardwareMonitor shows the sensors
- Some motherboards don't expose all sensors via WMI
- Update motherboard BIOS/chipset drivers

### Fans not categorized correctly

- Run `python test_fans.py` to see actual sensor names
- Fans not matching GPU/CPU/Chassis patterns are labeled as "other" type
- This is normal for some motherboards (e.g., "Fan #1", "Fan #2")
- Check `FAN_SUPPORT.md` for customization options

### High CPU usage

- Increase `--interval` to 5 or 10 seconds
- Some hardware has slow sensor access
- Use `--debug` to identify slow sensors

### Service logs

- Windows service logs: `C:\ProgramData\Rigbeat\service.log`
- Manual run logs: Use `--logfile` option
- Debug output: Use `--debug` flag

### Grafana shows "No data"

- Check Prometheus is scraping: http://localhost:9090/targets
- Verify metrics endpoint works: http://localhost:9182/metrics
- Check Prometheus datasource in Grafana settings
- Ensure job name matches: `rigbeat-hardware`

## 🛠️ Development

### Building from source

```bash
# Clone repository
git clone https://github.com/vegardhw/rigbeat.git
cd rigbeat

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python hardware_exporter.py --debug
```

### Running tests

```bash
pytest tests/
```

### Contributing

Pull requests welcome! Please:
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation

## 📜 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) - Hardware sensor access
- [Prometheus](https://prometheus.io/) - Metrics collection
- [Grafana](https://grafana.com/) - Dashboard visualization

## ⭐ Star History

If you find this useful, consider giving it a star! It helps others discover the project.

## 📞 Support

- 🐛 [Report bugs](https://github.com/vegardhw/rigbeat/issues)
- 💡 [Request features](https://github.com/vegardhw/rigbeat/issues)
- 💬 [Discussions](https://github.com/vegardhw/rigbeat/discussions)

---

**Made with ❤️ for the PC gaming community**