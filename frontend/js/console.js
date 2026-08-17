const overallStatus =
    document.getElementById("overall-status");

const cameraState =
    document.getElementById("camera-state");

const cameraAvailable =
    document.getElementById("camera-available");

const cameraLastFrame =
    document.getElementById("camera-last-frame");

const cameraError =
    document.getElementById("camera-error");

const sessionState =
    document.getElementById("session-state");

const sessionRunning =
    document.getElementById("session-running");

const sessionPhotos =
    document.getElementById("session-photos");

const sessionId =
    document.getElementById("session-id");

const sessionCollage =
    document.getElementById("session-collage");

const cpuTemperature =
    document.getElementById("cpu-temperature");

const systemUptime =
    document.getElementById("system-uptime");

const applicationUptime =
    document.getElementById("application-uptime");

const diskFree =
    document.getElementById("disk-free");

const diskTotal =
    document.getElementById("disk-total");

const diskUsed =
    document.getElementById("disk-used");

const diskPercent =
    document.getElementById("disk-percent");

const logOutput =
    document.getElementById("log-output");

const logCount =
    document.getElementById("log-count");


function yesNo(value) {
    return value ? "Ja" : "Nein";
}


function formatUptime(seconds) {
    if (
        seconds === null ||
        seconds === undefined
    ) {
        return "–";
    }

    let remaining =
        Math.floor(seconds);

    const days =
        Math.floor(
            remaining / 86400
        );

    remaining %= 86400;

    const hours =
        Math.floor(
            remaining / 3600
        );

    remaining %= 3600;

    const minutes =
        Math.floor(
            remaining / 60
        );

    const parts = [];

    if (days > 0) {
        parts.push(`${days} T`);
    }

    if (hours > 0 || days > 0) {
        parts.push(`${hours} Std`);
    }

    parts.push(`${minutes} Min`);

    return parts.join(" ");
}


function formatTimestamp(value) {
    if (!value) {
        return "–";
    }

    const date = new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return value;
    }

    return date.toLocaleTimeString(
        "de-DE"
    );
}


function setOverallStatus(data) {
    overallStatus.classList.remove(
        "ok",
        "error",
        "busy",
        "unknown"
    );

    if (!data.camera.available) {
        overallStatus.textContent =
            "Kamera nicht verfügbar";

        overallStatus.classList.add(
            "error"
        );

        return;
    }

    if (data.session.running) {
        overallStatus.textContent =
            "Fotosession läuft";

        overallStatus.classList.add(
            "busy"
        );

        return;
    }

    if (data.session.error) {
        overallStatus.textContent =
            "Fehler";

        overallStatus.classList.add(
            "error"
        );

        return;
    }

    overallStatus.textContent =
        "Bereit";

    overallStatus.classList.add(
        "ok"
    );
}


function updateStatus(data) {
    setOverallStatus(data);

    cameraState.textContent =
        data.camera.state;

    cameraAvailable.textContent =
        yesNo(
            data.camera.available
        );

    cameraLastFrame.textContent =
        formatTimestamp(
            data.camera.last_frame_at
        );

    cameraError.textContent =
        data.camera.last_error ?? "–";


    sessionState.textContent =
        data.session.state;

    sessionRunning.textContent =
        yesNo(
            data.session.running
        );

    sessionPhotos.textContent =
        data.session.photo_count;

    sessionId.textContent =
        data.session.id;

    sessionCollage.textContent =
        data.session.collage
            ? "vorhanden"
            : "–";


    const system =
        data.system;

    cpuTemperature.textContent =
        system.cpu_temperature_c !== null
            ? `${system.cpu_temperature_c} °C`
            : "–";

    systemUptime.textContent =
        formatUptime(
            system.system_uptime_seconds
        );

    applicationUptime.textContent =
        formatUptime(
            data.application.uptime_seconds
        );


    const disk =
        system.disk;

    diskFree.textContent =
        disk.free_gb !== null
            ? `${disk.free_gb} GB`
            : "–";

    diskTotal.textContent =
        disk.total_gb !== null
            ? `${disk.total_gb} GB`
            : "–";

    diskUsed.textContent =
        disk.used_gb !== null
            ? `${disk.used_gb} GB`
            : "–";

    diskPercent.textContent =
        disk.used_percent !== null
            ? `${disk.used_percent} %`
            : "–";
}


async function loadStatus() {
    try {
        const response = await fetch(
            "/api/admin/status",
            {
                cache: "no-store",
            }
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data =
            await response.json();

        updateStatus(data);

    } catch (error) {
        overallStatus.textContent =
            "Backend nicht erreichbar";

        overallStatus.classList.remove(
            "ok",
            "busy",
            "unknown"
        );

        overallStatus.classList.add(
            "error"
        );

        console.error(
            "Status request failed:",
            error
        );
    }
}


async function loadLogs() {
    try {
        const response = await fetch(
            "/api/admin/logs?limit=100",
            {
                cache: "no-store",
            }
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data =
            await response.json();

        logOutput.textContent =
            data.lines.join("\n");

        logCount.textContent =
            `${data.count} Einträge`;

        /*
         * Keep the newest log entries visible.
         */
        logOutput.scrollTop =
            logOutput.scrollHeight;

    } catch (error) {
        logOutput.textContent =
            "Log konnte nicht geladen werden.";

        console.error(
            "Log request failed:",
            error
        );
    }
}


function refreshConsole() {
    loadStatus();
    loadLogs();
}


/*
 * Status changes quickly enough that two seconds
 * are useful. Logs need no separate faster polling.
 */
refreshConsole();

window.setInterval(
    refreshConsole,
    2000
);

