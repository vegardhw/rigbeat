"""
Fan Detection Test Script
Run this to see all detected fans from LibreHardwareMonitor
Helps debug fan naming and categorization

Supports both HTTP API (preferred) and WMI (fallback) methods
"""

import sys
import time
import argparse
import re
from collections import defaultdict

# HTTP API support
try:
    import requests
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    requests = None

# WMI fallback
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    wmi = None

class LibreHardwareMonitorHTTP:
    """HTTP API client for fan testing"""

    def __init__(self, host="localhost", port=8085):
        self.base_url = f"http://{host}:{port}"
        self.connected = False

        if not HTTP_AVAILABLE:
            print("⚠️  HTTP API not available - 'requests' package not installed")
            return

        # Test connection
        self._test_connection()

    def _test_connection(self):
        """Test if LibreHardwareMonitor HTTP server is available"""
        try:
            response = requests.get(f"{self.base_url}/data.json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "Children" in data:
                    self.connected = True
                    print(f"✅ Connected to LibreHardwareMonitor HTTP API")
                    return
                else:
                    print(f"⚠️  HTTP API responded but data structure unexpected")
            else:
                print(f"❌ HTTP API returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to {self.base_url}")
        except Exception as e:
            print(f"❌ HTTP API error: {e}")
        
        self.connected = False

    def get_fan_sensors(self):
        """Get all fan sensors from HTTP API"""
        if not self.connected:
            return []

        try:
            response = requests.get(f"{self.base_url}/data.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self._extract_fan_sensors(data)
        except Exception as e:
            print(f"HTTP API error: {e}")
        return []

    def _extract_fan_sensors(self, node, parent_path=""):
        """Extract fan sensors from LibreHardwareMonitor HTTP API JSON tree"""
        fans = []

        # Update parent path
        if "Text" in node and node["Text"]:
            if parent_path:
                current_path = f"{parent_path}/{node['Text']}"
            else:
                current_path = node["Text"]
        else:
            current_path = parent_path

        # Check if this is a fan sensor - HTTP API format
        if ("Type" in node and node.get("Type") == "Fan"):
            sensor_name = node.get("Text", "Unknown")
            value_str = node.get("Value", "N/A")
            raw_value = node.get("RawValue", "N/A")
            
            # Parse the Value field (formatted string like "1850 RPM")
            rpm_value = 0.0
            if value_str and value_str != "N/A":
                try:
                    # Parse formatted string
                    cleaned = str(value_str).replace(',', '.').replace('RPM', '').strip()
                    import re
                    cleaned = re.sub(r'[^0-9.\\-]', '', cleaned)
                    if cleaned:
                        rpm_value = float(cleaned)
                except:
                    rpm_value = 0.0
            
            fan_data = {
                'Name': sensor_name,
                'Value': rpm_value,
                'Parent': current_path,
                'SensorType': 'Fan',
                'ValueStr': value_str,
                'RawValue': raw_value
            }
            fans.append(fan_data)

        # Recursively process children
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                fans.extend(self._extract_fan_sensors(child, current_path))

        return fans


def test_fan_detection(http_host="localhost", http_port=8085, method="auto"):
    """Test and display all detected fans with HTTP API and WMI support"""

    print("=" * 80)
    print("Rigbeat - Fan Detection Test (v0.1.3)")
    print("=" * 80)
    print()

    sensors = []
    connection_method = "none"
    connection_time = 0

    # Try HTTP API first (if available and not explicitly disabled)
    if method in ["auto", "http"] and HTTP_AVAILABLE:
        print(f"🔌 Testing LibreHardwareMonitor HTTP API at {http_host}:{http_port}...")
        start_time = time.time()

        http_client = LibreHardwareMonitorHTTP(http_host, http_port)
        if http_client.connected:
            sensors = http_client.get_fan_sensors()
            connection_time = time.time() - start_time
            connection_method = "http"
            print(f"✅ Connected via HTTP API in {connection_time:.3f}s")
            print("🚀 Performance optimized mode enabled")
            print()
        else:
            print("❌ HTTP API not available")
            if method == "http":
                print("💡 Enable HTTP server in LibreHardwareMonitor Options → Web Server")
                return 1
            else:
                print("🔄 Falling back to WMI...")
                print()

    # Fallback to WMI (if HTTP failed or method specified)
    if not sensors and method in ["auto", "wmi"] and WMI_AVAILABLE:
        print("🔍 Testing LibreHardwareMonitor WMI...")
        start_time = time.time()

        try:
            w = wmi.WMI(namespace="root\\LibreHardwareMonitor")
            all_sensors = w.Sensor()
            sensors = [s for s in all_sensors if s.SensorType == "Fan"]
            connection_time = time.time() - start_time
            connection_method = "wmi"
            print(f"✅ Connected via WMI in {connection_time:.3f}s")
            print("⚠️  Using WMI fallback - consider enabling HTTP API for better performance")
            print()
        except Exception as e:
            print(f"❌ WMI connection failed: {e}")

    # Error handling
    if not sensors:
        print("❌ ERROR: No connection method available")
        print()
        print("Requirements:")
        print("  1. LibreHardwareMonitor must be running as Administrator")

        if not HTTP_AVAILABLE and not WMI_AVAILABLE:
            print("  2. Install required packages: pip install requests pywin32")
        elif not HTTP_AVAILABLE:
            print("  2. For HTTP API: pip install requests")
            print("  3. Enable HTTP server in LibreHardwareMonitor Options")
        elif not WMI_AVAILABLE:
            print("  2. For WMI: pip install pywin32")
            print("  3. Enable WMI in LibreHardwareMonitor Options")
        else:
            print("  2. Enable HTTP server OR WMI in LibreHardwareMonitor Options")

        return 1

    # Performance comparison display
    if connection_method == "http":
        estimated_wmi_time = connection_time * 5  # Rough estimate
        print(f"📊 Performance: HTTP API ~{estimated_wmi_time/connection_time:.0f}x faster than WMI")
    elif connection_method == "wmi":
        print(f"📊 Performance: WMI mode - HTTP API could be ~5x faster")
    print()

    # Categorize fans with optimized patterns
    fans_by_type = defaultdict(list)
    all_fan_data = []

    # Pre-compile regex patterns for performance (matching main exporter)
    patterns = {
        'numbers': re.compile(r'\d+'),
        'sanitize': re.compile(r'[^a-zA-Z0-9_]'),
        'underscore': re.compile(r'_+')
    }

    for sensor in sensors:
        # Handle both HTTP API and WMI sensor formats
        if hasattr(sensor, 'Name'):  # WMI format
            # Only process fan sensors in WMI mode
            if hasattr(sensor, 'SensorType') and sensor.SensorType != 'Fan':
                continue
            sensor_name = sensor.Name
            # Fix: properly handle 0 values - only skip None/empty values
            raw_value = getattr(sensor, 'Value', None)
            value = float(raw_value) if raw_value is not None else 0
            parent = sensor.Parent
        else:  # HTTP API format (dict)
            # Only process fan sensors in HTTP API mode
            if sensor.get('SensorType') != 'Fan':
                continue
            sensor_name = sensor.get('Name', 'Unknown')
            value = float(sensor.get('Value', 0)) if sensor.get('Value') is not None else 0
            parent = sensor.get('Parent', 'Unknown')

        # Categorize using same logic as main exporter
        fan_name_lower = sensor_name.lower()

        if "gpu" in fan_name_lower or "vga" in fan_name_lower:
            fan_type = "GPU"
            numbers = patterns['numbers'].findall(sensor_name)
            if numbers:
                fan_label = f"gpu_fan_{numbers[0]}"
            else:
                fan_label = "gpu_fan"
        elif "cpu" in fan_name_lower:
            fan_type = "CPU"
            numbers = patterns['numbers'].findall(sensor_name)
            if numbers:
                fan_label = f"cpu_fan_{numbers[0]}"
            else:
                fan_label = "cpu_fan"
        elif "cha" in fan_name_lower or "chassis" in fan_name_lower or "case" in fan_name_lower:
            fan_type = "Chassis"
            numbers = patterns['numbers'].findall(sensor_name)
            if numbers:
                fan_label = f"chassis_fan_{numbers[0]}"
            else:
                fan_label = "chassis_fan"
        else:
            fan_type = "Other"
            # Sanitize fan label for Prometheus
            fan_label = patterns['sanitize'].sub('_', sensor_name.lower())
            fan_label = patterns['underscore'].sub('_', fan_label).strip('_')
            if not fan_label:
                fan_label = "unknown_fan"

            fans_by_type[fan_type].append({
                'name': sensor_name,
                'label': fan_label,
                'rpm': value,
                'parent': parent
            })

            all_fan_data.append({
                'type': fan_type,
                'name': sensor_name,
                'label': fan_label,
                'rpm': value,
                'parent': parent
            })

    # Display results
    if not all_fan_data:
        print("⚠ WARNING: No fans detected!")
        print()
        print("This could mean:")
        print("  1. LibreHardwareMonitor hasn't detected your fans yet")
        print("  2. Your motherboard doesn't expose fan sensors")
        print("  3. Fans are shown under a different sensor type")
        print()
        print("Try running LibreHardwareMonitor GUI and check what fans it shows.")
        return 1

    print(f"✓ Found {len(all_fan_data)} fan(s)")
    print()

    # Display by type
    for fan_type in ["GPU", "CPU", "Chassis", "Other"]:
        if fan_type in fans_by_type:
            print(f"{'─' * 80}")
            print(f"{fan_type} Fans:")
            print(f"{'─' * 80}")

            for fan in fans_by_type[fan_type]:
                status = "✓" if fan['rpm'] > 0 else "✗"
                print(f"  {status} {fan['name']:<30} → {fan['label']:<25} {fan['rpm']:>6.0f} RPM")
                print(f"     Parent: {fan['parent']}")
            print()

    # Summary table
    print("=" * 80)
    print("Summary - Prometheus Metric Labels")
    print("=" * 80)
    print(f"{'Metric':<50} {'Current Value':<15} {'Status'}")
    print("-" * 80)

    for fan in all_fan_data:
        metric = f"fan_speed_rpm{{fan=\"{fan['label']}\", type=\"{fan['type'].lower()}\"}}"
        value = f"{fan['rpm']:.0f} RPM"
        status = "RUNNING" if fan['rpm'] > 0 else "STOPPED/DISCONNECTED"
        print(f"{metric:<50} {value:<15} {status}")

    print("=" * 80)
    print()

    # Recommendations
    print("Recommendations:")
    print()

    gpu_fans = len(fans_by_type.get("GPU", []))
    cpu_fans = len(fans_by_type.get("CPU", []))
    chassis_fans = len(fans_by_type.get("Chassis", []))

    if gpu_fans > 0:
        print(f"  ✓ {gpu_fans} GPU fan(s) detected")
    else:
        print(f"  ⚠ No GPU fans detected (might be under different category)")

    if cpu_fans > 0:
        print(f"  ✓ {cpu_fans} CPU fan(s) detected")
    else:
        print(f"  ⚠ No CPU fans detected")

    if chassis_fans > 0:
        print(f"  ✓ {chassis_fans} chassis fan(s) detected")
    else:
        print(f"  ⚠ No chassis fans detected (check motherboard connections)")

    print()
    print("Next steps:")
    print("  1. Verify the labels match your expected fan configuration")
    if connection_method == "wmi":
        print("  2. Enable LibreHardwareMonitor HTTP server for better performance:")
        print("     → Options → Web Server → Enable Web Server ✅")
        print("  3. Update Grafana queries to use these exact labels")
        print("  4. Run 'python hardware_exporter.py' to start the exporter")
    else:
        print("  2. Update Grafana queries to use these exact labels")
        print("  3. Run 'python hardware_exporter.py' to start the exporter")
    print("  5. Check http://localhost:9182/metrics to see live data")
    print()

    return 0


def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description='Test fan detection with LibreHardwareMonitor HTTP API or WMI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_fans.py                    # Auto-detect (HTTP API preferred)
  python test_fans.py --method http      # Force HTTP API only
  python test_fans.py --method wmi       # Force WMI only
  python test_fans.py --http-port 8086   # Custom HTTP port
        """
    )

    parser.add_argument(
        '--method',
        choices=['auto', 'http', 'wmi'],
        default='auto',
        help='Connection method (default: auto - tries HTTP first, falls back to WMI)'
    )
    parser.add_argument(
        '--http-host',
        default='localhost',
        help='LibreHardwareMonitor HTTP API host (default: localhost)'
    )
    parser.add_argument(
        '--http-port',
        type=int,
        default=8085,
        help='LibreHardwareMonitor HTTP API port (default: 8085)'
    )

    args = parser.parse_args()

    return test_fan_detection(
        http_host=args.http_host,
        http_port=args.http_port, 
        method=args.method
    )


if __name__ == "__main__":
    sys.exit(main())