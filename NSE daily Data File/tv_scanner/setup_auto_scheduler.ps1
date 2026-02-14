# NilayChopdaScanner - Windows Task Scheduler Setup
# Run this ONCE to set up automatic daily scanning
# Right-click and select "Run with PowerShell"

Write-Host "`n=========================================================================" -ForegroundColor Cyan
Write-Host "NilayChopdaScanner - Windows Task Scheduler Setup" -ForegroundColor Green
Write-Host "=========================================================================`n" -ForegroundColor Cyan

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click the script and select 'Run with PowerShell as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "Admin rights confirmed ✓" -ForegroundColor Green
Write-Host ""

# Define paths
$scannerDir = "G:\My Drive\Trade_with_Nilay\NSE daily Data File\tv_scanner"
$pythonScript = "$scannerDir\nilaychopda_live_scanner.py"
$pythonExe = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe"

# Check if Python exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "Python not found at: $pythonExe" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ or update the path" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "Python found: $pythonExe ✓" -ForegroundColor Green
Write-Host ""

# Create task
Write-Host "Setting up Windows Task Scheduler..." -ForegroundColor Yellow
Write-Host ""

$taskName = "NilayChopdaScanner"
$taskDescription = "Automatic NSE stock scanner at 9:15 AM IST daily"

# Define task trigger (9:15 AM daily)
$trigger = New-ScheduledTaskTrigger -Daily -At "09:15"

# Define task action
$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "`"$pythonScript`"" `
    -WorkingDirectory $scannerDir

# Define task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register task
try {
    # Remove existing task if it exists
    $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Removing existing task..."
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Old task removed ✓" -ForegroundColor Green
    }
    
    # Create new task
    Register-ScheduledTask `
        -TaskName $taskName `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -Description $taskDescription `
        -RunLevel Highest | Out-Null
    
    Write-Host "Task created successfully! ✓" -ForegroundColor Green
    Write-Host ""
    
    # Verify task
    $task = Get-ScheduledTask -TaskName $taskName
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $($task.TaskName)"
    Write-Host "  Status: $($task.State)"
    Write-Host "  Run Time: 09:15 AM IST (Daily)"
    Write-Host ""
    
} catch {
    Write-Host "Error creating task: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "SETUP COMPLETE! ✓" -ForegroundColor Green
Write-Host "=========================================================================`n" -ForegroundColor Cyan

Write-Host "Your scanner will now:" -ForegroundColor Yellow
Write-Host "  ✓ Run automatically at 09:15 AM every weekday" -ForegroundColor Green
Write-Host "  ✓ No need to open any app or window" -ForegroundColor Green
Write-Host "  ✓ Scan all 18 signals (price: 50-2000)" -ForegroundColor Green
Write-Host "  ✓ Send Telegram alerts to @nilaychopda" -ForegroundColor Green
Write-Host "  ✓ Log results daily" -ForegroundColor Green
Write-Host ""

Write-Host "To view scheduled tasks:" -ForegroundColor Yellow
Write-Host "  1. Open 'Task Scheduler'" -ForegroundColor White
Write-Host "  2. Go to 'Task Scheduler Library'" -ForegroundColor White
Write-Host "  3. Look for 'NilayChopdaScanner'" -ForegroundColor White
Write-Host ""

Write-Host "To test right now:" -ForegroundColor Yellow
Write-Host "  Run: python nilaychopda_live_scanner.py" -ForegroundColor White
Write-Host ""

Write-Host "Log files (check daily results):" -ForegroundColor Yellow
Write-Host "  • nilaychopda_scheduler.log" -ForegroundColor White
Write-Host "  • scanner_daily.log" -ForegroundColor White
Write-Host "  • nilaychopda_scanner.log" -ForegroundColor White
Write-Host ""

Write-Host "==========================================================================" -ForegroundColor Cyan

Read-Host "Press Enter to close"
