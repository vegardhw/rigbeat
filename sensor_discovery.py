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
- ⚡ HTTP API structure investigation

Usage:
    python3 sensor_discovery.py [host] [port]

Examples:
    python3 sensor_discovery.py                    # Local LibreHardwareMonitor
    python3 sensor_discovery.py 192.168.1.100     # Remote system
    python3 sensor_discovery.py localhost 8080     # Custom port

Requirements:
- LibreHardwareMonitor running with HTTP server enabled
- Python 3.6+ with 'requests' package
"""

import requests
import json
import sys

def test_http_api(host="localhost", port=8085):
    """Test LibreHardwareMonitor HTTP API and show structure"""

    url = f"http://{host}:{port}/data.json"
    print(f"🔍 Rigbeat Sensor Discovery Tool")
    print(f"📡 Connecting to LibreHardwareMonitor at {url}")
    print("=" * 80)

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ HTTP API Response received")
            print(f"📊 Response size: {len(response.text)} characters")
            print()

            # Show top-level structure
            if isinstance(data, dict):
                print(f"🔍 Top-level keys: {list(data.keys())}")
                if "Text" in data:
                    print(f"📝 Root Text: {data['Text']}")
                if "Children" in data:
                    print(f"👥 Root Children: {len(data['Children'])}")
                    print()

                    # Show first few hardware components
                    print("🖥️  Hardware Components:")
                    for i, child in enumerate(data["Children"][:10]):  # Show up to 10 components
                        if isinstance(child, dict) and "Text" in child:
                            child_text = child["Text"]
                            child_children = len(child.get("Children", []))
                            print(f"  {i+1}. {child_text} ({child_children} children)")

                            # Explore each hardware component for sensors (not just the first one!)
                            if "Children" in child:
                                print(f"     🔍 Exploring {child_text}...")

                                # Check if this hardware has direct sensors or intermediate levels
                                direct_sensors = count_direct_sensors(child)
                                if direct_sensors > 0:
                                    print(f"       📊 {direct_sensors} sensors at this level")
                                    sensor_count = find_and_show_sensors(child, depth=1, max_sensors=20, sensors_found=0)  # Show more sensors
                                else:
                                    # Look for intermediate levels (like "Nuvoton NCT6792D")
                                    print(f"       🔍 Checking intermediate levels...")
                                    intermediate_count = 0
                                    total_sensors_found = 0

                                    for intermediate in child.get("Children", []):
                                        if isinstance(intermediate, dict) and "Text" in intermediate:
                                            intermediate_name = intermediate["Text"]
                                            intermediate_sensors = count_sensors(intermediate)

                                            if intermediate_sensors > 0:
                                                print(f"       📁 {intermediate_name}: {intermediate_sensors} sensors")

                                                # Show what sensor categories exist under this hardware
                                                if "Children" in intermediate:
                                                    print(f"          🔍 Sensor categories:")
                                                    for category in intermediate.get("Children", []):
                                                        if isinstance(category, dict) and "Text" in category:
                                                            category_name = category["Text"]
                                                            category_sensors = count_sensors(category)
                                                            print(f"             📂 {category_name}: {category_sensors} sensors")

                                                            # Show ALL sensors in each category (like the Special investigation)
                                                            if category_sensors > 0:
                                                                print(f"                🔍 Sensors in {category_name}:")
                                                                find_and_show_sensors(category, depth=4, max_sensors=category_sensors, sensors_found=0)

                                                if total_sensors_found < 50:  # Show many more sensors from each hardware component
                                                    subsensors = find_and_show_sensors(intermediate, depth=2, max_sensors=20, sensors_found=0)
                                                    total_sensors_found += subsensors
                                                intermediate_count += 1

                                    if intermediate_count == 0:
                                        print("       ❌ No sensors found in this component")
                                    else:
                                        sensor_count = total_sensors_found

                    print()

                    # Search for any sensors in the entire tree
                    print("🔍 Searching entire tree for sensors...")
                    total_sensors = count_sensors(data)
                    print(f"📊 Total sensors found: {total_sensors}")

                    if total_sensors > 0:
                        # Remove redundant sensor locations since Hardware Components now shows everything
                        # print("🔍 Finding sensor locations...")
                        # find_sensor_locations(data, path="Root", max_examples=15)  # Show more examples

                        # Special investigation for CPU/GPU/Fan sensors
                        print("\n🔍 Special Hardware Investigation:")
                        investigate_cpu_gpu_sensors(data)
                        print("\n🌬️ Fan Analysis:")
                        investigate_fan_sensors(data)

                    if total_sensors == 0:
                        print("❌ No sensors found anywhere in the JSON tree!")
                        print("💡 This might indicate:")
                        print("   1. LibreHardwareMonitor HTTP server disabled")
                        print("   2. Different JSON structure than expected")
                        print("   3. Hardware not properly detected")

            else:
                print(f"❌ Unexpected response type: {type(data)}")
                print(f"Response: {data}")

        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text[:200]}...")

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - Cannot reach LibreHardwareMonitor at {host}:{port}")
        print("\n💡 Troubleshooting Steps:")
        print("   1. Ensure LibreHardwareMonitor is running")
        print("   2. Enable HTTP server: Options → Web Server → Enable Web Server ✅")
        print(f"   3. Verify the address: http://{host}:{port}/data.json")
        print("   4. Check firewall settings if connecting remotely")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("\n💡 Please check your connection settings and try again.")

    print("=" * 80)


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
    print("🔍 Rigbeat Sensor Discovery Tool")
    print("=" * 40)
    print()
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8085
    else:
        host = "localhost"
        port = 8085
    
    test_http_api(host, port)