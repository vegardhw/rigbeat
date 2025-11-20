# Metrics API Reference

Complete reference for all Rigbeat Prometheus metrics.

## Metric Naming Convention

All Rigbeat metrics use the `rigbeat_` prefix for easy identification and filtering.

## Temperature Metrics

### `rigbeat_cpu_temperature_celsius`
**Type**: Gauge  
**Description**: CPU temperature in Celsius  
**Labels**: 
- `sensor` - Temperature sensor identifier

**Example Values**:
```prometheus
rigbeat_cpu_temperature_celsius{sensor="CPU Package"} 45.0
rigbeat_cpu_temperature_celsius{sensor="Core Complex 1"} 42.0  
rigbeat_cpu_temperature_celsius{sensor="Core Complex 2"} 44.0
rigbeat_cpu_temperature_celsius{sensor="CPU Die"} 43.0
```

**Sensor Types**:
- `CPU Package` - Overall CPU temperature (Intel/AMD)
- `Core Complex N` - AMD Ryzen CCX temperatures  
- `CPU Die` - Die temperature sensor
- `CPU CCD N` - Chiplet temperatures (AMD)

### `rigbeat_gpu_temperature_celsius`
**Type**: Gauge  
**Description**: GPU temperature in Celsius  
**Labels**:
- `gpu` - GPU device identifier

**Example Values**:
```prometheus
rigbeat_gpu_temperature_celsius{gpu="nvidia_geforce_rtx_4080"} 52.0
rigbeat_gpu_temperature_celsius{gpu="amd_radeon_rx_7900_xt"} 68.0
```

## Power Metrics

### `rigbeat_cpu_power_watts`
**Type**: Gauge  
**Description**: CPU power consumption in Watts  
**Labels**:
- `sensor` - Power sensor identifier

**Example Values**:
```prometheus
rigbeat_cpu_power_watts{sensor="CPU Package"} 65.2
```

**Sensor Types**:
- `CPU Package` - Total CPU package power consumption (Intel/AMD)

**Use Cases**:
- Performance per Watt calculations
- Power efficiency analysis  
- Thermal correlation with power draw
- System power budgeting

### `rigbeat_gpu_power_watts`
**Type**: Gauge  
**Description**: GPU power consumption in Watts  
**Labels**:
- `gpu` - GPU device identifier

**Example Values**:
```prometheus
rigbeat_gpu_power_watts{gpu="nvidia_geforce_rtx_4080"} 285.7
rigbeat_gpu_power_watts{gpu="amd_radeon_rx_7900_xt"} 315.2
```

**Use Cases**:
- Gaming power consumption monitoring
- Power limit detection and analysis
- Undervolting efficiency validation
- PSU capacity planning

## Performance Metrics

### `rigbeat_cpu_load_percent`
**Type**: Gauge  
**Description**: CPU load percentage  
**Labels**:
- `core` - CPU core identifier

**Example Values**:
```prometheus
rigbeat_cpu_load_percent{core="total"} 45.5
rigbeat_cpu_load_percent{core="core1"} 78.2
rigbeat_cpu_load_percent{core="core2"} 34.1
rigbeat_cpu_load_percent{core="core3"} 12.8
```

### `rigbeat_cpu_clock_mhz`
**Type**: Gauge  
**Description**: CPU clock speed in MHz  
**Labels**:
- `core` - CPU core identifier

**Example Values**:
```prometheus
rigbeat_cpu_clock_mhz{core="total"} 4200.0
rigbeat_cpu_clock_mhz{core="core1"} 4350.0
rigbeat_cpu_clock_mhz{core="core2"} 4100.0
```

### `rigbeat_gpu_load_percent`
**Type**: Gauge  
**Description**: GPU load percentage  
**Labels**:
- `gpu` - GPU device identifier
- `type` - Load type (core, memory, other)

**Example Values**:
```prometheus
rigbeat_gpu_load_percent{gpu="nvidia_geforce_rtx_4080",type="core"} 85.0
rigbeat_gpu_load_percent{gpu="nvidia_geforce_rtx_4080",type="memory"} 78.5
```

### `rigbeat_gpu_clock_mhz`
**Type**: Gauge  
**Description**: GPU clock speed in MHz  
**Labels**:
- `gpu` - GPU device identifier  
- `type` - Clock type (core, memory, other)

**Example Values**:
```prometheus
rigbeat_gpu_clock_mhz{gpu="nvidia_geforce_rtx_4080",type="core"} 2610.0
rigbeat_gpu_clock_mhz{gpu="nvidia_geforce_rtx_4080",type="memory"} 1313.0
```

## Fan Metrics

### `rigbeat_fan_speed_rpm`
**Type**: Gauge  
**Description**: Fan speed in RPM with intelligent categorization  
**Labels**:
- `fan` - Fan identifier (auto-generated from sensor name)
- `type` - Fan category (gpu, cpu, chassis, other)

**Example Values**:
```prometheus
# GPU Fans
rigbeat_fan_speed_rpm{fan="gpu_fan_1",type="gpu"} 1850.0
rigbeat_fan_speed_rpm{fan="gpu_fan_2",type="gpu"} 1820.0

# CPU Fans  
rigbeat_fan_speed_rpm{fan="cpu_fan",type="cpu"} 1450.0

# Chassis Fans
rigbeat_fan_speed_rpm{fan="chassis_fan_1",type="chassis"} 1200.0
rigbeat_fan_speed_rpm{fan="chassis_fan_2",type="chassis"} 1150.0

# Other (Pumps, etc.)
rigbeat_fan_speed_rpm{fan="aio_pump",type="other"} 2500.0
```

**Fan Types**:
- `gpu` - Graphics card fans
- `cpu` - CPU cooler fans
- `chassis` - Case fans (intake/exhaust)  
- `other` - Pumps, custom fans, unidentified

## Memory Metrics

### `rigbeat_memory_used_gb`
**Type**: Gauge  
**Description**: System memory used in GB

**Example Value**:
```prometheus
rigbeat_memory_used_gb 16.2
```

### `rigbeat_memory_available_gb`
**Type**: Gauge  
**Description**: System memory available in GB

**Example Value**:
```prometheus
rigbeat_memory_available_gb 15.8
```

### `rigbeat_gpu_memory_used_mb`
**Type**: Gauge  
**Description**: GPU memory used in MB  
**Labels**:
- `gpu` - GPU device identifier

**Example Value**:
```prometheus
rigbeat_gpu_memory_used_mb{gpu="nvidia_geforce_rtx_4080"} 8567.0
```

## System Information

### `rigbeat_system_info`
**Type**: Info  
**Description**: System hardware information  
**Labels**:
- `cpu` - Detected CPU model
- `gpu` - Detected GPU model  
- `motherboard` - Detected motherboard

**Example Value**:
```prometheus
rigbeat_system_info{cpu="AMD Ryzen 5 5600X",gpu="NVIDIA GeForce RTX 4080",motherboard="ASUS ROG STRIX B550-F"} 1
```

**Demo Mode Values**:
```prometheus
rigbeat_system_info{cpu="Demo CPU",gpu="Demo GPU",motherboard="Demo Board"} 1
```

## Query Examples

### Useful Prometheus Queries

**Average CPU temperature across all sensors**:
```promql
avg(rigbeat_cpu_temperature_celsius)
```

**Highest fan speed by type**:  
```promql
max(rigbeat_fan_speed_rpm) by (type)
```

**GPU utilization and temperature correlation**:
```promql
rigbeat_gpu_load_percent{type="core"} and rigbeat_gpu_temperature_celsius
```

**All chassis fans running below 800 RPM**:
```promql
rigbeat_fan_speed_rpm{type="chassis"} < 800
```

**CPU cores running above 4GHz**:
```promql
rigbeat_cpu_clock_mhz > 4000
```

**System memory usage percentage**:
```promql
(rigbeat_memory_used_gb / (rigbeat_memory_used_gb + rigbeat_memory_available_gb)) * 100
```

**CPU Performance per Watt**:
```promql
rigbeat_cpu_load_percent{core="total"} / rigbeat_cpu_power_watts
```

**GPU Performance per Watt**:
```promql
rigbeat_gpu_load_percent{type="core"} / rigbeat_gpu_power_watts
```

**Total system power consumption**:
```promql
rigbeat_cpu_power_watts + rigbeat_gpu_power_watts
```

**Power vs Temperature correlation**:
```promql
rigbeat_cpu_power_watts and rigbeat_cpu_temperature_celsius
```

## Alerting Rules

### Temperature Alerts

**High CPU temperature**:
```yaml
- alert: HighCPUTemp  
  expr: rigbeat_cpu_temperature_celsius > 85
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "CPU temperature high: {{ $labels.sensor }}"
    description: "CPU {{ $labels.sensor }} is running at {{ $value }}°C"
```

**GPU temperature critical**:
```yaml
- alert: GPUTempCritical
  expr: rigbeat_gpu_temperature_celsius > 90
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "GPU overheating: {{ $labels.gpu }}"
```

### Fan Alerts

**Fan stopped or running slow**:
```yaml
- alert: FanSlow
  expr: rigbeat_fan_speed_rpm < 300
  for: 30s
  labels:
    severity: warning
  annotations:
    summary: "Fan {{ $labels.fan }} running slowly"
    description: "{{ $labels.type }} fan {{ $labels.fan }} at {{ $value }} RPM"
```

**GPU fan failure**:
```yaml
- alert: GPUFanFailure
  expr: rigbeat_fan_speed_rpm{type="gpu"} < 100
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "GPU fan failure detected"
    description: "GPU fan {{ $labels.fan }} has stopped - check hardware"
```

### Power Alerts

**High CPU power consumption**:
```yaml
- alert: HighCPUPower
  expr: rigbeat_cpu_power_watts > 150
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "CPU power consumption high"
    description: "CPU drawing {{ $value }}W - check thermal throttling"
```

**GPU power limit reached**:
```yaml
- alert: GPUPowerLimit
  expr: rigbeat_gpu_power_watts > 350
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "GPU approaching power limit"
    description: "GPU at {{ $value }}W - performance may be limited"
```

**System power consumption high**:
```yaml
- alert: HighSystemPower
  expr: rigbeat_cpu_power_watts + rigbeat_gpu_power_watts > 500
  for: 3m
  labels:
    severity: info
  annotations:
    summary: "System power draw high"
    description: "Total CPU+GPU power: {{ $value }}W"
```

## Data Types

### Gauge Metrics
All Rigbeat metrics are **Gauge** type (except `rigbeat_system_info` which is **Info**):
- Values can increase or decrease
- Represent instantaneous measurements  
- Perfect for temperatures, speeds, percentages
- Last value is significant

### Label Cardinality
- **Low cardinality**: Designed to be Prometheus-friendly
- **Predictable labels**: Fan names normalized and consistent
- **No timestamps**: Uses Prometheus timestamps
- **Static info**: System information rarely changes

### Update Frequency
- **Default**: 2 seconds
- **Configurable**: 1-60 seconds via `--interval`
- **Service**: Consistent interval maintained
- **Demo mode**: Updates continue (with demo values)