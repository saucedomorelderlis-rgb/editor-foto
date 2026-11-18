Set-Location -Path $PSScriptRoot
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " INICIANDO ESTUDIO CINE IA (MCP + AGENTE VOZ + TELEGRAM)" -ForegroundColor Cyan
Write-Host " URL Local: http://localhost:18789" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Start-Process "http://localhost:18789"
.\python_embed\python.exe src\app_web.py
