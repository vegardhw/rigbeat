"""
Rigbeat - Prometheus Exporter
Exports Windows hardware metrics (CPU/GPU temps, fan speeds, loads, power) for Prometheus/Grafana

Requirements:
    - LibreHardwareMonitor running with HTTP server enabled (preferred) or WMI enabled (fallback)
    - Python 3.8+
    - pip install prometheus-client requests pywin32
"""

import time
import logging
import re
import argparse
import requests
import json
from typing import Dict, List, Optional
from prometheus_client import start_http_server, Gauge, Info

# Try to import WMI for fallback (optional)
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    wmi = None

# Sensor Mapping Configuration
# Maps LibreHardwareMonitor sensor names to standardized Prometheus metric names
SENSOR_NAME_MAPPING = {
    # CPU Temperature Sensors
    'Core (Tctl/Tdie)': 'cpu_temp_tctl',
    'CCD1 (Tdie)': 'cpu_temp_ccd1',
    'Package': 'cpu_package_temp',
    'Core Max': 'cpu_core_max_temp',
    'Core Average': 'cpu_core_avg_temp',
    
    # CPU Load Sensors  
    'CPU Total': 'cpu_load_total',
    'CPU Core Max': 'cpu_core_max_load',
    'CPU Core #1': 'cpu_core_1_load',
    'CPU Core #2': 'cpu_core_2_load',
    'CPU Core #3': 'cpu_core_3_load',
    'CPU Core #4': 'cpu_core_4_load',
    'CPU Core #5': 'cpu_core_5_load',
    'CPU Core #6': 'cpu_core_6_load',
    
    # CPU Clock Sensors
    'Bus Speed': 'cpu_bus_speed',
    'Core #1': 'cpu_core_1_clock',
    'Core #2': 'cpu_core_2_clock',
    'Core #3': 'cpu_core_3_clock',
    'Core #4': 'cpu_core_4_clock',
    'Core #5': 'cpu_core_5_clock',
    'Core #6': 'cpu_core_6_clock',
    
    # CPU Power Sensors
    'Package': 'cpu_package_power',
    'Core #1 (SMU)': 'cpu_core_1_power',
    'Core #2 (SMU)': 'cpu_core_2_power',
    'Core #3 (SMU)': 'cpu_core_3_power',
    'Core #4 (SMU)': 'cpu_core_4_power',
    'Core #5 (SMU)': 'cpu_core_5_power',
    'Core #6 (SMU)': 'cpu_core_6_power',
    
    # CPU Voltage Sensors
    'Core (SVI2 TFN)': 'cpu_core_voltage',
    'SoC (SVI2 TFN)': 'cpu_soc_voltage',
    
    # GPU Temperature Sensors
    'GPU Core': 'gpu_temp_core',
    'GPU Hot Spot': 'gpu_temp_hotspot',
    'GPU Memory': 'gpu_temp_memory',
    'GPU Memory Junction': 'gpu_temp_memory_junction',
    
    # GPU Load Sensors
    'GPU Core': 'gpu_load_core',
    'GPU Memory Controller': 'gpu_load_memory_controller',
    'GPU Video Engine': 'gpu_load_video_engine',
    'GPU 3D': 'gpu_load_3d',
    
    # GPU Clock Sensors
    'GPU Core': 'gpu_core_clock',
    'GPU Memory': 'gpu_memory_clock',
    'GPU Shader': 'gpu_shader_clock',
    
    # GPU Power Sensors
    'GPU Package': 'gpu_package_power',
    'GPU Board Power': 'gpu_board_power',
    
    # GPU Fan Sensors
    'GPU Fan 1': 'gpu_fan_1_speed',
    'GPU Fan 2': 'gpu_fan_2_speed',
    'GPU Fan 3': 'gpu_fan_3_speed',
    
    # GPU Memory Sensors
    'GPU Memory Free': 'gpu_memory_free',
    'GPU Memory Used': 'gpu_memory_used',
    'GPU Memory Total': 'gpu_memory_total',
    
    # GPU Throughput Sensors
    'GPU PCIe Rx': 'gpu_pcie_rx_throughput',
    'GPU PCIe Tx': 'gpu_pcie_tx_throughput',
    
    # Motherboard Temperature Sensors
    'Temperature #1': 'motherboard_temp_1',
    'Temperature #2': 'motherboard_temp_2',
    'Temperature #3': 'motherboard_temp_3',
    'Temperature #4': 'motherboard_temp_4',
    'Temperature #5': 'motherboard_temp_5',
    'CPU': 'motherboard_cpu_temp',
    'Motherboard': 'motherboard_temp',
    
    # Motherboard Voltage Sensors
    'Vcore': 'motherboard_vcore',
    'AVCC': 'motherboard_avcc',
    '+3.3V': 'motherboard_3v3',
    '+3V Standby': 'motherboard_3v_standby',
    'CPU Termination': 'motherboard_cpu_termination',
    '+12V': 'motherboard_12v',
    '+5V': 'motherboard_5v',
    'Battery': 'motherboard_battery',
    
    # Motherboard Fan Sensors  
    'CPU Fan': 'motherboard_cpu_fan',
    'Chassis Fan #1': 'motherboard_chassis_fan_1',
    'Chassis Fan #2': 'motherboard_chassis_fan_2',
    'Chassis Fan #3': 'motherboard_chassis_fan_3',
    'System Fan': 'motherboard_system_fan',
    
    # Memory Sensors
    'Memory': 'memory_load',
    'Virtual Memory': 'memory_virtual_load',
    'Memory Available': 'memory_available',
    'Memory Used': 'memory_used',
    
    # Storage/Drive Sensors
    'Used Space': 'drive_used_space',
    'Free Space': 'drive_free_space',
    'Total Activity': 'drive_total_activity',
    'Read Rate': 'drive_read_rate',
    'Write Rate': 'drive_write_rate',
    'Read Activity': 'drive_read_activity',
    'Write Activity': 'drive_write_activity',
    'Temperature': 'drive_temperature',
    
    # Network Sensors
    'Download Speed': 'network_download_speed',
    'Upload Speed': 'network_upload_speed',
    'Data Downloaded': 'network_data_downloaded',
    'Data Uploaded': 'network_data_uploaded',
}

def get_standardized_metric_name(sensor_name: str, component_type: str = '', sensor_type: str = '') -> str:
    """
    Get standardized Prometheus metric name for a sensor.
    
    Args:
        sensor_name: Original sensor name from LibreHardwareMonitor
        component_type: Component type (cpu, gpu, motherboard, etc.)
        sensor_type: Sensor type (temperature, load, clock, etc.)
    
    Returns:
        Standardized metric name or original name if no mapping found
    """
    # First try direct mapping
    if sensor_name in SENSOR_NAME_MAPPING:
        return SENSOR_NAME_MAPPING[sensor_name]
    
    # Fallback: create standardized name from components
    metric_name = sensor_name.lower()
    
    # Clean up common patterns
    metric_name = re.sub(r'[^\w\s]', '', metric_name)  # Remove special chars
    metric_name = re.sub(r'\s+', '_', metric_name)     # Replace spaces with underscores
    metric_name = re.sub(r'_+', '_', metric_name)      # Remove multiple underscores
    metric_name = metric_name.strip('_')               # Remove leading/trailing underscores
    
    # Add component type prefix if not already present
    if component_type and not metric_name.startswith(component_type):
        metric_name = f"{component_type}_{metric_name}"
    
    return metric_name

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
cpu_temp = Gauge('rigbeat_cpu_temperature_celsius', 'CPU temperature in Celsius', ['sensor'])
cpu_load = Gauge('rigbeat_cpu_load_percent', 'CPU load percentage', ['core'])
cpu_clock = Gauge('rigbeat_cpu_clock_mhz', 'CPU clock speed in MHz', ['core'])
cpu_power = Gauge('rigbeat_cpu_power_watts', 'CPU power consumption in Watts', ['sensor'])

gpu_temp = Gauge('rigbeat_gpu_temperature_celsius', 'GPU temperature in Celsius', ['gpu'])
gpu_load = Gauge('rigbeat_gpu_load_percent', 'GPU load percentage', ['gpu', 'type'])
gpu_memory = Gauge('rigbeat_gpu_memory_used_gb', 'GPU memory used in GB', ['gpu'])
gpu_clock = Gauge('rigbeat_gpu_clock_mhz', 'GPU clock speed in MHz', ['gpu', 'type'])
gpu_power = Gauge('rigbeat_gpu_power_watts', 'GPU power consumption in Watts', ['gpu'])

fan_rpm = Gauge('rigbeat_fan_speed_rpm', 'Fan speed in RPM', ['fan', 'type'])

memory_used = Gauge('rigbeat_memory_used_gb', 'System memory used in GB')
memory_available = Gauge('rigbeat_memory_available_gb', 'System memory available in GB')

system_info = Info('rigbeat_system', 'System information')


class HardwareMonitor:
    """Monitors hardware sensors via HTTP API (preferred) or WMI (fallback)"""

    def __init__(self, http_host="localhost", http_port=8085):
        self.http_host = http_host
        self.http_port = http_port
        self.http_url = f"http://{http_host}:{http_port}"
        self.use_http = False
        self.connected = False
        self.w = None

        # Performance optimizations
        self._session = None  # Reuse HTTP connections
        self._compiled_patterns = self._compile_regex_patterns()  # Cache regex patterns
        self._sensor_filter_cache = {}  # Cache sensor categorization

        # Try HTTP API first (performance optimized)
        self._try_http_connection()

        # Fallback to WMI if HTTP not available
        if not self.use_http:
            self._try_wmi_connection()

    def _compile_regex_patterns(self):
        """Pre-compile regex patterns for better performance"""
        return {
            'fan_numbers': re.compile(r'\d+'),
            'fan_sanitize': re.compile(r'[^a-zA-Z0-9_]'),
            'fan_underscore': re.compile(r'_+')
        }

    def _get_http_session(self):
        """Get or create HTTP session for connection reuse"""
        if self._session is None:
            self._session = requests.Session()
            self._session.timeout = 10
        return self._session

    def _try_http_connection(self):
        """Attempt to connect to LibreHardwareMonitor HTTP API"""
        try:
            logger.debug(f"Testing LibreHardwareMonitor HTTP API at {self.http_url}")
            session = self._get_http_session()
            response = session.get(f"{self.http_url}/data.json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "Children" in data:  # Validate response structure
                    self.use_http = True
                    self.connected = True
                    logger.info(f"🚀 Connected to LibreHardwareMonitor HTTP API at {self.http_url}")
                    logger.info("✅ Performance optimized mode enabled (HTTP API)")
                    return
                else:
                    logger.debug("HTTP response structure invalid")
            else:
                logger.debug(f"HTTP API returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.debug(f"HTTP API connection failed - LibreHardwareMonitor HTTP server not running on {self.http_url}")
        except requests.exceptions.Timeout:
            logger.debug("HTTP API connection timeout")
        except Exception as e:
            logger.debug(f"HTTP API connection error: {e}")

        logger.debug("HTTP API not available, will try WMI fallback")

    def _try_wmi_connection(self):
        """Fallback to WMI connection"""
        if not WMI_AVAILABLE:
            logger.warning("WMI module not available. Install with: pip install wmi pywin32")
            logger.info("💡 For better performance, enable LibreHardwareMonitor HTTP server in Options")
            self.connected = False
            return

        try:
            logger.debug("Attempting WMI connection to LibreHardwareMonitor")
            self.w = wmi.WMI(namespace="root\\LibreHardwareMonitor")
            self.connected = True
            self.use_http = False
            logger.info("⚠️  Connected via WMI fallback (higher CPU usage)")
            logger.info("💡 Enable LibreHardwareMonitor HTTP server for better performance")
        except Exception as e:
            logger.warning(f"Failed to connect to LibreHardwareMonitor WMI: {e}")
            logger.warning("LibreHardwareMonitor may not be running or WMI/HTTP may not be enabled")
            logger.info("Monitor will run in demo mode - no metrics will be collected")
            self.connected = False
            self.w = None

    def get_sensors(self) -> List:
        """Get all hardware sensors via HTTP API or WMI"""
        if not self.connected:
            return []

        if self.use_http:
            return self._get_sensors_http()
        else:
            return self._get_sensors_wmi()

    def _get_sensors_http(self) -> List[Dict]:
        """Get sensors from LibreHardwareMonitor HTTP API"""
        try:
            session = self._get_http_session()
            response = session.get(f"{self.http_url}/data.json")
            if response.status_code == 200:
                data = response.json()
                
                # Debug: Log the structure to understand the HTTP API format
                logger.debug(f"HTTP API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                if isinstance(data, dict) and "Children" in data:
                    logger.debug(f"Root has {len(data['Children'])} children")
                    
                    # Quick count to see if sensors exist anywhere
                    total_sensor_count = self._count_sensors_in_tree(data)
                    logger.debug(f"Total sensors found in JSON tree: {total_sensor_count}")
                
                sensors = self._extract_sensors_from_json(data)
                logger.debug(f"Retrieved {len(sensors)} sensors via HTTP API")
                
                # Debug: If extraction failed but sensors exist, investigate
                if len(sensors) == 0 and isinstance(data, dict):
                    logger.debug("No sensors extracted - investigating JSON structure and hierarchy...")
                    # Check for variable hierarchy depths
                    self._analyze_hierarchy_depths(data)
                    self._debug_json_structure(data, depth=0, max_depth=4)
                
                return sensors
            else:
                logger.error(f"HTTP API error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching sensors via HTTP: {e}")
            return []
    
    def _count_sensors_in_tree(self, node):
        """Count all sensors in the JSON tree"""
        count = 0
        if isinstance(node, dict):
            # Check if this node is a sensor
            if "Type" in node and ("RawValue" in node or "Value" in node):
                count += 1
            # Check children
            if "Children" in node and isinstance(node["Children"], list):
                for child in node["Children"]:
                    count += self._count_sensors_in_tree(child)
        return count
    
    def _analyze_hierarchy_depths(self, node, path="", depth=0, max_depth=6):
        """Analyze hierarchy depths to understand LibreHardwareMonitor structure"""
        if depth > max_depth:
            return
            
        if isinstance(node, dict):
            current_path = f"{path}/{node.get('Text', 'Unknown')}"
            
            # Check if this node has sensors
            direct_sensors = self._count_direct_sensors_at_level(node)
            if direct_sensors > 0:
                logger.debug(f"Sensors found at depth {depth}: {current_path} ({direct_sensors} sensors)")
            
            # Check children
            if "Children" in node and isinstance(node["Children"], list):
                for child in node["Children"]:
                    self._analyze_hierarchy_depths(child, current_path, depth + 1, max_depth)
    
    def _count_direct_sensors_at_level(self, node):
        """Count sensors at current level and immediate children"""
        count = 0
        
        # Check if this node is a sensor
        if "Type" in node and ("RawValue" in node or "Value" in node):
            count += 1
        
        # Check immediate children
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                if isinstance(child, dict) and "Type" in child and ("RawValue" in child or "Value" in child):
                    count += 1
        
        return count
    
    def _debug_json_structure(self, node, depth=0, max_depth=4):
        """Debug helper to understand JSON structure"""
        if depth > max_depth:
            return
            
        indent = "  " * depth
        if isinstance(node, dict):
            node_text = node.get('Text', 'No Text')
            logger.debug(f"{indent}Node: {node_text}")
            logger.debug(f"{indent}Keys: {list(node.keys())}")
            
            # Check if this is a sensor
            if "Type" in node:
                sensor_type = node.get('Type')
                has_raw = 'RawValue' in node
                has_value = 'Value' in node
                logger.debug(f"{indent}*** SENSOR: Type={sensor_type}, RawValue={has_raw}, Value={has_value}")
                if has_raw:
                    logger.debug(f"{indent}    RawValue: {node.get('RawValue')}")
                if has_value:
                    logger.debug(f"{indent}    Value: {node.get('Value')}")
                    
            # Check children
            if "Children" in node and isinstance(node["Children"], list):
                children_count = len(node["Children"])
                logger.debug(f"{indent}Children: {children_count}")
                
                # Show a few children for debugging
                for i, child in enumerate(node["Children"][:3]):  # First 3 children only
                    logger.debug(f"{indent}Child {i}:")
                    self._debug_json_structure(child, depth + 1, max_depth)
                    
                if children_count > 3:
                    logger.debug(f"{indent}... and {children_count - 3} more children")
        else:
            logger.debug(f"{indent}Non-dict: {type(node)}")

    def _get_sensors_wmi(self) -> List:
        """Get sensors from WMI (fallback method)"""
        if not self.w:
            return []
        try:
            sensors = self.w.Sensor()
            logger.debug(f"Retrieved {len(sensors)} sensors via WMI")
            return sensors
        except Exception as e:
            logger.error(f"Error reading WMI sensors: {e}")
            return []

    def _extract_sensors_from_json(self, node, parent_path="") -> List[Dict]:
        """Extract sensors from LibreHardwareMonitor JSON tree"""
        sensors = []

        # Build parent path
        if "Text" in node and node["Text"]:
            # Clean text for parent path
            clean_text = node["Text"].lower().replace(' ', '').replace('#', '')
            if parent_path:
                current_path = f"{parent_path}/{clean_text}"
            else:
                current_path = f"/{clean_text}"
        else:
            current_path = parent_path

        # Check if this node is a sensor - LibreHardwareMonitor HTTP API format
        is_sensor = False
        sensor_type = None
        sensor_value = None
        sensor_name = node.get("Text", "Unknown")

        # LibreHardwareMonitor HTTP API uses "Type" + "Value" (formatted string)
        # RawValue is typically "N/A" in HTTP API, so we need to parse Value
        if "Type" in node and "Value" in node:
            raw_value = node.get("RawValue")
            value_str = node.get("Value")
            
            if raw_value is not None and raw_value != "N/A" and str(raw_value).lower() != "n/a":
                # Preferred: Use RawValue if available and not N/A
                is_sensor = True
                sensor_type = node["Type"] 
                sensor_value = raw_value
                logger.debug(f"Found sensor with RawValue: {sensor_name} = {sensor_value} ({sensor_type}) at {current_path}")
            elif value_str is not None and value_str != "" and str(value_str).lower() != "n/a":
                # Fallback: Parse formatted Value string (e.g., "45.2 °C", "1850 RPM")
                is_sensor = True
                sensor_type = node["Type"]
                sensor_value = value_str
                logger.debug(f"Found sensor with Value string: {sensor_name} = {sensor_value} ({sensor_type}) at {current_path}")

        # If this is a sensor node, add it
        if is_sensor and sensor_type and sensor_value is not None:
            # Convert to WMI-like structure for compatibility
            try:
                # Handle both numeric and formatted string values
                if isinstance(sensor_value, (int, float)):
                    # Direct numeric value (from RawValue)
                    numeric_value = float(sensor_value)
                else:
                    # Parse formatted string (from Value field like "45.2 °C", "1850 RPM")
                    numeric_value = self._parse_sensor_value(str(sensor_value))
                    
                # Only add sensors with valid numeric values
                if numeric_value is not None and numeric_value >= 0:
                    sensor_data = {
                        "SensorType": sensor_type,
                        "Name": sensor_name,
                        "Value": numeric_value,
                        "Parent": current_path,
                        "Min": self._parse_sensor_value(str(node.get("Min", "0"))) or 0.0,
                        "Max": self._parse_sensor_value(str(node.get("Max", "0"))) or 0.0
                    }
                    sensors.append(sensor_data)
                    logger.debug(f"Added sensor: {sensor_type}/{sensor_name} = {numeric_value} (path: {current_path})")
                else:
                    logger.debug(f"Skipped sensor with invalid value: {sensor_name} = {sensor_value} -> {numeric_value}")
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse sensor value {sensor_value}: {e}")

        # Process children recursively
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                sensors.extend(self._extract_sensors_from_json(child, current_path))

        return sensors

    def _parse_sensor_value(self, value_str: str) -> float:
        """Parse sensor value from string, handling units and European decimal format"""
        if not value_str or value_str == "" or str(value_str).lower() in ["n/a", "null", "none"]:
            return None

        # Remove common units and clean up the string
        cleaned = str(value_str).replace('°C', '').replace('RPM', '').replace('%', '').replace('MHz', '').replace('W', '').replace('GB', '').replace('MB', '').replace('V', '').replace('A', '').strip()
        
        # Handle European decimal format (comma as decimal separator)
        cleaned = cleaned.replace(',', '.')
        
        # Remove any remaining non-numeric characters except decimal point and minus
        import re
        cleaned = re.sub(r'[^0-9.\-]', '', cleaned)
        
        try:
            value = float(cleaned)
            return value if value >= 0 else None  # Return None for negative values
        except (ValueError, TypeError):
            logger.debug(f"Could not parse sensor value: '{value_str}' -> '{cleaned}'")
            return None

    def _is_cpu_sensor(self, parent: str) -> bool:
        """Check if sensor belongs to CPU (Intel, AMD, or other)"""
        if not parent:
            return False

        parent_lower = parent.lower()

        # Comprehensive CPU detection patterns
        cpu_patterns = [
            "/cpu",          # Generic CPU path
            "/amdcpu",       # AMD-specific path
            "/intelcpu",     # Intel-specific path
            "cpu",           # Generic CPU in path
            "processor",     # Alternative CPU naming
            "ryzen",         # AMD Ryzen series
            "threadripper",  # AMD Threadripper
            "epyc",          # AMD EPYC
            "intel",         # Intel processors
            "xeon",          # Intel Xeon
            "core",          # Intel Core series
        ]

        return any(pattern in parent_lower for pattern in cpu_patterns)

    def update_metrics(self):
        """Update all Prometheus metrics"""
        sensors = self.get_sensors()

        if not sensors:
            logger.warning("No sensors found - is LibreHardwareMonitor running with HTTP server or WMI enabled?")
            return

        logger.debug(f"Processing {len(sensors)} sensors ({('HTTP API' if self.use_http else 'WMI')})")
        
        # Debug: Log sensor types for troubleshooting
        if logger.isEnabledFor(logging.DEBUG):
            sensor_types = {}
            for sensor in sensors:
                if isinstance(sensor, dict):
                    stype = sensor.get('SensorType', 'Unknown')
                else:
                    stype = getattr(sensor, 'SensorType', 'Unknown')
                sensor_types[stype] = sensor_types.get(stype, 0) + 1
            logger.debug(f"Sensor types found: {dict(sensor_types)}")

        for sensor in sensors:
            try:
                # Handle both HTTP API dict structure and WMI object structure
                if isinstance(sensor, dict):
                    # HTTP API response structure
                    sensor_type = sensor.get('SensorType', '')
                    sensor_name = sensor.get('Name', '')
                    value = float(sensor.get('Value', 0)) if sensor.get('Value') is not None else 0
                    parent = sensor.get('Parent', '')
                else:
                    # WMI object structure
                    sensor_type = getattr(sensor, 'SensorType', '')
                    sensor_name = getattr(sensor, 'Name', '')
                    # Fix: properly handle 0 values - only skip None/empty values
                    raw_value = getattr(sensor, 'Value', None)
                    value = float(raw_value) if raw_value is not None else 0
                    parent = getattr(sensor, 'Parent', '') or ''

                # Skip sensors with no name - allow 0 values as they're valid
                if not sensor_name:
                    continue
                
                # Only skip clearly invalid negative values for certain sensor types
                if value < 0 and sensor_type in ["Temperature", "Load", "Clock", "Power", "Fan"]:
                    continue
                
                # Determine component type for better metric naming
                component_type = ""
                if self._is_cpu_sensor(parent):
                    component_type = "cpu"
                elif "gpu" in parent.lower() or "geforce" in parent.lower() or "radeon" in parent.lower():
                    component_type = "gpu"
                elif "motherboard" in parent.lower() or any(mb in parent.lower() for mb in ["asrock", "asus", "msi", "gigabyte"]):
                    component_type = "motherboard"
                elif "memory" in parent.lower():
                    component_type = "memory"
                elif any(drive in parent.lower() for drive in ["ssd", "hdd", "wdc", "samsung", "elements"]):
                    component_type = "storage"
                elif any(net in parent.lower() for net in ["ethernet", "bluetooth", "tailscale"]):
                    component_type = "network"
                    
                # Get standardized metric name
                standardized_name = get_standardized_metric_name(sensor_name, component_type, sensor_type.lower())
                
                logger.debug(f"Processing sensor: {sensor_type}/{sensor_name} = {value} (parent: {parent}) -> {standardized_name}")

                # CPU Temperature
                if sensor_type == "Temperature" and self._is_cpu_sensor(parent):
                    # Clean up temperature sensor names for better display
                    if "ccd" in sensor_name.lower():
                        # Convert "CCD1 (Tdie)" or "CCD1" to "Core Complex 1"
                        sensor_label = sensor_name.replace("CCD", "Core Complex ").replace(" (Tdie)", "")
                    elif "tctl" in sensor_name.lower():
                        sensor_label = "CPU Package"
                    elif "die" in sensor_name.lower():
                        sensor_label = "CPU Die"
                    else:
                        sensor_label = sensor_name
                    cpu_temp.labels(sensor=sensor_label).set(value)

                # CPU Load
                elif sensor_type == "Load" and self._is_cpu_sensor(parent):
                    # Clean up core names (e.g., "CPU Core #1" -> "core1", "CPU Total" -> "total")
                    if "total" in sensor_name.lower():
                        core_label = "total"
                    else:
                        core_label = sensor_name.lower().replace("cpu ", "").replace("#", "").replace(" ", "")
                    cpu_load.labels(core=core_label).set(value)

                # CPU Clock
                elif sensor_type == "Clock" and self._is_cpu_sensor(parent):
                    if "total" in sensor_name.lower():
                        core_label = "total"
                    else:
                        core_label = sensor_name.lower().replace("cpu ", "").replace("#", "").replace(" ", "")
                    cpu_clock.labels(core=core_label).set(value)

                # GPU Temperature
                elif sensor_type == "Temperature" and any(x in parent.lower() for x in ["/gpu", "nvidia", "amd", "radeon"]):
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"
                    gpu_temp.labels(gpu=gpu_name).set(value)

                # GPU Load
                elif sensor_type == "Load" and any(x in parent.lower() for x in ["/gpu", "nvidia", "amd", "radeon"]):
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"
                    load_type = "core" if "Core" in sensor_name else "memory" if "Memory" in sensor_name else "other"
                    gpu_load.labels(gpu=gpu_name, type=load_type).set(value)

                # GPU Memory
                elif (sensor_type in ["SmallData", "Data"] and "Memory Used" in sensor_name and 
                      any(x in parent.lower() for x in ["/gpu", "nvidia", "amd", "radeon"])):
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"

                    # Enhanced unit detection and conversion for GPU memory
                    if value < 0:  # Skip invalid negative values
                        continue
                    elif value < 32:  # Likely already in GB (0.0 - 31.9 GB range)
                        memory_gb = round(value, 2)
                    elif value < 32000:  # Likely in MB (32 MB - 31.9 GB when converted)
                        memory_gb = round(value / 1024, 2)
                    else:  # Likely in KB or bytes
                        memory_gb = round(value / (1024 * 1024), 2)
                    
                    # Sanity check: GPU memory should be reasonable (0.0 GB to 128 GB)
                    if 0.0 <= memory_gb <= 128:
                        gpu_memory.labels(gpu=gpu_name).set(memory_gb)
                        if memory_gb > 0:  # Log non-zero values
                            logger.debug(f"GPU {gpu_name} memory: {value} -> {memory_gb} GB")
                    else:
                        logger.debug(f"Skipping invalid GPU memory value: {value} -> {memory_gb} GB")                # GPU Clock
                elif sensor_type == "Clock" and any(x in parent.lower() for x in ["/gpu", "nvidia", "amd", "radeon"]):
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"
                    clock_type = "core" if "Core" in sensor_name else "memory" if "Memory" in sensor_name else "other"
                    gpu_clock.labels(gpu=gpu_name, type=clock_type).set(value)

                # CPU Power
                elif sensor_type == "Power" and self._is_cpu_sensor(parent) and "Package" in sensor_name:
                    # CPU Package power consumption
                    cpu_power.labels(sensor="CPU Package").set(value)

                # GPU Power
                elif sensor_type == "Power" and any(x in parent.lower() for x in ["/gpu", "nvidia", "amd", "radeon"]) and "Package" in sensor_name:
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0" 
                    gpu_power.labels(gpu=gpu_name).set(value)

                # Fan Speeds
                elif sensor_type == "Fan":
                    # Categorize and label fans intelligently (optimized with cached patterns)
                    fan_name_lower = sensor_name.lower()

                    # Use cached patterns for performance
                    patterns = self._compiled_patterns

                    if "gpu" in fan_name_lower or "vga" in fan_name_lower:
                        fan_type = "gpu"
                        # Extract number from sensor name more reliably
                        numbers = patterns['fan_numbers'].findall(sensor_name)
                        if numbers:
                            fan_label = f"gpu_fan_{numbers[0]}"
                        else:
                            fan_label = "gpu_fan"
                    elif "cpu" in fan_name_lower:
                        fan_type = "cpu"
                        numbers = patterns['fan_numbers'].findall(sensor_name)
                        if numbers:
                            fan_label = f"cpu_fan_{numbers[0]}"
                        else:
                            fan_label = "cpu_fan"
                    elif "cha" in fan_name_lower or "chassis" in fan_name_lower or "case" in fan_name_lower:
                        fan_type = "chassis"
                        numbers = patterns['fan_numbers'].findall(sensor_name)
                        if numbers:
                            fan_label = f"chassis_fan_{numbers[0]}"
                        else:
                            fan_label = "chassis_fan"
                    else:
                        fan_type = "other"
                        # Sanitize fan label for Prometheus (optimized with cached patterns)
                        fan_label = patterns['fan_sanitize'].sub('_', sensor_name.lower())
                        fan_label = patterns['fan_underscore'].sub('_', fan_label).strip('_')
                        if not fan_label:
                            fan_label = "unknown_fan"

                    fan_rpm.labels(fan=fan_label, type=fan_type).set(value)

                # Memory (from motherboard/system)
                elif sensor_type == "Data":
                    if "Memory Used" in sensor_name:
                        # Convert to GB if the value is in bytes/MB
                        if value > 1000:  # Likely in MB or bytes
                            memory_value = value / 1024 if value > 10000 else value  # MB to GB conversion if needed
                        else:
                            memory_value = value  # Already in GB
                        memory_used.set(memory_value)
                    elif "Memory Available" in sensor_name:
                        # Convert to GB if the value is in bytes/MB
                        if value > 1000:  # Likely in MB or bytes
                            memory_value = value / 1024 if value > 10000 else value  # MB to GB conversion if needed
                        else:
                            memory_value = value  # Already in GB
                        memory_available.set(memory_value)

            except Exception as e:
                logger.debug(f"Error processing sensor {sensor_name if 'sensor_name' in locals() else 'unknown'}: {e}")
                continue

    def get_system_info(self) -> Dict:
        """Get system information via HTTP API or WMI"""
        if not self.connected:
            return {'cpu': 'Demo CPU', 'gpu': 'Demo GPU', 'motherboard': 'Demo Board'}

        if self.use_http:
            return self._get_system_info_http()
        else:
            return self._get_system_info_wmi()

    def _get_system_info_http(self) -> Dict:
        """Get system info from HTTP API"""
        try:
            response = requests.get(f"{self.http_url}/data.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._extract_system_info_from_json(data)
            else:
                return {'cpu': 'Unknown', 'gpu': 'Unknown', 'motherboard': 'Unknown'}
        except Exception as e:
            logger.error(f"Error getting system info via HTTP: {e}")
            return {'cpu': 'Unknown', 'gpu': 'Unknown', 'motherboard': 'Unknown'}

    def _get_system_info_wmi(self) -> Dict:
        """Get system info from WMI (fallback)"""
        if not self.w:
            return {'cpu': 'Demo CPU', 'gpu': 'Demo GPU', 'motherboard': 'Demo Board'}

        try:
            hardware = self.w.Hardware()
            info = {
                'cpu': 'Unknown',
                'gpu': 'Unknown', 
                'motherboard': 'Unknown'
            }

            for hw in hardware:
                hw_type = getattr(hw, 'HardwareType', '') or ''
                hw_name = getattr(hw, 'Name', '') or 'Unknown'

                if not hw_type:  # Skip if no hardware type
                    continue

                logger.debug(f"Found hardware: Type={hw_type}, Name={hw_name}")

                if hw_type.lower() in ["cpu", "processor"] or "cpu" in hw_type.lower() or "processor" in hw_type.lower():
                    info['cpu'] = hw_name
                    logger.info(f"Detected CPU: {hw_name}")
                elif "gpu" in hw_type.lower() or "nvidia" in hw_type.lower() or "amd" in hw_type.lower():
                    info['gpu'] = hw_name
                    logger.info(f"Detected GPU: {hw_name}")
                elif "motherboard" in hw_type.lower():
                    info['motherboard'] = hw_name
                    logger.info(f"Detected Motherboard: {hw_name}")

            return info
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'cpu': 'Unknown', 'gpu': 'Unknown', 'motherboard': 'Unknown'}

    def _extract_system_info_from_json(self, data) -> Dict:
        """Extract hardware info from JSON data"""
        info = {'cpu': 'Unknown', 'gpu': 'Unknown', 'motherboard': 'Unknown'}

        def search_hardware_node(node):
            if "Text" in node and node["Text"]:
                text = node["Text"]
                text_lower = text.lower()

                # CPU detection
                if any(x in text_lower for x in ["intel", "amd", "ryzen", "core i", "threadripper", "epyc"]):
                    if not any(x in text_lower for x in ["gpu", "graphics", "radeon rx", "geforce"]):
                        info['cpu'] = text
                        logger.debug(f"Detected CPU: {text}")

                # GPU detection
                elif any(x in text_lower for x in ["nvidia", "geforce", "quadro", "rtx", "gtx", "radeon", "rx "]):
                    info['gpu'] = text 
                    logger.debug(f"Detected GPU: {text}")

                # Motherboard detection
                elif any(x in text_lower for x in ["motherboard", "mainboard", "asus", "msi", "gigabyte", "asrock", "evga"]):
                    if "gpu" not in text_lower:  # Avoid GPU manufacturers
                        info['motherboard'] = text
                        logger.debug(f"Detected Motherboard: {text}")

            # Search children
            if "Children" in node and isinstance(node["Children"], list):
                for child in node["Children"]:
                    search_hardware_node(child)

        search_hardware_node(data)
        return info


def main():
    parser = argparse.ArgumentParser(description='Rigbeat - Prometheus Exporter')
    parser.add_argument('--port', type=int, default=9182, help='Port to expose metrics (default: 9182)')
    parser.add_argument('--interval', type=int, default=15, help='Update interval in seconds (default: 15, use 2-5 for real-time gaming or 10+ for general monitoring)')
    parser.add_argument('--logfile', type=str, help='Log file path (e.g., rigbeat.log)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--http-host', type=str, default='localhost', help='LibreHardwareMonitor HTTP API host (default: localhost)')
    parser.add_argument('--http-port', type=int, default=8085, help='LibreHardwareMonitor HTTP API port (default: 8085)')
    args = parser.parse_args()

    # Configure file logging if requested
    if args.logfile:
        file_handler = logging.FileHandler(args.logfile)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    # Set debug level if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    logger.info(f"Starting Rigbeat Exporter v0.1.3 on port {args.port}")
    logger.info(f"Update interval: {args.interval} seconds")

    if args.debug:
        logger.debug(f"LibreHardwareMonitor HTTP API target: {args.http_host}:{args.http_port}")
        logger.debug(f"WMI fallback: {'Available' if WMI_AVAILABLE else 'Not available (install with: pip install wmi pywin32)'}")

    # Initialize monitor
    try:
        monitor = HardwareMonitor(http_host=args.http_host, http_port=args.http_port)
        if not monitor.connected:
            logger.error("Failed to initialize hardware monitor. Check LibreHardwareMonitor setup.")
            logger.info("💡 Setup help:")
            logger.info("   1. Ensure LibreHardwareMonitor is running")
            logger.info("   2. Enable HTTP server in Options → Web Server (port 8085)")
            logger.info("   3. Or enable WMI in Options → WMI Provider")
            return 1
    except Exception as e:
        logger.error(f"Failed to initialize hardware monitor: {e}")
        return 1

    # Get and set system info
    sys_info = monitor.get_system_info()
    system_info.info(sys_info)
    logger.info(f"System: CPU={sys_info['cpu']}, GPU={sys_info['gpu']}")

    if monitor.use_http:
        logger.info("🚀 Using LibreHardwareMonitor HTTP API (optimized performance)")
    else:
        logger.info("⚠️  Using WMI fallback (higher CPU usage)")
        logger.info("💡 Enable HTTP server in LibreHardwareMonitor for better performance")

    # Start Prometheus HTTP server
    start_http_server(args.port)
    logger.info(f"Metrics available at http://localhost:{args.port}/metrics")

    # Windows Firewall reminder
    if args.port != 9182:
        logger.warning(f"Using non-default port {args.port} - ensure Windows Firewall allows this port")
    logger.info(f"🔥 Windows Firewall: Ensure port {args.port} is allowed for Prometheus scraping")
    logger.info(f"   Run: netsh advfirewall firewall add rule name=\"Rigbeat\" dir=in action=allow protocol=TCP localport={args.port}")

    # Main loop
    try:
        logger.info("Starting metrics collection loop...")
        while True:
            start_time = time.time()
            monitor.update_metrics()
            update_duration = time.time() - start_time

            if args.debug:
                logger.debug(f"Metrics update completed in {update_duration:.3f}s")

            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())