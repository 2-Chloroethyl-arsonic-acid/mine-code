@echo off
cd /d "%~dp0"
net session >nul 2>&1
if errorlevel 1 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
echo [1/2] 写入 hosts（把 GitHub 域名指向本地代理）...
GitHubProxy.exe --install-hosts
echo.
echo [2/2] 启动加速代理，请勿关闭本窗口（关闭即停止加速）
echo      停止加速请运行「停止并还原.bat」
echo.
GitHubProxy.exe
pause
