# Prometheus Queries & Grafana

Learn how to query fan metrics and create effective monitoring dashboards.

## Fan Metrics Format

All fans are exposed using this consistent metric format:

```prometheus
rigbeat_fan_speed_rpm{fan="LABEL", type="TYPE"} VALUE
```

Where:
- **`fan`**: Unique identifier for the specific fan
- **`type`**: Category (`gpu`, `cpu`, `chassis`, `other`)  
- **`VALUE`**: Current RPM reading

## Common Prometheus Queries

### Display All Fans
```promql
rigbeat_fan_speed_rpm
```

### Query by Fan Type

**GPU Fans Only**
```promql
rigbeat_fan_speed_rpm{type="gpu"}
```

**CPU Fans Only** 
```promql
rigbeat_fan_speed_rpm{type="cpu"}
```

**All Chassis Fans**
```promql
rigbeat_fan_speed_rpm{type="chassis"}
```

**Specific Fan**
```promql
rigbeat_fan_speed_rpm{fan="chassis_fan_1"}
```

### Alerting Queries

**Any Fan Below Threshold**
```promql
rigbeat_fan_speed_rpm < 500
```

**GPU Fans Below Gaming Speed**
```promql
rigbeat_fan_speed_rpm{type="gpu"} < 1000
```

**Critical Fans Stopped**
```promql
rigbeat_fan_speed_rpm{type=~"gpu|cpu"} < 100
```

## Grafana Dashboard Setup

### Fan Speed Panel with Color Coding

Create a stat panel with threshold-based colors:

```json
{
  "fieldConfig": {
    "defaults": {
      "thresholds": {
        "steps": [
          {"color": "red", "value": 0},      // Stopped - Critical
          {"color": "yellow", "value": 500}, // Slow - Warning  
          {"color": "green", "value": 1000}, // Normal - Good
          {"color": "blue", "value": 2000}   // High - Gaming
        ]
      },
      "unit": "rpm"
    }
  }
}
```

### Fan Speed Time Series

For trend monitoring, create a time series panel:

**Query**: `rigbeat_fan_speed_rpm`

**Panel Settings**:
- Group by: `{{type}} - {{fan}}`
- Y-axis label: "RPM"  
- Connect null values: true

### Fan Status Overview

Create a stat panel showing fan count by status:

**All Fans Running**
```promql
count(rigbeat_fan_speed_rpm > 100)
```

**Stopped Fans**
```promql
count(rigbeat_fan_speed_rpm < 100)
```

**Critical Fans (GPU/CPU) Running**
```promql
count(rigbeat_fan_speed_rpm{type=~"gpu|cpu"} > 100)
```

## Alerting Rules

### Basic Fan Monitoring

```yaml
groups:
  - name: rigbeat_fans
    rules:
      # Critical fan failure
      - alert: CriticalFanStopped
        expr: rigbeat_fan_speed_rpm{type=~"gpu|cpu"} < 100
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical fan {{ $labels.fan }} has stopped"
          description: "{{ $labels.type }} fan {{ $labels.fan }} RPM: {{ $value }}"

      # Any fan running slow
      - alert: FanRunningLow  
        expr: rigbeat_fan_speed_rpm < 500
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Fan {{ $labels.fan }} running slow"
          description: "{{ $labels.type }} fan {{ $labels.fan }} RPM: {{ $value }}"

      # GPU overheating protection
      - alert: GPUFanLowDuringLoad
        expr: |
          rigbeat_fan_speed_rpm{type="gpu"} < 1000
          and
          rigbeat_gpu_temperature_celsius > 70
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "GPU fan too slow for current temperature"
          description: "GPU fan {{ $labels.fan }} only at {{ $value }} RPM while GPU over 70°C"
```

### Advanced Alerting

**Fan Speed Variance Detection**
```promql
# Alert if fan speed changes drastically (possible failure)
abs(
  rate(rigbeat_fan_speed_rpm[5m]) * 300
) > 500
```

**Chassis Airflow Balance**
```promql
# Alert if intake/exhaust fans are significantly unbalanced
abs(
  avg(rigbeat_fan_speed_rpm{fan=~"chassis_fan_[12]"}) -
  avg(rigbeat_fan_speed_rpm{fan=~"chassis_fan_[34]"})  
) > 300
```

## Dashboard Organization Tips

### 1. Group by Function
Organize panels by fan purpose rather than location:

- **Critical Cooling**: GPU + CPU fans
- **Airflow Management**: Chassis fans  
- **Custom Cooling**: AIO pumps, etc.

### 2. Color Coding by Type
Use consistent colors across panels:

- 🔴 **GPU**: Red/Orange (hottest components)
- 🔵 **CPU**: Blue (processor cooling)
- 🟢 **Chassis**: Green (case airflow)
- 🟡 **Other**: Yellow (custom/misc)

### 3. Mobile-Friendly Layout
Since Rigbeat is designed for gaming PC monitoring:

- Use large, readable fonts
- Single-column layout for phones
- Important fans (GPU/CPU) at top
- Color-coded status indicators

### 4. Contextual Information
Combine fan metrics with related data:

```prometheus
# Fan speed vs temperature correlation
rigbeat_fan_speed_rpm{type="gpu"}
rigbeat_gpu_temperature_celsius

# System load context  
rigbeat_fan_speed_rpm{type="cpu"}
rigbeat_cpu_load_percent{core="total"}
```

## Example Dashboard Structure

```
┌─────────────────────────────────────────────────┐
│ 🔥 Critical Cooling Status                      │
│ GPU: ●●● (1850 RPM) CPU: ●●● (1450 RPM)         │
├─────────────────────────────────────────────────┤
│ 🌡️ Temperatures vs Fan Speed                    │
│ [Time series: temp + fan correlation]          │
├─────────────────────────────────────────────────┤
│ 💨 Chassis Airflow                             │
│ Intake: 1200 RPM | Exhaust: 1100 RPM          │
├─────────────────────────────────────────────────┤
│ 📊 All Fans Overview                           │
│ [Stat grid: all fans with color coding]       │
└─────────────────────────────────────────────────┘
```

This layout prioritizes critical information while providing comprehensive monitoring capabilities.

## Performance Monitoring

### Fan Efficiency Tracking
```promql
# RPM per degree ratio (cooling efficiency)
rigbeat_fan_speed_rpm{type="gpu"} / rigbeat_gpu_temperature_celsius
```

### Power vs Cooling Balance
```promql  
# High fan speed with low load might indicate dust buildup
rigbeat_fan_speed_rpm{type="cpu"} 
and
rigbeat_cpu_load_percent{core="total"} < 20
```

These queries help identify when fans are working harder than expected, potentially indicating maintenance needs.