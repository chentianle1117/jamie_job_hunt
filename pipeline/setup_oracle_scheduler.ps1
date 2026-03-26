# Oracle Scheduler Setup — Run ONCE to fully automate delivery
# Run: powershell -ExecutionPolicy Bypass -File "C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\setup_oracle_scheduler.ps1"

Write-Host "=== Oracle Scheduler Setup ===" -ForegroundColor Cyan

# Delivery task fires at 9:05am daily (5 min after Cowork's 9am search task)
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\run_oracle.ps1`""

$trigger  = New-ScheduledTaskTrigger -Daily -At "9:05AM"
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName    "OracleDelivery" `
    -Action      $action `
    -Trigger     $trigger `
    -Settings    $settings `
    -Description "Delivers Oracle job search results (Sheet + Email + Telegram). Cowork generates files at 9am; this picks up at 9:05am." `
    -Force

Write-Host "`n✅ OracleDelivery task registered — fires daily at 9:05am." -ForegroundColor Green
Write-Host "   Verify:  Get-ScheduledTask -TaskName OracleDelivery" -ForegroundColor Gray
Write-Host "   Remove:  Unregister-ScheduledTask -TaskName OracleDelivery -Confirm:`$false" -ForegroundColor Gray
