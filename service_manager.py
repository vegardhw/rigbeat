"""
Rigbeat Service Manager
Manage the Rigbeat Windows service: install, remove, start, stop, debug

Configuration:
- Service runs on port 9182 by default
- Update interval: 2 seconds (optimized for real-time monitoring)
- Sensor mode: essential (core metrics only, ~25-30 sensors)
- Logs to: C:\ProgramData\Rigbeat\service.log
- Uses LibreHardwareMonitor HTTP API (preferred) or WMI (fallback)
- HTTP API provides 6-42x better performance than WMI

Sensor Modes:
  essential:   Core gaming/monitoring metrics (~25-30 sensors) - Default
  extended:    Detailed monitoring (~60 sensors)
  diagnostic:  All available sensors (~150+ sensors)

Usage:
  Install:   python service_manager.py install
  Start:     python service_manager.py start
  Stop:      python service_manager.py stop
  Remove:    python service_manager.py remove
  Debug:     python service_manager.py debug
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import logging
import os
from hardware_exporter import HardwareMonitor, system_info
from prometheus_client import start_http_server
import time
import pythoncom

# Ensure log directory exists
log_dir = 'C:\\ProgramData\\Rigbeat'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename='C:\\ProgramData\\Rigbeat\\service.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RigbeatService(win32serviceutil.ServiceFramework):
    """Windows Service for Rigbeat"""

    _svc_name_ = "Rigbeat"
    _svc_display_name_ = "Rigbeat Service"
    _svc_description_ = "Prometheus exporter for hardware monitoring (CPU/GPU temps, fan speeds) - HTTP API optimized with intelligent sensor filtering"

    def __init__(self, args):
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.running = True
            socket.setdefaulttimeout(60)
            logger.info("Service initialized successfully")
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            raise

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        logger.info("Service stop requested")

    def SvcDoRun(self):
        """Main service loop"""
        try:
            # Report service start
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING)

            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            logger.info("Service starting...")

            # Report service running
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)

            # Run main service logic
            self.main()

        except Exception as e:
            logger.error(f"Service run error: {e}")
            servicemanager.LogErrorMsg(f"Service run error: {e}")
            # Report service stopped due to error
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def main(self):
        """Service main logic"""
        port = 9182
        interval = 2
        monitor = None
        sensor_mode = 'essential'  # Default to essential mode for service

        # HTTP API configuration (LibreHardwareMonitor defaults)
        http_host = "localhost"
        http_port = 8085

        try:
            # Initialize COM for WMI access in service context
            pythoncom.CoInitialize()
            logger.info("COM initialized for WMI access")

            logger.info(f"Starting Rigbeat Service v0.1.3 on port {port}")
            logger.info(f"Update interval: {interval} seconds")
            logger.info(f"Sensor mode: {sensor_mode}")
            logger.info(f"LibreHardwareMonitor HTTP API target: {http_host}:{http_port}")

            # Initialize hardware monitor with HTTP API support and sensor filtering
            try:
                monitor = HardwareMonitor(http_host=http_host, http_port=http_port, sensor_mode=sensor_mode)
                logger.info(f"Hardware monitor initialized with HTTP API support (mode: {sensor_mode})")
                # Get and set system info
                sys_info = monitor.get_system_info()
                system_info.info(sys_info)
                logger.info(f"System detected: CPU={sys_info['cpu']}, GPU={sys_info['gpu']}")

                # Log connection method and performance info
                if monitor.use_http:
                    logger.info("🚀 Using LibreHardwareMonitor HTTP API (6-42x performance improvement)")
                    logger.info(f"📊 Monitoring mode: {sensor_mode} (optimized sensor filtering enabled)")
                else:
                    logger.info("⚠️  Using WMI fallback (higher CPU usage)")
                    logger.info("💡 Enable LibreHardwareMonitor HTTP server for better performance")
                    logger.info(f"📊 Monitoring mode: {sensor_mode} (sensor filtering active)")

            except Exception as e:
                logger.warning(f"LibreHardwareMonitor not available: {e}")
                logger.info("Running in demo mode - no actual hardware metrics will be collected")
                monitor = None
                # Set basic system info for demo mode
                sys_info = {'cpu': 'Demo CPU', 'gpu': 'Demo GPU', 'motherboard': 'Demo Board'}
                system_info.info(sys_info)
                logger.info("Demo mode: Service will run without collecting metrics")

            # Start Prometheus HTTP server
            start_http_server(port)
            logger.info(f"Metrics available at http://localhost:{port}/metrics")

            # Main monitoring loop
            while self.running:
                try:
                    if monitor and monitor.connected:
                        start_time = time.time()
                        monitor.update_metrics()
                        update_duration = time.time() - start_time

                        # Log performance metrics for troubleshooting
                        if update_duration > 0.5:  # Log slow updates
                            logger.warning(f"Slow metrics update: {update_duration:.3f}s (consider reducing sensor count)")
                        elif update_duration > 0.1:
                            logger.debug(f"Metrics update took {update_duration:.3f}s")

                        # Log sensor filtering effectiveness periodically (every 5 minutes)
                        # This helps verify the service is running efficiently
                        current_time = time.time()
                        if not hasattr(monitor, '_last_sensor_log') or (current_time - monitor._last_sensor_log) > 300:
                            # Get quick sensor count for status logging
                            sensors = monitor.get_sensors()
                            if sensors:
                                logger.info(f"📊 Service running efficiently: {sensor_mode} mode filtering active")
                                logger.info(f"🔧 HTTP API performance: {update_duration:.3f}s update time")
                            monitor._last_sensor_log = current_time
                except Exception as e:
                    logger.error(f"Error updating metrics: {e}")
                    # Log additional context for troubleshooting
                    if monitor and hasattr(monitor, 'use_http'):
                        if monitor.use_http:
                            logger.error("🔌 HTTP API error - check LibreHardwareMonitor HTTP server status on port 8085")
                            logger.error("💡 Verify LibreHardwareMonitor Options → Web Server is enabled")
                        else:
                            logger.error("🔧 WMI error - check LibreHardwareMonitor WMI Provider access")
                            logger.error("💡 Verify LibreHardwareMonitor Options → WMI Provider is enabled")
                    logger.error(f"Sensor mode: {sensor_mode} - consider switching to diagnostic mode for troubleshooting")

                # Sleep with ability to interrupt
                for _ in range(interval * 10):  # Check stop event every 0.1s
                    if not self.running:
                        break
                    if win32event.WaitForSingleObject(self.stop_event, 100) == win32event.WAIT_OBJECT_0:
                        self.running = False
                        break
                    time.sleep(0.1)

        except ImportError as e:
            logger.error(f"Import error - missing dependencies: {e}")
            logger.error("Ensure 'requests' package is installed for HTTP API support")
            servicemanager.LogErrorMsg(f"Missing dependencies: {e}")
        except Exception as e:
            logger.error(f"Service error: {e}")
            servicemanager.LogErrorMsg(f"Service error: {e}")
        finally:
            logger.info("Service stopped")
            # Cleanup COM
            try:
                pythoncom.CoUninitialize()
                logger.info("COM uninitialized")
            except Exception:
                pass
            # Ensure we report stopped status
            try:
                self.ReportServiceStatus(win32service.SERVICE_STOPPED)
            except Exception:
                pass
if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RigbeatService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(RigbeatService)
