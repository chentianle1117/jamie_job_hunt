@echo off
title Oracle Job Search — Scheduler Setup
color 0B

echo.
echo  ============================================
echo   Oracle Job Search — One-Time Setup
echo  ============================================
echo.
echo  This will register a Windows Task Scheduler
echo  task called "OracleDelivery" that fires
echo  daily at 9:05am to send Jamie's job digest
echo  via Email + Telegram.
echo.
echo  (Cowork handles the search at 9:00am.)
echo.
pause

echo.
echo  Registering OracleDelivery scheduled task...
powershell -ExecutionPolicy Bypass -File "%~dp0setup_oracle_scheduler.ps1"

echo.
echo  ============================================
echo   Done! Verifying task...
echo  ============================================
powershell -Command "Get-ScheduledTask -TaskName 'OracleDelivery' | Select-Object TaskName, State, @{N='NextRun';E={($_ | Get-ScheduledTaskInfo).NextRunTime}} | Format-List"

echo.
echo  To test delivery right now (requires email_body.txt + telegram_msg.txt):
echo    powershell -ExecutionPolicy Bypass -File "%~dp0run_oracle.ps1"
echo.
pause
