# Release v0.1.3

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

## 🎨 Updated Grafana Dashboard v2.0

### **New Features**
- **Multi-system support** with hostname selector variable
- **User-based filtering** for family/team environments
- **Enhanced mobile optimization** for better tablet/phone experience
- **Improved layout** with better space utilization

### **Dashboard Improvements**
- ✅ **System selector dropdown** - switch between monitored PCs
- ✅ **User identification** in panel titles and legends
- ✅ **Location-based grouping** for organized monitoring
- ✅ **Responsive design** enhancements for all screen sizes

## 📚 Documentation Updates

### **New Multi-User Guide**
- **Comprehensive setup instructions** for multiple PC monitoring
- **Prometheus configuration examples** for different scenarios
- **Grafana panel configurations** for multi-system dashboards
- **Advanced alerting rules** with user/system context

## 🔧 Configuration Enhancements

### **Updated prometheus.yml**
- **Enhanced external_labels** with datacenter and replica identification
- **Multi-instance examples** showing gaming PC, workstation, and HTPC setups
- **Smart alerting rules** with user and system context
- **Federation-ready configuration** for scalable deployments

## 🎯 Use Cases

### **Family Households**
- Monitor kids' gaming PC, parents' workstations, and family HTPC
- User-specific alerts and maintenance notifications
- Centralized view of all household systems

### **Small Teams/Offices**
- Development team workstation monitoring
- Build server and gaming rig oversight
- Performance comparison across team members' systems

### **Home Lab Enthusiasts**
- Multi-server monitoring with Rigbeat on each Windows system
- Cluster performance tracking and optimization
- Historical analysis across multiple systems

## 📦 Assets

- **`rigbeat-v0.1.3-win64.zip`** - Complete package with multi-user examples
- **`grafana_dashboard_v2.json`** - Updated dashboard with multi-system support
- **`prometheus_multi_user.yml`** - Example multi-PC Prometheus configuration
- **[📚 Documentation](https://vegardhw.github.io/rigbeat/)** - Updated with multi-user guides

## 🔄 Upgrade Instructions

### From v0.1.2

1. **Update Rigbeat** (optional - existing installs work fine):
   ```bash
   # Stop service
   net stop Rigbeat

   # Replace files with new version
   # Start service
   net start Rigbeat
   ```

2. **Update Grafana Dashboard**:
   - Import new `grafana_dashboard_v2.json`
   - Configure hostname variable for your systems
   - Customize user labels as needed

3. **Enhance Prometheus Config** (optional):
   - Add user/location labels to existing targets
   - Configure additional Rigbeat instances
   - Update alerting rules with system context

### New Multi-System Setup

1. **Deploy Rigbeat** on each PC (same installation as before)
2. **Configure Prometheus** with enhanced labels per system
3. **Import updated Grafana dashboard** with multi-system support
4. **Configure alerts** with user/system-specific routing
