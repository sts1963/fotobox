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

    switch (state) {

        case "start":
            startScreen.classList.remove("hidden");
            countdownScreen.classList.add("hidden");

            startButton.disabled = false;
            break;


        case "countdown":
            startScreen.classList.add("hidden");
            countdownScreen.classList.remove("hidden");

            startButton.disabled = true;

            if (message.countdown !== null) {
                countdownElement.textContent =
                    message.countdown;
            }

            break;


        case "capturing":
            startScreen.classList.add("hidden");
            countdownScreen.classList.add("hidden");

            startButton.disabled = true;
            break;


        case "processing":
            startButton.disabled = true;
            break;


        case "preview":
            startButton.disabled = false;
            break;


        case "printing":
            startButton.disabled = true;
            break;


        case "error":
            startButton.disabled = false;

            console.error(
                "Fotobox error:",
                message.error
            );

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


connectWebSocket();
