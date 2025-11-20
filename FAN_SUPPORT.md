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
- **Labels**: `cpu_fan`, `cpu_fan_1`, `cpu_fan_2` (numbered if multiple)
- **Type**: `cpu`
- **Examples**: "CPU Fan", "CPU Fan #1", "CPU Fan 2"

### 📦 Chassis Fans
- **Detection**: Sensors with "CHA", "Chassis", or "Case" in the name
- **Labels**: `chassis_fan_1`, `chassis_fan_2`, etc. (auto-numbered from sensor name)
- **Type**: `chassis`
- **Examples**: "CHA1 Fan", "Chassis Fan #1", "Case Fan 2"

### 🔧 Other Fans
- **Detection**: Any other fan sensors (pumps, etc.)
- **Labels**: Sanitized version of sensor name (Prometheus-compliant)
- **Type**: `other`
- **Examples**: "Pump Fan" → `pump_fan`, "AIO Pump" → `aio_pump`, "Fan #2" → `fan_2`

## Prometheus Metrics

All fans are exposed with this metric format:

```
rigbeat_fan_speed_rpm{fan="LABEL", type="TYPE"} VALUE
```

### Example Metrics Output

```prometheus
# GPU fans
rigbeat_fan_speed_rpm{fan="gpu_fan", type="gpu"} 1850.0

# CPU fans
rigbeat_fan_speed_rpm{fan="cpu_fan", type="cpu"} 1450.0

# Chassis fans
rigbeat_fan_speed_rpm{fan="chassis_fan_1", type="chassis"} 1200.0
rigbeat_fan_speed_rpm{fan="chassis_fan_2", type="chassis"} 1150.0

# Other
rigbeat_fan_speed_rpm{fan="pump_fan", type="other"} 2500.0
rigbeat_fan_speed_rpm{fan="fan_2", type="other"} 1100.0
```

## Grafana Dashboard Queries

### Display All Fans
```promql
rigbeat_fan_speed_rpm
```

### GPU Fan Only
```promql
rigbeat_fan_speed_rpm{type="gpu"}
```

### CPU Fan Only
```promql
rigbeat_fan_speed_rpm{type="cpu"}
```

### All Chassis Fans
```promql
rigbeat_fan_speed_rpm{type="chassis"}
```

### Specific Chassis Fan
```promql
rigbeat_fan_speed_rpm{fan="chassis_fan_1"}
```

### Alerting: Any Fan Below Threshold
```promql
rigbeat_fan_speed_rpm < 500
```

## Testing Fan Detection

Run the test script to see what fans are detected:

```bash
python test_fans.py
```

### Demo Mode vs Hardware Mode

**Hardware Mode** (LibreHardwareMonitor running):
Shows actual detected fans with real RPM values

**Demo Mode** (LibreHardwareMonitor not available):
- Service runs successfully for testing deployment
- No fan metrics are collected (by design)
- System info shows demo values
- Useful for CI/CD testing and VM deployment validation

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

### Example: Improved Number Detection

The current system automatically extracts numbers from sensor names:

```python
elif sensor_type == "Fan":
    fan_name_lower = sensor_name.lower()

    if "gpu" in fan_name_lower or "vga" in fan_name_lower:
        fan_type = "gpu"
        numbers = re.findall(r'\d+', sensor_name)
        if numbers:
            fan_label = f"gpu_fan_{numbers[0]}"
        else:
            fan_label = "gpu_fan"
```

## Common Issues

### Issue: No Fans Detected or "Demo Mode"

**Causes:**
1. LibreHardwareMonitor not running (service runs in demo mode)
2. Running without Administrator privileges
3. Motherboard doesn't expose fan sensors via WMI
4. WMI not enabled in LibreHardwareMonitor

**Solutions:**
1. **For Demo Mode Testing**: This is normal - service is working correctly
2. **For Hardware Monitoring**: Start LibreHardwareMonitor as Administrator
3. **Enable WMI**: Check LibreHardwareMonitor Options → "WMI" is enabled
4. **Verify Detection**: If LibreHardwareMonitor GUI shows fans, they should be detected
5. **Restart Service**: After starting LibreHardwareMonitor, restart Rigbeat service

### Issue: Fan Shows 0 RPM

**Causes:**
1. Fan not connected to motherboard
2. Fan header not enabled in BIOS
3. Fan running too slow to detect

**Solutions:**
1. Check physical connection
2. Enable fan header in BIOS
3. Set minimum fan speed in BIOS

### Issue: Windows Service COM Errors

**Symptoms:** "OLE error 0x8004100e", service fails to start

**Cause:** Windows service context requires proper COM initialization for WMI access

**Solution:** 
- **Fixed in v1.0.1+**: Service now properly initializes COM
- Update to latest version and reinstall service:
  ```bash
  python service_manager.py remove
  python service_manager.py install
  net start Rigbeat
  ```
- Check service logs: `C:\ProgramData\Rigbeat\service.log`

### Issue: Service Starts but No Metrics

**Symptoms:** Service running, endpoint responds, but no fan metrics

**Diagnosis:**
1. Check if running in demo mode (service logs will indicate this)
2. Verify LibreHardwareMonitor is running with WMI enabled
3. Test fan detection: `python test_fans.py`
4. Check service can access LibreHardwareMonitor WMI namespace

**Solution:**
- If demo mode: Install and run LibreHardwareMonitor, then restart service
- If hardware mode but no fans: Check motherboard BIOS settings for fan monitoring

### Issue: Wrong Fan Label

**Cause:** Fan name doesn't match detection patterns or falls into "other" category

**Solution:** 
1. Run `python test_fans.py` to see actual sensor names
2. Fans not matching GPU/CPU/Chassis patterns are labeled as "other" type
3. For edge cases, update detection logic in `hardware_exporter.py`

### Issue: Duplicate Fan Labels

**Cause:** This is now automatically handled by regex number extraction

**Current Implementation:**
The system automatically extracts numbers from sensor names using `re.findall(r'\d+', sensor_name)`:
- "GPU Fan #12" → `gpu_fan_12`
- "Chassis Fan 3" → `chassis_fan_3`
- "CHA_FAN_2" → `chassis_fan_2`

## Best Practices

1. **Test Deployment First**: Use demo mode to verify service installation before requiring hardware
2. **Always test detection**: Run `test_fans.py` before deploying to production hardware
3. **Use descriptive labels**: Make them easy to understand in Grafana
4. **Document custom patterns**: Add comments if you modify detection logic
5. **Monitor service health**: Set up alerts for demo mode vs hardware mode transitions
6. **Monitor 0 RPM fans**: Set up alerts for stopped fans (hardware mode only)
7. **Group by type**: Use the `type` label for organizing dashboards
8. **Service logs**: Monitor `C:\ProgramData\Rigbeat\service.log` for mode changes

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
  expr: rigbeat_fan_speed_rpm < 100
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
rigbeat_fan_speed_rpm{fan="gpu_fan", type="gpu"} 1850
rigbeat_fan_speed_rpm{fan="cpu_fan", type="cpu"} 1450
rigbeat_fan_speed_rpm{fan="chassis_fan_1", type="chassis"} 1200  # Front intake
rigbeat_fan_speed_rpm{fan="chassis_fan_2", type="chassis"} 1150  # Front intake
rigbeat_fan_speed_rpm{fan="chassis_fan_3", type="chassis"} 1100  # Rear exhaust
rigbeat_fan_speed_rpm{fan="chassis_fan_4", type="chassis"} 1050  # Top exhaust
```

## Support

If you need help with fan detection:

1. Run `python test_fans.py` and share output
2. Check LibreHardwareMonitor shows the fans
3. Look at sensor names in the test output
4. Open an issue on GitHub with details