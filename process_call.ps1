# Windows equivalent of process_call.sh.
# One shot: transcribe a call recording, run the analysis pass, open the finished note.
#
#   .\process_call.ps1 -Audio "C:\Users\you\Downloads\call.m4a" -Prospect "Arcenith"

param(
    [Parameter(Mandatory = $true)][string]$Audio,
    [string]$Prospect = "Unknown"
)

Set-Location -Path $PSScriptRoot

Write-Host "Transcribing: $Audio"
Write-Host "Prospect: $Prospect"
Write-Host ""

$py = ".\.venv\Scripts\python.exe"
$transcribeOut = & $py "transcribe.py" $Audio "--prospect" $Prospect
$transcribeOut | ForEach-Object { Write-Host $_ }

$savedLine = $transcribeOut | Where-Object { $_ -like "Saved: *" } | Select-Object -Last 1
if (-not $savedLine) {
    Write-Host "Could not find the saved note path in transcribe.py output. Stopping before analysis."
    exit 1
}
$notePath = $savedLine -replace "^Saved: ", ""

$key = $null
if (Test-Path ".env") {
    $envLine = Get-Content ".env" | Where-Object { $_ -match "^OPENROUTER_API_KEY=" } | Select-Object -First 1
    if ($envLine) { $key = ($envLine -replace "^OPENROUTER_API_KEY=", "").Trim() }
}

if ($key) {
    Write-Host ""
    Write-Host "Running analysis pass..."
    & $py "analyze.py" $notePath
} else {
    Write-Host ""
    Write-Host "OPENROUTER_API_KEY is empty in .env, skipping the analysis pass."
    Write-Host "You are getting the raw transcript only."
}

Invoke-Item $notePath
