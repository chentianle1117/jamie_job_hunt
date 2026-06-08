# google_workspace_mcp_refresh.ps1
# Pre-refresh Google OAuth access tokens for workspace-mcp.
#
# The workspace-mcp stores refresh_tokens but does not auto-refresh access tokens
# on expiry — it falls through to "ACTION REQUIRED" re-auth instead. This script
# runs out-of-band, refreshes any near-expired access tokens, and writes them
# back so the MCP always sees fresh tokens.
#
# Schedule: Windows Task Scheduler, every 50 minutes (access tokens last 1 hour).
# Setup 2026-05-05.

$credsDir     = "$env:USERPROFILE\.google_workspace_mcp\credentials"
$logFile      = "$env:USERPROFILE\.google_workspace_mcp\refresh.log"
$thresholdMin = 10  # refresh if access token expires within this many minutes

function Write-Log {
    param([string]$msg)
    $ts   = (Get-Date).ToUniversalTime().ToString("o")
    $line = "[$ts] $msg"
    Write-Host $line
    try {
        Add-Content -Path $logFile -Value $line -Encoding UTF8 -ErrorAction Stop
    } catch {
        Write-Host "log write failed: $_"
    }
}

if (-not (Test-Path $credsDir)) {
    Write-Log "CREDS_DIR does not exist: $credsDir"
    exit 1
}

$files = Get-ChildItem -Path $credsDir -Filter "*.json" | Where-Object {
    $_.Name -notlike "oauth_states*" -and $_.Name -notmatch "\.revoked-"
}

if ($files.Count -eq 0) {
    Write-Log "no credential files found"
    exit 0
}

Write-Log "checking $($files.Count) credential files"

foreach ($f in $files) {
    try {
        $creds = Get-Content $f.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Write-Log "SKIP $($f.Name): read failed - $_"
        continue
    }

    if (-not $creds.refresh_token) {
        Write-Log "SKIP $($f.Name): no refresh_token"
        continue
    }

    $needsRefresh = $true
    if ($creds.expiry) {
        try {
            # Stored as naive ISO ("2026-05-05T16:30:38.445831") — treat as UTC
            $exp = [DateTime]::ParseExact(
                ($creds.expiry -replace '\.[0-9]+$',''),
                "yyyy-MM-ddTHH:mm:ss",
                [System.Globalization.CultureInfo]::InvariantCulture,
                [System.Globalization.DateTimeStyles]::AssumeUniversal -bor [System.Globalization.DateTimeStyles]::AdjustToUniversal
            )
            $now = (Get-Date).ToUniversalTime()
            if ($exp -gt $now.AddMinutes($thresholdMin)) {
                $needsRefresh = $false
                $remaining = [int]($exp - $now).TotalMinutes
                Write-Log "OK   $($f.Name): expires in $remaining min (expiry $($creds.expiry))"
            }
        } catch {
            Write-Log "WARN $($f.Name): could not parse expiry, will refresh"
        }
    }

    if (-not $needsRefresh) { continue }

    $body = @{
        client_id     = $creds.client_id
        client_secret = $creds.client_secret
        refresh_token = $creds.refresh_token
        grant_type    = "refresh_token"
    }
    $tokenUri = if ($creds.token_uri) { $creds.token_uri } else { "https://oauth2.googleapis.com/token" }

    try {
        $resp = Invoke-RestMethod -Uri $tokenUri -Method Post -Body $body -ContentType "application/x-www-form-urlencoded" -TimeoutSec 15
    } catch {
        Write-Log "FAIL $($f.Name): refresh HTTP error - $_"
        continue
    }

    if (-not $resp.access_token -or -not $resp.expires_in) {
        Write-Log "FAIL $($f.Name): response missing access_token / expires_in"
        continue
    }

    $newExpiry = (Get-Date).ToUniversalTime().AddSeconds([int]$resp.expires_in).ToString("yyyy-MM-ddTHH:mm:ss.ffffff")
    $creds.token  = $resp.access_token
    $creds.expiry = $newExpiry
    if ($resp.refresh_token) {
        # Google rarely rotates refresh_tokens but handle it
        $creds.refresh_token = $resp.refresh_token
    }

    # Atomic write: write to .tmp (UTF-8 *without* BOM — workspace-mcp's Python
    # parser chokes on BOM and falls back to fresh OAuth), then replace
    $tmp = "$($f.FullName).tmp"
    $json = $creds | ConvertTo-Json -Depth 10
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($tmp, $json, $utf8NoBom)
    Move-Item -Path $tmp -Destination $f.FullName -Force
    Write-Log "REFRESHED $($f.Name): new expiry $newExpiry"
}

Write-Log "done"
exit 0
