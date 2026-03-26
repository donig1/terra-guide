#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  Terra Guide — START AUTOMATIK PËR RASPBERRY PI
#  Ekzekuto:  chmod +x start_pi.sh && ./start_pi.sh
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

# ── Gjej user-in real (edhe nëse fillohet me sudo) ────────────
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

# ── DISPLAY dhe XAUTHORITY ────────────────────────────────────
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="$REAL_HOME/.Xauthority"
echo "[DISPLAY] DISPLAY=$DISPLAY  USER=$REAL_USER"

# ── Shto user në grupin gpio nëse mungon (njëherë) ────────────
if ! groups "$USER" | grep -q gpio; then
    echo "[GPIO] Duke shtuar $USER në grupin gpio..."
    sudo usermod -a -G gpio,dialout,spi,i2c "$USER"
    echo "[GPIO] KUJDES: Riniso Pi me:  sudo reboot"
    echo "       Pastaj ekzekuto:        ./start_pi.sh"
    exit 0
fi

# ── Kontrollo pygame ──────────────────────────────────────────
python3 -c "import pygame" 2>/dev/null || sudo apt install -y python3-pygame

# ── Kontrollo rpi-lgpio (Pi 5) ────────────────────────────────
python3 -c "import RPi.GPIO" 2>/dev/null || \
    sudo pip3 install rpi-lgpio --break-system-packages

# ── Kontrollo pyserial ────────────────────────────────────────
python3 -c "import serial" 2>/dev/null || sudo apt install -y python3-serial

echo ""
echo "[START] Duke nisur Terra Guide..."
echo ""

# ── Nis si user normal (jo sudo) ─────────────────────────────
# GPIO punon pa sudo nëse user është në grupin 'gpio'
if [ "$EUID" -eq 0 ]; then
    echo "[KUJDES] Mos ekzekuto me sudo! Rinis si user normal:"
    echo "         ./start_pi.sh"
    exit 1
fi

exec python3 pi_main.py
