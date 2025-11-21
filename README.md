# 🖥️ Rigbeat

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Prometheus](https://img.shields.io/badge/Prometheus-compatible-orange.svg)](https://prometheus.io/)
[![Documentation](https://img.shields.io/badge/docs-VitePress-blue.svg)](https://vegardhw.github.io/rigbeat/)

<div align="center">
    <img src="docs/logo.svg" alt="Rigbeat Logo" width="200"/>
</div>

**Prometheus exporter for Windows hardware monitoring** - Track your gaming PC's temperatures, fan speeds, and performance with beautiful Grafana dashboards.

> 🎯 **Perfect for gaming PCs, workstations, and home labs**

<!-- DASHBOARD SCREENSHOT PLACEHOLDER - Add your Grafana dashboard screenshot here -->
![Dashboard Preview](https://via.placeholder.com/800x400?text=🎮+Gaming+PC+Dashboard+Screenshot+Coming+Soon)
*📱 Mobile-optimized dashboard showing CPU/GPU temps, fan speeds, and system performance*

## ✨ Key Features

- 🌡️ **Real-time Temperature Monitoring** - CPU/GPU temperatures per core and sensor
- 💨 **Smart Fan Detection** - Auto-categorizes GPU, CPU, chassis, and other fans
- ⚡ **Power Consumption Tracking** - CPU/GPU power draw monitoring for efficiency analysis
- 📊 **Performance Metrics** - CPU/GPU load, clock speeds, memory usage
- 📱 **Mobile-Optimized Dashboard** - Perfect for tablets and phones
- 🛡️ **Robust Windows Service** - Graceful handling with demo mode support
- 🔧 **Low Overhead** - Under 50MB RAM, minimal performance impact

## 🚀 Quick Start

### 1. **Download & Install**
```bash
# Download latest release from GitHub
# https://github.com/vegardhw/rigbeat/releases

# Install LibreHardwareMonitor (required)
# https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases

# Run install script as Administrator
# Right-click Install-Rigbeat.bat → "Run as Administrator"
```

### 2. **Verify Installation**
Visit **http://localhost:9182/metrics** to see your hardware metrics:
```prometheus
rigbeat_cpu_temperature_celsius{sensor="CPU Package"} 45.0
rigbeat_cpu_power_watts{sensor="CPU Package"} 65.2
rigbeat_gpu_temperature_celsius{gpu="nvidia_geforce_rtx_4080"} 52.0
rigbeat_gpu_power_watts{gpu="nvidia_geforce_rtx_4080"} 185.5
rigbeat_fan_speed_rpm{fan="gpu_fan_1",type="gpu"} 1850.0
```

### 3. **Set Up Dashboard**
Import the included Grafana dashboard for beautiful visualizations:

<!-- GRAFANA DASHBOARD INSTRUCTIONS PLACEHOLDER -->
*📊 Complete Grafana setup instructions and dashboard gallery in the documentation*

## 📖 Docs

**[📚 Full Documentation →](https://vegardhw.github.io/rigbeat/)**

| Section | Description |
|---------|-------------|
| **[🚀 Getting Started](https://vegardhw.github.io/rigbeat/getting-started/installation)** | Installation, requirements, first run |
| **[📖 User Guide](https://vegardhw.github.io/rigbeat/guide/overview)** | Hardware setup, Grafana, Prometheus |
| **[🔧 Troubleshooting](https://vegardhw.github.io/rigbeat/troubleshooting/common-issues)** | Common issues and solutions |
| **[📊 Metrics Reference](https://vegardhw.github.io/rigbeat/reference/metrics)** | Complete API documentation |

## 🎯 Why Rigbeat?

| Feature | Benefit |
|---------|---------|
| **🎮 Gaming Focused** | Designed specifically for Windows gaming hardware |
| **🧠 Smart Detection** | Automatically identifies and categorizes your fans |
| **📱 Mobile First** | Dashboard works beautifully on your phone/tablet |

## 📊 What You Get

### Smart Hardware Detection
```prometheus
# Intelligent fan categorization
rigbeat_fan_speed_rpm{fan="gpu_fan_1",type="gpu"} 1850.0      # Graphics card
rigbeat_fan_speed_rpm{fan="cpu_fan",type="cpu"} 1450.0        # CPU cooler
rigbeat_fan_speed_rpm{fan="chassis_fan_1",type="chassis"} 1200.0  # Case fans

# Comprehensive temperature monitoring
rigbeat_cpu_temperature_celsius{sensor="CPU Package"} 45.0
rigbeat_cpu_temperature_celsius{sensor="Core Complex 1"} 42.0
rigbeat_gpu_temperature_celsius{gpu="nvidia_geforce_rtx_4080"} 52.0

# Power consumption tracking
rigbeat_cpu_power_watts{sensor="CPU Package"} 65.2
rigbeat_gpu_power_watts{gpu="nvidia_geforce_rtx_4080"} 185.5

# Performance metrics
rigbeat_cpu_load_percent{core="total"} 45.5
rigbeat_gpu_load_percent{gpu="nvidia_geforce_rtx_4080",type="core"} 85.0
```

### Mobile-Optimized Dashboard
<!-- DASHBOARD FEATURES SCREENSHOT PLACEHOLDER -->
![Dashboard Features](https://via.placeholder.com/600x300?text=📊+Temperature+Gauges+%7C+Fan+RPM+%7C+Performance+Charts)
*🎨 Beautiful temperature gauges, fan monitoring, and performance tracking*

## 💡 Perfect For

- **🎮 Gaming PCs** - Monitor thermals during intense sessions
- **💼 Workstations** - Track performance during heavy workloads
- **🏠 Home Labs** - Keep tabs on 24/7 systems
- **🔧 System Builders** - Validate cooling performance

## 🛠️ Development & Contributing

Rigbeat is open source and welcomes contributions!

- **[🔧 Development Setup](https://vegardhw.github.io/rigbeat/development/building)** - Build from source
- **[🤝 Contributing Guide](https://vegardhw.github.io/rigbeat/development/contributing)** - Help improve Rigbeat
- **[🏗️ Architecture](https://vegardhw.github.io/rigbeat/development/architecture)** - Technical overview

### 🤖 Built with AI Assistance

This project was created through AI-assisted development. Every component - from Windows service architecture to mobile-optimized dashboards - was designed and implemented collaboratively with Claude AI.

## 📜 License & Support

- **License**: MIT - see [LICENSE](LICENSE) file
- **Issues**: [Report bugs or request features](https://github.com/vegardhw/rigbeat/issues)
- **Discussions**: [Community chat and questions](https://github.com/vegardhw/rigbeat/discussions)

## 🙏 Acknowledgments

- **[LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)** - Hardware sensor access
- **[Prometheus](https://prometheus.io/)** - Metrics collection and alerting
- **[Grafana](https://grafana.com/)** - Beautiful dashboard visualization

---

**⭐ Star this project if you find it useful!**

Made with ❤️ for the PC gaming and monitoring community