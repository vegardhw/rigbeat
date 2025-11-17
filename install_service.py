"""
Windows Service installer for Rigbeat
Run with: python install_service.py install
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import logging
from hardware_exporter import HardwareMonitor
from prometheus_client import start_http_server
import time

logging.basicConfig(
    filename='C:\\ProgramData\\PCHardwareMonitor\\service.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class PCHardwareMonitorService(win32serviceutil.ServiceFramework):
    """Windows Service for Rigbeat"""
    
    _svc_name_ = "PCHardwareMonitor"
    _svc_display_name_ = "Rigbeat Service"
    _svc_description_ = "Prometheus exporter for hardware monitoring (CPU/GPU temps, fan speeds)"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        socket.setdefaulttimeout(60)
        
    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        logging.info("Service stop requested")
        
    def SvcDoRun(self):
        """Main service loop"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        logging.info("Service starting...")
        self.main()
        
    def main(self):
        """Service main logic"""
        port = 9182
        interval = 2
        
        try:
            logging.info(f"Starting Rigbeat on port {port}")
            
            # Initialize hardware monitor
            monitor = HardwareMonitor()
            sys_info = monitor.get_system_info()
            logging.info(f"System detected: {sys_info}")
            
            # Start Prometheus HTTP server
            start_http_server(port)
            logging.info(f"Metrics endpoint: http://localhost:{port}/metrics")
            
            # Main monitoring loop
            while self.running:
                try:
                    monitor.update_metrics()
                except Exception as e:
                    logging.error(f"Error updating metrics: {e}")
                
                # Sleep with ability to interrupt
                for _ in range(interval * 10):  # Check stop event every 0.1s
                    if not self.running:
                        break
                    time.sleep(0.1)
                    
        except Exception as e:
            logging.error(f"Service error: {e}")
            servicemanager.LogErrorMsg(f"Service error: {e}")
        finally:
            logging.info("Service stopped")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PCHardwareMonitorService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PCHardwareMonitorService)


# Usage:
# Install:   python install_service.py install
# Start:     python install_service.py start
# Stop:      python install_service.py stop
# Remove:    python install_service.py remove
# Debug:     python install_service.py debug
