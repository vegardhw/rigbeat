@echo off
REM Rigbeat - Quick Install Script
REM Run as Administrator

echo ============================================
echo Rigbeat - Installation
echo ============================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges!
    echo Right-click and select "Run as Administrator"
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.8 or higher
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

echo [2/6] Installing Python dependencies...
if exist "requirements.txt" (
    echo Installing from requirements.txt...
    pip install -r requirements.txt
) else (
    echo Installing individual packages...
    pip install prometheus-client wmi pywin32
)
if %errorLevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.

echo [3/6] Creating service directory...
if not exist "C:\ProgramData\Rigbeat" (
    mkdir "C:\ProgramData\Rigbeat"
)
echo.

echo [4/6] Copying files...
copy hardware_exporter.py "C:\ProgramData\Rigbeat\"
copy install_service.py "C:\ProgramData\Rigbeat\"
copy test_fans.py "C:\ProgramData\Rigbeat\"
if exist "requirements.txt" (
    copy requirements.txt "C:\ProgramData\Rigbeat\"
)
echo.

echo [5/6] Installing Windows service...
cd "C:\ProgramData\Rigbeat"
python install_service.py install
if %errorLevel% neq 0 (
    echo ERROR: Failed to install service!
    pause
    exit /b 1
)
echo.

echo [6/6] Validating installation...
echo Testing hardware_exporter.py...
python hardware_exporter.py --help >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: hardware_exporter.py validation failed
) else (
    echo ✓ Hardware exporter validated
)
echo.

echo ============================================
echo Installation Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Download LibreHardwareMonitor from:
echo    https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases
echo.
echo 2. Run LibreHardwareMonitor.exe as Administrator
echo    - Enable "Run on Windows Startup" in Options
echo    - Enable "WMI" in Options (required!)
echo.
echo 3. Test fan detection (optional but recommended):
echo    cd "C:\ProgramData\Rigbeat"
echo    python test_fans.py
echo.
echo 4. Start the Rigbeat service:
echo    net start Rigbeat
echo.
echo 5. Verify metrics at: http://localhost:9182/metrics
echo.
echo 6. Configure Prometheus and import Grafana dashboard
echo.
echo Advanced options:
echo - Enable debug logging: python hardware_exporter.py --debug
echo - Save logs to file: python hardware_exporter.py --logfile rigbeat.log
echo - Custom port: python hardware_exporter.py --port 9183
echo.
echo Troubleshooting:
echo - If fans not detected: Run test_fans.py to diagnose
echo - Check service logs: C:\ProgramData\Rigbeat\service.log
echo - Ensure LibreHardwareMonitor shows your fans
echo.
echo For full documentation, visit:
echo https://github.com/vegardhw/rigbeat
echo.
pause
