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
                sensors = self._extract_sensors_from_json(data)
                logger.debug(f"Retrieved {len(sensors)} sensors via HTTP API")
                return sensors
            else:
                logger.error(f"HTTP API error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching sensors via HTTP: {e}")
            return []
    
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
        
        # If this is a sensor node (has Type and Value)
        if "Type" in node and "Value" in node:
            # Convert to WMI-like structure for compatibility
            sensor_data = {
                "SensorType": node["Type"],
                "Name": node["Text"],
                "Value": self._parse_sensor_value(node.get("Value", "0")),
                "Parent": current_path,
                "Min": self._parse_sensor_value(node.get("Min", "0")),
                "Max": self._parse_sensor_value(node.get("Max", "0"))
            }
            sensors.append(sensor_data)
        
        # Process children recursively
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                sensors.extend(self._extract_sensors_from_json(child, current_path))
        
        return sensors
    
    def _parse_sensor_value(self, value_str: str) -> float:
        """Parse sensor value from string, handling units"""
        if not value_str or value_str == "":
            return 0.0
        
        # Remove common units and parse number
        cleaned = str(value_str).replace('°C', '').replace('RPM', '').replace('%', '').replace('MHz', '').replace('W', '').replace('GB', '').replace('MB', '').strip()
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

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
                    value = float(sensor.Value) if sensor.Value else 0
                    parent = getattr(sensor, 'Parent', '') or ''

                # Skip sensors with no name or invalid values
                if not sensor_name or value < 0:
                    continue

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
                elif sensor_type == "SmallData" and "Memory Used" in sensor_name and any(x in parent.lower() for x in ["/gpu", "nvidia", "amd", "radeon"]):
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"
                    # Convert MB to GB with proper decimal precision
                    memory_gb = round(value / 1024, 2) if value > 100 else value  # Assume MB if > 100, else already GB
                    gpu_memory.labels(gpu=gpu_name).set(memory_gb)

                # GPU Clock
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