const connectionStatus =
    document.getElementById("connection-status");

const startButton =
    document.getElementById("start-button");

const startScreen =
    document.getElementById("start-screen");

const countdownScreen =
    document.getElementById("countdown-screen");

const countdownElement =
    document.getElementById("countdown");

const captureScreen =
    document.getElementById("capture-screen");

const processingScreen =
    document.getElementById("processing-screen");

const previewScreen =
    document.getElementById("preview-screen");

const collagePreview =
    document.getElementById("collage-preview");

const captureStatus =
    document.getElementById("capture-status");

const captureTitle =
    document.getElementById(
        "capture-title"
    );

const capturePhotoContainer =
    document.getElementById(
        "capture-photo-container"
    );

const capturePhotoPreview =
    document.getElementById(
        "capture-photo-preview"
    );

const nextPhotoCountdown =
    document.getElementById(
        "next-photo-countdown"
    );

const errorScreen =
    document.getElementById("error-screen");

const errorMessage =
    document.getElementById("error-message");

const restartButton =
    document.getElementById("restart-button");

const previewRestartButton =
    document.getElementById("preview-restart-button");

const printButton =
    document.getElementById("print-button");

const cameraStream =
    document.getElementById("camera-stream");

cameraStream.addEventListener(
    "error",
    () => {
        console.log(
            "Camera stream interrupted."
        );
    }
);

let socket = null;
let cameraAvailable = null;
let cameraStatusTimer = null;
let serverConnected = false;
let currentState = null;

function restartCameraStream() {
    const cameraStream =
        document.getElementById("camera-stream");

    if (!cameraStream) {
        return;
    }

    /*
     * The timestamp forces Safari to create a new
     * HTTP connection instead of reusing the old
     * interrupted MJPEG request.
     */
    cameraStream.src =
        `/api/camera/stream?v=${Date.now()}`;
}


async function checkCameraStatus() {
    try {
        const response = await fetch(
            "/api/camera/status",
            {
                cache: "no-store",
            }
        );

        if (!response.ok) {
            return;
        }

        const status = await response.json();

        const wasAvailable =
            cameraAvailable;

        cameraAvailable =
            status.available === true;
        updateReadyState();
       
        /*
         * Camera has recovered:
         *
         * false -> true
         *
         * Reconnect the MJPEG stream.
         */
        if (
            wasAvailable === false &&
            cameraAvailable === true
        ) {
            console.log(
                "Camera recovered. Restarting stream."
            );

            restartCameraStream();
        }

    } catch (error) {
         cameraAvailable = false;
         updateReadyState(); 
        
         console.error(
            "Unable to read camera status:",
            error
        );
    }
}


function startCameraStatusMonitor() {
    if (cameraStatusTimer !== null) {
        return;
    }

    checkCameraStatus();

    cameraStatusTimer = window.setInterval(
        checkCameraStatus,
        2000
    );
}

function setConnected(connected) {
    serverConnected = connected;
    updateReadyState();
}

function updateReadyState() {
    if (!serverConnected) {
        connectionStatus.textContent =
            "Verbindung getrennt";

        startButton.disabled = true;
        return;
    }

    if (cameraAvailable !== true) {
        connectionStatus.textContent =
            "Kamera nicht verfügbar";

        startButton.disabled = true;
        return;
    }

    connectionStatus.textContent = "Bereit";
    startButton.disabled =
        currentState !== "start";
}

function hideSessionScreens() {
    startScreen.classList.add("hidden");
    countdownScreen.classList.add("hidden");
    captureScreen.classList.add("hidden");
    processingScreen.classList.add("hidden");
    previewScreen.classList.add("hidden");
    errorScreen.classList.add("hidden");
}


function sendCommand(type) {
    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {
        return;
    }

    socket.send(
        JSON.stringify({
            type: type,
        })
    );
}


function updateState(message) {
    const state = message.state;
    currentState = state;
    console.log(
        "Fotobox state:",
        state
    );

    hideSessionScreens();

    switch (state) {

        case "start":
            startScreen.classList.remove(
                "hidden"
            );

           updateReadyState(); 
           break;


        case "countdown":
            countdownScreen.classList.remove(
                "hidden"
            );

            startButton.disabled = true;

            if (message.countdown !== null) {
                countdownElement.textContent =
                    message.countdown;
            }

            break;


case "capturing": {
    captureScreen.classList.remove(
        "hidden"
    );

    startButton.disabled = true;

    const captured =
        Array.isArray(message.photos)
            ? message.photos.length
            : 0;

    const nextPhoto =
        Math.min(
            captured + 1,
            3
        );

    capturePhotoContainer.classList.add(
        "hidden"
    );

    nextPhotoCountdown.classList.add(
        "hidden"
    );

    if (
        message.capture_phase === "preview"
        && message.preview_photo !== null
    ) {
        captureTitle.textContent =
            `Foto ${message.preview_photo} aufgenommen`;

        captureStatus.textContent =
            "So sieht es aus:";

        const sessionId =
            encodeURIComponent(
                message.session_id
            );

        capturePhotoPreview.src =
            `/api/session/${sessionId}/photo/`
            + `${message.preview_photo}`
            + `?v=${Date.now()}`;

        capturePhotoContainer.classList.remove(
            "hidden"
        );

    } else if (
        message.capture_phase === "waiting"
    ) {
        captureTitle.textContent =
            "Bereit machen";

        captureStatus.textContent =
            `Foto ${nextPhoto} von 3`;

        nextPhotoCountdown.textContent =
            message.next_photo_in;

        nextPhotoCountdown.classList.remove(
            "hidden"
        );

    } else {
        captureTitle.textContent =
            "Aufnahme läuft";

        captureStatus.textContent =
            `Foto ${nextPhoto} von 3`;
    }

    break;
}


        case "processing":
            processingScreen.classList.remove(
                "hidden"
            );

            startButton.disabled = true;
            break;


        case "preview": {
            previewScreen.classList.remove(
                "hidden"
            );

            startButton.disabled = true;

            const sessionId =
                encodeURIComponent(
                    message.session_id
                );

            /*
             * The session ID already makes the URL unique.
             * The timestamp additionally prevents Safari from
             * showing an old cached preview during development.
             */
            collagePreview.src =
                `/api/session/${sessionId}/collage`
                + `?v=${Date.now()}`;

            break;
        }


        case "printing":
            startButton.disabled = true;
            break;


        case "error":
            errorScreen.classList.remove(
                "hidden"
            );

            startButton.disabled = true;

            errorMessage.textContent =
                message.error
                ?? "Unbekannter Fehler";

            break;
    }
}


function connectWebSocket() {
    const protocol =
        window.location.protocol === "https:"
            ? "wss:"
            : "ws:";

    const url =
        `${protocol}//${window.location.host}/ws`;

    socket = new WebSocket(url);


    socket.addEventListener(
        "open",
        () => {
            setConnected(true);
        }
    );


    socket.addEventListener(
        "message",
        (event) => {
            const message =
                JSON.parse(event.data);

            switch (message.type) {

                case "state":
                    updateState(message);
                    break;

                case "error":
                    console.error(
                        message.message
                    );
                    break;
            }
        }
    );


    socket.addEventListener(
        "close",
        () => {
            setConnected(false);

            startButton.disabled = true;

            window.setTimeout(
                connectWebSocket,
                2000
            );
        }
    );


    socket.addEventListener(
        "error",
        () => {
            setConnected(false);
        }
    );
}


startButton.addEventListener(
    "click",
    () => {
        sendCommand(
            "start_session"
        );
    }
);


restartButton.addEventListener(
    "click",
    () => {
        sendCommand(
            "restart"
        );
    }
);


previewRestartButton.addEventListener(
    "click",
    () => {
        sendCommand(
            "restart"
        );
    }
);


/*
 * Printing is intentionally not implemented yet.
 * The button remains disabled until the CUPS/SELPHY
 * integration is available.
 */
printButton.disabled = true;


connectWebSocket();
startCameraStatusMonitor();
