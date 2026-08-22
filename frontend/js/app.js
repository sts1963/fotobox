var connectionStatus =
    document.getElementById(
        "connection-status"
    );

var startButton =
    document.getElementById(
        "start-button"
    );

var startScreen =
    document.getElementById(
        "start-screen"
    );

var countdownScreen =
    document.getElementById(
        "countdown-screen"
    );

var countdownElement =
    document.getElementById(
        "countdown"
    );

var captureScreen =
    document.getElementById(
        "capture-screen"
    );

var processingScreen =
    document.getElementById(
        "processing-screen"
    );

var previewScreen =
    document.getElementById(
        "preview-screen"
    );

var collagePreview =
    document.getElementById(
        "collage-preview"
    );

var captureStatus =
    document.getElementById(
        "capture-status"
    );

var captureTitle =
    document.getElementById(
        "capture-title"
    );

var capturePhotoContainer =
    document.getElementById(
        "capture-photo-container"
    );

var capturePhotoPreview =
    document.getElementById(
        "capture-photo-preview"
    );

var nextPhotoCountdown =
    document.getElementById(
        "next-photo-countdown"
    );

var errorScreen =
    document.getElementById(
        "error-screen"
    );

var errorMessage =
    document.getElementById(
        "error-message"
    );

var restartButton =
    document.getElementById(
        "restart-button"
    );

var previewRestartButton =
    document.getElementById(
        "preview-restart-button"
    );

var printButton =
    document.getElementById(
        "print-button"
    );

var cameraStream =
    document.getElementById(
        "camera-stream"
    );

var adminButton =
    document.getElementById(
        "admin-button"
    );

var adminHoldTimer = null;
var adminHoldTriggered = false;
var socket = null;
var cameraAvailable = null;
var cameraStatusTimer = null;
var serverConnected = false;
var currentState = null;


cameraStream.addEventListener(
    "error",
    function () {
        console.log(
            "Camera stream interrupted."
        );
    }
);


function restartCameraStream() {
    var stream =
        document.getElementById(
            "camera-stream"
        );

    if (!stream) {
        return;
    }

    stream.src =
        "/api/camera/stream?v="
        + Date.now();
}


function requestJson(
    method,
    url,
    data,
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

    if (data !== null) {
        request.setRequestHeader(
            "Content-Type",
            "application/json"
        );
    }

    request.onreadystatechange =
        function () {
            if (
                request.readyState !== 4
            ) {
                return;
            }

            if (
                request.status >= 200
                && request.status < 300
            ) {
                var result = null;

                try {
                    result =
                        JSON.parse(
                            request.responseText
                        );
                } catch (error) {
                    if (failure) {
                        failure(
                            "Invalid JSON response"
                        );
                    }

                    return;
                }

                if (success) {
                    success(
                        result
                    );
                }

                return;
            }

            if (failure) {
                failure(
                    "HTTP "
                    + request.status
                );
            }
        };

    request.onerror =
        function () {
            if (failure) {
                failure(
                    "Network error"
                );
            }
        };

    if (data !== null) {
        request.send(
            JSON.stringify(
                data
            )
        );
    } else {
        request.send();
    }
}


function checkCameraStatus() {
    requestJson(
        "GET",
        "/api/camera/status?v="
            + Date.now(),
        null,

        function (status) {
            var wasAvailable =
                cameraAvailable;

            cameraAvailable =
                status.available === true;

            updateReadyState();

            if (
                wasAvailable === false
                && cameraAvailable === true
            ) {
                console.log(
                    "Camera recovered. "
                    + "Restarting stream."
                );

                restartCameraStream();
            }
        },

        function (error) {
            cameraAvailable = false;

            updateReadyState();

            console.log(
                "Unable to read camera status: "
                + error
            );
        }
    );
}


function startCameraStatusMonitor() {
    if (
        cameraStatusTimer !== null
    ) {
        return;
    }

    checkCameraStatus();

    cameraStatusTimer =
        window.setInterval(
            checkCameraStatus,
            2000
        );
}


function setConnected(
    connected
) {
    serverConnected =
        connected;

    updateReadyState();
}


function updateReadyState() {
    if (!serverConnected) {
        connectionStatus.textContent =
            "Verbindung getrennt";

        startButton.disabled =
            true;

        return;
    }

    if (
        cameraAvailable !== true
    ) {
        connectionStatus.textContent =
            "Kamera nicht verfügbar";

        startButton.disabled =
            true;

        return;
    }

    connectionStatus.textContent =
        "Bereit";

    startButton.disabled =
        currentState !== "start";
}


function hideSessionScreens() {
    startScreen.classList.add(
        "hidden"
    );

    countdownScreen.classList.add(
        "hidden"
    );

    captureScreen.classList.add(
        "hidden"
    );

    processingScreen.classList.add(
        "hidden"
    );

    previewScreen.classList.add(
        "hidden"
    );

    errorScreen.classList.add(
        "hidden"
    );
}


function sendCommand(
    type
) {
    if (
        !socket
        || socket.readyState
            !== WebSocket.OPEN
    ) {
        return;
    }

    socket.send(
        JSON.stringify({
            type: type
        })
    );
}


function updateState(
    message
) {
    var state =
        message.state;

    currentState =
        state;

    console.log(
        "Fotobox state: "
        + state
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

            startButton.disabled =
                true;

            if (
                message.countdown
                !== null
                && message.countdown
                !== undefined
            ) {
                countdownElement.textContent =
                    message.countdown;
            }

            break;


        case "capturing":
            captureScreen.classList.remove(
                "hidden"
            );

            startButton.disabled =
                true;

            var captured = 0;

            if (
                Array.isArray(
                    message.photos
                )
            ) {
                captured =
                    message.photos.length;
            }

            var nextPhoto =
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
                message.capture_phase
                    === "preview"
                && message.preview_photo
                    !== null
                && message.preview_photo
                    !== undefined
            ) {
                captureTitle.textContent =
                    "Foto "
                    + message.preview_photo
                    + " aufgenommen";

                captureStatus.textContent =
                    "So sieht es aus:";

                var previewSessionId =
                    encodeURIComponent(
                        message.session_id
                    );

                capturePhotoPreview.src =
                    "/api/session/"
                    + previewSessionId
                    + "/photo/"
                    + message.preview_photo
                    + "?v="
                    + Date.now();

                capturePhotoContainer.classList.remove(
                    "hidden"
                );

            } else if (
                message.capture_phase
                    === "waiting"
            ) {
                captureTitle.textContent =
                    "Bereit machen";

                captureStatus.textContent =
                    "Foto "
                    + nextPhoto
                    + " von 3";

                nextPhotoCountdown.textContent =
                    message.next_photo_in;

                nextPhotoCountdown.classList.remove(
                    "hidden"
                );

            } else {
                captureTitle.textContent =
                    "Aufnahme läuft";

                captureStatus.textContent =
                    "Foto "
                    + nextPhoto
                    + " von 3";
            }

            break;


        case "processing":
            processingScreen.classList.remove(
                "hidden"
            );

            startButton.disabled =
                true;
            processingScreen.querySelector(
                "h2"
            ).textContent =
                "Fotos aufgenommen";

            processingScreen.querySelector(
                "p"
            ).textContent =
                "Die Collage wird erstellt …";

            break;


        case "preview":
            previewScreen.classList.remove(
                "hidden"
            );

            startButton.disabled =
                true;

            printButton.disabled =
                false;

            var collageSessionId =
                encodeURIComponent(
                    message.session_id
                );

            collagePreview.src =
                "/api/session/"
                + collageSessionId
                + "/collage?v="
                + Date.now();

            break;


        case "printing":
            processingScreen.classList.remove(
                "hidden"
            );

            startButton.disabled =
                true;

            printButton.disabled =
                true;

            processingScreen.querySelector(
                "h2"
            ).textContent =
                "Foto wird gedruckt";

            processingScreen.querySelector(
                "p"
            ).textContent =
                "Bitte einen Moment warten …";

            break;

        case "error":
            errorScreen.classList.remove(
                "hidden"
            );

            startButton.disabled =
                true;

            if (
                message.error !== null
                && message.error
                    !== undefined
            ) {
                errorMessage.textContent =
                    message.error;
            } else {
                errorMessage.textContent =
                    "Unbekannter Fehler";
            }

            break;
    }
}


function connectWebSocket() {
    var protocol =
        window.location.protocol
            === "https:"
        ? "wss:"
        : "ws:";

    var url =
        protocol
        + "//"
        + window.location.host
        + "/ws";

    try {
        socket =
            new WebSocket(
                url
            );

    } catch (error) {
        setConnected(
            false
        );

        window.setTimeout(
            connectWebSocket,
            2000
        );

        return;
    }

    socket.onopen =
        function () {
            setConnected(
                true
            );
        };


    socket.onmessage =
        function (event) {
            var message;

            try {
                message =
                    JSON.parse(
                        event.data
                    );
            } catch (error) {
                console.log(
                    "Invalid WebSocket message."
                );

                return;
            }

            switch (
                message.type
            ) {

                case "state":
                    updateState(
                        message
                    );

                    break;

                case "error":
                    console.log(
                        message.message
                    );

                    break;
            }
        };


    socket.onclose =
        function () {
            setConnected(
                false
            );

            startButton.disabled =
                true;

            window.setTimeout(
                connectWebSocket,
                2000
            );
        };


    socket.onerror =
        function () {
            setConnected(
                false
            );
        };
}


startButton.addEventListener(
    "click",
    function () {
        sendCommand(
            "start_session"
        );
    }
);


restartButton.addEventListener(
    "click",
    function () {
        sendCommand(
            "restart"
        );
    }
);


previewRestartButton.addEventListener(
    "click",
    function () {
        sendCommand(
            "restart"
        );
    }
);

printButton.addEventListener(
    "click",
    function () {
        printButton.disabled =
            true;

        sendCommand(
            "print"
        );
    }
);

function startAdminHold(
    event
) {
    if (event) {
        event.preventDefault();
    }

    adminHoldTriggered =
        false;

    adminButton.className =
        "admin-holding";

    adminHoldTimer =
        window.setTimeout(
            function () {
                adminHoldTriggered =
                    true;

                window.location.href =
                    "/backgrounds";
            },
            2000
        );
}


function cancelAdminHold(
    event
) {
    if (event) {
        event.preventDefault();
    }

    if (
        adminHoldTimer !== null
    ) {
        window.clearTimeout(
            adminHoldTimer
        );

        adminHoldTimer =
            null;
    }

    adminButton.className =
        "";
}


/*
 * Touch events for the iPad.
 */
adminButton.addEventListener(
    "touchstart",
    function (event) {
        startAdminHold(
            event
        );
    },
    false
);

adminButton.addEventListener(
    "touchend",
    function (event) {
        cancelAdminHold(
            event
        );
    },
    false
);

adminButton.addEventListener(
    "touchcancel",
    function (event) {
        cancelAdminHold(
            event
        );
    },
    false
);


/*
 * Mouse events for Mac/desktop use.
 */
adminButton.addEventListener(
    "mousedown",
    function (event) {
        startAdminHold(
            event
        );
    },
    false
);

adminButton.addEventListener(
    "mouseup",
    function (event) {
        cancelAdminHold(
            event
        );
    },
    false
);

adminButton.addEventListener(
    "mouseleave",
    function (event) {
        cancelAdminHold(
            event
        );
    },
    false
);


/*
 * Prevent the normal link click.
 * Navigation happens only after the hold timer.
 */
adminButton.addEventListener(
    "click",
    function (event) {
        event.preventDefault();

        return false;
    },
    false
);

connectWebSocket();
startCameraStatusMonitor();
