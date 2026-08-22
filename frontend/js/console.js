var overallStatus =
    document.getElementById("overall-status");

var cameraState =
    document.getElementById("camera-state");

var cameraAvailable =
    document.getElementById("camera-available");

var cameraLastFrame =
    document.getElementById("camera-last-frame");

var cameraError =
    document.getElementById("camera-error");

var sessionState =
    document.getElementById("session-state");

var sessionRunning =
    document.getElementById("session-running");

var sessionPhotos =
    document.getElementById("session-photos");

var sessionId =
    document.getElementById("session-id");

var sessionCollage =
    document.getElementById("session-collage");

var cpuTemperature =
    document.getElementById("cpu-temperature");

var systemUptime =
    document.getElementById("system-uptime");

var applicationUptime =
    document.getElementById("application-uptime");

var diskFree =
    document.getElementById("disk-free");

var diskTotal =
    document.getElementById("disk-total");

var diskUsed =
    document.getElementById("disk-used");

var diskPercent =
    document.getElementById("disk-percent");

var logOutput =
    document.getElementById("log-output");

var logCount =
    document.getElementById("log-count");

var printerStatus =
    document.getElementById("printer-status");

var printerAvailable =
    document.getElementById("printer-available");

var printerReady =
    document.getElementById("printer-ready");

var printerMessage =
    document.getElementById("printer-message");

var printerTestButton =
    document.getElementById("printer-test-button");

var printerTestStatus =
    document.getElementById("printer-test-status");

var shutdownButton =
    document.getElementById("shutdown-button");

var shutdownDialog =
    document.getElementById("shutdown-dialog");

var shutdownCancel =
    document.getElementById("shutdown-cancel");

var shutdownConfirm =
    document.getElementById("shutdown-confirm");


function requestJson(
    method,
    url,
    success,
    failure
) {
    var request =
        new XMLHttpRequest();

    request.open(
        method,
        url,
        true
    );

    request.setRequestHeader(
        "Cache-Control",
        "no-cache"
    );

    request.onreadystatechange =
        function () {
            if (request.readyState !== 4) {
                return;
            }

            var data = null;

            if (request.responseText) {
                try {
                    data = JSON.parse(
                        request.responseText
                    );
                } catch (error) {
                    if (failure) {
                        failure(
                            "Ungültige Serverantwort."
                        );
                    }

                    return;
                }
            }

            if (
                request.status >= 200
                && request.status < 300
            ) {
                if (success) {
                    success(data);
                }

                return;
            }

            if (failure) {
                var message =
                    "HTTP " + request.status;

                if (
                    data
                    && data.detail
                ) {
                    message =
                        data.detail;
                }

                failure(message);
            }
        };

    request.onerror =
        function () {
            if (failure) {
                failure(
                    "Netzwerkfehler."
                );
            }
        };

    request.send();
}


function yesNo(value) {
    return value
        ? "Ja"
        : "Nein";
}


function formatUptime(seconds) {
    if (
        seconds === null
        || seconds === undefined
    ) {
        return "–";
    }

    var remaining =
        Math.floor(seconds);

    var days =
        Math.floor(
            remaining / 86400
        );

    remaining =
        remaining % 86400;

    var hours =
        Math.floor(
            remaining / 3600
        );

    remaining =
        remaining % 3600;

    var minutes =
        Math.floor(
            remaining / 60
        );

    var parts = [];

    if (days > 0) {
        parts.push(
            days + " T"
        );
    }

    if (
        hours > 0
        || days > 0
    ) {
        parts.push(
            hours + " Std"
        );
    }

    parts.push(
        minutes + " Min"
    );

    return parts.join(" ");
}


function formatTimestamp(value) {
    if (!value) {
        return "–";
    }

    var date =
        new Date(value);

    if (isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleTimeString();
}


function setOverallStatus(data) {
    overallStatus.className =
        "status-badge";

    if (!data.camera.available) {
        overallStatus.textContent =
            "Kamera nicht verfügbar";

        overallStatus.className +=
            " error";

        return;
    }

    if (data.session.running) {
        overallStatus.textContent =
            "Fotosession läuft";

        overallStatus.className +=
            " busy";

        return;
    }

    if (data.session.error) {
        overallStatus.textContent =
            "Fehler";

        overallStatus.className +=
            " error";

        return;
    }

    overallStatus.textContent =
        "Bereit";

    overallStatus.className +=
        " ok";
}


function updateStatus(data) {
    setOverallStatus(data);

    cameraState.textContent =
        data.camera.state;

    cameraAvailable.textContent =
        yesNo(data.camera.available);

    cameraLastFrame.textContent =
        formatTimestamp(
            data.camera.last_frame_at
        );

    cameraError.textContent =
        data.camera.last_error
        ? data.camera.last_error
        : "–";


    sessionState.textContent =
        data.session.state;

    sessionRunning.textContent =
        yesNo(data.session.running);

    sessionPhotos.textContent =
        data.session.photo_count;

    sessionId.textContent =
        data.session.id;

    sessionCollage.textContent =
        data.session.collage
        ? "vorhanden"
        : "–";


    var system =
        data.system;

    cpuTemperature.textContent =
        system.cpu_temperature_c !== null
        ? system.cpu_temperature_c + " °C"
        : "–";

    systemUptime.textContent =
        formatUptime(
            system.system_uptime_seconds
        );

    applicationUptime.textContent =
        formatUptime(
            data.application.uptime_seconds
        );


    var disk =
        system.disk;

    diskFree.textContent =
        disk.free_gb !== null
        ? disk.free_gb + " GB"
        : "–";

    diskTotal.textContent =
        disk.total_gb !== null
        ? disk.total_gb + " GB"
        : "–";

    diskUsed.textContent =
        disk.used_gb !== null
        ? disk.used_gb + " GB"
        : "–";

    diskPercent.textContent =
        disk.used_percent !== null
        ? disk.used_percent + " %"
        : "–";
}


function updatePrinterStatus(data) {
    printerAvailable.textContent =
        yesNo(data.available);

    printerReady.textContent =
        yesNo(data.ready);

    printerMessage.textContent =
        data.message
        ? data.message
        : "–";

    printerTestButton.disabled =
        !(
            data.enabled
            && data.available
            && data.ready
        );

    if (!data.enabled) {
        printerStatus.textContent =
            "Deaktiviert";
        return;
    }

    if (!data.available) {
        printerStatus.textContent =
            "Nicht verbunden";
        return;
    }

    if (!data.ready) {
        printerStatus.textContent =
            "Nicht bereit";
        return;
    }

    printerStatus.textContent =
        "Bereit";
}


function loadStatus() {
    requestJson(
        "GET",
        "/api/admin/status?v="
            + Date.now(),

        function (data) {
            updateStatus(data);
        },

        function () {
            overallStatus.textContent =
                "Backend nicht erreichbar";

            overallStatus.className =
                "status-badge error";
        }
    );
}


function loadPrinterStatus() {
    requestJson(
        "GET",
        "/api/admin/printer/status?v="
            + Date.now(),

        function (data) {
            updatePrinterStatus(data);
        },

        function () {
            printerStatus.textContent =
                "Status nicht verfügbar";

            printerAvailable.textContent =
                "–";

            printerReady.textContent =
                "–";

            printerTestButton.disabled =
                true;
        }
    );
}


function loadLogs() {
    requestJson(
        "GET",
        "/api/admin/logs?limit=40&v="
            + Date.now(),

        function (data) {
            logOutput.textContent =
                data.lines.join("\n");

            logCount.textContent =
                data.count
                + " Einträge";

            logOutput.scrollTop =
                logOutput.scrollHeight;
        },

        function () {
            logOutput.textContent =
                "Log konnte nicht geladen werden.";
        }
    );
}


function runPrinterTest() {
    printerTestButton.disabled =
        true;

    printerTestStatus.textContent =
        "Testdruck wird gestartet …";

    requestJson(
        "POST",
        "/api/admin/printer/test",

        function () {
            printerTestStatus.textContent =
                "Testdruck wurde an den "
                + "Drucker gesendet.";

            loadPrinterStatus();
        },

        function (error) {
            printerTestStatus.textContent =
                "Fehler: " + error;

            loadPrinterStatus();
        }
    );
}


printerTestButton.onclick =
    function () {
        runPrinterTest();
    };


function refreshConsole() {
    loadStatus();
    loadPrinterStatus();
    loadLogs();
}


refreshConsole();

window.setInterval(
    refreshConsole,
    2000
);
