# 🖥️ Rigbeat

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Prometheus](https://img.shields.io/badge/Prometheus-compatible-orange.svg)](https://prometheus.io/)

A lightweight Prometheus exporter for Windows that monitors PC hardware metrics in real-time. Perfect for gaming PCs, workstations, and anyone who wants beautiful Grafana dashboards showing CPU/GPU temperatures, fan speeds, and system loads.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Dashboard+Preview+Coming+Soon)

## ✨ Features

- 🌡️ **CPU Temperature** - Per-core temperature monitoring
- 🎮 **GPU Metrics** - Temperature, load, memory usage, clock speeds (NVIDIA/AMD)
- 💨 **Fan Speeds** - All detected fans (GPU, CPU, Chassis 1-4)
- 📊 **System Load** - CPU/GPU utilization per core
- ⚡ **Clock Speeds** - Real-time CPU/GPU frequencies
- 🎯 **Low Overhead** - <50MB RAM, minimal CPU usage
- 📱 **Mobile Friendly** - Access from any device with a browser
- 🔄 **Auto-refresh** - 1-5 second update intervals
- 📈 **Historical Data** - Track trends, identify thermal issues

## 🚀 Quick Start

### Prerequisites

- Windows 10/11
- Python 3.8 or higher
- Administrator rights (for sensor access)
- Prometheus & Grafana (or use Docker setup below)

### Installation

1. **Install LibreHardwareMonitor** (provides sensor access)
   ```bash
   # Download from: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
   # Extract and run LibreHardwareMonitor.exe as Administrator
   # Enable: Options → "Run On Windows Startup" (optional)
   ```

2. **Install the exporter**
   ```bash
   pip install rigbeat
   ```

3. **Run the exporter**
   ```bash
   # Simple run
   rigbeat

   # Custom port
   rigbeat --port 9182

   # Custom update interval (in seconds)
   rigbeat --interval 2
   ```

4. **Verify it's working**
   ```bash
   # Visit in browser
   http://localhost:9182/metrics
   
   # You should see Prometheus metrics like:
   # cpu_temperature_celsius{sensor="CPU Package"} 45.0
   # gpu_temperature_celsius{gpu="NVIDIA GeForce RTX 4080"} 52.0
   # fan_speed_rpm{fan="cpu_fan"} 1450.0
   ```

### Install as Windows Service (Optional)

```bash
# Install service (runs on startup)
rigbeat --install-service

# Start service
net start rigbeat

# Stop service
net stop rigbeat

# Uninstall service
rigbeat --uninstall-service
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
  - job_name: 'rigbeat'
    scrape_interval: 2s
    static_configs:
      - targets: ['localhost:9182']
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
| `cpu_temperature_celsius` | CPU temperature | `sensor` |
| `cpu_load_percent` | CPU load per core | `core` |
| `cpu_clock_mhz` | CPU clock speed | `core` |
| `gpu_temperature_celsius` | GPU temperature | `gpu` |
| `gpu_load_percent` | GPU load | `gpu`, `type` |
| `gpu_memory_used_mb` | GPU memory usage | `gpu` |
| `gpu_clock_mhz` | GPU clock speed | `gpu`, `type` |
| `fan_speed_rpm` | Fan speed | `fan` |
| `memory_used_gb` | System RAM used | - |
| `memory_available_gb` | System RAM available | - |
| `system_info` | System information | `cpu`, `gpu`, `motherboard` |

## 🔧 Configuration

### Command Line Options

```bash
rigbeat --help

Options:
  --port PORT           Port to expose metrics (default: 9182)
  --interval INTERVAL   Update interval in seconds (default: 2)
  --install-service     Install as Windows service
  --uninstall-service   Uninstall Windows service
  --debug               Enable debug logging
```

### Environment Variables

```bash
# Set custom port
set PC_HARDWARE_MONITOR_PORT=9182

# Set update interval
set PC_HARDWARE_MONITOR_INTERVAL=2
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

### No sensors showing up

- Some motherboards don't expose all sensors
- Try running LibreHardwareMonitor first to see what's detected
- Update motherboard BIOS/chipset drivers

### High CPU usage

- Increase `--interval` to 5 or 10 seconds
- Some hardware has slow sensor access

### Grafana shows "No data"

- Check Prometheus is scraping: http://localhost:9090/targets
- Verify metrics endpoint works: http://localhost:9182/metrics
- Check Prometheus datasource in Grafana settings

## 🛠️ Development

### Building from source

```bash
# Clone repository
git clone https://github.com/yourusername/rigbeat.git
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

- 🐛 [Report bugs](https://github.com/yourusername/rigbeat/issues)
- 💡 [Request features](https://github.com/yourusername/rigbeat/issues)
- 💬 [Discussions](https://github.com/yourusername/rigbeat/discussions)

---

**Made with ❤️ for the PC gaming community**