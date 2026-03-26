@echo off
title Terra Guide — Laptop
color 0A
cls

echo.
echo  ████████╗███████╗██████╗ ██████╗  █████╗      ██████╗ ██╗   ██╗██╗██████╗ ███████╗
echo  ╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗    ██╔════╝ ██║   ██║██║██╔══██╗██╔════╝
echo     ██║   █████╗  ██████╔╝██████╔╝███████║    ██║  ███╗██║   ██║██║██║  ██║█████╗
echo     ██║   ██╔══╝  ██╔══██╗██╔══██╗██╔══██║    ██║   ██║██║   ██║██║██║  ██║██╔══╝
echo     ██║   ███████╗██║  ██║██║  ██║██║  ██║    ╚██████╔╝╚██████╔╝██║██████╔╝███████╗
echo     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝  ╚═════╝ ╚═╝╚═════╝ ╚══════╝
echo.
echo  Robot Bujqesor Autonom — v3.0   [ LAPTOP CLIENT ]
echo  ════════════════════════════════════════════════════════════════════
echo.

:: ── Kontrollo Python ─────────────────────────────────────────────────────
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo  [GABIM] Python 3.11 nuk u gjet!
    pause
    exit /b 1
)

:: ── IP e Raspberry Pi ── NDRYSHO KETE me IP-ne reale te Pi ────────────────
::    Gjej IP-ne me komanden:  hostname -I   (ne terminal te Pi)
set PI_IP=192.168.1.100
set PI_PORT=5000
set DASH_URL=http://%PI_IP%:%PI_PORT%

echo.
echo   Pi adresa:  %DASH_URL%
echo.
echo   KUJDES: Sigurohu qe ne Raspberry Pi eshte nisur:
echo           python3 main.py
echo.

:: ── [1/3] Nis fytyren — lidhet me Pi dhe merr te dhenat live ─────────────
echo  [1/3]  Duke nisur Fytyren e Fermerit...
echo          (Fytyra merr te dhenat live nga Pi cdo 2 sekonda)
start "  Terra Guide — Fytyra  " cmd /k "cd /d "%~dp0" && py -3.11 laptop_face.py"

:: ── [2/3] Prit pak qe fytyra te nise ─────────────────────────────────────
echo  [2/3]  Duke pritur 5 sekonda...
timeout /t 5 /nobreak >nul

:: ── [3/3] Hap dashboard ne browser ───────────────────────────────────────
echo  [3/3]  Duke hapur Dashboard ne browser...
start %DASH_URL%

echo.
echo  ════════════════════════════════════════════════════════════════════
echo.
echo   [ OK ]  Laptopi eshte i lidhur me Robotin!
echo.
echo   FYTYRA    ^>  Dritarja "Terra Guide - Fytyra"  (pygame)
echo             ^>  Merr te dhena live nga Pi cdo 2s
echo   DASHBOARD ^>  %DASH_URL%  (browser)
echo             ^>  Azhurnohet live cdo 3s
echo.
echo   SI FUNKSIONON LIDHJA:
echo     Laptop laptop_face.py  ──► GET %DASH_URL%/api/live
echo     Laptop browser         ──► GET %DASH_URL%
echo     Te dyja marrin te dhenat live nga Pi
echo.
echo  [Mbyll kete dritare — Fytyra vazhdon ne dritaren tjeter]
echo.
pause
