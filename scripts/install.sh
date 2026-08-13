#!/bin/bash

set -e

INSTALL_DIR="/opt/fotobox"
SERVICE_USER="fotobox"

echo "Installing Fotobox..."

if [ "$EUID" -ne 0 ]; then
echo "Please run this script as root."
exit 1
fi

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
echo "Creating user $SERVICE_USER..."
useradd --system --home "$INSTALL_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi

echo "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

echo "Copying application..."
cp -a ./. "$INSTALL_DIR/"

echo "Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/.venv"

echo "Installing Python dependencies..."
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo "Setting permissions..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

echo "Installing systemd service..."
cp "$INSTALL_DIR/systemd/fotobox.service" 
/etc/systemd/system/fotobox.service

systemctl daemon-reload
systemctl enable fotobox.service
systemctl restart fotobox.service

echo
echo "Fotobox installation completed."
echo
echo "Status:"
systemctl --no-pager status fotobox.service

