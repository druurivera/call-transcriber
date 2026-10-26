# Windows mic recorder, single source. Needs ffmpeg on PATH.
# Run "ffmpeg -list_devices true -f dshow -i dummy" once to find your exact
# microphone name, then pass it with -Device "audio=Your Mic Name".
#
# For real two channel speaker separation like record.sh does on Mac with
# BlackHole, install VB-Audio Virtual Cable, set it as your call app's output,
# then record an Aggregate-style mix the same way: list devices, pick yours.
#
#   .\record.ps1 -Name "Arcenith" -Device "audio=Microphone Array"

param(
    [string]$Name = "call",
    [string]$Device = "audio=Microphone"
)

$date = Get-Date -Format "yyyy-MM-dd"
$outDir = Join-Path $HOME "call-recordings"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out = Join-Path $outDir "$date-$Name.wav"

Write-Host "Recording to $out. Say the consent line now. Ctrl+C to stop."
ffmpeg -f dshow -i $Device -ac 2 -ar 48000 $out
