# Compila el fuente canónico de la entrega; no regenera ni sobrescribe sus resultados.
$ErrorActionPreference='Stop'
& .tools/tectonic/tectonic.exe -X compile informe/latex/reporte_eva02.tex --keep-logs
if($LASTEXITCODE -ne 0){throw 'Falló la compilación PDF'}
