# Fan Detection & Categories

Rigbeat automatically categorizes your PC's fans into logical groups for easy monitoring and alerting.

## How Fan Detection Works

The exporter scans LibreHardwareMonitor's WMI sensors and automatically categorizes fans based on their sensor names. This smart detection system helps organize your dashboard and makes alerting more targeted.

## Supported Fan Types

### 🎮 GPU Fans
Graphics card cooling fans, typically the most critical for gaming performance.

- **Detection Pattern**: Sensors containing "GPU" or "VGA" 
- **Prometheus Labels**: `gpu_fan`, `gpu_fan_1`, `gpu_fan_2`
- **Type Label**: `gpu`
- **Examples**: "GPU Fan", "GPU Fan #1", "VGA Fan"

### 🔥 CPU Fans  
Processor cooling fans, essential for system stability.

- **Detection Pattern**: Sensors containing "CPU"
- **Prometheus Labels**: `cpu_fan`, `cpu_fan_1`, `cpu_fan_2`
- **Type Label**: `cpu`
- **Examples**: "CPU Fan", "CPU Fan #1", "CPU Fan 2"

### 📦 Chassis Fans
Case fans for airflow - intake and exhaust fans.

- **Detection Pattern**: Sensors containing "CHA", "Chassis", or "Case"
- **Prometheus Labels**: `chassis_fan_1`, `chassis_fan_2` (auto-numbered)
- **Type Label**: `chassis`  
- **Examples**: "CHA1 Fan", "Chassis Fan #1", "Case Fan 2"

### 🔧 Other Fans
AIO pumps, custom cooling solutions, and miscellaneous fans.

- **Detection Pattern**: Any other fan sensors
- **Prometheus Labels**: Sanitized sensor name (Prometheus-compliant)
- **Type Label**: `other`
- **Examples**: "Pump Fan" → `pump_fan`, "AIO Pump" → `aio_pump`

## Smart Numbering

The system automatically extracts numbers from sensor names to create consistent labels:

- `"GPU Fan #12"` → `gpu_fan_12`
- `"Chassis Fan 3"` → `chassis_fan_3` 
- `"CHA_FAN_2"` → `chassis_fan_2`

This ensures each fan gets a unique, predictable identifier for monitoring.

## Testing Fan Detection

Use the included test script to see what fans Rigbeat detects on your system:

```bash
python test_fans.py
```

### Expected Output (Hardware Mode)
```
================================================================================
Rigbeat - Fan Detection Test
================================================================================

✓ Connected to LibreHardwareMonitor WMI

✓ Found 5 fan(s)

────────────────────────────────────────────────────────────────────────────────
GPU Fans:
────────────────────────────────────────────────────────────────────────────────
  ✓ GPU Fan #1                   → gpu_fan_1                1850 RPM
     Parent: /nvidiagpu/0

────────────────────────────────────────────────────────────────────────────────
CPU Fans:  
────────────────────────────────────────────────────────────────────────────────
  ✓ CPU Fan                      → cpu_fan                  1450 RPM
     Parent: /lpc/nct6798d/0

────────────────────────────────────────────────────────────────────────────────
Chassis Fans:
────────────────────────────────────────────────────────────────────────────────
  ✓ Chassis Fan #1               → chassis_fan_1            1200 RPM
     Parent: /lpc/nct6798d/0
  ✓ Chassis Fan #2               → chassis_fan_2            1150 RPM
     Parent: /lpc/nct6798d/0
```

### Demo Mode vs Hardware Mode

**Hardware Mode** (LibreHardwareMonitor running):
- Shows actual detected fans with real RPM values
- Ready for production monitoring

**Demo Mode** (LibreHardwareMonitor not available):
- Service runs successfully for testing deployment  
- No fan metrics collected (by design)
- Perfect for CI/CD testing and VM deployment validation

## Example Gaming PC Setup

A typical gaming PC might have this fan configuration:

```prometheus
# GPU cooling
rigbeat_fan_speed_rpm{fan="gpu_fan_1", type="gpu"} 1850
rigbeat_fan_speed_rpm{fan="gpu_fan_2", type="gpu"} 1820

# CPU cooling  
rigbeat_fan_speed_rpm{fan="cpu_fan", type="cpu"} 1450

# Case airflow
rigbeat_fan_speed_rpm{fan="chassis_fan_1", type="chassis"} 1200  # Front intake
rigbeat_fan_speed_rpm{fan="chassis_fan_2", type="chassis"} 1150  # Front intake
rigbeat_fan_speed_rpm{fan="chassis_fan_3", type="chassis"} 1100  # Rear exhaust
rigbeat_fan_speed_rpm{fan="chassis_fan_4", type="chassis"} 1050  # Top exhaust

# Custom cooling
rigbeat_fan_speed_rpm{fan="aio_pump", type="other"} 2500
```

## Customizing Detection

If your fans aren't detected correctly, you can modify the detection patterns in `hardware_exporter.py`:

```python
elif sensor_type == "Fan":
    fan_name_lower = sensor_name.lower()

    # Add your custom pattern here
    if "my_custom_fan" in fan_name_lower:
        fan_type = "custom"
        fan_label = "my_custom_fan_label"
    # ... rest of existing detection logic
```

::: tip Best Practice
Always test detection changes with `python test_fans.py` before deploying to production.
:::