# Cola de trabajos para Claude. Ejecuta cada .ps1 que aparezca en reports\claude_queue
# y deja su salida en reports\claude_out\<nombre>.log y el código en <nombre>.exit.
# Ciérralo con Ctrl+C o cerrando la ventana.
$ErrorActionPreference = 'Continue'
$root  = Split-Path -Parent $PSScriptRoot
$queue = Join-Path $root 'reports\claude_queue'
$out   = Join-Path $root 'reports\claude_out'
$done  = Join-Path $queue 'done'
New-Item -ItemType Directory -Force -Path $queue,$out,$done | Out-Null
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
Set-Location $root
Write-Host "Cola de Claude activa en $queue"
Set-Content -Path (Join-Path $out 'runner.alive') -Value (Get-Date -Format o)
while ($true) {
  Set-Content -Path (Join-Path $out 'runner.alive') -Value (Get-Date -Format o)
  $jobs = Get-ChildItem -Path $queue -Filter '*.ps1' -File | Sort-Object Name
  foreach ($j in $jobs) {
    $name = $j.BaseName
    $log  = Join-Path $out "$name.log"
    Write-Host "[$(Get-Date -Format HH:mm:ss)] $name"
    Set-Content -Path (Join-Path $out "$name.running") -Value (Get-Date -Format o)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & powershell -NoProfile -ExecutionPolicy Bypass -File $j.FullName *> $log
    $code = $LASTEXITCODE
    $sw.Stop()
    Add-Content -Path $log -Value "`n### exit=$code seconds=$([math]::Round($sw.Elapsed.TotalSeconds,1))"
    Move-Item -Force $j.FullName (Join-Path $done $j.Name)
    Remove-Item -Force (Join-Path $out "$name.running") -ErrorAction SilentlyContinue
    Set-Content -Path (Join-Path $out "$name.exit") -Value $code
    Write-Host "   -> exit $code ($([math]::Round($sw.Elapsed.TotalSeconds,1)) s)"
  }
  Start-Sleep -Seconds 3
}
