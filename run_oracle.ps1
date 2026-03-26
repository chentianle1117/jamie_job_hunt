###############################################################
# run_oracle.ps1 — Oracle Job Search: Cleanup + Delivery
#
# This is the SINGLE script to run after each Oracle search.
# It does 3 things:
#   1. Archives expired/old Notion entries (reads cleanup_pages.json)
#   2. Sends the daily email to Jamie
#   3. Sends the Telegram digest
#
# Run: powershell -ExecutionPolicy Bypass -File "C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\run_oracle.ps1"
###############################################################

$baseDir       = "C:\Users\chent\Agentic_Workflows_2026\oracle-job-search"
$date          = Get-Date -Format "MMM d, yyyy"
$NOTION_TOKEN  = $env:NOTION_TOKEN
$NOTION_VER    = "2022-06-28"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Oracle Pipeline - $date" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ─────────────────────────────────────────────
# STEP 1: Notion Cleanup (archive expired pages)
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[1/3] Notion Cleanup..." -ForegroundColor Yellow

$cleanupPath = "$baseDir\cleanup_pages.json"
if (Test-Path $cleanupPath) {
    $pages = Get-Content $cleanupPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($pages.Count -gt 0) {
        $notionHeaders = @{
            "Authorization"  = "Bearer $NOTION_TOKEN"
            "Notion-Version" = $NOTION_VER
            "Content-Type"   = "application/json"
        }
        $archiveBody = '{"archived": true}'
        $ok = 0; $fail = 0

        foreach ($p in $pages) {
            $url = "https://api.notion.com/v1/pages/$($p.id)"
            try {
                Invoke-RestMethod -Uri $url -Method Patch -Headers $notionHeaders -Body $archiveBody -ErrorAction Stop | Out-Null
                Write-Host "  [OK] $($p.reason)" -ForegroundColor Green
                $ok++
            }
            catch {
                $code = $_.Exception.Response.StatusCode.value__
                Write-Host "  [FAIL] $($p.reason) (HTTP $code)" -ForegroundColor Red
                $fail++
            }
            Start-Sleep -Milliseconds 350
        }
        Write-Host "  Cleanup done: $ok archived, $fail failed" -ForegroundColor Cyan

        # Rename the file so it doesn't re-run next time
        $archiveName = "$baseDir\cleanup_pages_done_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        Move-Item $cleanupPath $archiveName -Force
        Write-Host "  Moved cleanup file to: $archiveName" -ForegroundColor DarkGray
    } else {
        Write-Host "  No pages to clean up." -ForegroundColor DarkGray
    }
} else {
    Write-Host "  No cleanup_pages.json found - skipping." -ForegroundColor DarkGray
}

# ─────────────────────────────────────────────
# STEP 2: Send Email
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[2/3] Sending email to Jamie..." -ForegroundColor Yellow

$emailBodyPath = "$baseDir\email_body.txt"
if (Test-Path $emailBodyPath) {
    & "C:\Users\chent\go\bin\gog.exe" gmail send `
        --to      jamiecheng0103@gmail.com `
        --subject "Daily Job Feed - $date" `
        --body-file $emailBodyPath `
        --account tianlechen0324@gmail.com
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Email sent." -ForegroundColor Green
    } else {
        Write-Host "  [WARN] gog.exe exited with code $LASTEXITCODE - check OAuth token" -ForegroundColor Red
    }
} else {
    Write-Host "  [SKIP] email_body.txt not found." -ForegroundColor Red
}

# ─────────────────────────────────────────────
# STEP 3: Send Telegram
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "[3/3] Sending Telegram..." -ForegroundColor Yellow

$telegramPath = "$baseDir\telegram_msg.txt"
if (Test-Path $telegramPath) {
    $botToken = $env:TELEGRAM_BOT_TOKEN
    $chatId   = $env:TELEGRAM_CHAT_ID
    $msg      = Get-Content $telegramPath -Raw -Encoding UTF8
    $body     = @{ chat_id = $chatId; text = $msg } | ConvertTo-Json -Depth 2
    try {
        Invoke-RestMethod -Uri "https://api.telegram.org/bot$botToken/sendMessage" `
            -Method Post -Body $body -ContentType "application/json; charset=utf-8" | Out-Null
        Write-Host "  [OK] Telegram sent." -ForegroundColor Green
    }
    catch {
        Write-Host "  [FAIL] Telegram error: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "  [SKIP] telegram_msg.txt not found." -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Oracle Pipeline Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
