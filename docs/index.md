---
layout: home

hero:
  name: "Rigbeat"
  text: "Windows Hardware Monitoring"
  tagline: "Prometheus exporter for PC hardware metrics with beautiful Grafana dashboards"
  image:
    src: /logo.svg
    alt: Rigbeat
  actions:
    - theme: brand
      text: Get Started
      link: /getting-started/installation
    - theme: alt
      text: View on GitHub
      link: https://github.com/vegardhw/rigbeat

features:
  - icon: 🌡️
    title: Temperature Monitoring
    details: Monitor CPU and GPU temperatures per core/sensor with intelligent labeling
  - icon: 💨
    title: Smart Fan Detection
    details: Auto-categorizes GPU, CPU, Chassis, and other fans with intelligent naming
  - icon: 📊
    title: System Metrics
    details: Track CPU/GPU loads, clock speeds, and memory usage in real-time
  - icon: 📱
    title: Mobile Optimized
    details: Beautiful Grafana dashboards that work perfectly on tablets and phones
  - icon: 🛡️
    title: Robust Service
    details: Windows service with graceful handling, demo mode, and proper COM initialization
  - icon: ⚡
    title: Low Overhead
    details: Under 50MB RAM usage with minimal CPU impact on your gaming performance
---

## What is Rigbeat?

Rigbeat is a lightweight **Prometheus exporter** designed specifically for Windows gaming PCs and workstations. It monitors your hardware in real-time and exposes metrics that can be visualized in beautiful **Grafana dashboards**.

Perfect for:
- 🎮 **Gaming PCs** - Monitor temps during intense sessions
- 💼 **Workstations** - Track hardware performance during heavy workloads
- 🏠 **Home Labs** - Keep tabs on your hardware health
- 🔧 **System Builders** - Validate cooling performance

## Dashboard Preview

![Dashboard Preview](images/dashboard-preview.png)
*📱 Mobile-optimized Grafana dashboard showing real-time hardware monitoring*

## Quick Example

```prometheus
# CPU Temperatures
rigbeat_cpu_temperature_celsius{sensor="CPU Package"} 45.0
rigbeat_cpu_temperature_celsius{sensor="Core Complex 1"} 42.0

# GPU Metrics
rigbeat_gpu_temperature_celsius{gpu="NVIDIA GeForce RTX 4080"} 52.0
rigbeat_gpu_load_percent{gpu="nvidia_geforce_rtx_4080",type="core"} 85.0

# Smart Fan Detection
rigbeat_fan_speed_rpm{fan="gpu_fan_1",type="gpu"} 1850.0
rigbeat_fan_speed_rpm{fan="cpu_fan",type="cpu"} 1450.0
rigbeat_fan_speed_rpm{fan="chassis_fan_1",type="chassis"} 1200.0
```

## Why Choose Rigbeat?

- **🎯 Gaming Focused**: Designed specifically for Windows gaming hardware
- **🧠 Smart Detection**: Automatically identifies and categorizes your fans
- **📱 Mobile First**: Dashboard works beautifully on your phone/tablet
- **🛡️ Production Ready**: Robust Windows service with proper error handling
- **☁️ VM Compatible**: Test deployment on virtual machines with demo mode
- **📈 Historical Data**: Track thermal trends and identify issues over time

[Get Started →](/getting-started/installation)
