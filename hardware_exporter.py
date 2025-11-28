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
from collections import defaultdict
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
        'gpu': ['Temperature', 'Load', 'Power', 'Fan', 'Clock', 'Data', 'SmallData'],  # GPU essentials + memory (includes core temp, memory used/free/total)
        'motherboard': ['Temperature', 'Fan'],         # System temps and cooling
        'memory': ['Data', 'SmallData'],               # Main RAM usage (Data=GB, SmallData=MB)
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
# Note: Most mappings are now handled dynamically in get_standardized_metric_name()
# which uses context-aware logic (component_type + sensor_type) for accurate mapping.
# This avoids ambiguity issues with sensors that have the same name but different meanings
# (e.g., "GPU Core" appears in Temperature, Load, and Clock sensor types).

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
    sensor_type_lower = sensor_type.lower() if sensor_type else ''
    sensor_name_lower = sensor_name.lower() if sensor_name else ''
    
    # =========================================================================
    # CONTEXT-AWARE PATTERNS FIRST (component_type + sensor_type required)
    # These must be checked BEFORE static mappings to avoid ambiguous matches
    # =========================================================================
    
    # GPU context-aware patterns - check component AND sensor type together
    if component_type == 'gpu':
        # GPU Temperature sensors
        if sensor_type_lower == 'temperature':
            if sensor_name == 'GPU Core' or sensor_name_lower == 'core':
                return 'gpu_temp_core'
            elif 'memory' in sensor_name_lower and 'junction' in sensor_name_lower:
                return 'gpu_temp_memory_junction'
            elif 'memory' in sensor_name_lower:
                return 'gpu_temp_memory'
            elif 'hot' in sensor_name_lower or 'hotspot' in sensor_name_lower:
                return 'gpu_temp_hotspot'
        
        # GPU Load sensors
        elif sensor_type_lower == 'load':
            if sensor_name == 'GPU Core' or sensor_name_lower in ['core', 'gpu core']:
                return 'gpu_load_core'
            elif sensor_name == 'GPU Memory' or sensor_name_lower == 'gpu memory':
                return 'gpu_memory_load'  # Memory usage percentage
            elif 'memory controller' in sensor_name_lower:
                return 'gpu_load_memory_controller'
            elif 'video engine' in sensor_name_lower or sensor_name_lower == 'video engine':
                return 'gpu_load_video_engine'
            elif '3d' in sensor_name_lower or 'd3d' in sensor_name_lower:
                return 'gpu_load_3d'
            elif sensor_name_lower == 'bus' or sensor_name == 'GPU Bus':
                return 'gpu_load_bus'
            elif sensor_name_lower == 'power' or sensor_name == 'GPU Power':
                return 'gpu_load_power'
        
        # GPU Clock sensors
        elif sensor_type_lower == 'clock':
            if sensor_name == 'GPU Core' or sensor_name_lower == 'core':
                return 'gpu_core_clock'
            elif sensor_name == 'GPU Memory' or sensor_name_lower == 'memory':
                return 'gpu_memory_clock'
            elif 'shader' in sensor_name_lower:
                return 'gpu_shader_clock'
        
        # GPU Memory sensors (Data/SmallData type) - memory sizes in MB
        elif sensor_type_lower in ['data', 'smalldata']:
            # Explicit name matches first
            if sensor_name in ['GPU Memory Free', 'D3D Dedicated Memory Free', 'D3D Shared Memory Free']:
                return 'gpu_memory_free'
            elif sensor_name in ['GPU Memory Used', 'D3D Dedicated Memory Used', 'D3D Shared Memory Used']:
                return 'gpu_memory_used'
            elif sensor_name in ['GPU Memory Total', 'D3D Dedicated Memory Total', 'D3D Shared Memory Total']:
                return 'gpu_memory_total'
            # Partial matches
            elif 'free' in sensor_name_lower:
                return 'gpu_memory_free'
            elif 'used' in sensor_name_lower:
                return 'gpu_memory_used'
            elif 'total' in sensor_name_lower:
                return 'gpu_memory_total'
        
        # GPU Power sensors
        elif sensor_type_lower == 'power':
            if 'package' in sensor_name_lower:
                return 'gpu_package_power'
            elif 'board' in sensor_name_lower:
                return 'gpu_board_power'
        
        # GPU Fan sensors
        elif sensor_type_lower == 'fan':
            if re.match(r'^GPU Fan \d+', sensor_name):
                fan_num = re.search(r'Fan (\d+)', sensor_name).group(1)
                return f"gpu_fan_{fan_num}_speed"
            else:
                return 'gpu_fan_speed'
    
    # Memory (RAM) context-aware patterns
    elif component_type == 'memory':
        # Memory Load sensors
        if sensor_type_lower == 'load':
            if sensor_name == 'Memory' or sensor_name_lower == 'memory':
                return 'memory_load'
            elif 'virtual' in sensor_name_lower:
                return 'memory_virtual_load'
        
        # Memory Data sensors - distinguish physical vs virtual memory
        elif sensor_type_lower in ['data', 'smalldata']:
            is_virtual = 'virtual' in sensor_name_lower
            
            if 'available' in sensor_name_lower:
                return 'memory_virtual_available' if is_virtual else 'memory_available'
            elif 'used' in sensor_name_lower:
                return 'memory_virtual_used' if is_virtual else 'memory_used'
            elif 'total' in sensor_name_lower:
                return 'memory_virtual_total' if is_virtual else 'memory_total'
    
    # CPU context-aware patterns
    elif component_type == 'cpu':
        # CPU Temperature sensors
        if sensor_type_lower == 'temperature':
            if 'package' in sensor_name_lower:
                return 'cpu_package_temp'
            elif 'tctl' in sensor_name_lower or 'tdie' in sensor_name_lower:
                return 'cpu_temp_tctl'
            elif 'ccd1' in sensor_name_lower:
                return 'cpu_temp_ccd1'
            elif 'ccd2' in sensor_name_lower:
                return 'cpu_temp_ccd2'
            elif sensor_name == 'Core Max':
                return 'cpu_core_max_temp'
            elif sensor_name == 'Core Average':
                return 'cpu_core_avg_temp'
        
        # CPU Power sensors
        elif sensor_type_lower == 'power':
            if 'package' in sensor_name_lower or sensor_name_lower == 'package':
                return 'cpu_package_power'
            elif sensor_name_lower == 'core':
                return 'cpu_core_power'
        
        # CPU Load sensors
        elif sensor_type_lower == 'load':
            if sensor_name == 'CPU Total':
                return 'cpu_load_total'
            elif sensor_name == 'CPU Core Max':
                return 'cpu_core_max_load'
        
        # CPU Voltage sensors
        elif sensor_type_lower == 'voltage':
            if 'svi2' in sensor_name_lower and 'core' in sensor_name_lower:
                return 'cpu_core_voltage'
            elif 'svi2' in sensor_name_lower and 'soc' in sensor_name_lower:
                return 'cpu_soc_voltage'
    
    # =========================================================================
    # DYNAMIC PATTERNS (numbered sensors like Core #1, Chassis Fan #2, etc.)
    # =========================================================================
    
    # CPU Core patterns: "Core #1", "Core #2", etc.
    if re.match(r'^Core #\d+', sensor_name):
        core_num = re.search(r'#(\d+)', sensor_name).group(1)
        if sensor_type_lower == 'load':
            return f"cpu_core_{core_num}_load"
        elif sensor_type_lower == 'temperature':
            return f"cpu_core_{core_num}_temp"
        elif sensor_type_lower == 'clock':
            return f"cpu_core_{core_num}_clock"
        elif sensor_type_lower == 'power':
            return f"cpu_core_{core_num}_power"
    
    # CPU Core Power patterns with SMU: "Core #1 (SMU)", etc.
    elif re.match(r'^Core #\d+.*SMU', sensor_name):
        core_num = re.search(r'#(\d+)', sensor_name).group(1)
        return f"cpu_core_{core_num}_power"
    
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
    
    # GPU Fan patterns (fallback): "GPU Fan 1", "GPU Fan 2", etc.
    elif re.match(r'^GPU Fan \d+', sensor_name):
        fan_num = re.search(r'Fan (\d+)', sensor_name).group(1)
        return f"gpu_fan_{fan_num}_speed"
    
    # =========================================================================
    # STATIC MAPPINGS (only for unambiguous sensor names)
    # =========================================================================
    
    # Only use static mapping for clearly unambiguous names
    unambiguous_mappings = {
        # CPU sensors with unique names
        'Bus Speed': 'cpu_bus_speed',
        
        # Motherboard sensors
        'CPU': 'motherboard_cpu_temp',
        'Motherboard': 'motherboard_temp',
        'Vcore': 'motherboard_vcore',
        'AVCC': 'motherboard_avcc',
        '+3.3V': 'motherboard_3v3',
        '+3V Standby': 'motherboard_3v_standby',
        'CPU Termination': 'motherboard_cpu_termination',
        '+12V': 'motherboard_12v',
        '+5V': 'motherboard_5v',
        'Battery': 'motherboard_battery',
        'CPU Fan': 'motherboard_cpu_fan',
        'System Fan': 'motherboard_system_fan',
        
        # Storage sensors
        'Used Space': 'drive_used_space',
        'Free Space': 'drive_free_space',
        'Total Activity': 'drive_total_activity',
        'Read Rate': 'drive_read_rate',
        'Write Rate': 'drive_write_rate',
        'Read Activity': 'drive_read_activity',
        'Write Activity': 'drive_write_activity',
        
        # Network sensors
        'Download Speed': 'network_download_speed',
        'Upload Speed': 'network_upload_speed',
        'Data Downloaded': 'network_data_downloaded',
        'Data Uploaded': 'network_data_uploaded',
    }
    
    if sensor_name in unambiguous_mappings:
        return unambiguous_mappings[sensor_name]
    
    # =========================================================================
    # FALLBACK: Generate metric name from sensor name
    # =========================================================================
    
    metric_name = sensor_name_lower
    
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
                'Data': 'megabytes', 'SmallData': 'megabytes', 'Throughput': 'mb_per_sec'
            }
            unit = unit_map.get(sensor_type, 'units')
            
            # Create descriptive help text based on sensor type
            type_descriptions = {
                'Temperature': 'Temperature reading',
                'Load': 'Load percentage',
                'Clock': 'Clock frequency',
                'Power': 'Power consumption',
                'Fan': 'Fan speed',
                'Voltage': 'Voltage level',
                'Data': 'Data size',
                'SmallData': 'Data size',
                'Throughput': 'Data throughput'
            }
            description = type_descriptions.get(sensor_type, sensor_type)
            help_text = f"{description} in {unit}"
        
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

    def _get_hardware_component(self, parent: str) -> str:
        """Extract the top-level hardware component from a sensor path.
        
        Path structures vary by source:
          HTTP API: /sensor/COMPUTERNAME/hardwareComponent/sensorGroup/sensorName
          WMI:      /hardwareComponent/sensorGroup/sensorName
        
        We need to find the hardware component segment, skipping:
          - 'sensor' prefix (HTTP API)
          - computer name (HTTP API)
          - 'computer' (sometimes present)
        
        Examples:
          /sensor/WIN-PC/genericmemory/load/memory -> 'genericmemory' -> Memory
          /sensor/WIN-PC/genericmemory/data/virtualmemoryused -> 'genericmemory' -> Memory
          /nvidiageforcertx3070/temperature/gpucore -> 'nvidiageforcertx3070' -> GPU
          /amdryzen75800x/temperature/coremax -> 'amdryzen75800x' -> CPU
        """
        if not parent:
            return "unknown"
        
        # Split path into segments
        parts = [p for p in parent.lower().split('/') if p]
        if not parts:
            return "unknown"
        
        # Skip known prefixes to find the hardware component
        # HTTP API paths start with: /sensor/COMPUTERNAME/...
        # We need to skip 'sensor' and the computer name (which varies)
        idx = 0
        
        # Skip 'sensor' prefix if present
        if idx < len(parts) and parts[idx] == 'sensor':
            idx += 1
            # After 'sensor', the next segment is ALWAYS the computer name - skip it unconditionally
            if idx < len(parts):
                idx += 1
        # Also skip 'computer' if it appears as first segment (alternative format)
        elif idx < len(parts) and parts[idx] == 'computer':
            idx += 1
        
        # Now we should be at the hardware component
        if idx >= len(parts):
            return "unknown"
        
        hw_component = parts[idx]
        
        # Classify based on hardware component name
        # GPU detection - check first to avoid false matches
        if any(gpu in hw_component for gpu in ["gpu", "nvidia", "geforce", "radeon", "rtx", "gtx", "quadro", "amd rx"]):
            return "gpu"
        
        # CPU detection
        if any(cpu in hw_component for cpu in ["cpu", "amdcpu", "intelcpu", "ryzen", "threadripper", "epyc", "xeon", "corei", "processor"]):
            return "cpu"
        # Special case: Virtual CPU in VMs (the hardware component is literally "virtual")
        if hw_component == "virtual" or hw_component.startswith("virtualcpu"):
            return "cpu"
        
        # Memory detection - includes "Generic Memory" -> "genericmemory"
        if any(mem in hw_component for mem in ["memory", "ram", "genericmemory"]):
            return "memory"
        
        # Motherboard detection
        if any(mb in hw_component for mb in ["motherboard", "mainboard", "asrock", "asus", "msi", "gigabyte", "nuvoton", "nct", "lpc"]):
            return "motherboard"
        
        # Storage detection
        if any(drive in hw_component for drive in ["ssd", "hdd", "nvme", "samsung", "wdc", "seagate", "toshiba", "storage", "disk"]):
            return "storage"
        
        # Network detection
        if any(net in hw_component for net in ["ethernet", "network", "nic", "bluetooth", "wifi", "tailscale"]):
            return "network"
        
        return "other"

    def _is_cpu_sensor(self, parent: str) -> bool:
        """Check if sensor belongs to CPU based on top-level hardware component"""
        return self._get_hardware_component(parent) == "cpu"

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
                
                # Quick component type detection for filtering (uses top-level hardware component)
                component_type = self._get_hardware_component(parent)
                
                if should_include_sensor(sensor_type, component_type, self.sensor_mode):
                    filtered_count += 1
            
            logger.info(f"📊 Monitoring {filtered_count}/{total_count} sensors (mode: {self.sensor_mode})")
        
        # Debug: Log sensor types for troubleshooting
        if logger.isEnabledFor(logging.DEBUG):
            sensor_types = {}
            critical_metrics = []
            gpu_sensors_by_type = defaultdict(list)  # Track GPU sensors by type
            
            for sensor in sensors:
                if isinstance(sensor, dict):
                    stype = sensor.get('SensorType', 'Unknown')
                    sname = sensor.get('Name', 'Unknown')
                    parent = sensor.get('Parent', 'Unknown')
                else:
                    stype = getattr(sensor, 'SensorType', 'Unknown')
                    sname = getattr(sensor, 'Name', 'Unknown')
                    parent = getattr(sensor, 'Parent', 'Unknown')
                    
                sensor_types[stype] = sensor_types.get(stype, 0) + 1
                
                # Track GPU sensors specifically
                if 'gpu' in parent.lower() or 'geforce' in parent.lower() or 'nvidia' in parent.lower():
                    gpu_sensors_by_type[stype].append(sname)
                
                # Track critical metrics that user specifically mentioned
                if any(metric in sname for metric in ['GPU Memory Free', 'GPU Memory Used', 'GPU Memory Total', 'GPU Core', 'Package']):
                    critical_metrics.append(f"{stype}/{sname}")
            
            logger.debug(f"Sensor types found: {dict(sensor_types)}")
            
            # Show GPU sensors breakdown for troubleshooting
            if gpu_sensors_by_type:
                logger.debug("GPU Sensors Breakdown:")
                for stype, names in sorted(gpu_sensors_by_type.items()):
                    logger.debug(f"  {stype}: {names}")
            
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
                
                # Determine component type using top-level hardware component extraction
                # This prevents false matches like "virtualmemory" matching the "/virtual" CPU pattern
                component_type = self._get_hardware_component(parent)
                    
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
                    # Pass through raw values - let Grafana handle unit conversions
                    # SmallData = MB, Data = GB (as reported by LibreHardwareMonitor)
                    metric.set(value)
                    logger.debug(f"✅ Set metric {standardized_name}: {value}")
                    
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
    parser.add_argument('--interval', type=int, default=2, help='Update interval in seconds (default: 2, use 2-5 for real-time gaming or 10+ for general monitoring)')
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