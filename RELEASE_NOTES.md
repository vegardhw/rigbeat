# Release v0.1.3

## 🚀 Major Performance Improvements

### **LibreHardwareMonitor HTTP API Integration**
- **~90% performance improvement** - eliminated 7-8% CPU overhead from WMI polling
- **HTTP API preferred** with automatic WMI fallback for compatibility
- **Native JSON interface** - cleaner and more efficient than WMI COM objects
- **Enhanced debug logging** to verify which connection method is active

### **Smart Connection Management**
```bash
# Performance comparison:
# WMI (old):  7-8% CPU spikes every 2-15 seconds
# HTTP (new): <1% CPU usage for sensor collection

# Enable debug mode to see connection method:
python hardware_exporter.py --debug
```

**Setup Requirements:**
- **LibreHardwareMonitor HTTP server** enabled in Options → Web Server (port 8085)
- **Automatic fallback** to WMI if HTTP unavailable
- **Windows Firewall** configuration for Prometheus scraping

### **Network Configuration**

**Windows Firewall Setup** (required for Prometheus scraping):
```powershell
# Allow Rigbeat port through Windows Firewall
netsh advfirewall firewall add rule name="Rigbeat" dir=in action=allow protocol=TCP localport=9182

# For custom ports (replace XXXX with your port)
netsh advfirewall firewall add rule name="Rigbeat-Custom" dir=in action=allow protocol=TCP localport=XXXX
```

**LibreHardwareMonitor HTTP Server Setup:**
1. Open LibreHardwareMonitor
2. Go to Options → Web Server
3. Check "Enable Web Server" (port 8085)
4. Rigbeat will automatically detect and use HTTP API

## 🏢 Multi-User & Multi-PC Support

### **Enhanced Prometheus Configuration**
- **Multi-system monitoring** through improved Prometheus labeling
- **User-specific identification** with hostname, user, and location labels
- **Federation support** for large deployments with multiple Prometheus instances
- **Flexible deployment** - same Rigbeat codebase across all systems

### **Family & Team-Friendly Setup**
```yaml
# Example: Monitor multiple PCs with user identification
- job_name: 'rigbeat-gaming-pc'
  static_configs:
    - targets: ['192.168.1.10:9182']
      labels:
        instance: 'gaming-pc-main'
        user: 'primary'
        location: 'office'
        hostname: 'GAMING-DESKTOP'
```

### **Smart Multi-System Queries**
```promql
# Filter by user
rigbeat_cpu_temperature_celsius{user="primary"}

# Compare systems
rigbeat_gpu_temperature_celsius{instance=~"gaming.*|workstation.*"}

# Family dashboard
rigbeat_fan_speed_rpm{location="office"}
```
## 📦 Assets

- **`rigbeat-v0.1.3-win64.zip`** - Complete package with multi-user examples
- **`grafana_dashboard_v2.json`** - Updated dashboard with multi-system support
- **`prometheus_multi_user.yml`** - Example multi-PC Prometheus configuration

## 🔄 Upgrade Instructions

### From v0.1.2

1. **Update Rigbeat Dependencies**:
   ```bash
   # Stop service
   net stop Rigbeat

   # Update Python dependencies
   pip install -r requirements.txt

   # Replace files with new version
   # Start service
   net start Rigbeat
   ```

2. **Enable HTTP API for Performance** (recommended):
   - Open LibreHardwareMonitor
   - Go to Options → Web Server
   - Check "Enable Web Server" (port 8085)
   - Rigbeat will automatically detect and use HTTP API
   - Verify in debug logs: `python hardware_exporter.py --debug`

3. **Configure Windows Firewall**:
   ```powershell
   netsh advfirewall firewall add rule name="Rigbeat" dir=in action=allow protocol=TCP localport=9182
   ```

4. **Update Grafana Dashboard**:
   - Import new `grafana_dashboard_v2.json`
   - Configure hostname variable for your systems
   - Customize user labels as needed

5. **Enhance Prometheus Config** (optional):
   - Add user/location labels to existing targets
   - Configure additional Rigbeat instances
   - Update alerting rules with system context
