# Rigbeat - Modern PowerShell Installer
# Run as Administrator for full installation

#Requires -RunAsAdministrator

[CmdletBinding()]
param(
    [switch]$SkipPythonCheck,
    [switch]$Quiet
)

# Color functions for better user experience
function Write-Success { param($Message) Write-Host "$Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "$Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "$Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "$Message" -ForegroundColor Red }
function Write-Step { param($Step, $Message) Write-Host "[$Step] $Message" -ForegroundColor Magenta }

# Progress tracking
$TotalSteps = 7
$CurrentStep = 0

function Show-Progress {
    param($Activity, $Status)
    $script:CurrentStep++
    $PercentComplete = ($script:CurrentStep / $TotalSteps) * 100
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $PercentComplete
}

# Header
Clear-Host
Write-Host "============================================" -ForegroundColor Blue
Write-Host "        Rigbeat - Installation v0.1.3      " -ForegroundColor Blue
Write-Host "    Windows Hardware Monitoring System     " -ForegroundColor Blue
Write-Host "============================================" -ForegroundColor Blue
Write-Host ""

# Check for Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script requires Administrator privileges!"
    Write-Warning "Please right-click and select 'Run as Administrator'"
    if (-not $Quiet) { Read-Host "Press Enter to exit" }
    exit 1
}

# Function to check if command exists
function Test-Command {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Function to install Python via winget
function Install-PythonWithWinget {
    Write-Step $script:CurrentStep "Installing Python via winget..."
    Show-Progress "Installing Python" "Downloading and installing Python 3.14"

    if (-not (Test-Command "winget")) {
        Write-Error "winget is not available on this system"
        Write-Info "Please install Python manually from: https://www.python.org/downloads/"
        Write-Info "Make sure to check 'Add Python to PATH' during installation"
        throw "winget not available"
    }

    try {
        # Install Python 3.14 (stable and well-tested)
        Write-Info "Installing Python 3.14 via winget..."
        $result = winget install Python.Python.3.14 --exact --silent --accept-package-agreements --accept-source-agreements 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python installed successfully via winget"
            Write-Info "Refreshing environment variables..."

            # Refresh PATH environment variable
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")

            # Wait a moment for installation to complete
            Start-Sleep -Seconds 3

            return $true
        } else {
            Write-Warning "winget installation may have had issues: $result"
            return $false
        }
    }
    catch {
        Write-Error "Failed to install Python via winget: $_"
        return $false
    }
}

# Function to validate Python installation
function Test-PythonInstallation {
    Write-Info "Checking for Python installation..."

    # Try common Python commands
    $pythonCommands = @("python", "python3", "py")

    foreach ($cmd in $pythonCommands) {
        if (Test-Command $cmd) {
            try {
                $version = & $cmd --version 2>&1
                if ($version -match "Python (\d+)\.(\d+)") {
                    $major = [int]$matches[1]
                    $minor = [int]$matches[2]

                    if ($major -eq 3 -and $minor -ge 8) {
                        Write-Success "Found compatible Python: $version"
                        return $cmd
                    } else {
                        Write-Warning "Found Python $version (requires 3.8+)"
                    }
                }
            }
            catch {
                # Continue checking other commands
            }
        }
    }

    return $null
}

try {
    # Step 1: Check Python installation
    Show-Progress "Checking Prerequisites" "Validating Python installation"
    Write-Step 1 "Checking Python installation..."

    if (-not $SkipPythonCheck) {
        $pythonCmd = Test-PythonInstallation

        if (-not $pythonCmd) {
            Write-Warning "Python 3.8+ not found"
            Write-Info "Would you like to install Python automatically using winget? (Recommended)"

            if ($Quiet) {
                $installChoice = "Y"
            } else {
                $installChoice = Read-Host "Install Python via winget? [Y/n]"
            }

            if ($installChoice -eq "" -or $installChoice.ToLower() -eq "y") {
                $installed = Install-PythonWithWinget

                if ($installed) {
                    $pythonCmd = Test-PythonInstallation
                    if (-not $pythonCmd) {
                        Write-Error "Python installation verification failed"
                        Write-Info "Please restart your command prompt and try again, or install Python manually:"
                        Write-Info "https://www.python.org/downloads/"
                        exit 1
                    }
                } else {
                    Write-Error "Automatic Python installation failed"
                    Write-Info "Please install Python 3.8+ manually from: https://www.python.org/downloads/"
                    Write-Info "Make sure to check 'Add Python to PATH' during installation"
                    exit 1
                }
            } else {
                Write-Info "Please install Python 3.8+ manually from: https://www.python.org/downloads/"
                Write-Info "Make sure to check 'Add Python to PATH' during installation"
                exit 1
            }
        }
    } else {
        $pythonCmd = "python"  # Assume python is available when skipping check
    }

    # Step 2: Install Python dependencies
    Show-Progress "Installing Dependencies" "Installing required Python packages"
    Write-Step 2 "Installing Python dependencies..."

    $packages = @("prometheus-client", "wmi", "pywin32")

    if (Test-Path "requirements.txt") {
        Write-Info "Installing from requirements.txt..."
        & $pythonCmd -m pip install -r requirements.txt --upgrade
    } else {
        Write-Info "Installing individual packages: $($packages -join ', ')"
        & $pythonCmd -m pip install $packages --upgrade
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install Python dependencies"
    }
    Write-Success "Dependencies installed successfully"

    # Step 3: Create service directory
    Show-Progress "Setting up Directories" "Creating Rigbeat directory structure"
    Write-Step 3 "Creating service directory..."

    $serviceDir = "C:\ProgramData\Rigbeat"
    if (-not (Test-Path $serviceDir)) {
        New-Item -ItemType Directory -Path $serviceDir -Force | Out-Null
        Write-Success "Created directory: $serviceDir"
    } else {
        Write-Info "Directory already exists: $serviceDir"
    }

    # Step 4: Copy files
    Show-Progress "Copying Files" "Installing Rigbeat files"
    Write-Step 4 "Copying files to installation directory..."

    $filesToCopy = @(
        "hardware_exporter.py",
        "service_manager.py",
        "test_fans.py"
    )

    # Optional files
    $optionalFiles = @(
        "requirements.txt",
        "grafana_dashboard.json",
        "prometheus_config.yml",
        "FAN_SUPPORT.md"
    )

    foreach ($file in $filesToCopy) {
        if (Test-Path $file) {
            Copy-Item $file $serviceDir -Force
            Write-Success "Copied: $file"
        } else {
            Write-Error "Required file not found: $file"
            throw "Missing required file: $file"
        }
    }

    foreach ($file in $optionalFiles) {
        if (Test-Path $file) {
            Copy-Item $file $serviceDir -Force
            Write-Info "Copied optional file: $file"
        }
    }

    # Step 5: Install Windows service
    Show-Progress "Installing Service" "Setting up Windows service"
    Write-Step 5 "Installing Windows service..."

    Push-Location $serviceDir
    try {
        & $pythonCmd service_manager.py install
        if ($LASTEXITCODE -ne 0) {
            throw "Service installation failed"
        }
        Write-Success "Windows service installed successfully"
    }
    finally {
        Pop-Location
    }

    # Step 6: Validate installation
    Show-Progress "Validating Installation" "Testing installation components"
    Write-Step 6 "Validating installation..."

    Push-Location $serviceDir
    try {
        # Test hardware exporter
        & $pythonCmd hardware_exporter.py --help | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Hardware exporter validated"
        } else {
            Write-Warning "Hardware exporter validation failed"
        }

        # Check if service is registered
        $service = Get-Service -Name "Rigbeat" -ErrorAction SilentlyContinue
        if ($service) {
            Write-Success "Windows service registered: $($service.Status)"
        } else {
            Write-Warning "Windows service not found"
        }
    }
    finally {
        Pop-Location
    }

    # Step 7: Complete
    Show-Progress "Installation Complete" "Rigbeat installed successfully"
    Write-Step 7 "Installation complete!"

    Write-Progress -Activity "Installation" -Completed

    # Success message
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "        Installation Successful!            " -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""

    # Next steps
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "1. Install LibreHardwareMonitor:" -ForegroundColor White
    Write-Host "   Download: " -NoNewline -ForegroundColor White
    Write-Host "https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases" -ForegroundColor Cyan
    Write-Host "   Run as Administrator" -ForegroundColor Green
    Write-Host "   Enable 'WMI' in Options (required!)" -ForegroundColor Green
    Write-Host "   Enable 'Run on Windows Startup' (optional)" -ForegroundColor Green
    Write-Host ""

    Write-Host "2. Test Hardware Detection (Optional but recommended):" -ForegroundColor White
    Write-Host "   cd ""$serviceDir""" -ForegroundColor Gray
    Write-Host "   python test_fans.py" -ForegroundColor Gray
    Write-Host ""

    Write-Host "3. Start Rigbeat Service:" -ForegroundColor White
    Write-Host "   net start Rigbeat" -ForegroundColor Gray
    Write-Host ""

    Write-Host "4. Verify Installation:" -ForegroundColor White
    Write-Host "   Visit: " -NoNewline -ForegroundColor White
    Write-Host "http://localhost:9182/metrics" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "Advanced Options:" -ForegroundColor Yellow
    Write-Host "- Debug logging: python hardware_exporter.py --debug" -ForegroundColor Gray
    Write-Host "- Custom port: python hardware_exporter.py --port 9183" -ForegroundColor Gray
    Write-Host "- Service logs: $serviceDir\service.log" -ForegroundColor Gray
    Write-Host ""

    Write-Host "Documentation: " -NoNewline -ForegroundColor White
    Write-Host "https://vegardhw.github.io/rigbeat/" -ForegroundColor Cyan
    Write-Host "GitHub: " -NoNewline -ForegroundColor White
    Write-Host "https://github.com/vegardhw/rigbeat" -ForegroundColor Cyan
    Write-Host ""

    Write-Success "Installation completed successfully!"
}
catch {
    Write-Error "Installation failed: $_"
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "- Ensure you are running as Administrator" -ForegroundColor Gray
    Write-Host "- Check internet connection for package downloads" -ForegroundColor Gray
    Write-Host "- Verify Python 3.8+ is installed and in PATH" -ForegroundColor Gray
    Write-Host "- Check Windows Event Viewer for detailed errors" -ForegroundColor Gray
    Write-Host ""
    Write-Host "For support, visit: https://github.com/vegardhw/rigbeat/issues" -ForegroundColor Cyan

    if (-not $Quiet) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}

if (-not $Quiet) {
    Read-Host "Press Enter to exit"
}