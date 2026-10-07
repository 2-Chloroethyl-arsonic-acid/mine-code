@echo off
setlocal DisableDelayedExpansion
title Turtle Pet

set "PYW=C:\Users\Administrator\AppData\Local\Programs\Python\Python313\pythonw.exe"

if not exist "%PYW%" (
    for /f "delims=" %%i in ('where pythonw 2^>nul') do set "PYW=%%i"
)
if not exist "%PYW%" (
    echo [ERROR] pythonw not found!
    pause
    exit /b 1
)

start "" "%PYW%" "%~dp0»ÆÔµ¹ê×À³è.py"
