@echo off
REM Rigbeat - Installation Wrapper
REM This launches the modern PowerShell installer

echo ============================================
echo Rigbeat - Installation v0.1.3
echo ============================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This installation requires Administrator privileges.
    echo.
    echo Please right-click this file and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo Launching PowerShell installer...
echo.

REM Check if PowerShell is available (it should be on Win10/11)
powershell -Command "Write-Host 'PowerShell available'" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: PowerShell is not available on this system.
    echo Please install PowerShell or use manual installation instructions.
    pause
    exit /b 1
)

REM Launch the PowerShell installer
powershell -ExecutionPolicy Bypass -File "%~dp0Install-Rigbeat.ps1"

echo.
echo PowerShell installer completed.
pause
