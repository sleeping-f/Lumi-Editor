@echo off
title Lumi Editor — Desktop Shortcut Generator
echo Creating Lumi Editor Desktop Shortcut...

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$shortcutPath = Join-Path $desktop 'Lumi Editor.lnk'; " ^
  "$targetExe = Join-Path '%~dp0' 'dist\LumiEditor.exe'; " ^
  "if (-not (Test-Path $targetExe)) { $targetExe = Join-Path '%~dp0' 'main.py' }; " ^
  "$s = $ws.CreateShortcut($shortcutPath); " ^
  "$s.TargetPath = $targetExe; " ^
  "$s.WorkingDirectory = '%~dp0'; " ^
  "$iconPath = Join-Path '%~dp0' 'assets\logo.ico'; " ^
  "if (Test-Path $iconPath) { $s.IconLocation = $iconPath }; " ^
  "$s.Description = 'Lumi Editor - Batch Edit. Simplified.'; " ^
  "$s.Save(); " ^
  "Write-Host 'Shortcut created successfully on Desktop!'"

echo.
pause
