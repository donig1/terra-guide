#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  Terra Guide — START AUTOMATIK PËR RASPBERRY PI
#  Ekzekuto:  chmod +x start_pi.sh && ./start_pi.sh
#  Ose vendos në autostart:  @reboot cd ~/Desktop/Terra\ Guide && ./start_pi.sh
# ══════════════════════════════════════════════════════════════

cd "$(dirname "$0")"

echo ""
echo "  ████████╗███████╗██████╗ ██████╗  █████╗     ██████╗ ██╗"
echo "     ██║   ██╔════╝██╔══██╗██╔══██╗██╔══██╗   ██╔════╝ ██║"
echo "     ██║   █████╗  ██████╔╝██████╔╝███████║   ██║  ███╗██║"
echo "     ██║   ██╔══╝  ██╔══██╗██╔══██╗██╔══██║   ██║   ██║██║"
echo "     ██║   ███████╗██║  ██║██║  ██║██║  ██║   ╚██████╔╝██║"
echo "     ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝ ╚═╝"
echo ""
echo "  Robot Bujqesor Autonom — Raspberry Pi"
echo "  ══════════════════════════════════════"
echo ""

# ── Kontrollo DISPLAY ─────────────────────────────────────────
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
    echo "[DISPLAY] DISPLAY vendosur: :0"
fi

# ── Kontrollo nëse pygame është instaluar ─────────────────────
python3 -c "import pygame" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INSTALIM] Duke instaluar pygame..."
    sudo apt install -y python3-pygame
fi

# ── Kontrollo nëse rpi-lgpio është instaluar (Pi 5) ───────────
python3 -c "import RPi.GPIO" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INSTALIM] Duke instaluar rpi-lgpio për Pi 5..."
    sudo pip3 install rpi-lgpio --break-system-packages
fi

# ── Instalo serial nëse mungon ────────────────────────────────
python3 -c "import serial" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INSTALIM] Duke instaluar pyserial..."
    sudo apt install -y python3-serial
fi

echo ""
echo "[START] Duke nisur Terra Guide..."
echo ""

# ── Nis gjithçka ──────────────────────────────────────────────
sudo -E DISPLAY=$DISPLAY python3 pi_main.py
