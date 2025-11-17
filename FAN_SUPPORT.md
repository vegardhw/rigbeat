# Fan Support Reference

## Supported Fan Types

The exporter automatically categorizes fans into these types:

### 🎮 GPU Fans
- **Detection**: Sensors with "GPU" or "VGA" in the name
- **Labels**: `gpu_fan`, `gpu_fan_1`, `gpu_fan_2`
- **Type**: `gpu`
- **Examples**: "GPU Fan", "GPU Fan #1", "VGA Fan"

### 🔥 CPU Fans
- **Detection**: Sensors with "CPU" in the name
- **Labels**: `cpu_fan`
- **Type**: `cpu`
- **Examples**: "CPU Fan", "CPU Fan #1"

### 📦 Chassis Fans
- **Detection**: Sensors with "CHA", "Chassis", or "Case" in the name
- **Labels**: `chassis_fan_1`, `chassis_fan_2`, `chassis_fan_3`, `chassis_fan_4`
- **Type**: `chassis`
- **Examples**: "CHA1 Fan", "Chassis Fan #1", "Case Fan 1"

### 🔧 Other Fans
- **Detection**: Any other fan sensors (pumps, etc.)
- **Labels**: Cleaned version of sensor name
- **Type**: `other`
- **Examples**: "Pump Fan", "AIO Pump"

## Prometheus Metrics

All fans are exposed with this metric format:

```
fan_speed_rpm{fan="LABEL", type="TYPE"} VALUE
```

### Example Metrics Output

```prometheus
# GPU fans
fan_speed_rpm{fan="gpu_fan", type="gpu"} 1850.0

# CPU fans
fan_speed_rpm{fan="cpu_fan", type="cpu"} 1450.0

# Chassis fans
fan_speed_rpm{fan="chassis_fan_1", type="chassis"} 1200.0
fan_speed_rpm{fan="chassis_fan_2", type="chassis"} 1150.0

# Other
fan_speed_rpm{fan="pump_fan", type="other"} 2500.0
```

## Grafana Dashboard Queries

### Display All Fans
```promql
fan_speed_rpm
```

### GPU Fan Only
```promql
fan_speed_rpm{type="gpu"}
```

### CPU Fan Only
```promql
fan_speed_rpm{type="cpu"}
```

### All Chassis Fans
```promql
fan_speed_rpm{type="chassis"}
```

### Specific Chassis Fan
```promql
fan_speed_rpm{fan="chassis_fan_1"}
```

### Alerting: Any Fan Below Threshold
```promql
fan_speed_rpm < 500
```

## Testing Fan Detection

Run the test script to see what fans are detected:

```bash
python test_fans.py
```

### Expected Output

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

## Customizing Fan Detection

If your fans aren't being detected correctly, edit `hardware_exporter.py`:

### Example: Adding Custom Fan Pattern

```python
elif sensor_type == "Fan":
    fan_name_lower = sensor_name.lower()
    
    # Add your custom pattern here
    if "my_custom_fan" in fan_name_lower:
        fan_type = "custom"
        fan_label = "my_custom_fan_label"
    # ... rest of the code
```

### Example: Custom Chassis Fan Numbering

```python
elif "cha" in fan_name_lower or "chassis" in fan_name_lower:
    fan_type = "chassis"
    
    # Custom mapping for your motherboard
    if "sys1" in sensor_name:
        fan_label = "chassis_fan_1"
    elif "sys2" in sensor_name:
        fan_label = "chassis_fan_2"
    # ... etc
```

## Common Issues

### Issue: No Fans Detected

**Causes:**
1. LibreHardwareMonitor not running
2. Running without Administrator privileges
3. Motherboard doesn't expose fan sensors via WMI

**Solutions:**
1. Start LibreHardwareMonitor as Administrator
2. Check LibreHardwareMonitor GUI - if it shows fans, they should be detected
3. Enable "WMI" in LibreHardwareMonitor Options

### Issue: Fan Shows 0 RPM

**Causes:**
1. Fan not connected to motherboard
2. Fan header not enabled in BIOS
3. Fan running too slow to detect

**Solutions:**
1. Check physical connection
2. Enable fan header in BIOS
3. Set minimum fan speed in BIOS

### Issue: Wrong Fan Label

**Cause:** Fan name doesn't match detection patterns

**Solution:** 
1. Run `python test_fans.py` to see actual sensor names
2. Update detection logic in `hardware_exporter.py`
3. Add custom pattern matching

### Issue: Duplicate Fan Labels

**Cause:** Multiple fans matching the same pattern

**Solution:**
Add number detection to differentiate:

```python
if "fan" in fan_name_lower:
    # Extract number from sensor name
    import re
    number = re.search(r'(\d+)', sensor_name)
    if number:
        fan_label = f"chassis_fan_{number.group(1)}"
```

## Best Practices

1. **Always test first**: Run `test_fans.py` before deploying
2. **Use descriptive labels**: Make them easy to understand in Grafana
3. **Document custom patterns**: Add comments if you modify detection logic
4. **Monitor 0 RPM fans**: Set up alerts for stopped fans
5. **Group by type**: Use the `type` label for organizing dashboards

## Grafana Dashboard Tips

### Fan Speed Panel with Color Coding

```json
{
  "fieldConfig": {
    "defaults": {
      "thresholds": {
        "steps": [
          {"color": "red", "value": 0},     // Stopped
          {"color": "yellow", "value": 500}, // Slow
          {"color": "green", "value": 1000}  // Normal
        ]
      }
    }
  }
}
```

### Alert When Any Fan Stops

```yaml
- alert: FanStopped
  expr: fan_speed_rpm < 100
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Fan {{ $labels.fan }} has stopped"
```

## Example Configuration

### Typical Gaming PC Setup

- **GPU Fan**: 1x or 2x (depending on GPU model)
- **CPU Fan**: 1x
- **Chassis Front**: 2x (intake)
- **Chassis Rear**: 1x (exhaust)
- **Chassis Top**: 1-2x (exhaust)

### Detected Metrics

```
fan_speed_rpm{fan="gpu_fan", type="gpu"} 1850
fan_speed_rpm{fan="cpu_fan", type="cpu"} 1450
fan_speed_rpm{fan="chassis_fan_1", type="chassis"} 1200  # Front intake
fan_speed_rpm{fan="chassis_fan_2", type="chassis"} 1150  # Front intake
fan_speed_rpm{fan="chassis_fan_3", type="chassis"} 1100  # Rear exhaust
fan_speed_rpm{fan="chassis_fan_4", type="chassis"} 1050  # Top exhaust
```

## Support

If you need help with fan detection:

1. Run `python test_fans.py` and share output
2. Check LibreHardwareMonitor shows the fans
3. Look at sensor names in the test output
4. Open an issue on GitHub with details