#!/bin/bash

set -euo pipefail

INSTALL_DIR="/opt/fotobox"
SERVICE_USER="fotobox"
SERVICE_FILE="/etc/systemd/system/fotobox.service"

echo "=== Fotobox Installation ==="

if [ "$EUID" -ne 0 ]; then
    echo "Bitte dieses Skript mit sudo ausführen."
    exit 1
fi

echo
echo "Installiere Systempakete..."

apt-get update

apt-get install -y \
    git \
    python3 \
    python3-venv \
    python3-pip \
    cups \
    cups-client \
    cups-filters \
    printer-driver-gutenprint \
    v4l-utils \
    usbutils \
    unzip

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    echo
    echo "Erzeuge Systembenutzer $SERVICE_USER..."

    useradd \
        --system \
        --home "$INSTALL_DIR" \
        --shell /usr/sbin/nologin \
        "$SERVICE_USER"
fi

echo
echo "Ergänze Geräteberechtigungen..."

usermod -aG video,lp "$SERVICE_USER"

echo
echo "Erzeuge Installationsverzeichnis..."

mkdir -p "$INSTALL_DIR"

echo
echo "Kopiere Anwendung nach $INSTALL_DIR..."

tar \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='.pytest_cache' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='data/sessions' \
    --exclude='data/logs/*.log' \
    -cf - . \
    | tar -xf - -C "$INSTALL_DIR"

mkdir -p \
    "$INSTALL_DIR/data/sessions" \
    "$INSTALL_DIR/data/logs" \
    "$INSTALL_DIR/data/calibration"

echo
echo "Erzeuge Python-Umgebung..."

rm -rf "$INSTALL_DIR/.venv"

python3 -m venv \
    "$INSTALL_DIR/.venv"

"$INSTALL_DIR/.venv/bin/python" \
    -m pip install --upgrade pip

"$INSTALL_DIR/.venv/bin/python" \
    -m pip install \
    -r "$INSTALL_DIR/requirements.txt"

echo
echo "Setze Berechtigungen..."

chown -R \
    "$SERVICE_USER:$SERVICE_USER" \
    "$INSTALL_DIR"

echo
echo "Installiere systemd-Service..."

cp \
    "$INSTALL_DIR/systemd/fotobox.service" \
    "$SERVICE_FILE"

systemctl daemon-reload
systemctl enable fotobox.service
systemctl restart fotobox.service

echo
echo "Prüfe Gutenprint-Version..."

GUTENPRINT_VERSION="$(
    dpkg-query \
        -W \
        -f='${Version}' \
        printer-driver-gutenprint \
        2>/dev/null \
        || true
)"

echo "Gutenprint-Version: ${GUTENPRINT_VERSION:-nicht installiert}"

case "$GUTENPRINT_VERSION" in
    5.3.6*|5.3.7*|5.3.8*|5.4.*|6.*)
        echo "Gutenprint-Version ist für den getesteten CP510 ausreichend."
        ;;
    *)
        echo
        echo "WARNUNG:"
        echo "Für den Canon SELPHY CP510 wurde Gutenprint 5.3.6 getestet."
        echo "Mit Gutenprint 5.3.4 kann beim KP-108IN der Fehler"
        echo "'Incorrect paper loaded (01 vs 11), aborting job!' auftreten."
        echo
        echo "Siehe README: Canon SELPHY CP510 / Gutenprint 5.3.6."
        ;;
esac

echo
echo "Fotobox Installation abgeschlossen."
echo
echo "Service-Status:"

systemctl \
    --no-pager \
    --full \
    status fotobox.service
