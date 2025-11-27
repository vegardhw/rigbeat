#!/usr/bin/env python3
"""
Rigbeat Sensor Discovery Tool
============================

Comprehensive hardware sensor discovery and analysis tool for LibreHardwareMonitor.
This script helps you understand what sensors are available on your system and how
they map to Prometheus metrics in Rigbeat.

Features:
- 🔍 Complete hardware component analysis (CPU, GPU, motherboard, storage, network)
- 🌡️ Sensor type breakdown (temperature, load, clock, power, fan, voltage, etc.)
- 🌬️ Dedicated fan analysis with RPM status monitoring  
- 📊 Sensor count statistics across all hardware
- 🎯 Standardized metric name mapping preview
- ⚡ HTTP API structure investigation (preferred)
- 🔄 WMI fallback support for compatibility

Usage:
    python3 sensor_discovery.py [options]

Examples:
    python3 sensor_discovery.py                          # Auto-detect (HTTP preferred)
    python3 sensor_discovery.py --method http            # Force HTTP API only
    python3 sensor_discovery.py --method wmi             # Force WMI only
    python3 sensor_discovery.py --host 192.168.1.100     # Remote system
    python3 sensor_discovery.py --port 8080              # Custom port

Requirements:
- LibreHardwareMonitor running with HTTP server enabled (preferred) or WMI enabled (fallback)
- Python 3.6+ with 'requests' package
- For WMI fallback: pip install pywin32
"""

import requests
import json
import sys
import argparse
from collections import defaultdict

# Try to import WMI for fallback (optional)
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    wmi = None

def test_connection_methods(host="localhost", port=8085, method="auto"):
    """Test both HTTP API and WMI methods for LibreHardwareMonitor"""
    
    print(f"🔍 Rigbeat Sensor Discovery Tool v0.1.3")
    print("=" * 50)
    print()
    
    sensors = []
    connection_method = "none"
    
    # Try HTTP API first (if available and not explicitly disabled)
    if method in ["auto", "http"]:
        print(f"🔌 Testing LibreHardwareMonitor HTTP API at {host}:{port}...")
        http_sensors = test_http_api(host, port)
        if http_sensors:
            sensors = http_sensors
            connection_method = "http"
            print("✅ HTTP API connection successful")
            print("🚀 Performance optimized mode enabled")
        else:
            print("❌ HTTP API not available")
            if method == "http":
                print("💡 Enable HTTP server in LibreHardwareMonitor Options → Web Server")
                return
            else:
                print("🔄 Falling back to WMI...")
        print()
    
    # Fallback to WMI (if HTTP failed or method specified)
    if not sensors and method in ["auto", "wmi"] and WMI_AVAILABLE:
        print("🔍 Testing LibreHardwareMonitor WMI...")
        wmi_sensors = test_wmi_api()
        if wmi_sensors:
            sensors = wmi_sensors
            connection_method = "wmi"
            print("✅ WMI connection successful")
            print("⚠️  Using WMI fallback - consider enabling HTTP API for better performance")
        else:
            print("❌ WMI connection failed")
        print()
    elif not sensors and method in ["auto", "wmi"] and not WMI_AVAILABLE:
        print("❌ WMI not available - install with: pip install pywin32")
        print()
    
    # Error handling
    if not sensors:
        print("❌ ERROR: No connection method available")
        print()
        print("Requirements:")
        print("  1. LibreHardwareMonitor must be running as Administrator")
        if method != "wmi":
            print("  2. Enable HTTP server in LibreHardwareMonitor Options → Web Server")
        if method != "http":
            print("  3. Or enable WMI in LibreHardwareMonitor Options → WMI Provider")
        return
    
    # Analyze sensors using existing analysis function
    print(f"📊 Analyzing {len(sensors)} sensors via {connection_method.upper()}...")
    analyze_sensors_simple(sensors, connection_method)


def get_hardware_component(parent: str) -> str:
    """Extract the top-level hardware component from a sensor path.
    
    Path structure: /computer/hardwareComponent/sensorGroup/sensorName
    We need the first meaningful segment after /computer/ to identify the hardware.
    
    This function is aligned with hardware_exporter.py's _get_hardware_component method.
    
    Examples:
      /genericmemory/load/memory -> 'genericmemory' -> Memory
      /genericmemory/data/virtualmemoryused -> 'genericmemory' -> Memory (NOT CPU!)
      /nvidiageforcertx3070/temperature/gpucore -> 'nvidiageforcertx3070' -> GPU
      /amdryzen75800x/temperature/coremax -> 'amdryzen75800x' -> CPU
    """
    if not parent:
        return "Other"
    
    # Split path and get the first meaningful segment (skip empty and 'computer')
    parts = [p for p in parent.lower().split('/') if p and p != 'computer']
    if not parts:
        return "Other"
    
    # First segment is the hardware component
    hw_component = parts[0]
    
    # Classify based on hardware component name
    # GPU detection - check first to avoid false matches
    if any(gpu in hw_component for gpu in ["gpu", "nvidia", "geforce", "radeon", "rtx", "gtx", "quadro", "amd rx"]):
        return "GPU"
    
    # CPU detection
    if any(cpu in hw_component for cpu in ["cpu", "amdcpu", "intelcpu", "ryzen", "threadripper", "epyc", "xeon", "corei", "processor"]):
        return "CPU"
    # Special case: Virtual CPU in VMs (the hardware component is literally "virtual")
    if hw_component == "virtual" or hw_component.startswith("virtualcpu"):
        return "CPU"
    
    # Memory detection - includes "Generic Memory" -> "genericmemory"
    if any(mem in hw_component for mem in ["memory", "ram", "genericmemory"]):
        return "Memory"
    
    # Motherboard detection
    if any(mb in hw_component for mb in ["motherboard", "mainboard", "asrock", "asus", "msi", "gigabyte", "nuvoton", "nct", "lpc"]):
        return "Motherboard"
    
    # Storage detection
    if any(drive in hw_component for drive in ["ssd", "hdd", "nvme", "samsung", "wdc", "seagate", "toshiba", "storage", "disk"]):
        return "Storage"
    
    # Network detection
    if any(net in hw_component for net in ["ethernet", "network", "nic", "bluetooth", "wifi", "tailscale"]):
        return "Network"
    
    return "Other"


def analyze_sensors_simple(sensors, connection_method):
    """Simple sensor analysis for both HTTP and WMI data"""
    
    # Group sensors by type and component
    sensor_types = defaultdict(int)
    components = defaultdict(lambda: defaultdict(list))  # component -> sensor_type -> [sensors]
    critical_sensors = []
    
    # DEBUG: Track unique parent paths and their detected components
    parent_to_component = {}
    
    for sensor in sensors:
        sensor_type = sensor.get('SensorType', 'Unknown')
        sensor_name = sensor.get('Name', 'Unknown')
        sensor_value = sensor.get('Value', 0)
        parent = sensor.get('Parent', 'Unknown')
        
        sensor_types[sensor_type] += 1
        
        # Identify component type using TOP-LEVEL hardware component extraction
        # This prevents false matches like "virtualmemory" matching the "/virtual" CPU pattern
        # Path structure: /computer/hardwareComponent/sensorGroup/sensorName
        # We extract the first meaningful segment to classify the hardware
        
        component = get_hardware_component(parent)
        
        # DEBUG: Track path -> component mapping
        if parent not in parent_to_component:
            parent_to_component[parent] = component
        
        # Store sensor details by component and type
        components[component][sensor_type].append({
            'name': sensor_name,
            'value': sensor_value,
            'parent': parent
        })
        
        # Track critical sensors mentioned by user
        if any(critical in sensor_name for critical in ['GPU Memory', 'Package', 'GPU Core']):
            critical_sensors.append(f"{sensor_type}/{sensor_name} = {sensor_value}")
    
    # Display results
    print("=" * 80)
    print("📊 SENSOR ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Connection Method: {connection_method.upper()}")
    print(f"Total Sensors: {len(sensors)}")
    print()
    
    # DEBUG: Show parent path to component mapping
    print("🔍 DEBUG: Parent Path → Component Mapping:")
    for path, comp in sorted(parent_to_component.items()):
        # Extract first segment for clarity
        parts = [p for p in path.lower().split('/') if p and p != 'computer']
        hw_segment = parts[0] if parts else "(empty)"
        print(f"  {path}")
        print(f"    → hw_segment: '{hw_segment}' → Component: {comp}")
    print()
    
    print("🔧 Sensor Types Overview:")
    for stype, count in sorted(sensor_types.items()):
        print(f"  {stype}: {count}")
    print()
    
    print("=" * 80)
    print("💻 DETAILED COMPONENT BREAKDOWN")
    print("=" * 80)
    
    for component in sorted(components.keys()):
        print()
        print(f"{'─' * 80}")
        print(f"🔹 {component.upper()}")
        print(f"{'─' * 80}")
        
        component_sensors = components[component]
        for sensor_type in sorted(component_sensors.keys()):
            sensor_list = component_sensors[sensor_type]
            print(f"\n  📂 {sensor_type} ({len(sensor_list)} sensors):")
            print(f"  {'─' * 76}")
            
            # Show all sensors in a table format
            for idx, s in enumerate(sensor_list, 1):
                # Format value based on sensor type
                if sensor_type == 'Temperature':
                    value_str = f"{s['value']:.1f}°C"
                elif sensor_type == 'Load':
                    value_str = f"{s['value']:.1f}%"
                elif sensor_type == 'Fan':
                    value_str = f"{s['value']:.0f} RPM"
                elif sensor_type == 'Clock':
                    value_str = f"{s['value']:.0f} MHz"
                elif sensor_type == 'Power':
                    value_str = f"{s['value']:.1f}W"
                elif sensor_type == 'Data':
                    value_str = f"{s['value']:.0f} MB"
                else:
                    value_str = f"{s['value']}"
                
                # Truncate long names
                display_name = s['name'][:45] + '...' if len(s['name']) > 48 else s['name']
                
                print(f"    {idx:2}. {display_name:<48} {value_str:>12}")
    
    print()
    print("=" * 80)
    
    if critical_sensors:
        print()
        print("🎯 Critical Sensors Found:")
        for sensor in critical_sensors[:15]:  # Show first 15
            print(f"  ✓ {sensor}")
        if len(critical_sensors) > 15:
            print(f"  ... and {len(critical_sensors) - 15} more")
    
    print()
    print("💡 Next Steps:")
    print("  1. Run 'python hardware_exporter.py --debug' to see detailed sensor processing")
    print("  2. Check http://localhost:9182/metrics for live Prometheus metrics")
    if connection_method == "wmi":
        print("  3. Consider enabling HTTP server for better performance")


def test_wmi_api():
    """Test LibreHardwareMonitor WMI interface"""
    if not WMI_AVAILABLE:
        return []
    
    try:
        w = wmi.WMI(namespace="root\\LibreHardwareMonitor")
        sensors = w.Sensor()
        
        # Convert WMI sensors to consistent format
        converted_sensors = []
        for sensor in sensors:
            converted_sensors.append({
                'Name': getattr(sensor, 'Name', 'Unknown'),
                'SensorType': getattr(sensor, 'SensorType', 'Unknown'),
                'Value': getattr(sensor, 'Value', 0),
                'Parent': getattr(sensor, 'Parent', 'Unknown')
            })
        
        return converted_sensors
        
    except Exception as e:
        print(f"WMI Error: {e}")
        return []


def test_http_api(host="localhost", port=8085):
    """Test LibreHardwareMonitor HTTP API and return sensors"""

    url = f"http://{host}:{port}/data.json"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"📊 HTTP API Response: {len(response.text)} characters")
            
            # Extract sensors from JSON structure
            sensors = extract_sensors_from_json(data)
            return sensors
            
        else:
            print(f"HTTP Error {response.status_code}")
            return []
            
    except requests.exceptions.ConnectionError:
        print(f"Connection failed - HTTP server not running")
        return []
    except Exception as e:
        print(f"HTTP API Error: {e}")
        return []


def extract_sensors_from_json(node, parent_path=""):
    """Extract sensors from LibreHardwareMonitor JSON tree"""
    sensors = []

    # Build parent path
    if "Text" in node and node["Text"]:
        clean_text = node["Text"].lower().replace(' ', '').replace('#', '')
        if parent_path:
            current_path = f"{parent_path}/{clean_text}"
        else:
            current_path = f"/{clean_text}"
    else:
        current_path = parent_path

    # Check if this node is a sensor
    if "Type" in node and "Value" in node:
        sensor_name = node.get("Text", "Unknown")
        sensor_type = node.get("Type")
        value_str = node.get("Value", "")
        
        # Parse value
        try:
            if isinstance(value_str, (int, float)):
                numeric_value = float(value_str)
            else:
                # Parse formatted string (e.g., "45.2 °C", "1850 RPM")
                cleaned = str(value_str).replace('°C', '').replace('RPM', '').replace('%', '').replace('MHz', '').replace('W', '').strip()
                cleaned = cleaned.replace(',', '.')
                import re
                cleaned = re.sub(r'[^0-9.\-]', '', cleaned)
                numeric_value = float(cleaned) if cleaned else 0
        except:
            numeric_value = 0
        
        if numeric_value >= 0:  # Only include valid values
            sensor_data = {
                "SensorType": sensor_type,
                "Name": sensor_name,
                "Value": numeric_value,
                "Parent": current_path
            }
            sensors.append(sensor_data)

    # Process children recursively
    if "Children" in node and isinstance(node["Children"], list):
        for child in node["Children"]:
            sensors.extend(extract_sensors_from_json(child, current_path))

    return sensors


def count_direct_sensors(node):
    """Count sensors directly at this level (not in children)"""
    if not isinstance(node, dict):
        return 0

    count = 0
    # Check if this node itself is a sensor
    if "Type" in node and ("RawValue" in node or "Value" in node):
        count += 1

    # Check immediate children only (not recursive)
    if "Children" in node and isinstance(node["Children"], list):
        for child in node["Children"]:
            if isinstance(child, dict) and "Type" in child and ("RawValue" in child or "Value" in child):
                count += 1

    return count


def count_direct_sensors(node):
    """Count sensors directly at this level (not in children)"""
    if not isinstance(node, dict):
        return 0

    count = 0
    # Check if this node itself is a sensor
    if "Type" in node and ("RawValue" in node or "Value" in node):
        count += 1

    # Check immediate children only (not recursive)
    if "Children" in node and isinstance(node["Children"], list):
        for child in node["Children"]:
            if isinstance(child, dict) and "Type" in child and ("RawValue" in child or "Value" in child):
                count += 1

    return count


def find_and_show_sensors(node, depth=0, max_sensors=5, sensors_found=0):
    """Find and show sensors in a node and its children"""

    if sensors_found >= max_sensors:
        return sensors_found

    if isinstance(node, dict):
        # Check if this node is a sensor - must have Type and valid Value
        if "Type" in node and "Value" in node:
            value = node.get("Value")
            if value is not None and str(value).strip() and str(value).lower() not in ["n/a", "", "null"]:
                if sensors_found < max_sensors:
                    sensor_name = node.get("Text", "Unknown")
                    sensor_type = node.get("Type", "Unknown")
                    raw_value = node.get("RawValue", "N/A")
                    value = node.get("Value", "N/A")
                    indent = "       " + "  " * depth
                    print(f"{indent}🌡️  {sensor_type}: {sensor_name}")
                    print(f"{indent}     RawValue: {raw_value}, Value: {value}")

                    # Show what the parsed value would be
                    if value and str(value) not in ["N/A", "n/a", ""]:
                        try:
                            # Parse like the main script does
                            cleaned = str(value).replace(',', '.').replace('°C', '').replace('RPM', '').replace('%', '').replace('MHz', '').replace('W', '').replace('V', '').replace('A', '').strip()
                            import re
                            cleaned = re.sub(r'[^0-9.\\-]', '', cleaned)
                            if cleaned:
                                parsed = float(cleaned)
                                print(f"{indent}     Parsed: {parsed}")
                        except:
                            pass
                sensors_found += 1

        # Check children recursively (look deeper!)
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                sensors_found = find_and_show_sensors(child, depth + 1, max_sensors, sensors_found)
                if sensors_found >= max_sensors:
                    break

    return sensors_found


def find_sensor_locations(node, path="", max_examples=10, examples_found=0):
    """Find where sensors are located in the tree"""
    if examples_found >= max_examples:
        return examples_found

    if isinstance(node, dict):
        current_path = f"{path}/{node.get('Text', 'Unknown')}" if node.get('Text') else path

        # Check if this node is a sensor
        if "Type" in node and ("RawValue" in node or "Value" in node):
            if examples_found < max_examples:
                sensor_name = node.get("Text", "Unknown") 
                sensor_type = node.get("Type", "Unknown")
                raw_value = node.get("RawValue", "N/A")
                value_str = node.get("Value", "N/A")
                print(f"  📍 {current_path}")
                print(f"     Type: {sensor_type}, Name: {sensor_name}")
                print(f"     RawValue: {raw_value}, Value: {value_str}")

                # Show parsing result for Value field
                if value_str and value_str != "N/A":
                    try:
                        # Simple parsing simulation
                        cleaned = str(value_str).replace(',', '.').replace('°C', '').replace('RPM', '').replace('%', '').replace('MHz', '').replace('W', '').replace('GB', '').replace('MB', '').replace('V', '').replace('A', '').strip()
                        import re
                        cleaned = re.sub(r'[^0-9.\\-]', '', cleaned)
                        if cleaned:
                            parsed_value = float(cleaned)
                            print(f"     Parsed: {parsed_value}")
                    except:
                        print(f"     Parsed: FAILED")

            return examples_found + 1

        # Check children
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                examples_found = find_sensor_locations(child, current_path, max_examples, examples_found)
                if examples_found >= max_examples:
                    break

    return examples_found


def count_sensors(node):
    """Recursively count sensors in JSON tree"""
    count = 0

    if isinstance(node, dict):
        # Check if this node is a sensor - must have Type and Value fields
        if "Type" in node and "Value" in node:
            # Make sure it's a real sensor with a valid value (not just structure nodes)
            value = node.get("Value")
            if value is not None and str(value).strip() and str(value).lower() not in ["n/a", "", "null"]:
                count += 1

        # Check children recursively
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                count += count_sensors(child)

    return count


def investigate_cpu_gpu_sensors(node, path=""):
    """Special investigation to find CPU/GPU sensors"""
    if isinstance(node, dict):
        current_path = f"{path}/{node.get('Text', 'Unknown')}" if node.get('Text') else path
        node_text = node.get('Text', '').lower()

        # Look for CPU or GPU hardware
        if any(keyword in node_text for keyword in ['ryzen', 'intel', 'cpu', 'processor', 'geforce', 'radeon', 'nvidia', 'amd']):
            if any(keyword in node_text for keyword in ['ryzen', 'intel', 'cpu', 'processor']):
                hardware_type = "CPU"
            else:
                hardware_type = "GPU"

            print(f"  🔍 Investigating {hardware_type}: {node.get('Text', 'Unknown')}")

            if "Children" in node:
                for category in node.get("Children", []):
                    if isinstance(category, dict) and "Text" in category:
                        category_name = category["Text"]
                        category_sensors = count_sensors(category)
                        print(f"    📂 {category_name}: {category_sensors} sensors")
                        
                        # Show sample sensors from each category
                        if category_sensors > 0:
                            sample_count = find_and_show_sensors(category, depth=0, max_sensors=2, sensors_found=0)
        
        # Continue searching in children
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                investigate_cpu_gpu_sensors(child, current_path)


def investigate_fan_sensors(node, current_path=""):
    """Special investigation for fan sensors across all hardware components"""
    if isinstance(node, dict):
        node_text = node.get("Text", "").lower()
        current_path = f"{current_path}/{node.get('Text', 'Unknown')}" if node.get("Text") else current_path
        
        # Look for fan sensors in any hardware component
        if "Children" in node:
            fan_categories = []
            all_fans = []
            
            # Check if this node has fan categories or fan sensors
            for child in node.get("Children", []):
                if isinstance(child, dict):
                    child_text = child.get("Text", "").lower()
                    
                    # Check if this is a fan category
                    if "fan" in child_text:
                        fan_count = count_sensors(child)
                        if fan_count > 0:
                            fan_categories.append((child["Text"], fan_count, child))
                    
                    # Check if this child contains fan sensors
                    elif "Children" in child:
                        for grandchild in child.get("Children", []):
                            if isinstance(grandchild, dict) and "fan" in grandchild.get("Text", "").lower():
                                grandchild_count = count_sensors(grandchild)
                                if grandchild_count > 0:
                                    fan_categories.append((f"{child['Text']}/{grandchild['Text']}", grandchild_count, grandchild))
            
            # Display fan information if found
            if fan_categories:
                print(f"  🌬️ Found fans in {node.get('Text', 'Unknown')}:")
                for category_name, fan_count, category_node in fan_categories:
                    print(f"    📂 {category_name}: {fan_count} fan sensors")
                    
                    # Show actual fan sensors with values
                    if "Children" in category_node:
                        for fan_sensor in category_node.get("Children", []):
                            if isinstance(fan_sensor, dict) and "Value" in fan_sensor:
                                fan_name = fan_sensor.get("Text", "Unknown")
                                fan_value = fan_sensor.get("Value", "N/A")
                                fan_type = fan_sensor.get("Type", "Unknown")
                                print(f"      🌀 {fan_name}: {fan_value} ({fan_type})")
                                
                                # Parse and show RPM value
                                try:
                                    if fan_value and "RPM" in str(fan_value):
                                        rpm_str = str(fan_value).replace("RPM", "").replace(",", ".").strip()
                                        rpm_value = float(rpm_str)
                                        status = "🔴 Stopped" if rpm_value == 0 else "🟢 Running" if rpm_value < 1000 else "🟡 High Speed"
                                        print(f"        Status: {status} ({rpm_value} RPM)")
                                except:
                                    pass
        
        # Continue searching in children
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                investigate_fan_sensors(child, current_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Rigbeat Sensor Discovery Tool - Analyze LibreHardwareMonitor sensors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sensor_discovery.py                    # Auto-detect (HTTP preferred)
  python sensor_discovery.py --method http      # Force HTTP API only  
  python sensor_discovery.py --method wmi       # Force WMI only
  python sensor_discovery.py --host 192.168.1.100  # Remote system
        """
    )

    parser.add_argument(
        '--method',
        choices=['auto', 'http', 'wmi'],
        default='auto',
        help='Connection method (default: auto - tries HTTP first, falls back to WMI)'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='LibreHardwareMonitor HTTP API host (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8085,
        help='LibreHardwareMonitor HTTP API port (default: 8085)'
    )

    args = parser.parse_args()
    
    # Run the enhanced discovery with both HTTP and WMI support
    test_connection_methods(
        host=args.host,
        port=args.port, 
        method=args.method
    )