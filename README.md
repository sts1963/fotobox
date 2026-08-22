# Fotobox

Lokale Fotobox-Software für einen Raspberry Pi mit USB-Webcam, iPad-Bedienoberfläche und optionalem Canon-SELPHY-Fotodrucker.

Die Anwendung läuft vollständig lokal auf dem Raspberry Pi. Das iPad dient als Bedienoberfläche; Aufnahme, Bildverarbeitung, Collage-Erstellung, Druck und Archivierung werden vom Raspberry Pi übernommen.

## Funktionsumfang

- Livebild der Webcam auf dem iPad
- Start einer Fotosession über Touch-Bedienung
- konfigurierbarer Countdown
- drei Aufnahmen pro Session
- Vorschau zwischen den Aufnahmen
- automatische 2×2-Collage
- frei wählbares Logo in der vierten Zelle
- definierter Außenrand und Abstand zwischen den Bildern
- optionaler Greenscreen-Hintergrund
- Greenscreen-Kalibrierung und Testmasken
- USB-Druck auf Canon SELPHY CP510 über CUPS/Gutenprint
- automatische Druckererkennung
- Testdruck über die Servicekonsole
- Servicekonsole für Kamera, Session, System und Drucker
- Hintergrund- und Logo-Verwaltung
- Session- und Greenscreen-Einstellungen
- Archiv aller Fotosessions
- Anzeige einzelner Collagen
- ZIP-Download aller Collagen
- Löschen einzelner Sessions
- Löschen aller alten Sessions bei Schutz der aktuellen Session
- lokale Logdatei und Diagnosefunktionen

## Systemübersicht

```text
                  ┌──────────────────────┐
                  │        iPad          │
                  │ Fotobox-Oberfläche   │
                  └──────────┬───────────┘
                             │
                       HTTP / WebSocket
                             │
                  ┌──────────▼───────────┐
                  │    Raspberry Pi 4B   │
                  │ FastAPI / Uvicorn    │
                  └──────────┬───────────┘
                             │
          ┌──────────────────┼───────────────────┐
          │                  │                   │
    ┌─────▼─────┐      ┌─────▼──────┐     ┌──────▼──────┐
    │ USB-Webcam│      │ Bild/Collage│     │ CUPS        │
    │ C920      │      │ Verarbeitung│     │ Gutenprint  │
    └───────────┘      └────────────┘     └──────┬──────┘
                                                  │ USB
                                           ┌──────▼──────┐
                                           │ SELPHY CP510│
                                           └─────────────┘
```

Die Anwendung verwendet eine zentrale Session-State-Machine. Nach einem erfolgreichen Druckauftrag wird für den nächsten Gast eine neue Session erzeugt.

# Benötigte Komponenten

## Raspberry Pi

Getestet mit:

- Raspberry Pi 4B
- 64-Bit Raspberry Pi OS / Debian 13 Trixie
- Python 3.13
- Netzwerkverbindung zwischen Raspberry Pi und iPad/Mac

## Webcam

Getestet mit:

- Logitech C920 PRO HD Webcam
- USB
- `/dev/video0`
- 1280 × 720
- 30 fps
- MJPEG

Andere V4L2-kompatible USB-Webcams können grundsätzlich funktionieren.

## Bediengerät

Getestet mit einem älteren iPad als Touch-Bedienoberfläche.

Die Fotobox-Oberfläche wurde bewusst so implementiert, dass sie auch mit älteren Safari-Versionen funktioniert. Deshalb verwendet der dafür relevante JavaScript-Code unter anderem `XMLHttpRequest` und vermeidet moderne Sprachmerkmale, die auf alten iOS-Versionen nicht verfügbar sind.

Ein Mac oder anderer moderner Browser eignet sich besonders für Administration und ZIP-Download.

## Drucker

Getestet mit:

- Canon SELPHY CP510
- USB
- CUPS
- Gutenprint
- CUPS-Druckername `fotobox`
- Verbrauchsmaterial KP-108IN
- Postcard 100 × 148 mm

## Optionales 3,5-Zoll-Display

Ein 480×320-Display am Raspberry Pi kann die lokale Servicekonsole anzeigen. Das Repository enthält dafür:

```text
scripts/console-kiosk.sh
```

## Optionaler Greenscreen

Vorhanden sind:

- Greenscreen-Verarbeitung
- konfigurierbare HSV-Grenzwerte
- Feathering
- Referenzaufnahme
- Kalibrierung
- Testmasken
- virtuelle Hintergründe

Die finale Kalibrierung hängt stark von Stoff, Farbe und Beleuchtung ab.

# Installation

## 1. Raspberry Pi OS vorbereiten

Das Projekt wurde auf Debian 13 Trixie entwickelt.

System aktualisieren:

```bash
sudo apt update
sudo apt upgrade
```

## 2. Repository klonen

```bash
mkdir -p ~/projects
cd ~/projects
git clone <URL-DES-FOTOBOX-REPOSITORIES> fotobox
cd fotobox
```

## 3. Automatische Installation

Das Installationsskript richtet ein:

- Systempakete
- Systembenutzer `fotobox`
- Gruppenberechtigungen für `video` und `lp`
- Installation unter `/opt/fotobox`
- Python-virtuelle Umgebung
- Python-Abhängigkeiten
- Datenverzeichnisse
- systemd-Service
- Autostart des Backends
- Gutenprint-Versionsprüfung

Ausführen:

```bash
sudo ./scripts/install.sh
```

Die produktive Installation liegt danach unter:

```text
/opt/fotobox
```

Der systemd-Service läuft als:

```text
User=fotobox
Group=fotobox
```

Das Installationsskript kopiert bewusst keine Entwicklungsumgebung, Python-Caches, Logs oder alten Sessions mit.

## 4. Python-Abhängigkeiten

Die getesteten direkten Abhängigkeiten sind:

```text
fastapi==0.141.1
uvicorn[standard]==0.52.1
PyYAML==6.0.3
Pillow==12.3.0
opencv-python-headless==5.0.0.93
python-multipart==0.0.32

pytest==9.1.1
pytest-asyncio==1.4.0
```

## 5. Zentrale Konfiguration

```text
config/fotobox.yaml
```

Beispiel:

```yaml
camera:
  device: /dev/video0
  width: 1280
  height: 720
  fps: 30
  jpeg_quality: 80
  retry_interval: 2.0

session:
  root: data/sessions
  countdown_seconds: 5
  photo_count: 3
  interval_seconds: 5.0

collage:
  width: 1800
  height: 1200
  margin: 60
  gap: 24
  jpeg_quality: 95
  logo: assets/logo.png

background:
  enabled: false
  mode: greenscreen
  images:
    - assets/backgrounds/background_01.jpg
    - assets/backgrounds/background_02.jpg
    - assets/backgrounds/background_03.jpg
  greenscreen:
    hue_min: 25
    hue_max: 105
    saturation_min: 35
    value_min: 5
    feather: 3

printer:
  enabled: true
  name: fotobox
```

Wichtigste Werte:

| Einstellung | Bedeutung |
|---|---|
| `camera.device` | V4L2-Gerät der Webcam |
| `countdown_seconds` | Countdown vor dem ersten Foto |
| `photo_count` | Anzahl Fotos; das aktuelle 2×2-Layout erwartet drei |
| `interval_seconds` | Abstand zwischen den Aufnahmen |
| `collage.margin` | äußerer weißer Rand |
| `collage.gap` | Abstand zwischen Collage-Feldern |
| `collage.logo` | aktives Logo |
| `background.enabled` | Greenscreen ein/aus |
| `printer.enabled` | Druckfunktion ein/aus |
| `printer.name` | CUPS-Druckername |

# Canon SELPHY CP510

## USB-Erkennung

```bash
lsusb | grep -i -E 'canon|selphy'
```

Getestetes Gerät:

```text
04a9:3128 Canon, Inc. SELPHY CP510
```

CUPS-Gerät prüfen:

```bash
lpinfo -v
```

Beispiel:

```text
gutenprint53+usb://canon-cp510/NONE_UNKNOWN
```

Treiber prüfen:

```bash
lpinfo -m | grep -i 'Canon SELPHY CP510'
```

## CUPS-Queue einrichten

Beispiel:

```bash
sudo lpadmin \
    -p fotobox \
    -E \
    -v 'gutenprint53+usb://canon-cp510/NONE_UNKNOWN' \
    -m 'gutenprint.5.3://canon-cp510/expert'
```

Als Standarddrucker:

```bash
sudo lpadmin -d fotobox
```

Status:

```bash
lpstat -t
```

Optionen:

```bash
lpoptions -p fotobox -l
```

Für KP-108IN wird `Postcard` 100 × 148 mm verwendet.

## Gutenprint 5.3.6 auf Debian Trixie

Im getesteten Aufbau verursachte Gutenprint 5.3.4 beim CP510 mit KP-108IN:

```text
Incorrect paper loaded (01 vs 11), aborting job!
```

Mit Gutenprint 5.3.6 funktionierte der Druck korrekt.

Das Installationsskript aktualisiert Gutenprint **nicht automatisch aus Debian Testing/Forky**. Es prüft lediglich die installierte Version und gibt bei einem älteren Stand eine Warnung aus.

Falls Trixie nur 5.3.4 anbietet, kann Forky gezielt und niedrig priorisiert eingebunden werden.

### Forky-Quelle anlegen

```bash
sudo nano /etc/apt/sources.list.d/forky.sources
```

Inhalt:

```text
Types: deb
URIs: http://deb.debian.org/debian
Suites: forky
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
```

### Forky herunterpriorisieren

```bash
sudo nano /etc/apt/preferences.d/forky
```

Inhalt:

```text
Package: *
Pin: release n=forky
Pin-Priority: 50
```

Dann:

```bash
sudo apt update
```

Kontrolle:

```bash
apt policy printer-driver-gutenprint
```

Der normale Candidate sollte weiterhin aus Trixie stammen.

### Installation zuerst simulieren

```bash
sudo apt-get -s install -t forky \
  printer-driver-gutenprint \
  libgutenprint9 \
  libgutenprint-common
```

Nur wenn ausschließlich diese drei Gutenprint-Pakete aktualisiert werden, installieren:

```bash
sudo apt-get install -t forky \
  printer-driver-gutenprint \
  libgutenprint9 \
  libgutenprint-common
```

Danach:

```bash
sudo systemctl restart cups
```

Kontrolle:

```bash
lpinfo -m | grep -i 'Canon SELPHY CP510'
```

Erwartet:

```text
Canon SELPHY CP510 - CUPS+Gutenprint v5.3.6
```

# systemd

Das Repository enthält:

```text
systemd/fotobox.service
```

Produktiv verwendet wird:

```ini
[Unit]
Description=Fotobox Web Application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple

WorkingDirectory=/opt/fotobox
ExecStart=/opt/fotobox/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

Restart=on-failure
RestartSec=5

User=fotobox
Group=fotobox

Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Status:

```bash
systemctl status fotobox.service
```

Neustart:

```bash
sudo systemctl restart fotobox.service
```

Logs:

```bash
journalctl -u fotobox.service -f
```

# Bedienung

## Normale Fotosession

1. Fotobox auf dem iPad öffnen.
2. Im Livebild positionieren.
3. **Start** antippen.
4. Countdown läuft.
5. Foto 1 wird aufgenommen.
6. kurze Vorschau.
7. Foto 2 und Foto 3 folgen.
8. automatische 2×2-Collage.
9. vierte Zelle enthält das Logo.
10. Collage wird angezeigt.
11. **Drucken** oder **Neu starten** wählen.

## Drucken

Während der Vorschau prüft die Oberfläche regelmäßig den SELPHY.

Bei betriebsbereitem Drucker:

```text
Drucker bereit.
```

Der Button **Drucken** ist aktiv.

Bei ausgeschaltetem oder getrenntem Drucker bleibt er deaktiviert. Wird der Drucker während der Vorschau eingeschaltet, aktualisiert sich der Status automatisch.

Nach **Drucken** erscheint:

```text
Druckauftrag wurde gestartet.
```

Das bedeutet, dass CUPS den Auftrag angenommen hat. Der physische Ausdruck kann danach noch laufen.

Die Fotobox erzeugt anschließend eine neue Session für den nächsten Gast.

# Administrationsseiten

## Servicekonsole

```text
/console
```

Zeigt:

- Kamera
- Session
- System
- Speicher
- Drucker
- Testdruck
- Log

Die Seite ist für Desktop, iPad und das kleine 480×320-Service-Display angepasst.

## Gestaltung

```text
/backgrounds
```

Verwaltet:

```text
assets/backgrounds/
assets/logos/
assets/logo.png
```

## Einstellungen

```text
/settings
```

Für Session- und Greenscreen-Parameter.

## Session-Archiv

```text
/sessions
```

Zeigt:

- Anzahl Sessions
- Anzahl Collagen
- Speicherverbrauch
- neueste Session
- einzelne Sessions

Möglichkeiten:

- Collage ansehen
- Session löschen
- alle Collagen als ZIP herunterladen
- alle alten Sessions löschen

Die aktuell aktive Session wird geschützt.

# Collagen nach der Party sichern

Unter `/sessions`:

```text
Alle Collagen als ZIP laden
```

Das ZIP enthält:

```text
collage-0001.jpg
collage-0002.jpg
collage-0003.jpg
...
```

Direkter API-Endpunkt:

```text
GET /api/admin/sessions/collages.zip
```

Empfohlener Ablauf:

1. ZIP herunterladen.
2. ZIP auf dem Mac öffnen.
3. Inhalt kontrollieren.
4. dauerhaft sichern.
5. erst danach alte Sessions löschen.

# Datenablage

```text
data/sessions/<session-id>/
├── photo_01.jpg
├── photo_02.jpg
├── photo_03.jpg
├── processed_01.jpg
├── processed_02.jpg
├── processed_03.jpg
└── collage.jpg
```

Zusätzlich:

```text
data/calibration/
data/logs/fotobox.log
data/test-print.jpg
```

# Greenscreen

Aktivierung:

```yaml
background:
  enabled: true
  mode: greenscreen
```

Parameter:

```yaml
greenscreen:
  hue_min: 25
  hue_max: 105
  saturation_min: 35
  value_min: 5
  feather: 3
```

Empfehlungen:

- gleichmäßige Beleuchtung
- wenig Schatten
- Abstand zwischen Person und Hintergrund
- möglichst keine grüne Kleidung
- ausreichend heller Greenscreen

Die finale Kalibrierung sollte mit dem tatsächlich eingesetzten Greenscreen durchgeführt werden.

# Fehlersuche

## Backend

```bash
systemctl status fotobox.service
```

```bash
journalctl \
    -u fotobox.service \
    -n 100 \
    --no-pager
```

```bash
tail -f data/logs/fotobox.log
```

## Kamera

```bash
lsusb
v4l2-ctl --list-devices
ls -l /dev/video*
```

## Drucker

```bash
lsusb | grep -i -E 'canon|selphy'
lpinfo -v
lpstat -t
lpstat -l -p fotobox
lpoptions -p fotobox -l
lpinfo -m | grep -i 'Canon SELPHY CP510'
```

Druckerstatus direkt über den Service:

```bash
source .venv/bin/activate

python - <<'PY'
from app.services.container import print_service

for key, value in print_service.get_status().items():
    print(f"{key}: {value}")
PY
```

# Party-Workflow

## Vor der Party

1. Raspberry Pi, Webcam, iPad und SELPHY anschließen.
2. Fotobox starten.
3. `/console` kontrollieren.
4. Kamera prüfen.
5. SELPHY einschalten.
6. optional Testdruck.
7. Papier und Farbband kontrollieren.
8. Logo und Hintergründe einstellen.
9. alte Collagen als ZIP sichern.
10. alte Sessions löschen.
11. vollständige Testsession durchführen.

## Während der Party

```text
Start
  ↓
Countdown
  ↓
Foto 1
  ↓
Foto 2
  ↓
Foto 3
  ↓
Collage
  ↓
Drucken / Neu starten
  ↓
nächste Session
```

## Nach der Party

1. `/sessions` auf dem Mac öffnen.
2. alle Collagen als ZIP laden.
3. ZIP prüfen.
4. dauerhaft sichern.
5. Sessions auf dem Raspberry Pi löschen.

# Projektstruktur

```text
app/
├── api/
├── core/
├── models/
└── services/

frontend/
├── index.html
├── console.html
├── backgrounds.html
├── settings.html
├── sessions.html
├── css/
└── js/

assets/
├── backgrounds/
├── logos/
└── logo.png

config/
└── fotobox.yaml

data/
├── sessions/
├── calibration/
└── logs/

scripts/
├── console-kiosk.sh
└── install.sh

systemd/
└── fotobox.service

tests/
```

# Entwicklung

Virtuelle Umgebung:

```bash
source .venv/bin/activate
```

Tests:

```bash
pytest -q
```

Aktueller validierter Stand:

```text
29 passed
```

Installationsskript prüfen:

```bash
bash -n scripts/install.sh
```

Abhängigkeiten prüfen:

```bash
python -m pip install \
    --dry-run \
    -r requirements.txt
```

Entwicklungsserver:

```bash
python -m uvicorn \
    app.main:app \
    --host 0.0.0.0 \
    --port 8000
```

Nach Backend-Änderungen:

```bash
sudo systemctl restart fotobox.service
```

Auf älteren iPads sollte nach Änderungen an JavaScript oder CSS die Cache-Version in den HTML-Dateien erhöht werden.

# Sicherheit und Datenschutz

- Die Anwendung ist für ein lokales, vertrauenswürdiges Fotobox-Netz gedacht.
- Die Admin-API besitzt derzeit keine Benutzeranmeldung.
- Die Fotobox sollte nicht ohne zusätzliche Absicherung direkt aus dem Internet erreichbar sein.
- Fotos können personenbezogene Daten darstellen.
- Nach einer Veranstaltung sollten die Daten entsprechend dem vorgesehenen Zweck gesichert oder gelöscht werden.

# Aktueller Entwicklungsstand

- Aufnahme: funktionsfähig
- mehrere Sessions hintereinander: funktionsfähig
- Collage: funktionsfähig
- SELPHY-CP510-Druck: funktionsfähig
- Druckerüberwachung: funktionsfähig
- Testdruck: funktionsfähig
- Servicekonsole: funktionsfähig
- Session-Archiv: funktionsfähig
- ZIP-Export: funktionsfähig
- Session-Bereinigung: funktionsfähig
- Greenscreen: implementiert; finale Kalibrierung mit dem endgültigen Greenscreen steht noch aus
