var shutdownButton =
    document.getElementById(
        "shutdown-button"
    );

var shutdownPanel =
    document.getElementById(
        "shutdown-panel"
    );

var shutdownPin =
    document.getElementById(
        "shutdown-pin"
    );

var shutdownCancel =
    document.getElementById(
        "shutdown-cancel"
    );

var shutdownConfirm =
    document.getElementById(
        "shutdown-confirm"
    );

var shutdownMessage =
    document.getElementById(
        "shutdown-message"
    );

var saveButton =
    document.getElementById(
        "save-settings"
    );

var messageElement =
    document.getElementById(
        "settings-message"
    );

var calibrateButton =
    document.getElementById(
        "calibrate-greenscreen"
    );

var previewMaskButton =
    document.getElementById(
        "preview-mask"
    );

var applyCalibrationButton =
    document.getElementById(
        "apply-calibration"
    );

var calibrationMessage =
    document.getElementById(
        "calibration-message"
    );

var calibrationPreview =
    document.getElementById(
        "calibration-preview"
    );

var calibrationReference =
    document.getElementById(
        "calibration-reference"
    );

var calibrationMask =
    document.getElementById(
        "calibration-mask"
    );

var calibrationSuggestion =
    null;

function showCalibrationMessage(
    text,
    type
) {
    calibrationMessage.textContent =
        text;

    calibrationMessage.className =
        "settings-message";

    if (type) {
        calibrationMessage.className +=
            " " + type;
    }
}

function calibrateGreenscreen() {
    calibrateButton.disabled =
        true;

    previewMaskButton.disabled =
        true;

    applyCalibrationButton.disabled =
        true;

    showCalibrationMessage(
        "Kalibrierung läuft …"
    );

    requestJson(
        "POST",
        "/api/admin/greenscreen/calibrate",
        null,

        function (data) {
            calibrationSuggestion =
                data;

            calibrateButton.disabled =
                false;

            previewMaskButton.disabled =
                false;

            applyCalibrationButton.disabled =
                false;

            calibrationReference.src =
                "/api/greenscreen/calibration/reference?v="
                + Date.now();

            showCalibrationMessage(
                "Kalibrierung abgeschlossen.",
                "success"
            );
        },

        function (error) {
            calibrateButton.disabled =
                false;

            showCalibrationMessage(
                "Kalibrierung fehlgeschlagen: "
                + error,
                "error"
            );
        }
    );
}

function previewCalibrationMask() {
    if (!calibrationSuggestion) {
        return;
    }

    previewMaskButton.disabled =
        true;

    requestJson(
        "POST",
        "/api/admin/greenscreen/mask",
        {
            hue_min:
                calibrationSuggestion.hue_min,

            hue_max:
                calibrationSuggestion.hue_max,

            saturation_min:
                calibrationSuggestion.saturation_min,

            value_min:
                calibrationSuggestion.value_min
        },

        function () {
            calibrationMask.src =
                "/api/greenscreen/calibration/mask?v="
                + Date.now();

            calibrationPreview.className =
                "calibration-preview";

            previewMaskButton.disabled =
                false;
        },

        function (error) {
            previewMaskButton.disabled =
                false;

            showCalibrationMessage(
                "Maske konnte nicht erzeugt werden: "
                + error,
                "error"
            );
        }
    );
}

function applyCalibration() {
    if (!calibrationSuggestion) {
        return;
    }

    setValue(
        "hue-min",
        calibrationSuggestion.hue_min
    );

    setValue(
        "hue-max",
        calibrationSuggestion.hue_max
    );

    setValue(
        "saturation-min",
        calibrationSuggestion.saturation_min
    );

    setValue(
        "value-min",
        calibrationSuggestion.value_min
    );

    setValue(
        "feather",
        calibrationSuggestion.feather
    );

    showCalibrationMessage(
        "Kalibrierungswerte wurden in "
        + "die Eingabefelder übernommen. "
        + "Zum dauerhaften Speichern noch "
        + "\"Änderungen speichern\" drücken.",
        "success"
    );
}

calibrateButton.addEventListener(
    "click",
    function () {
        calibrateGreenscreen();
    }
);

previewMaskButton.addEventListener(
    "click",
    function () {
        previewCalibrationMask();
    }
);

applyCalibrationButton.addEventListener(
    "click",
    function () {
        applyCalibration();
    }
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

function showShutdownMessage(
    text,
    type
) {
    shutdownMessage.textContent =
        text;

    shutdownMessage.className =
        "settings-message";

    if (type) {
        shutdownMessage.className +=
            " " + type;
    }
}


function openShutdownPanel() {
    shutdownPin.value = "";

    showShutdownMessage(
        ""
    );

    shutdownPanel.className =
        "shutdown-panel";

    shutdownPin.focus();
}


function closeShutdownPanel() {
    shutdownPin.value = "";

    shutdownPanel.className =
        "shutdown-panel hidden";

    showShutdownMessage(
        ""
    );
}


function shutdownSystem() {
    var pin =
        shutdownPin.value;

    if (!pin) {
        showShutdownMessage(
            "Bitte Admin-PIN eingeben.",
            "error"
        );

        return;
    }

    shutdownConfirm.disabled =
        true;

    shutdownCancel.disabled =
        true;

    showShutdownMessage(
        "Fotobox wird ausgeschaltet …"
    );

    requestJson(
        "POST",
        "/api/admin/shutdown",
        {
            pin: pin
        },

        function () {
            shutdownPin.value = "";

            showShutdownMessage(
                "System wird heruntergefahren.",
                "success"
            );

            shutdownButton.disabled =
                true;

            shutdownConfirm.disabled =
                true;
        },

        function (error) {
            shutdownConfirm.disabled =
                false;

            shutdownCancel.disabled =
                false;

            shutdownPin.value = "";

            showShutdownMessage(
                "Ausschalten nicht möglich: "
                + error,
                "error"
            );

            shutdownPin.focus();
        }
    );
}


shutdownButton.addEventListener(
    "click",
    function () {
        openShutdownPanel();
    }
);


shutdownCancel.addEventListener(
    "click",
    function () {
        closeShutdownPanel();
    }
);


shutdownConfirm.addEventListener(
    "click",
    function () {
        shutdownSystem();
    }
);

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
