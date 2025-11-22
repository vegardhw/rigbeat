# HTTP API & Performance

Troubleshoot LibreHardwareMonitor HTTP API connection and performance optimization.

## Performance Comparison

| Method | CPU Usage | Benefits | Drawbacks |
|--------|-----------|----------|-----------|
| **HTTP API** | <1% | ✅ Native JSON<br>✅ Network ready<br>✅ Better error handling | Requires HTTP server enabled |
| **WMI Fallback** | 7-8% spikes | ✅ Legacy compatibility<br>✅ No extra setup | ❌ High CPU overhead<br>❌ COM complexity |

## Enable HTTP API

### 1. LibreHardwareMonitor Setup

1. **Open LibreHardwareMonitor** as Administrator
2. **Go to Options** → **Web Server**  
3. **Enable Web Server** ✅ (default port 8085)
4. **Optional**: Change port if needed
5. **Restart Rigbeat** to detect HTTP API

### 2. Verify HTTP API Access

**Test in browser:**
Visit `http://localhost:8085/data.json` - should show JSON sensor data

**Test in Rigbeat:**
```bash
python hardware_exporter.py --debug
```

Look for:
```
🚀 Connected to LibreHardwareMonitor HTTP API at http://localhost:8085
✅ Performance optimized mode enabled (HTTP API)
```

## Troubleshooting Connection Issues

### HTTP API Not Detected

**Symptoms:**
```
⚠️ Connected via WMI fallback (higher CPU usage)
💡 Enable LibreHardwareMonitor HTTP server for better performance
```

**Solutions:**

1. **Check HTTP Server Status:**
   - LibreHardwareMonitor → Options → Web Server
   - Ensure "Enable Web Server" is checked ✅
   - Note the port number (default: 8085)

2. **Test Manual Connection:**
   ```bash
   # Test if HTTP server is responding
   curl http://localhost:8085/data.json
   
   # Or in PowerShell
   Invoke-WebRequest http://localhost:8085/data.json
   ```

3. **Check Port Conflicts:**
   ```bash
   # Check if port 8085 is in use
   netstat -an | findstr :8085
   ```

4. **Restart LibreHardwareMonitor:**
   - Close LibreHardwareMonitor completely
   - Run as Administrator 
   - Re-enable Web Server
   - Restart Rigbeat service

### Custom HTTP API Configuration

**Different Host/Port:**
```bash
# Connect to remote LibreHardwareMonitor
python hardware_exporter.py --http-host 192.168.1.100 --http-port 8085

# Custom port
python hardware_exporter.py --http-port 8086
```

**Debug Connection:**
```bash
python hardware_exporter.py --debug --http-host localhost --http-port 8085
```

### Network/Firewall Issues

**Allow LibreHardwareMonitor HTTP Server:**
```powershell
# Allow inbound connections to LibreHardwareMonitor HTTP server
netsh advfirewall firewall add rule name="LibreHardwareMonitor-HTTP" dir=in action=allow protocol=TCP localport=8085

# Allow Rigbeat Prometheus endpoint
netsh advfirewall firewall add rule name="Rigbeat" dir=in action=allow protocol=TCP localport=9182
```

**Test Network Connectivity:**
```bash
# From another machine, test Rigbeat
curl http://[RIGBEAT-PC-IP]:9182/metrics

# Test LibreHardwareMonitor HTTP API
curl http://[LHM-PC-IP]:8085/data.json
```

## Performance Optimization

### Monitor CPU Usage

**Before (WMI):**
```
Task Manager → Details → python.exe
CPU spikes: 7-8% every 15 seconds
```

**After (HTTP API):**
```
Task Manager → Details → python.exe
CPU usage: <1% steady
```

### Debug Performance

**Enable verbose logging:**
```bash
python hardware_exporter.py --debug --interval 5
```

**Look for timing information:**
```
Retrieved 47 sensors via HTTP API
Metrics update completed in 0.023s
```

vs WMI:
```
Retrieved 47 sensors via WMI
Metrics update completed in 0.156s
```

### Optimize Update Intervals

**HTTP API (efficient):**
```bash
# Can handle faster updates efficiently
python hardware_exporter.py --interval 2
```

**WMI Fallback (conservative):**
```bash  
# Use longer intervals to reduce CPU impact
python hardware_exporter.py --interval 30
```

## Advanced Configuration

### Multiple LibreHardwareMonitor Instances

**Monitor remote systems:**
```bash
# Connect to different LibreHardwareMonitor instances
python hardware_exporter.py --http-host 192.168.1.10 --port 9182  # Gaming PC
python hardware_exporter.py --http-host 192.168.1.11 --port 9183  # Workstation  
python hardware_exporter.py --http-host 192.168.1.12 --port 9184  # Server
```

### Hybrid Deployment

**Some systems HTTP, others WMI:**
- Modern systems: Enable HTTP API for best performance
- Legacy systems: Keep WMI enabled
- Rigbeat automatically detects and uses best available method

### Network Security

**Secure HTTP API access:**
1. **LibreHardwareMonitor** → Options → Web Server → Authentication
2. **Configure username/password** if exposing over network
3. **Use firewall rules** to limit source IPs
4. **Consider VPN** for remote monitoring

## Migration from WMI

### Gradual Transition

1. **Keep WMI enabled** during transition
2. **Enable HTTP server** in LibreHardwareMonitor  
3. **Restart Rigbeat** - automatically uses HTTP
4. **Verify performance improvement** in Task Manager
5. **Disable WMI** once confident in HTTP API

### Rollback Plan

If HTTP API causes issues:

1. **Disable Web Server** in LibreHardwareMonitor
2. **Keep WMI enabled** 
3. **Restart Rigbeat** - automatically falls back to WMI
4. **Report issues** for troubleshooting

## Common Error Messages

### "HTTP API connection failed"

**Debug output:**
```
HTTP API connection failed - LibreHardwareMonitor HTTP server not running
```

**Solution:** Enable Web Server in LibreHardwareMonitor Options

### "HTTP response structure invalid"

**Debug output:**
```
HTTP response structure invalid
```

**Causes:**
- Wrong port (not LibreHardwareMonitor)
- Different web service running on port 8085
- LibreHardwareMonitor not fully loaded

**Solution:** Verify `http://localhost:8085/data.json` shows sensor data

### "Connection timeout"

**Debug output:**
```
HTTP API connection timeout
```

**Causes:**
- LibreHardwareMonitor frozen/unresponsive
- Network issues
- Firewall blocking connection

**Solution:** Restart LibreHardwareMonitor, check firewall rules

This HTTP API integration provides significant performance improvements while maintaining full backward compatibility!