Set-Location -Path $PSScriptRoot
git add .
$fecha = Get-Date -Format "yyyy-MM-dd HH:mm"
git commit -m "Actualizacion Estudio Cine IA ($fecha)"
git push -u origin main
Write-Host "[OK] Codigo sincronizado con GitHub." -ForegroundColor Green
