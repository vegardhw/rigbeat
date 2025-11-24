# Common Issues

Quick solutions for the most frequent Rigbeat problems.

## 🚀 Quick Diagnostics

Before diving into specific issues, run these quick checks:

```cmd
# 1. Check service status
sc query Rigbeat

# 2. Test hardware detection
python test_fans.py

# 3. Verify metrics endpoint
curl http://localhost:9182/metrics

# 4. Check service logs
type "C:\ProgramData\Rigbeat\service.log"
```

## 🎭 Demo Mode vs Hardware Mode

**Demo Mode** is normal for testing and development:
- ✅ Service runs successfully
- ✅ `/metrics` endpoint responds
- ❌ No real hardware metrics collected
- 💡 Perfect for CI/CD and VM testing

**Hardware Mode** provides real monitoring:
- ✅ LibreHardwareMonitor connection established
- ✅ Real sensor data collected
- 📊 All metrics populated with actual values

**To switch from Demo to Hardware Mode:**
1. Install [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
2. Run as Administrator
3. Enable **Options → WMI**
4. Restart Rigbeat service: `net stop Rigbeat && net start Rigbeat`

## ⚠️ Service Won't Start

### Symptoms
- Service status: Stopped
- Windows Event Viewer shows startup errors
- COM/WMI error messages

### Solutions

#### **Install/Reinstall Service**
```cmd
# Remove existing service
python service-manager.py remove

# Install fresh service
python service-manager.py install

# Start service
net start Rigbeat
```

#### **Permission Issues**
- Ensure installation ran as Administrator
- Check service runs under proper account (LocalSystem)
- Verify WMI permissions for service account

#### **Missing Dependencies**
```cmd
# Install Python dependencies
pip install -r requirements.txt

# Install Windows service dependencies
pip install pywin32
```

## 🌐 Network/Port Issues

### Metrics Endpoint Unreachable

#### Check Port Binding
```cmd
netstat -an | findstr :9182
```
Should show: `0.0.0.0:9182 ... LISTENING`

#### Test Different Port
```cmd
# Stop service
net stop Rigbeat

# Test manual startup with different port
python hardware_exporter.py --port 9183

# Access: http://localhost:9183/metrics
```

#### Firewall Configuration
```cmd
# Add Windows Firewall exception
netsh advfirewall firewall add rule name="Rigbeat" dir=in action=allow protocol=TCP localport=9182
```

## 🔧 LibreHardwareMonitor Issues

### "WMI Connection Failed"

#### Verification Steps
1. **LibreHardwareMonitor Running**: Check system tray
2. **Administrator Mode**: Right-click → "Run as Administrator"
3. **WMI Enabled**: Options → WMI checkbox must be checked
4. **WMI Namespace**: Test with `wmic /namespace:\\root\LibreHardwareMonitor path sensor get name`

#### Common Fixes
- Restart LibreHardwareMonitor as Administrator
- Reinstall LibreHardwareMonitor
- Update to latest LHM version
- Check Windows WMI service is running: `net start winmgmt`

### Hardware Not Detected

#### Motherboard Compatibility
Not all hardware exposes sensors via WMI:
- Check if LibreHardwareMonitor GUI shows your hardware
- Some systems require BIOS settings changes
- Virtual machines typically don't have hardware sensors

#### BIOS Settings
Enable in BIOS/UEFI:
- Hardware monitoring
- Fan monitoring
- Temperature sensors
- Chipset-specific monitoring features

## 📊 Prometheus/Grafana Integration

### No Data in Prometheus

#### Prometheus Configuration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rigbeat'
    static_configs:
      - targets: ['localhost:9182']
    scrape_interval: 15s
```

#### Verification Steps
1. **Direct Access**: Visit `http://localhost:9182/metrics`
2. **Prometheus Targets**: Check `http://prometheus:9090/targets`
3. **Query Test**: Use Prometheus web UI to query `rigbeat_cpu_temperature_celsius`

### Grafana Shows "No Data"

#### Data Source Check
- Verify Prometheus URL in Grafana data source
- Test connection from Grafana to Prometheus
- Confirm time range includes recent data

#### Query Validation
- Test queries in Prometheus web UI first
- Verify metric names match exactly
- Check for typos in label selectors

## 💾 Performance Issues

### High CPU Usage

#### Causes & Solutions
1. **Update Interval Too Fast**: Change from 2s to 15s+ for standard monitoring
2. **WMI Query Issues**: Restart LibreHardwareMonitor and Rigbeat service
3. **Hardware Conflicts**: Some motherboards have WMI performance issues

```cmd
# Run with longer interval for better performance
python hardware_exporter.py --interval 30
```

### Memory Leaks

#### Symptoms
- Rigbeat memory usage grows continuously
- System becomes unstable over time

#### Solutions
- Update to latest version (memory handling improvements)
- Schedule periodic service restart if needed
- Monitor logs for error patterns indicating memory issues

## 🔍 Advanced Diagnostics

### Enable Debug Logging

#### Temporary Debug Mode
```cmd
# Stop service
net stop Rigbeat

# Run with debug logging
python hardware_exporter.py --debug --logfile rigbeat_debug.log

# Check detailed logs
type rigbeat_debug.log
```

#### Service Debug Logging
```cmd
# Install service with debug mode
python service-manager.py debug
```

### WMI Troubleshooting

#### Test WMI Access Directly
```cmd
# List available WMI namespaces
wmic /namespace:\\root path __NAMESPACE get name

# Test LibreHardwareMonitor namespace
wmic /namespace:\\root\LibreHardwareMonitor path sensor get name,value,sensortype

# Check WMI service health
winmgmt /verifyrepository
```

## 📞 Getting Additional Help

### Information to Gather

Before seeking support, collect:

```cmd
# System information
systeminfo > system_info.txt

# Rigbeat diagnostics
python test_fans.py > fan_detection.txt

# Service logs
copy "C:\ProgramData\Rigbeat\service.log" service_debug.log

# Metrics output
curl http://localhost:9182/metrics > metrics_output.txt
```

### Support Channels

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/vegardhw/rigbeat/issues)
- **💬 Questions**: [GitHub Discussions](https://github.com/vegardhw/rigbeat/discussions)
- **📖 Documentation**: Search these docs first

### Specific Issue Pages

- **🌀 Fan Detection Problems**: [Fan Issues Guide](/troubleshooting/fan-issues)
- **📊 Metrics/Monitoring**: [Metrics Reference](/reference/metrics)
- **🔧 Service Management**: [Installation Guide](/getting-started/installation)

Most issues are resolved by ensuring LibreHardwareMonitor runs as Administrator with WMI enabled, then restarting the Rigbeat service.