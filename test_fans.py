"""
Fan Detection Test Script
Run this to see all detected fans from LibreHardwareMonitor
Helps debug fan naming and categorization
"""

import wmi
import sys
from collections import defaultdict

def test_fan_detection():
    """Test and display all detected fans"""

    print("=" * 80)
    print("Rigbeat - Fan Detection Test")
    print("=" * 80)
    print()

    try:
        w = wmi.WMI(namespace="root\\LibreHardwareMonitor")
        print("✓ Connected to LibreHardwareMonitor WMI")
        print()
    except Exception as e:
        print(f"✗ ERROR: Failed to connect to LibreHardwareMonitor")
        print(f"  {e}")
        print()
        print("Make sure:")
        print("  1. LibreHardwareMonitor is running")
        print("  2. It's running as Administrator")
        print("  3. WMI is enabled in Options")
        return 1

    # Get all sensors
    try:
        sensors = w.Sensor()
    except Exception as e:
        print(f"✗ ERROR: Failed to read sensors: {e}")
        return 1

    # Categorize fans
    fans_by_type = defaultdict(list)
    all_fan_data = []

    for sensor in sensors:
        if sensor.SensorType == "Fan":
            sensor_name = sensor.Name
            value = float(sensor.Value) if sensor.Value else 0
            parent = sensor.Parent

            # Categorize
            fan_name_lower = sensor_name.lower()

            if "gpu" in fan_name_lower or "vga" in fan_name_lower:
                fan_type = "GPU"
                if "1" in sensor_name:
                    fan_label = "gpu_fan_1"
                elif "2" in sensor_name:
                    fan_label = "gpu_fan_2"
                else:
                    fan_label = "gpu_fan"
            elif "cpu" in fan_name_lower:
                fan_type = "CPU"
                fan_label = "cpu_fan"
            elif "cha" in fan_name_lower or "chassis" in fan_name_lower or "case" in fan_name_lower:
                fan_type = "Chassis"
                if "1" in sensor_name or "#1" in sensor_name:
                    fan_label = "chassis_fan_1"
                elif "2" in sensor_name or "#2" in sensor_name:
                    fan_label = "chassis_fan_2"
                elif "3" in sensor_name or "#3" in sensor_name:
                    fan_label = "chassis_fan_3"
                elif "4" in sensor_name or "#4" in sensor_name:
                    fan_label = "chassis_fan_4"
                else:
                    fan_label = "chassis_fan"
            else:
                fan_type = "Other"
                fan_label = sensor_name.lower().replace(" ", "_").replace("#", "")

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
    print("  2. Update Grafana queries to use these exact labels")
    print("  3. Run 'python hardware_exporter.py' to start the exporter")
    print("  4. Check http://localhost:9182/metrics to see live data")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(test_fan_detection())