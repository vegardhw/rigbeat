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
cpu_temp = Gauge('cpu_temperature_celsius', 'CPU temperature in Celsius', ['sensor'])
cpu_load = Gauge('cpu_load_percent', 'CPU load percentage', ['core'])
cpu_clock = Gauge('cpu_clock_mhz', 'CPU clock speed in MHz', ['core'])

gpu_temp = Gauge('gpu_temperature_celsius', 'GPU temperature in Celsius', ['gpu'])
gpu_load = Gauge('gpu_load_percent', 'GPU load percentage', ['gpu', 'type'])
gpu_memory = Gauge('gpu_memory_used_mb', 'GPU memory used in MB', ['gpu'])
gpu_clock = Gauge('gpu_clock_mhz', 'GPU clock speed in MHz', ['gpu', 'type'])

fan_rpm = Gauge('fan_speed_rpm', 'Fan speed in RPM', ['fan', 'type'])

memory_used = Gauge('memory_used_gb', 'System memory used in GB')
memory_available = Gauge('memory_available_gb', 'System memory available in GB')

system_info = Info('system', 'System information')


class HardwareMonitor:
    """Monitors hardware sensors via WMI (LibreHardwareMonitor)"""
    
    def __init__(self):
        try:
            self.w = wmi.WMI(namespace="root\\LibreHardwareMonitor")
            logger.info("Successfully connected to LibreHardwareMonitor WMI")
        except Exception as e:
            logger.error(f"Failed to connect to LibreHardwareMonitor WMI: {e}")
            logger.error("Make sure LibreHardwareMonitor is running with WMI enabled!")
            raise
    
    def get_sensors(self) -> List:
        """Get all hardware sensors"""
        try:
            return self.w.Sensor()
        except Exception as e:
            logger.error(f"Error reading sensors: {e}")
            return []
    
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
                parent = sensor.Parent
                
                # CPU Temperature
                if sensor_type == "Temperature" and "CPU" in parent:
                    cpu_temp.labels(sensor=sensor_name).set(value)
                
                # CPU Load
                elif sensor_type == "Load" and "CPU" in parent:
                    # Clean up core names (e.g., "CPU Core #1" -> "core1")
                    core_label = sensor_name.lower().replace("cpu ", "").replace("#", "").replace(" ", "")
                    cpu_load.labels(core=core_label).set(value)
                
                # CPU Clock
                elif sensor_type == "Clock" and "CPU" in parent:
                    core_label = sensor_name.lower().replace("cpu ", "").replace("#", "").replace(" ", "")
                    cpu_clock.labels(core=core_label).set(value)
                
                # GPU Temperature
                elif sensor_type == "Temperature" and any(x in parent for x in ["GPU", "NVIDIA", "AMD", "Radeon"]):
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"
                    gpu_temp.labels(gpu=gpu_name).set(value)
                
                # GPU Load
                elif sensor_type == "Load" and any(x in parent for x in ["GPU", "NVIDIA", "AMD", "Radeon"]):
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"
                    load_type = "core" if "Core" in sensor_name else "memory" if "Memory" in sensor_name else "other"
                    gpu_load.labels(gpu=gpu_name, type=load_type).set(value)
                
                # GPU Memory
                elif sensor_type == "SmallData" and "Memory Used" in sensor_name:
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"
                    gpu_memory.labels(gpu=gpu_name).set(value)
                
                # GPU Clock
                elif sensor_type == "Clock" and any(x in parent for x in ["GPU", "NVIDIA", "AMD", "Radeon"]):
                    gpu_name = parent.split("/")[-1] if "/" in parent else "gpu0"
                    clock_type = "core" if "Core" in sensor_name else "memory" if "Memory" in sensor_name else "other"
                    gpu_clock.labels(gpu=gpu_name, type=clock_type).set(value)
                
                # Fan Speeds
                elif sensor_type == "Fan":
                    # Create clean fan labels
                    fan_name = sensor_name.lower().replace(" ", "_").replace("#", "")
                    fan_rpm.labels(fan=fan_name).set(value)
                
                # Memory (from motherboard/system)
                elif sensor_type == "Data":
                    if "Memory Used" in sensor_name:
                        memory_used.set(value)
                    elif "Memory Available" in sensor_name:
                        memory_available.set(value)
                        
            except Exception as e:
                logger.debug(f"Error processing sensor {sensor_name}: {e}")
                continue
    
    def get_system_info(self) -> Dict:
        """Get system information"""
        try:
            hardware = self.w.Hardware()
            info = {
                'cpu': 'Unknown',
                'gpu': 'Unknown',
                'motherboard': 'Unknown'
            }
            
            for hw in hardware:
                hw_type = hw.HardwareType
                hw_name = hw.Name
                
                if hw_type == "CPU" or "Processor" in hw_type:
                    info['cpu'] = hw_name
                elif hw_type == "GpuNvidia" or hw_type == "GpuAmd":
                    info['gpu'] = hw_name
                elif hw_type == "Motherboard":
                    info['motherboard'] = hw_name
            
            return info
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {'cpu': 'Unknown', 'gpu': 'Unknown', 'motherboard': 'Unknown'}


def main():
    parser = argparse.ArgumentParser(description='Rigbeat - Prometheus Exporter')
    parser.add_argument('--port', type=int, default=9182, help='Port to expose metrics (default: 9182)')
    parser.add_argument('--interval', type=int, default=2, help='Update interval in seconds (default: 2)')
    args = parser.parse_args()
    
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