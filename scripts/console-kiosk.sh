#!/bin/bash

set -e

wlr-randr \
    --output SPI-1 \
    --transform 270

exec chromium \
    --kiosk \
    --no-first-run \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --ozone-platform=wayland \
    http://localhost:8000/console
