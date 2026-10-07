@echo off
cd /d "%~dp0"
net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
echo 正在还原 hosts...
GitHubProxy.exe --restore-hosts
echo 已还原，GitHub 加速已停止。
pause
