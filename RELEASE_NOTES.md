# Release v0.1.2

## ⚡ New Features

### 🔋 CPU & GPU Power Monitoring
- **CPU Power Consumption**: Track CPU package power draw in real-time
  - Metric: `rigbeat_cpu_power_watts{sensor="CPU Package"}`
  - Shows total processor power consumption in Watts
  - Essential for performance tuning and efficiency analysis

- **GPU Power Consumption**: Monitor graphics card power usage
  - Metric: `rigbeat_gpu_power_watts{gpu="gpu_name"}`
  - Real-time GPU power draw monitoring
  - Critical for gaming performance optimization and power limit analysis

### 📊 Enhanced Monitoring Capabilities
- **Performance per Watt**: Calculate efficiency ratios for both CPU and GPU
- **Power Trend Analysis**: Track power consumption patterns during different workloads
- **Thermal Correlation**: Analyze relationship between power draw and temperatures
- **Gaming Optimization**: Monitor power limits during intensive gaming sessions

## 🎯 Why Power Monitoring Matters

### For Gaming PCs
- **Power Limit Detection**: Know when your GPU is hitting power limits
- **Efficiency Tuning**: Optimize performance per watt for better acoustics
- **PSU Sizing**: Validate your power supply is adequate for your system
- **Undervolting Validation**: Measure power savings from undervolting

### For Workstations
- **Workload Analysis**: Understand power consumption of different tasks
- **Cost Optimization**: Track power costs for always-on systems
- **Thermal Management**: Correlate power spikes with temperature increases
- **Hardware Validation**: Ensure components operate within specifications

### for System Builders
- **Component Testing**: Validate power consumption against specifications
- **Build Optimization**: Balance performance and power efficiency
- **Client Validation**: Prove power efficiency claims to customers

## 🔧 Technical Implementation

### Power Sensor Detection
The exporter now detects LibreHardwareMonitor's "Power" sensor type and specifically targets "Package" sensors:

```python
# CPU Package Power (from CPU > Powers > Package)
rigbeat_cpu_power_watts{sensor="CPU Package"} 65.2

# GPU Package Power (from GPU > Powers > GPU Package)
rigbeat_gpu_power_watts{gpu="nvidia_geforce_rtx_4080"} 285.7
```

### Sensor Compatibility
- **CPU**: Works with Intel and AMD processors that expose package power
- **GPU**: Compatible with NVIDIA and AMD graphics cards
- **Requirements**: LibreHardwareMonitor must detect power sensors (hardware dependent)

## 📊 New Dashboard Panels

### Power Consumption Gauges
```promql
# Current CPU power draw
rigbeat_cpu_power_watts

# Current GPU power draw
rigbeat_gpu_power_watts
```

### Efficiency Calculations
```promql
# CPU Performance per Watt
rigbeat_cpu_load_percent{core="total"} / rigbeat_cpu_power_watts

# GPU Performance per Watt
rigbeat_gpu_load_percent{type="core"} / rigbeat_gpu_power_watts
```

### Power vs Temperature Correlation
```promql
# Power/Temperature relationship visualization
rigbeat_cpu_power_watts and rigbeat_cpu_temperature_celsius
rigbeat_gpu_power_watts and rigbeat_gpu_temperature_celsius
```

## ⚙️ Configuration & Setup

### No Configuration Required
Power monitoring works automatically when:
1. LibreHardwareMonitor is running with WMI enabled
2. Hardware supports power sensors (most modern CPUs/GPUs)
3. Rigbeat service detects the "Package" power sensors

### Verification
Check power metrics are working:
```bash
# Visit metrics endpoint
curl http://localhost:9182/metrics | grep power

# Expected output:
# rigbeat_cpu_power_watts{sensor="CPU Package"} 45.2
# rigbeat_gpu_power_watts{gpu="nvidia_geforce_rtx_4080"} 180.5
```

## 🚀 Upgrade Instructions

### From v0.1.1

```bash
# Stop the service
net stop Rigbeat

# Download v0.1.2 release files
# Extract and copy to C:\ProgramData\Rigbeat\

# Restart service (no reinstall needed)
net start Rigbeat

# Verify power metrics are available
curl http://localhost:9182/metrics | findstr power
```

### For Development/Testing
```bash
# Update files in development directory
git pull origin main

# Test power detection
python hardware_exporter.py --debug

# Check for power sensor detection in logs
```

## 📈 Updated Grafana Dashboard

The included `grafana_dashboard.json` now features:

### New Panels
- **📊 Power Consumption Overview**: Real-time CPU and GPU power draw
- **⚡ Efficiency Metrics**: Performance per Watt calculations
- **📈 Power History**: Historical power consumption trends
- **🔗 Power vs Load Correlation**: Understand power scaling with workload

### Enhanced Mobile Experience
- Power gauges optimized for tablet/phone viewing
- Quick-glance efficiency indicators
- Color-coded power limit warnings

## 🎮 Gaming Use Cases

### Real-Time Power Monitoring
Monitor power consumption while gaming to:
- Detect GPU power limit throttling
- Optimize settings for efficiency vs performance
- Validate cooling adequacy under load
- Track power consumption across different games

### Example Gaming Dashboard View
```
┌─────────────────────┬─────────────────────┐
│ 🔥 CPU: 65°C | 45W  │ 🎮 GPU: 72°C | 280W │
├─────────────────────┴─────────────────────┤
│ ⚡ Total System Power: ~325W              │
│ 📊 Efficiency: 2.1 FPS/W                  │
│ 🚨 GPU Power Limit: Not Reached           │
└─────────────────────────────────────────────┘
```

## ⚠️ Hardware Requirements

### Power Sensor Support
- **CPU**: Modern Intel (8th gen+) and AMD (Ryzen+) processors
- **GPU**: Most NVIDIA (GTX 10 series+) and AMD (RX 400+) graphics cards
- **Motherboard**: Must expose power sensors via hardware monitoring

### Troubleshooting
If power metrics don't appear:
1. Verify LibreHardwareMonitor shows "Powers" section for CPU/GPU
2. Check hardware monitoring is enabled in BIOS/UEFI
3. Ensure latest chipset and GPU drivers installed
4. Some OEM systems may have limited sensor exposure

## 📝 Complete Changelog

### Added
- CPU power consumption monitoring (`rigbeat_cpu_power_watts`)
- GPU power consumption monitoring (`rigbeat_gpu_power_watts`)
- Power sensor detection for "Package" type sensors
- Enhanced documentation with power monitoring examples

### Improved
- Hardware monitoring capabilities now include power management
- Better correlation between thermal and power metrics
- Enhanced debugging output includes power sensor detection

### Technical
- Added power sensor type detection in `update_metrics()`
- New Prometheus gauge metrics for CPU and GPU power
- Updated metric documentation and examples

## 🎯 What's Next (v0.1.3+)

### Planned Power Features
- **Individual GPU Power Rails**: 8-pin connector power monitoring
- **CPU Core Power**: Per-core power consumption (if supported)
- **Memory Power**: RAM power consumption monitoring
- **Power Alerts**: Configurable alerts for power limit scenarios

### Enhanced Analytics
- **Power Efficiency Trends**: Long-term efficiency analysis
- **Cost Calculation**: Electricity cost estimation based on usage
- **Comparative Analysis**: Power consumption vs other systems

---

## 💬 Support & Feedback

Power monitoring is hardware-dependent. If you experience issues:

- 🐛 **Report Issues**: [GitHub Issues](https://github.com/vegardhw/rigbeat/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/vegardhw/rigbeat/discussions)
- 📖 **Documentation**: [https://vegardhw.github.io/rigbeat/](https://vegardhw.github.io/rigbeat/)

**Power monitoring makes Rigbeat even more valuable for system optimization and efficiency analysis!** ⚡