#!/usr/bin/env python3
"""
Debug LibreHardwareMonitor HTTP API
Quick test to see what the HTTP API actually returns
"""

import requests
import json
import sys

def test_http_api(host="localhost", port=8085):
    """Test LibreHardwareMonitor HTTP API and show structure"""
    
    url = f"http://{host}:{port}/data.json"
    print(f"Testing LibreHardwareMonitor HTTP API at {url}")
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
                                sensor_count = find_and_show_sensors(child, depth=1, max_sensors=3, sensors_found=0)
                                if sensor_count == 0:
                                    print("       ❌ No sensors found in this component")
                                elif sensor_count > 3:
                                    print(f"       ... and {sensor_count - 3} more sensors in this component")
                    
                    print()
                    
                    # Search for any sensors in the entire tree
                    print("🔍 Searching entire tree for sensors...")
                    total_sensors = count_sensors(data)
                    print(f"📊 Total sensors found: {total_sensors}")
                    
                    if total_sensors > 0:
                        print("🔍 Finding sensor locations...")
                        find_sensor_locations(data, path="Root", max_examples=10)
                    
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
        print(f"❌ Connection failed - LibreHardwareMonitor HTTP server not running")
        print("💡 Enable HTTP server in LibreHardwareMonitor:")
        print("   Options → Web Server → Enable Web Server ✅")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("=" * 80)


def find_and_show_sensors(node, depth=0, max_sensors=5, sensors_found=0):
    """Find and show sensors in a node and its children"""
    
    if sensors_found >= max_sensors:
        return sensors_found
        
    if isinstance(node, dict):
        # Check if this node is a sensor
        if "Type" in node and ("RawValue" in node or "Value" in node):
            if sensors_found < max_sensors:
                sensor_name = node.get("Text", "Unknown")
                sensor_type = node.get("Type", "Unknown")
                raw_value = node.get("RawValue", "N/A")
                value = node.get("Value", "N/A")
                indent = "       " + "  " * depth
                print(f"{indent}🌡️  {sensor_type}: {sensor_name}")
                print(f"{indent}     RawValue: {raw_value}, Value: {value}")
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
                print(f"  📍 {current_path}")
                print(f"     Type: {sensor_type}, Name: {sensor_name}, RawValue: {raw_value}")
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
        # Check if this node is a sensor
        if "Type" in node and ("RawValue" in node or "Value" in node):
            count += 1
            
        # Check children
        if "Children" in node and isinstance(node["Children"], list):
            for child in node["Children"]:
                count += count_sensors(child)
    
    return count


if __name__ == "__main__":
    if len(sys.argv) > 1:
        host = sys.argv[1]
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8085
    else:
        host = "localhost"
        port = 8085
    
    test_http_api(host, port)