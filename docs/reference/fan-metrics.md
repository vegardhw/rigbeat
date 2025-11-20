# Fan Metrics API

Complete reference for fan monitoring metrics and labels.

## Metric Definition

```prometheus
rigbeat_fan_speed_rpm{fan="LABEL", type="TYPE"} VALUE
```

**Metric Name**: `rigbeat_fan_speed_rpm`
**Type**: Gauge
**Unit**: Revolutions per minute (RPM)
**Description**: Current fan speed reading from hardware sensors

## Labels

### `fan` Label
Unique identifier for each physical fan, automatically generated from sensor names.

| Pattern | Generated Label | Example Sensor Name |
|---------|----------------|-------------------|
| GPU fans | `gpu_fan`, `gpu_fan_N` | "GPU Fan", "GPU Fan #1" |
| CPU fans | `cpu_fan`, `cpu_fan_N` | "CPU Fan", "CPU Fan 2" |  
| Chassis fans | `chassis_fan_N` | "Chassis Fan #1", "CHA1" |
| Other fans | `sanitized_name` | "Pump Fan" → `pump_fan` |

### `type` Label  
Categorical grouping for fan purpose and location.

| Type | Description | Use Cases |
|------|------------|-----------|
| `gpu` | Graphics card cooling fans | Gaming temperature alerts, GPU thermal management |
| `cpu` | Processor cooling fans | System stability monitoring, CPU thermal alerts |
| `chassis` | Case airflow fans (intake/exhaust) | Airflow balance, dust monitoring |  
| `other` | AIO pumps, custom cooling | Specialized cooling system monitoring |

## Automatic Label Generation

### Number Extraction
The system uses regex patterns to extract numbers from sensor names:

```python
numbers = re.findall(r'\d+', sensor_name)
```

**Examples**:
- `"GPU Fan #12"` → `gpu_fan_12`
- `"Chassis Fan 3"` → `chassis_fan_3`
- `"CHA_FAN_2"` → `chassis_fan_2`
- `"Fan Header 5"` → `chassis_fan_5` (if detected as chassis)

### Name Sanitization
For fans that don't match standard patterns, names are sanitized for Prometheus compatibility:

```python
# Convert to lowercase, replace invalid chars with underscore
fan_label = re.sub(r'[^a-zA-Z0-9_]', '_', sensor_name.lower())
# Remove duplicate underscores
fan_label = re.sub(r'_+', '_', fan_label).strip('_')
```

**Examples**:
- `"AIO Pump"` → `aio_pump`
- `"Custom Fan #1"` → `custom_fan_1`
- `"Water-Pump"` → `water_pump`

## Value Ranges

| Condition | Typical RPM Range | Interpretation |
|-----------|------------------|----------------|
| Stopped | 0 - 100 | Fan failure or disabled |
| Idle | 500 - 800 | Low system load |
| Normal | 800 - 1500 | Standard operation |
| Gaming | 1500 - 2500 | High performance cooling |
| Maximum | 2500+ | Extreme cooling or stress |

## Example Outputs

### Gaming PC with Custom Loop
```prometheus
# GPU fans (high-end gaming card)
rigbeat_fan_speed_rpm{fan="gpu_fan_1", type="gpu"} 2100.0
rigbeat_fan_speed_rpm{fan="gpu_fan_2", type="gpu"} 2050.0

# CPU air cooler
rigbeat_fan_speed_rpm{fan="cpu_fan", type="cpu"} 1650.0

# Case airflow (intake front, exhaust rear/top)  
rigbeat_fan_speed_rpm{fan="chassis_fan_1", type="chassis"} 1400.0
rigbeat_fan_speed_rpm{fan="chassis_fan_2", type="chassis"} 1380.0
rigbeat_fan_speed_rpm{fan="chassis_fan_3", type="chassis"} 1200.0

# Custom water cooling
rigbeat_fan_speed_rpm{fan="pump_fan", type="other"} 3200.0
rigbeat_fan_speed_rpm{fan="radiator_fan_1", type="other"} 1800.0
rigbeat_fan_speed_rpm{fan="radiator_fan_2", type="other"} 1790.0
```

### Workstation Setup  
```prometheus
# Workstation graphics card
rigbeat_fan_speed_rpm{fan="gpu_fan", type="gpu"} 1200.0

# CPU tower cooler
rigbeat_fan_speed_rpm{fan="cpu_fan", type="cpu"} 900.0

# Conservative case cooling
rigbeat_fan_speed_rpm{fan="chassis_fan_1", type="chassis"} 800.0
rigbeat_fan_speed_rpm{fan="chassis_fan_2", type="chassis"} 750.0
```

### Compact ITX Build
```prometheus
# Single GPU fan
rigbeat_fan_speed_rpm{fan="gpu_fan", type="gpu"} 2800.0

# Low-profile CPU cooler  
rigbeat_fan_speed_rpm{fan="cpu_fan", type="cpu"} 2200.0

# Single exhaust fan
rigbeat_fan_speed_rpm{fan="chassis_fan_1", type="chassis"} 1600.0
```

## Query Patterns

### Basic Queries

**All Fans**
```promql
rigbeat_fan_speed_rpm
```

**By Type**  
```promql
rigbeat_fan_speed_rpm{type="gpu"}
rigbeat_fan_speed_rpm{type="cpu"}  
rigbeat_fan_speed_rpm{type="chassis"}
```

**Specific Fan**
```promql
rigbeat_fan_speed_rpm{fan="gpu_fan_1"}
```

### Monitoring Queries

**Fan Health Check**
```promql
# Fans below minimum operational speed
rigbeat_fan_speed_rpm < 500

# Critical fans stopped
rigbeat_fan_speed_rpm{type=~"gpu|cpu"} < 100

# Any fan stopped
rigbeat_fan_speed_rpm == 0
```

**Performance Analysis**
```promql  
# Average fan speed by type
avg by (type) (rigbeat_fan_speed_rpm)

# Maximum fan speed in system
max(rigbeat_fan_speed_rpm)

# Fan speed variance (detect failing fans)
stddev by (fan) (rigbeat_fan_speed_rpm[5m])
```

### Alerting Queries

**Critical System Protection**
```promql
# GPU thermal protection
rigbeat_fan_speed_rpm{type="gpu"} < 1000 and rigbeat_gpu_temperature_celsius > 75

# CPU thermal protection  
rigbeat_fan_speed_rpm{type="cpu"} < 800 and rigbeat_cpu_temperature_celsius > 70
```

**Maintenance Alerts**
```promql
# Possible dust buildup (high fan speed, low load)
rigbeat_fan_speed_rpm > 2000 and rigbeat_cpu_load_percent{core="total"} < 30

# Unbalanced airflow
abs(
  avg(rigbeat_fan_speed_rpm{fan=~"chassis_fan_[12]"}) -
  avg(rigbeat_fan_speed_rpm{fan=~"chassis_fan_[34]"})
) > 400
```

## Integration Notes

### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'rigbeat-fans'
    static_configs:
      - targets: ['localhost:9182']
    scrape_interval: 15s
    metrics_path: '/metrics'
    params:
      collect[]: ['rigbeat_fan_speed_rpm']
```

### Grafana Variables
Create dynamic dashboards using template variables:

**Fan Type Variable**
```
label_values(rigbeat_fan_speed_rpm, type)
```

**Specific Fans Variable** 
```
label_values(rigbeat_fan_speed_rpm{type="$fan_type"}, fan)
```

**Dynamic Fan Query**
```
rigbeat_fan_speed_rpm{type="$fan_type", fan="$fan_name"}
```

## Data Retention Considerations

### Storage Requirements
Fan metrics are lightweight but numerous:

- **Single fan**: ~1KB per day at 15s intervals  
- **Gaming PC (8 fans)**: ~8KB per day
- **Enterprise (20+ fans)**: ~20KB per day

### Downsampling Strategy
For long-term storage:

```yaml
# Prometheus recording rules
groups:
  - name: rigbeat_fans_downsampled
    interval: 5m
    rules:
      # Hourly averages for long-term trends
      - record: rigbeat:fan_speed_rpm:1h_avg
        expr: avg_over_time(rigbeat_fan_speed_rpm[1h])
        
      # Daily peak speeds for capacity planning
      - record: rigbeat:fan_speed_rpm:1d_max  
        expr: max_over_time(rigbeat_fan_speed_rpm[1d])
```

This reference covers all aspects of fan metrics for effective monitoring and alerting.