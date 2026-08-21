var saveButton =
    document.getElementById(
        "save-settings"
    );

var messageElement =
    document.getElementById(
        "settings-message"
    );


function getElement(id) {
    return document.getElementById(id);
}


function setValue(
    id,
    value
) {
    getElement(id).value =
        value;
}


function numberValue(id) {
    return Number(
        getElement(id).value
    );
}


function showMessage(
    text,
    type
) {
    messageElement.textContent =
        text;

    messageElement.className =
        "settings-message";

    if (type) {
        messageElement.className +=
            " " + type;
    }
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

            var result = null;

            try {
                if (
                    request.responseText
                ) {
                    result =
                        JSON.parse(
                            request.responseText
                        );
                }

            } catch (error) {
                if (failure) {
                    failure(
                        "Ungültige Antwort "
                        + "vom Server."
                    );
                }

                return;
            }

            if (
                request.status >= 200
                && request.status < 300
            ) {
                if (success) {
                    success(
                        result
                    );
                }

                return;
            }

            if (failure) {
                var message =
                    "HTTP "
                    + request.status;

                if (
                    result
                    && result.detail
                ) {
                    message =
                        result.detail;
                }

                failure(
                    message
                );
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


function applySettings(
    settings
) {
    setValue(
        "countdown-seconds",
        settings.session.countdown_seconds
    );

    setValue(
        "interval-seconds",
        settings.session.interval_seconds
    );

    getElement(
        "background-enabled"
    ).checked =
        settings.background.enabled === true;

    var greenscreen =
        settings.background.greenscreen;

    setValue(
        "hue-min",
        greenscreen.hue_min
    );

    setValue(
        "hue-max",
        greenscreen.hue_max
    );

    setValue(
        "saturation-min",
        greenscreen.saturation_min
    );

    setValue(
        "value-min",
        greenscreen.value_min
    );

    setValue(
        "feather",
        greenscreen.feather
    );
}


function loadSettings() {
    showMessage(
        "Einstellungen werden geladen …"
    );

    saveButton.disabled =
        true;

    requestJson(
        "GET",
        "/api/admin/settings?v="
            + Date.now(),
        null,

        function (settings) {
            applySettings(
                settings
            );

            showMessage(
                ""
            );

            saveButton.disabled =
                false;
        },

        function (error) {
            showMessage(
                "Einstellungen konnten nicht "
                + "geladen werden: "
                + error,
                "error"
            );
        }
    );
}


function buildPayload() {
    return {
        session: {
            countdown_seconds:
                numberValue(
                    "countdown-seconds"
                ),

            interval_seconds:
                numberValue(
                    "interval-seconds"
                )
        },

        background: {
            enabled:
                getElement(
                    "background-enabled"
                ).checked,

            greenscreen: {
                hue_min:
                    numberValue(
                        "hue-min"
                    ),

                hue_max:
                    numberValue(
                        "hue-max"
                    ),

                saturation_min:
                    numberValue(
                        "saturation-min"
                    ),

                value_min:
                    numberValue(
                        "value-min"
                    ),

                feather:
                    numberValue(
                        "feather"
                    )
            }
        }
    };
}


function saveSettings() {
    saveButton.disabled =
        true;

    showMessage(
        "Einstellungen werden gespeichert …"
    );

    requestJson(
        "PUT",
        "/api/admin/settings",
        buildPayload(),

        function (settings) {
            applySettings(
                settings
            );

            showMessage(
                "Einstellungen gespeichert "
                + "und übernommen.",
                "success"
            );

            saveButton.disabled =
                false;
        },

        function (error) {
            showMessage(
                "Einstellungen konnten nicht "
                + "gespeichert werden: "
                + error,
                "error"
            );

            saveButton.disabled =
                false;
        }
    );
}


saveButton.addEventListener(
    "click",
    function () {
        saveSettings();
    }
);


loadSettings();
