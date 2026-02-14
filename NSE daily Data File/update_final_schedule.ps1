# Update Windows Task for NSE Scanner
$taskName = "NSE Daily Scanner Runner"
$pythonPath = "python.exe"
$scriptPath = "G:\My Drive\Trade_with_Nilay\NSE daily Data File\nse_daily_runner.py"
$workingDir = "G:\My Drive\Trade_with_Nilay\NSE daily Data File"

# Delete old tasks
schtasks /delete /tn "NSE Daily 2773 Stocks" /f 2>$null
schtasks /delete /tn "NSE Daily Stock Update" /f 2>$null

# Create new task with multiple triggers
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`"" -WorkingDirectory $workingDir

# Create multiple triggers
$trigger1 = New-ScheduledTaskTrigger -Daily -At "8:30AM"
$trigger2 = New-ScheduledTaskTrigger -Daily -At "1:00PM"
$trigger3 = New-ScheduledTaskTrigger -Daily -At "4:00PM"

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register task with first trigger, add others
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger1 -Settings $settings -Description "Runs NSE Scanner at 8:30 AM, 1 PM, 4 PM daily" -Force

# Add additional triggers
$task = Get-ScheduledTask -TaskName $taskName
$task.Triggers.Add($trigger2)
$task.Triggers.Add($trigger3)
$task | Set-ScheduledTask

Write-Host "✅ DAILY SCHEDULE UPDATED!"
Write-Host "Task: $taskName"
Write-Host "Runs at: 8:30 AM, 1:00 PM, 4:00 PM daily"
Write-Host "Script: $scriptPath"