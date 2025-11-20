# Power Monitoring

Monitor CPU and GPU power consumption for performance optimization and efficiency analysis.

## Overview

Rigbeat tracks power consumption from LibreHardwareMonitor's power sensors, providing real-time insights into your system's energy usage and efficiency.

## Supported Power Metrics

### 🔌 CPU Power Monitoring

**Metric**: `rigbeat_cpu_power_watts{sensor="CPU Package"}`

- **Package Power**: Total processor power consumption
- **Real-time tracking** of power draw changes
- **Essential for** thermal analysis and efficiency tuning

```prometheus
# Example: Intel i7-13700K under load
rigbeat_cpu_power_watts{sensor="CPU Package"} 125.3

# Example: AMD Ryzen 7 7700X gaming
rigbeat_cpu_power_watts{sensor="CPU Package"} 89.7
```

### 🎮 GPU Power Monitoring

**Metric**: `rigbeat_gpu_power_watts{gpu="device_name"}`

- **Graphics card power consumption** monitoring
- **Power limit detection** for performance analysis
- **Critical for gaming** and rendering workloads

```prometheus
# Example: RTX 4080 gaming at 1440p
rigbeat_gpu_power_watts{gpu="nvidia_geforce_rtx_4080"} 285.7

# Example: RX 7900 XT rendering
rigbeat_gpu_power_watts{gpu="amd_radeon_rx_7900_xt"} 315.2
```

## Hardware Requirements

### Power Sensor Support

**Modern Hardware Required**:
- **CPU**: Intel 8th gen+ or AMD Ryzen+ processors
- **GPU**: Most NVIDIA GTX 10 series+ and AMD RX 400+ cards
- **Motherboard**: Must expose power sensors via WMI

**Verification Steps**:
1. Check LibreHardwareMonitor shows "Powers" section
2. Look for "Package" sensors under CPU/GPU
3. Ensure sensors show non-zero values under load

### Compatibility Notes

**Supported Platforms**:
- ✅ Desktop processors (Intel Core, AMD Ryzen)
- ✅ High-end mobile processors (H-series)
- ✅ Discrete graphics cards (gaming/workstation)
- ❌ Basic integrated graphics
- ❌ Some OEM/laptop systems (limited sensor exposure)

## Monitoring Use Cases

### 🎮 Gaming Optimization

**Power Limit Detection**:
```promql
# Alert when GPU hits power limit
rigbeat_gpu_power_watts > 350
```

**Performance per Watt**:
```promql
# GPU efficiency calculation
rigbeat_gpu_load_percent{type="core"} / rigbeat_gpu_power_watts
```

**Thermal Correlation**:
```promql
# Power vs temperature analysis
increase(rigbeat_gpu_power_watts[5m]) and increase(rigbeat_gpu_temperature_celsius[5m])
```

### 💼 Workstation Analysis

**Workload Power Profiling**:
- Monitor power during rendering/encoding
- Identify power-hungry applications
- Optimize settings for efficiency

**Cost Analysis**:
```promql
# Estimate electricity cost (example: $0.12/kWh)
(rigbeat_cpu_power_watts + rigbeat_gpu_power_watts) * 0.12 / 1000
```

### 🔧 System Building

**PSU Sizing Validation**:
```promql
# Peak system power consumption
max_over_time((rigbeat_cpu_power_watts + rigbeat_gpu_power_watts)[1h])
```

**Efficiency Testing**:
- Compare power consumption across different components
- Validate manufacturer specifications
- Test undervolting effectiveness

## Dashboard Integration

### Power Consumption Overview

**Single Stat Panel**:
```json
{
  "targets": [
    {
      "expr": "rigbeat_cpu_power_watts + rigbeat_gpu_power_watts",
      "legendFormat": "Total System Power"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "watt",
      "thresholds": {
        "steps": [
          {"color": "green", "value": 0},
          {"color": "yellow", "value": 300},
          {"color": "red", "value": 500}
        ]
      }
    }
  }
}
```

### Power History Graph

**Time Series Panel**:
```json
{
  "targets": [
    {"expr": "rigbeat_cpu_power_watts", "legendFormat": "CPU"},
    {"expr": "rigbeat_gpu_power_watts", "legendFormat": "GPU"}
  ],
  "yAxes": [
    {
      "label": "Power (Watts)",
      "min": 0
    }
  ]
}
```

### Efficiency Gauge

**Performance per Watt**:
```json
{
  "targets": [
    {
      "expr": "rigbeat_gpu_load_percent{type=\"core\"} / rigbeat_gpu_power_watts",
      "legendFormat": "GPU Efficiency (Load/W)"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "custom": {
        "displayMode": "basic"
      }
    }
  }
}
```

## Alerting Strategies

### Performance Alerts

**GPU Power Limit Warning**:
```yaml
- alert: GPUPowerLimit
  expr: rigbeat_gpu_power_watts > 350
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "GPU approaching power limit"
    description: "GPU at {{ $value }}W - check for power limiting"
```

**High System Power**:
```yaml
- alert: HighSystemPower
  expr: rigbeat_cpu_power_watts + rigbeat_gpu_power_watts > 500
  for: 5m
  labels:
    severity: info
  annotations:
    summary: "System power draw high"
    description: "Total power: {{ $value }}W"
```

### Efficiency Alerts

**Low GPU Efficiency**:
```yaml
- alert: LowGPUEfficiency
  expr: rigbeat_gpu_load_percent{type="core"} / rigbeat_gpu_power_watts < 0.2
  for: 10m
  labels:
    severity: info
  annotations:
    summary: "GPU efficiency low"
    description: "GPU efficiency: {{ $value }} load/watt"
```

## Troubleshooting

### No Power Metrics Appear

**Check LibreHardwareMonitor**:
1. Verify "Powers" section exists in LHM GUI
2. Look for "Package" sensors under CPU/GPU
3. Ensure values change under load

**Hardware Limitations**:
- Some systems don't expose power sensors
- OEM/laptop systems often have limited access
- Integrated graphics rarely support power monitoring

**BIOS Settings**:
- Enable hardware monitoring features
- Check for power management settings
- Update BIOS to latest version

### Incorrect Power Readings

**Sensor Validation**:
- Compare with other monitoring tools (HWiNFO64, etc.)
- Check readings make sense under different loads
- Verify sensors respond to load changes

**Calibration**:
- Power readings are hardware-reported values
- Some variance between monitoring tools is normal
- Focus on relative changes rather than absolute accuracy

### Missing GPU Power

**Driver Requirements**:
- Ensure latest GPU drivers installed
- Some older cards lack power sensor support
- Check manufacturer specifications

**LibreHardwareMonitor Support**:
- Update to latest LHM version
- Verify GPU is detected in LHM
- Some GPU variants have limited sensor support

## Advanced Analysis

### Power Efficiency Trends

**Track efficiency over time**:
```promql
# CPU efficiency trend
rate(rigbeat_cpu_load_percent[5m]) / rate(rigbeat_cpu_power_watts[5m])

# GPU efficiency during gaming
avg_over_time(rigbeat_gpu_load_percent{type="core"}[10m]) / avg_over_time(rigbeat_gpu_power_watts[10m])
```

### Workload Characterization

**Identify power-hungry periods**:
```promql
# High power consumption periods
rigbeat_cpu_power_watts > bool 100 or rigbeat_gpu_power_watts > bool 250
```

### Thermal-Power Correlation

**Analyze thermal efficiency**:
```promql
# Power per degree temperature
rigbeat_gpu_power_watts / rigbeat_gpu_temperature_celsius
```

Power monitoring adds a crucial dimension to system analysis, enabling optimization for performance, efficiency, and cost.