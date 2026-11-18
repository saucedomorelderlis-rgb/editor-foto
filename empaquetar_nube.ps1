Set-Location -Path $PSScriptRoot
if (Test-Path "estudio_nube.zip") { Remove-Item "estudio_nube.zip" -Force }
$elementos = @("src", "proyectos", "bin_cpp", "requirements.txt") | Where-Object { Test-Path $_ }
Compress-Archive -Path $elementos -DestinationPath "estudio_nube.zip" -Force
Write-Host "[OK] Paquete ligero 'estudio_nube.zip' generado correctamente." -ForegroundColor Green
Write-Host "Subelo a tu carpeta 'MyDrive/editor_foto' en Google Drive junto a tus .safetensors." -ForegroundColor Yellow
