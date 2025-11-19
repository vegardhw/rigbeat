"""
Rigbeat - Prometheus Exporter
Exports Windows hardware metrics (CPU/GPU temps, fan speeds, loads) for Prometheus/Grafana

Requirements:
    - LibreHardwareMonitor running with WMI enabled
    - Python 3.8+
    - pip install prometheus-client wmi pywin32
"""

import time
import wmi
import logging
import re
from prometheus_client import start_http_server, Gauge, Info
from typing import Dict, List
import argparse

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

gpu_temp = Gauge('rigbeat_gpu_temperature_celsius', 'GPU temperature in Celsius', ['gpu'])
gpu_load = Gauge('rigbeat_gpu_load_percent', 'GPU load percentage', ['gpu', 'type'])
gpu_memory = Gauge('rigbeat_gpu_memory_used_mb', 'GPU memory used in MB', ['gpu'])
gpu_clock = Gauge('rigbeat_gpu_clock_mhz', 'GPU clock speed in MHz', ['gpu', 'type'])

fan_rpm = Gauge('rigbeat_fan_speed_rpm', 'Fan speed in RPM', ['fan', 'type'])

memory_used = Gauge('rigbeat_memory_used_gb', 'System memory used in GB')
memory_available = Gauge('rigbeat_memory_available_gb', 'System memory available in GB')

system_info = Info('rigbeat_system', 'System information')


class HardwareMonitor:
    """Monitors hardware sensors via WMI (LibreHardwareMonitor)"""

    def __init__(self):
        try:
            self.w = wmi.WMI(namespace="root\\LibreHardwareMonitor")
            self.connected = True
            logger.info("Successfully connected to LibreHardwareMonitor WMI")
        except Exception as e:
            logger.warning(f"Failed to connect to LibreHardwareMonitor WMI: {e}")
            logger.warning("LibreHardwareMonitor may not be running or WMI may not be enabled")
            logger.info("Monitor will run in demo mode - no metrics will be collected")
            self.connected = False
            self.w = None

    def get_sensors(self) -> List:
        """Get all hardware sensors"""
        if not self.connected or not self.w:
            return []
        try:
            return self.w.Sensor()
        except Exception as e:
            logger.error(f"Error reading sensors: {e}")
            return []

    def _is_cpu_sensor(self, parent: str) -> bool:
        """Check if sensor belongs to CPU (Intel, AMD, or other)"""
        if not parent:
            return False

        parent_lower = parent.lower()

        # Comprehensive CPU detection patterns
        cpu_patterns = [
            "/cpu",          # Generic CPU path
            "/amdcpu",       # AMD-specific path
            "/intelcpu",     # Intel-specific path (if it exists)
            "cpu",           # Generic CPU in path
            "processor",     # Alternative CPU naming
            "ryzen",         # AMD Ryzen series
            "threadripper",  # AMD Threadripper
            "epyc",          # AMD EPYC
            "intel",         # Intel processors
            "xeon",          # Intel Xeon
            "core",          # Intel Core series (but not "core" alone to avoid confusion with cores)
        ]

        return any(pattern in parent_lower for pattern in cpu_patterns)

    def update_metrics(self):
        """Update all Prometheus metrics"""
        sensors = self.get_sensors()

        if not sensors:
            logger.warning("No sensors found - is LibreHardwareMonitor running?")
            return

        for sensor in sensors:
            try:
                sensor_type = sensor.SensorType
                sensor_name = sensor.Name
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
                    gpu_memory.labels(gpu=gpu_name).set(value)

                # GPU Clock
                elif sensor_type == "Clock" and any(x in parent.lower() for x in ["/gpu", "nvidia", "amd", "radeon"]):
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"
                    clock_type = "core" if "Core" in sensor_name else "memory" if "Memory" in sensor_name else "other"
                    gpu_clock.labels(gpu=gpu_name, type=clock_type).set(value)

                # Fan Speeds
                elif sensor_type == "Fan":
                    # Categorize and label fans intelligently
                    fan_name_lower = sensor_name.lower()

                    if "gpu" in fan_name_lower or "vga" in fan_name_lower:
                        fan_type = "gpu"
                        # Extract number from sensor name more reliably
                        numbers = re.findall(r'\d+', sensor_name)
                        if numbers:
                            fan_label = f"gpu_fan_{numbers[0]}"
                        else:
                            fan_label = "gpu_fan"
                    elif "cpu" in fan_name_lower:
                        fan_type = "cpu"
                        numbers = re.findall(r'\d+', sensor_name)
                        if numbers:
                            fan_label = f"cpu_fan_{numbers[0]}"
                        else:
                            fan_label = "cpu_fan"
                    elif "cha" in fan_name_lower or "chassis" in fan_name_lower or "case" in fan_name_lower:
                        fan_type = "chassis"
                        numbers = re.findall(r'\d+', sensor_name)
                        if numbers:
                            fan_label = f"chassis_fan_{numbers[0]}"
                        else:
                            fan_label = "chassis_fan"
                    else:
                        fan_type = "other"
                        # Sanitize fan label for Prometheus (alphanumeric + underscore only)
                        fan_label = re.sub(r'[^a-zA-Z0-9_]', '_', sensor_name.lower())
                        fan_label = re.sub(r'_+', '_', fan_label).strip('_')
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
                logger.debug(f"Error processing sensor {sensor_name}: {e}")
                continue

    def get_system_info(self) -> Dict:
        """Get system information"""
        if not self.connected or not self.w:
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


def main():
    parser = argparse.ArgumentParser(description='Rigbeat - Prometheus Exporter')
    parser.add_argument('--port', type=int, default=9182, help='Port to expose metrics (default: 9182)')
    parser.add_argument('--interval', type=int, default=2, help='Update interval in seconds (default: 2)')
    parser.add_argument('--logfile', type=str, help='Log file path (e.g., rigbeat.log)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # Configure file logging if requested
    if args.logfile:
        file_handler = logging.FileHandler(args.logfile)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    # Set debug level if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.info(f"Starting Rigbeat Exporter on port {args.port}")
    logger.info(f"Update interval: {args.interval} seconds")

    # Initialize monitor
    try:
        monitor = HardwareMonitor()
    except Exception as e:
        logger.error("Failed to initialize hardware monitor. Exiting.")
        return 1

    # Get and set system info
    sys_info = monitor.get_system_info()
    system_info.info(sys_info)
    logger.info(f"System: CPU={sys_info['cpu']}, GPU={sys_info['gpu']}")

    # Start Prometheus HTTP server
    start_http_server(args.port)
    logger.info(f"Metrics available at http://localhost:{args.port}/metrics")

    # Main loop
    try:
        while True:
            monitor.update_metrics()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())