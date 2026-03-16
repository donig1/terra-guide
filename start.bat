@echo off
title Terra Guide  –  Robot Bujqesor
echo ╔══════════════════════════════════╗
echo ║    Terra Guide  –  Duke u nisur  ║
echo ╚══════════════════════════════════╝
echo.

:: Nis backend ne dritare te re
start "Terra Guide Backend" cmd /k "cd /d "%~dp0" && py -3.11 main.py"

:: Prit 5 sekonda qe Flask te startoje
timeout /t 5 /nobreak >nul

:: Nis fytyren e fermerit
echo [FACE] Duke hapur fytyren e fermerit...
py -3.11 face_engine.py

pause
