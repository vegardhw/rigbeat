"""
Rigbeat - Prometheus Exporter
Exports Windows hardware metrics (CPU/GPU temps, fan speeds, loads) for Prometheus/Grafana

Requirements:
    - LibreHardwareMonitor running with WMI enabled
    - Python 3.8+
    - pip install prometheus-client wmi pywin32
"""
import time
