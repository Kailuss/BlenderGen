$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$blenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
$pythonExe = 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe'
$stateFile = Join-Path (Get-Location) 'reports/ejercicio02_delivery_state.json'
$started = Get-Date
function Set-DeliveryState([string]$stage, [string]$errorMessage = '') {
    @{stage=$stage;started=$started.ToString('o');updated=(Get-Date).ToString('o');error=$errorMessage} |
        ConvertTo-Json | Set-Content -LiteralPath $stateFile -Encoding utf8
}
try {
    Set-DeliveryState 'Calculando físicas: 160 subpasos, máximo 6 h y 10 GiB'
    & $blenderExe --factory-startup -b dist/Ejercicio02_metralla_20261028/03b_impactos_retenidos.blend -t 2 --python-exit-code 1 --python tools/calculate_shrapnel_final.py *> reports/ejercicio02_delivery_calculation.log
    if ($LASTEXITCODE -ne 0) { throw 'Falló el cálculo; consultar ejercicio02_delivery_calculation.log' }
    $replay = 'dist/Ejercicio02_metralla_20261028/04_fisicas_calculadas.blend'
    if (!(Test-Path -LiteralPath $replay) -or (Get-Item -LiteralPath $replay).LastWriteTime -lt $started) { throw 'No hay reproducción nueva.' }
    Set-DeliveryState 'Auditoría de daños, dimensiones y cubierta'
    & $blenderExe --factory-startup -b $replay -t 2 --python-exit-code 1 --python tools/audit_shrapnel_house.py *> reports/ejercicio02_physics_audit.log
    if ($LASTEXITCODE -ne 0) { throw 'No pasó la auditoría física.' }
    Set-DeliveryState 'Horneando humo y renderizando imagen de control'
    & $blenderExe --factory-startup -b $replay -t 2 --python-exit-code 1 --python tools/finish_shrapnel_house.py -- --bake --proof *> reports/ejercicio02_finish.log
    if ($LASTEXITCODE -ne 0) { throw 'Falló el acabado; consultar ejercicio02_finish.log' }
    Set-DeliveryState 'Revisando anclajes y densidad óptica de la reproducción'
    & $blenderExe --factory-startup -b dist/Ejercicio02_metralla_20261028/05_render_listo.blend -t 2 --python-exit-code 1 --python tools/refine_shrapnel_finish.py *> reports/ejercicio02_finish_refined.log
    if ($LASTEXITCODE -ne 0) { throw 'Falló el ajuste final de presentación.' }
    Set-DeliveryState 'Reabriendo y verificando entrega y cachés'
    & $blenderExe --factory-startup -b dist/Ejercicio02_metralla_20261028/05_render_listo.blend -t 2 --python-exit-code 1 --python tools/verify_shrapnel_delivery.py *> reports/ejercicio02_delivery_verified.log
    if ($LASTEXITCODE -ne 0) { throw 'Falló la verificación de la entrega.' }
    & $pythonExe tools/write_shrapnel_readme.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló la generación de instrucciones.' }
    Set-DeliveryState 'Verificación técnica terminada; pendiente revisión visual y ZIP'
} catch {
    Set-DeliveryState 'ERROR' $_.Exception.Message
    Write-Error $_
    exit 1
}
