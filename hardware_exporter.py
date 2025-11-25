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

# Sensor Filtering Configuration
# Control which sensor types and components to monitor for performance optimization
SENSOR_FILTER_CONFIG = {
    # Essential sensors (always included) - core gaming/monitoring metrics
    'essential': {
        'cpu': ['Temperature', 'Load', 'Power'],      # CPU temps, loads, power (includes package power)
        'gpu': ['Temperature', 'Load', 'Power', 'Fan', 'Clock', 'Data'],  # GPU essentials + memory (includes core temp, memory used/free/total)
        'motherboard': ['Temperature', 'Fan'],         # System temps and cooling
        'memory': ['Data'],                            # Main RAM usage
    },
    
    # Extended sensors (optional) - detailed monitoring
    'extended': {
        'cpu': ['Clock', 'Voltage'],                  # CPU frequencies, voltages
        'gpu': ['Throughput'],                        # GPU PCIe traffic  
        'motherboard': ['Voltage'],                   # System voltages
        'memory': ['Load'],                           # Virtual memory stats
        'storage': ['Temperature', 'Load', 'Throughput'],  # Drive monitoring
        'network': ['Load', 'Data', 'Throughput'],    # Network monitoring
    },
    
    # Diagnostic sensors (development/troubleshooting) - everything
    'diagnostic': 'all'  # Include all sensors found
}

# Default monitoring mode - can be changed via command line
DEFAULT_SENSOR_MODE = 'essential'  # Options: 'essential', 'extended', 'diagnostic'

def should_include_sensor(sensor_type: str, component_type: str, mode: str = DEFAULT_SENSOR_MODE) -> bool:
    """
    Determine if a sensor should be included based on filtering configuration.
    
    Args:
        sensor_type: Type of sensor (Temperature, Load, Fan, etc.)
        component_type: Component type (cpu, gpu, motherboard, etc.)
        mode: Monitoring mode ('essential', 'extended', 'diagnostic')
    
    Returns:
        True if sensor should be included, False otherwise
    """
    if mode == 'diagnostic':
        return True
    
    # Check essential sensors first (always included)
    essential = SENSOR_FILTER_CONFIG.get('essential', {})
    if component_type in essential and sensor_type in essential[component_type]:
        return True
    
    # Check extended sensors if in extended mode
    if mode == 'extended':
        extended = SENSOR_FILTER_CONFIG.get('extended', {})
        if component_type in extended and sensor_type in extended[component_type]:
            return True
    
    return False

# Sensor Mapping Configuration
# Maps LibreHardwareMonitor sensor names to standardized Prometheus metric names
SENSOR_NAME_MAPPING = {
    # CPU Temperature Sensors
    'Core (Tctl/Tdie)': 'cpu_temp_tctl',
    'CCD1 (Tdie)': 'cpu_temp_ccd1',
    'CCD2 (Tdie)': 'cpu_temp_ccd2', 
    'Package': 'cpu_package_temp',
    'Core Max': 'cpu_core_max_temp',
    'Core Average': 'cpu_core_avg_temp',
    
    # CPU Load Sensors (generic patterns)
    'CPU Total': 'cpu_load_total',
    'CPU Core Max': 'cpu_core_max_load',
    # Note: Individual cores handled dynamically (Core #1, Core #2, etc.)
    
    # CPU Clock Sensors
    'Bus Speed': 'cpu_bus_speed',
    # Note: Individual cores handled dynamically
    
    # CPU Power Sensors
    'Package': 'cpu_package_power',              # CPU Package power (common name)
    'CPU Package': 'cpu_package_power',          # Alternative CPU Package name
    'Package (SMU)': 'cpu_package_power',        # AMD SMU power reporting
    'Core': 'cpu_core_power',                    # Generic core power
    # Note: Package and individual cores handled dynamically
    
    # CPU Voltage Sensors
    'Core (SVI2 TFN)': 'cpu_core_voltage',
    'SoC (SVI2 TFN)': 'cpu_soc_voltage',
    
    # GPU Temperature Sensors
    'GPU Core': 'gpu_temp_core',                 # Main GPU core temp
    'GPU Temperature': 'gpu_temp_core',          # Alternative GPU core temp name
    'Core': 'gpu_temp_core',                     # Simple core name in GPU context
    'GPU Hot Spot': 'gpu_temp_hotspot',
    'GPU Memory': 'gpu_temp_memory',
    'GPU Memory Junction': 'gpu_temp_memory_junction',
    'Hot Spot': 'gpu_temp_hotspot',              # Alternative hotspot name
    
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
    
    # GPU Fan Sensors (dynamic numbering)
    # Note: GPU Fan 1, GPU Fan 2, etc. handled dynamically
    
    # GPU Memory Sensors
    'GPU Memory Free': 'gpu_memory_free',
    'GPU Memory Used': 'gpu_memory_used',
    'GPU Memory Total': 'gpu_memory_total',
    'Memory Free': 'gpu_memory_free',            # Alternative name in GPU context
    'Memory Used': 'gpu_memory_used',            # Alternative name in GPU context
    'Memory Total': 'gpu_memory_total',          # Alternative name in GPU context
    'GPU Dedicated Memory Free': 'gpu_memory_free',    # NVIDIA naming
    'GPU Dedicated Memory Used': 'gpu_memory_used',    # NVIDIA naming
    
    # GPU Throughput Sensors
    'GPU PCIe Rx': 'gpu_pcie_rx_throughput',
    'GPU PCIe Tx': 'gpu_pcie_tx_throughput',
    
    # Motherboard Temperature Sensors (generic numbering)
    # Note: Temperature #1, Temperature #2, etc. handled dynamically
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
    # Note: Chassis Fan #1, Chassis Fan #2, etc. handled dynamically
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
        Standardized metric name or generated name if no mapping found
    """
    # First try direct mapping
    if sensor_name in SENSOR_NAME_MAPPING:
        return SENSOR_NAME_MAPPING[sensor_name]
    
    # Handle dynamic patterns for numbered sensors
    # CPU Core patterns: "Core #1", "Core #2", etc.
    if re.match(r'^Core #\d+', sensor_name):
        core_num = re.search(r'#(\d+)', sensor_name).group(1)
        if sensor_type.lower() in ['load', 'temperature']:
            return f"cpu_core_{core_num}_load" if 'load' in sensor_type.lower() else f"cpu_core_{core_num}_temp"
        elif sensor_type.lower() == 'clock':
            return f"cpu_core_{core_num}_clock"
        elif sensor_type.lower() == 'power':
            return f"cpu_core_{core_num}_power"
    
    # CPU Package Power patterns: "Package", "CPU Package", "Package (SMU)"
    elif sensor_type.lower() == 'power' and ('package' in sensor_name.lower() or sensor_name.lower() == 'package'):
        return 'cpu_package_power'
    
    # CPU Core Power patterns: "Core #1 (SMU)", "Core", etc.
    elif re.match(r'^Core #\d+.*SMU', sensor_name):
        core_num = re.search(r'#(\d+)', sensor_name).group(1)
        return f"cpu_core_{core_num}_power"
    elif sensor_type.lower() == 'power' and sensor_name.lower() == 'core' and component_type == 'cpu':
        return 'cpu_core_power'
    
    # GPU Fan patterns: "GPU Fan 1", "GPU Fan 2", etc.
    elif re.match(r'^GPU Fan \d+', sensor_name):
        fan_num = re.search(r'Fan (\d+)', sensor_name).group(1)
        return f"gpu_fan_{fan_num}_speed"
    
    # GPU context-aware patterns
    elif component_type == 'gpu':
        # GPU Temperature sensors with simple names in GPU context
        if sensor_type.lower() == 'temperature':
            if sensor_name.lower() in ['core', 'gpu core', 'gpu temperature']:
                return 'gpu_temp_core'
            elif 'memory' in sensor_name.lower():
                return 'gpu_temp_memory'
            elif 'hot' in sensor_name.lower() or 'hotspot' in sensor_name.lower():
                return 'gpu_temp_hotspot'
        
        # GPU Memory sensors (Data type) with simple names in GPU context
        elif sensor_type.lower() in ['data', 'smalldata']:
            if 'free' in sensor_name.lower() or sensor_name.lower() == 'memory free':
                return 'gpu_memory_free'
            elif 'used' in sensor_name.lower() or sensor_name.lower() == 'memory used':
                return 'gpu_memory_used'
            elif 'total' in sensor_name.lower() or sensor_name.lower() == 'memory total':
                return 'gpu_memory_total'
    
    # Motherboard Temperature patterns: "Temperature #1", "Temperature #2", etc.
    elif re.match(r'^Temperature #\d+', sensor_name):
        temp_num = re.search(r'#(\d+)', sensor_name).group(1)
        return f"motherboard_temp_{temp_num}"
    
    # Motherboard Voltage patterns: "Voltage #1", "Voltage #2", etc.
    elif re.match(r'^Voltage #\d+', sensor_name):
        volt_num = re.search(r'#(\d+)', sensor_name).group(1)
        return f"motherboard_voltage_{volt_num}"
    
    # Chassis Fan patterns: "Chassis Fan #1", "Chassis Fan #2", etc.
    elif re.match(r'^Chassis Fan #\d+', sensor_name):
        fan_num = re.search(r'#(\d+)', sensor_name).group(1)
        return f"motherboard_chassis_fan_{fan_num}"
    
    # CPU context-aware patterns (for sensors that might have generic names)
    elif component_type == 'cpu':
        # CPU Temperature sensors
        if sensor_type.lower() == 'temperature':
            if 'package' in sensor_name.lower():
                return 'cpu_package_temp'
            elif 'tctl' in sensor_name.lower() or 'tdie' in sensor_name.lower():
                return 'cpu_temp_tctl'
        # CPU Power sensors with generic names
        elif sensor_type.lower() == 'power':
            if 'package' in sensor_name.lower() or sensor_name.lower() == 'package':
                return 'cpu_package_power'
    
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

# Dynamic Prometheus metrics - created on demand for HTTP API sensors
hardware_metrics = {}

def get_or_create_metric(metric_name: str, sensor_type: str, help_text: str = ""):
    """
    Get existing metric or create new one dynamically for HTTP API sensors.
    
    Args:
        metric_name: Standardized metric name  
        sensor_type: Type of sensor (Temperature, Load, etc.)
        help_text: Help text for the metric
    
    Returns:
        Prometheus Gauge metric
    """
    if metric_name not in hardware_metrics:
        # Create appropriate help text if not provided
        if not help_text:
            unit_map = {
                'Temperature': 'celsius', 'Load': 'percent', 'Clock': 'mhz', 
                'Power': 'watts', 'Fan': 'rpm', 'Voltage': 'volts',
                'Data': 'mb', 'Throughput': 'mb_per_sec'
            }
            unit = unit_map.get(sensor_type, 'units')
            help_text = f"{sensor_type} sensor value in {unit}"
        
        # Create the metric with rigbeat prefix and no labels (metric name is descriptive enough)
        full_metric_name = f"rigbeat_{metric_name}"
        hardware_metrics[metric_name] = Gauge(full_metric_name, help_text)
        logger.debug(f"Created new metric: {full_metric_name}")
    
    return hardware_metrics[metric_name]

system_info = Info('rigbeat_system', 'System information')


class HardwareMonitor:
    """Monitors hardware sensors via HTTP API (preferred) or WMI (fallback)"""

    def __init__(self, http_host="localhost", http_port=8085, sensor_mode=DEFAULT_SENSOR_MODE):
        self.http_host = http_host
        self.http_port = http_port
        self.http_url = f"http://{http_host}:{http_port}"
        self.sensor_mode = sensor_mode
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
        
        # Count sensors by filtering
        if self.sensor_mode != 'diagnostic':
            filtered_count = 0
            total_count = len(sensors)
            for sensor in sensors:
                if isinstance(sensor, dict):
                    sensor_type = sensor.get('SensorType', '')
                    parent = sensor.get('Parent', '')
                else:
                    sensor_type = getattr(sensor, 'SensorType', '')
                    parent = getattr(sensor, 'Parent', '') or ''
                
                # Quick component type detection for filtering
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
                
                if should_include_sensor(sensor_type, component_type, self.sensor_mode):
                    filtered_count += 1
            
            logger.info(f"📊 Monitoring {filtered_count}/{total_count} sensors (mode: {self.sensor_mode})")
        
        # Debug: Log sensor types for troubleshooting
        if logger.isEnabledFor(logging.DEBUG):
            sensor_types = {}
            critical_metrics = []
            for sensor in sensors:
                if isinstance(sensor, dict):
                    stype = sensor.get('SensorType', 'Unknown')
                    sname = sensor.get('Name', 'Unknown')
                else:
                    stype = getattr(sensor, 'SensorType', 'Unknown')
                    sname = getattr(sensor, 'Name', 'Unknown')
                sensor_types[stype] = sensor_types.get(stype, 0) + 1
                
                # Track critical metrics that user specifically mentioned
                if any(metric in sname for metric in ['GPU Memory Free', 'GPU Memory Used', 'GPU Memory Total', 'GPU Core', 'Package']):
                    critical_metrics.append(f"{stype}/{sname}")
            
            logger.debug(f"Sensor types found: {dict(sensor_types)}")
            if critical_metrics:
                logger.debug(f"Critical sensors found: {critical_metrics}")

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
                
                # Apply sensor filtering based on mode
                if not should_include_sensor(sensor_type, component_type, self.sensor_mode):
                    logger.debug(f"Filtered out sensor: {sensor_type}/{sensor_name} (mode: {self.sensor_mode})")
                    continue
                
                logger.debug(f"Processing sensor: {sensor_type}/{sensor_name} = {value} (parent: {parent}) -> {standardized_name}")

                # Create metric dynamically and set value
                metric = get_or_create_metric(standardized_name, sensor_type)
                
                # Set metric value directly (no labels needed - metric name is descriptive)
                try:
                    # Apply unit conversions for specific sensor types
                    converted_value = value
                    if sensor_type in ['Data', 'SmallData'] and 'memory' in standardized_name:
                        # Convert memory values: if >1000 assume MB, convert to GB
                        if value > 1000:
                            converted_value = round(value / 1024, 2)
                    
                    metric.set(converted_value)
                    logger.debug(f"✅ Set metric {standardized_name}: {converted_value}")
                    
                except Exception as e:
                    logger.warning(f"Failed to set metric {standardized_name}: {e}")

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
    parser.add_argument('--sensor-mode', type=str, default=DEFAULT_SENSOR_MODE, 
                        choices=['essential', 'extended', 'diagnostic'],
                        help='Sensor monitoring mode (default: essential) - essential: core metrics only (~20-30 sensors), extended: detailed monitoring (~50-80 sensors), diagnostic: all sensors (~150+ sensors)')
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
    logger.info(f"Sensor mode: {args.sensor_mode}")

    if args.debug:
        logger.debug(f"LibreHardwareMonitor HTTP API target: {args.http_host}:{args.http_port}")
        logger.debug(f"WMI fallback: {'Available' if WMI_AVAILABLE else 'Not available (install with: pip install wmi pywin32)'}")

    # Initialize monitor
    try:
        monitor = HardwareMonitor(http_host=args.http_host, http_port=args.http_port, sensor_mode=args.sensor_mode)
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