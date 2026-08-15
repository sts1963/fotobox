const captureScreen =
    document.getElementById("capture-screen");

const processingScreen =
    document.getElementById("processing-screen");

const errorScreen =
    document.getElementById("error-screen");

const captureStatus =
    document.getElementById("capture-status");

const errorMessage =
    document.getElementById("error-message");

const restartButton =
    document.getElementById("restart-button");

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


let socket = null;

function hideSessionScreens() {
    startScreen.classList.add("hidden");
    countdownScreen.classList.add("hidden");
    captureScreen.classList.add("hidden");
    processingScreen.classList.add("hidden");
    errorScreen.classList.add("hidden");
}

function setConnected(connected) {
    if (connected) {
        connectionStatus.textContent = "Bereit";
    } else {
        connectionStatus.textContent =
            "Verbindung zur Fotobox verloren";
    }
}


function updateState(message) {
    const state = message.state;

    console.log("Fotobox state:", state);

    hideSessionScreens();

    switch (state) {

        case "start":
            startScreen.classList.remove("hidden");
            startButton.disabled = false;
            break;

        case "countdown":
            countdownScreen.classList.remove("hidden");
            startButton.disabled = true;

            if (message.countdown !== null) {
                countdownElement.textContent =
                    message.countdown;
            }

            break;

        case "capturing": {
            captureScreen.classList.remove("hidden");
            startButton.disabled = true;

            const captured =
                Array.isArray(message.photos)
                    ? message.photos.length
                    : 0;

            const nextPhoto =
                Math.min(captured + 1, 3);

            captureStatus.textContent =
                `Foto ${nextPhoto} von 3`;

            break;
        }

        case "processing":
            processingScreen.classList.remove("hidden");
            startButton.disabled = true;
            break;

        case "preview":
            startButton.disabled = true;
            break;

        case "printing":
            startButton.disabled = true;
            break;

        case "error":
            errorScreen.classList.remove("hidden");
            startButton.disabled = true;

            errorMessage.textContent =
                message.error ??
                "Unbekannter Fehler";

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


    socket.addEventListener("open", () => {
        setConnected(true);
    });


    socket.addEventListener("message", (event) => {

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
    });


    socket.addEventListener("close", () => {

        setConnected(false);

        startButton.disabled = true;

        window.setTimeout(
            connectWebSocket,
            2000
        );
    });


    socket.addEventListener("error", () => {
        setConnected(false);
    });
}


startButton.addEventListener("click", () => {

    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {
        return;
    }

    socket.send(
        JSON.stringify({
            type: "start_session",
        })
    );
});

restartButton.addEventListener(
    "click",
    () => {
        if (
            !socket ||
            socket.readyState !== WebSocket.OPEN
        ) {
            return;
        }

        socket.send(
            JSON.stringify({
                type: "restart",
            })
        );
    }
);

connectWebSocket();
