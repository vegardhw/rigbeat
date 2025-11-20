# Fan Monitoring Troubleshooting

Common issues with fan detection and monitoring, plus their solutions.

## No Fans Detected

### Symptoms
- Test script shows "Found 0 fans"
- `/metrics` endpoint has no `rigbeat_fan_speed_rpm` metrics
- Service logs show "Demo mode" or "No sensors found"

### Causes & Solutions

#### 🎭 **Demo Mode (Normal for Testing)**
**Cause**: LibreHardwareMonitor not running or not accessible

**When This Is Normal**:
- Testing deployment on VMs
- CI/CD pipeline validation  
- Development without hardware sensors

**When This Is a Problem**:
- Production hardware monitoring
- Expecting real fan metrics

**Solution**: Install and run LibreHardwareMonitor with WMI enabled

#### 🔧 **LibreHardwareMonitor Not Running**
**Symptoms**: Service can't connect to WMI namespace

**Solution**:
1. Download [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
2. Run as Administrator  
3. Enable **Options → WMI** (critical!)
4. Restart Rigbeat service:
   ```cmd
   net stop Rigbeat
   net start Rigbeat
   ```

#### 🛡️ **Permission Issues**
**Symptoms**: "Access denied" or WMI connection errors

**Solutions**:
- Run LibreHardwareMonitor as Administrator
- Ensure Rigbeat service runs with proper privileges
- Check Windows User Account Control settings

#### 🏠 **Hardware/BIOS Issues** 
**Symptoms**: LibreHardwareMonitor GUI shows fans, but Rigbeat doesn't detect them

**Solutions**:
1. Enable fan monitoring in BIOS
2. Check if fan headers are enabled
3. Verify fans are connected to motherboard (not directly to PSU)
4. Update motherboard chipset drivers

## Fan Shows 0 RPM

### Causes & Solutions

#### 🔌 **Physical Connection**
- **Check**: Fan connected to motherboard header (not PSU)
- **Check**: Cable properly seated
- **Test**: Swap fan to different header

#### ⚙️ **BIOS Configuration**
- **Check**: Fan header enabled in BIOS
- **Check**: Fan curve configured (not disabled)  
- **Check**: Minimum fan speed set appropriately

#### 🔧 **Fan Hardware**
- **Check**: Fan spins when system starts
- **Test**: Connect known-working fan to same header
- **Replace**: Fan may be faulty

## Service Issues

### Windows Service COM Errors

#### Symptoms
```
OLE error 0x8004100e
Service fails to start
CoInitializeEx failed
```

#### Cause
Windows service context requires proper COM initialization for WMI access.

#### Solution
**Fixed in v0.1.1+** - Service now properly initializes COM:

```cmd
# Update to latest version and reinstall
python service-manager.py remove
python service-manager.py install
net start Rigbeat
```

Check service logs: `C:\ProgramData\Rigbeat\service.log`

### Service Starts but No Metrics

#### Symptoms
- Service status: Running
- `/metrics` endpoint responds
- No fan metrics in output  
- Service logs show successful startup

#### Diagnosis Steps

1. **Check service mode**:
   ```cmd
   # Look for "demo mode" vs "hardware mode" in logs
   type "C:\ProgramData\Rigbeat\service.log"
   ```

2. **Test fan detection manually**:
   ```cmd
   cd "C:\ProgramData\Rigbeat"
   python test_fans.py
   ```

3. **Verify LibreHardwareMonitor**:
   - Is it running?
   - Is WMI enabled in options?
   - Does the GUI show your fans?

4. **Check WMI namespace**:
   ```cmd
   # Test if WMI namespace exists
   wmic /namespace:\\root\LibreHardwareMonitor path sensor get name
   ```

#### Solutions
- **Demo Mode**: Install LibreHardwareMonitor, restart service
- **Hardware Mode + No Fans**: Check BIOS fan settings
- **WMI Issues**: Reinstall LibreHardwareMonitor with Administrator

## Fan Label Issues

### Wrong Fan Categories

#### Symptoms
- GPU fan labeled as "other" instead of "gpu"
- Chassis fans not detected as "chassis"

#### Cause
Fan sensor names don't match detection patterns.

#### Diagnosis
```cmd
python test_fans.py
```
Look at the actual sensor names vs expected patterns.

#### Solution
Update detection logic in `hardware_exporter.py`:

```python
elif sensor_type == "Fan":
    fan_name_lower = sensor_name.lower()
    
    # Add custom patterns for your hardware
    if "your_gpu_fan_name" in fan_name_lower:
        fan_type = "gpu"
        fan_label = "gpu_fan"
    # ... existing logic
```

### Duplicate Fan Labels

#### Symptoms
Multiple fans with same Prometheus label (causes metric conflicts)

#### Current Status
**Fixed in current version** - automatic number extraction prevents this:
- "GPU Fan #1" → `gpu_fan_1`  
- "GPU Fan #2" → `gpu_fan_2`

#### If Still Occurring
Update to latest version or manually improve numbering logic.

## Performance Issues

### High CPU Usage

#### Symptoms
- Rigbeat service using excessive CPU
- System slowdown during monitoring

#### Causes & Solutions

1. **Too Frequent Updates**:
   ```cmd
   # Check current interval
   python hardware_exporter.py --help
   
   # For standard monitoring, use 15+ seconds
   python hardware_exporter.py --interval 15
   
   # Only use 2-5 seconds for real-time gaming monitoring
   ```

2. **WMI Query Issues**:
   - Restart LibreHardwareMonitor
   - Restart Rigbeat service
   - Check for Windows updates

### Memory Leaks

#### Symptoms
- Rigbeat memory usage grows over time
- System becomes unstable after long periods

#### Solutions
1. **Update to Latest**: Memory handling improvements in recent versions
2. **Service Restart**: Schedule periodic restart if needed
3. **Monitor Logs**: Check for error patterns in service logs

## Network/Access Issues

### Metrics Endpoint Not Accessible

#### Symptoms
- `http://localhost:9182/metrics` doesn't respond
- "Connection refused" errors

#### Solutions

1. **Check Service Status**:
   ```cmd
   sc query Rigbeat
   # Should show "RUNNING"
   ```

2. **Check Port Binding**:
   ```cmd
   netstat -an | findstr :9182
   # Should show LISTENING
   ```

3. **Firewall Rules**:
   ```cmd
   # Add firewall exception if needed
   netsh advfirewall firewall add rule name="Rigbeat" dir=in action=allow protocol=TCP localport=9182
   ```

4. **Test Different Port**:
   ```cmd
   python hardware_exporter.py --port 9183
   ```

## Grafana Integration Issues

### No Data in Grafana

#### Symptoms
- Prometheus can scrape metrics successfully
- Grafana shows "No data" for queries

#### Solutions

1. **Check Prometheus Config**:
   ```yaml
   scrape_configs:
     - job_name: 'rigbeat'
       static_configs:
         - targets: ['localhost:9182']
       scrape_interval: 15s
   ```

2. **Verify Data in Prometheus**:
   - Visit Prometheus web UI
   - Query: `rigbeat_fan_speed_rpm`
   - Confirm data exists

3. **Check Grafana Data Source**:
   - Test connection to Prometheus
   - Verify URL and access settings

### Missing Fan Metrics

#### Symptoms
- Some metrics work (CPU, GPU temp)
- Fan metrics specifically missing

#### Check
1. **Demo vs Hardware Mode**: Fan metrics only work in hardware mode
2. **LibreHardwareMonitor**: Must be running with WMI enabled  
3. **Fan Detection**: Use `test_fans.py` to verify fans are detected

## Getting Help

If these troubleshooting steps don't resolve your issue:

1. **Gather Information**:
   ```cmd
   # Run diagnostics
   python test_fans.py > fan_test.log
   
   # Check service logs  
   type "C:\ProgramData\Rigbeat\service.log" > service.log
   
   # Test metrics endpoint
   curl http://localhost:9182/metrics > metrics.log
   ```

2. **Check Known Issues**:
   - Review [GitHub Issues](https://github.com/vegardhw/rigbeat/issues)
   - Search for your specific hardware/motherboard

3. **Report Issue**:
   - Open GitHub issue with diagnostic logs
   - Include hardware details (motherboard, fans)
   - Specify if LibreHardwareMonitor GUI shows the fans

::: tip Pro Tip
Most fan detection issues are resolved by ensuring LibreHardwareMonitor runs as Administrator with WMI enabled, then restarting the Rigbeat service.
:::