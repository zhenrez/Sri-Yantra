@echo off
setlocal
cd /d "%~dp0"
title Sri Yantra Workbench Launcher

where powershell.exe >nul 2>nul
if errorlevel 1 (
  echo Windows PowerShell was not found.
  echo This launcher requires the PowerShell included with Windows 11.
  pause
  exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-windows.ps1"
set "SRI_EXIT=%ERRORLEVEL%"
if not "%SRI_EXIT%"=="0" pause
exit /b %SRI_EXIT%
