"""
Windows Service installer for Rigbeat
Run with: python install_service.py install

Configuration:
- Service runs on port 9182 by default
- Update interval: 2 seconds
- Logs to: C:\\ProgramData\\Rigbeat\\service.log
- Requires LibreHardwareMonitor running with WMI enabled

Usage:
  Install:   python install_service.py install
  Start:     python install_service.py start
  Stop:      python install_service.py stop
  Remove:    python install_service.py remove
  Debug:     python install_service.py debug
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import logging
import os
from hardware_exporter import HardwareMonitor
from prometheus_client import start_http_server, Info
import time

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
    _svc_description_ = "Prometheus exporter for hardware monitoring (CPU/GPU temps, fan speeds)"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        socket.setdefaulttimeout(60)

        # Initialize system info metric
        self.system_info = Info('rigbeat_system', 'System information')

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        logger.info("Service stop requested")

    def SvcDoRun(self):
        """Main service loop"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        logger.info("Service starting...")
        self.main()

    def main(self):
        """Service main logic"""
        port = 9182
        interval = 2

        try:
            logger.info(f"Starting Rigbeat Service on port {port}")
            logger.info(f"Update interval: {interval} seconds")

            # Initialize hardware monitor
            monitor = HardwareMonitor()

            # Get and set system info
            sys_info = monitor.get_system_info()
            self.system_info.info(sys_info)
            logger.info(f"System detected: CPU={sys_info['cpu']}, GPU={sys_info['gpu']}")

            # Start Prometheus HTTP server
            start_http_server(port)
            logger.info(f"Metrics available at http://localhost:{port}/metrics")

            # Main monitoring loop
            while self.running:
                try:
                    monitor.update_metrics()
                except Exception as e:
                    logger.error(f"Error updating metrics: {e}")

                # Sleep with ability to interrupt
                for _ in range(interval * 10):  # Check stop event every 0.1s
                    if not self.running:
                        break
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"Service error: {e}")
            servicemanager.LogErrorMsg(f"Service error: {e}")
        finally:
            logger.info("Service stopped")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RigbeatService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(RigbeatService)
