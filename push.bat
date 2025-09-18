@echo off
REM === Wrapper to run push.ps1 from .bat ===

set SCRIPT_DIR=%~dp0
set PS_SCRIPT=%SCRIPT_DIR%push.ps1

REM Pass all arguments from .bat to .ps1
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*
