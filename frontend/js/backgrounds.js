var library =
    document.getElementById(
        "background-library"
    );

var libraryTitle =
    document.getElementById(
        "library-title"
    );

var libraryDescription =
    document.getElementById(
        "library-description"
    );

var libraryCount =
    document.getElementById(
        "library-count"
    );

var uploadForm =
    document.getElementById(
        "upload-form"
    );

var uploadFile =
    document.getElementById(
        "upload-file"
    );

var uploadStatus =
    document.getElementById(
        "upload-status"
    );

var selectionDialog =
    document.getElementById(
        "selection-dialog"
    );

var selectionPreview =
    document.getElementById(
        "selection-preview"
    );

var selectionTitle =
    document.getElementById(
        "selection-title"
    );

var selectionCancel =
    document.getElementById(
        "selection-cancel"
    );

var logoLibrary =
    document.getElementById(
        "logo-library"
    );

var activeLogoImage =
    document.getElementById(
        "active-logo-image"
    );

var activeLogoStatus =
    document.getElementById(
        "active-logo-status"
    );

var logoUploadForm =
    document.getElementById(
        "logo-upload-form"
    );

var logoUploadFile =
    document.getElementById(
        "logo-upload-file"
    );

var logoUploadStatus =
    document.getElementById(
        "logo-upload-status"
    );

var greenscreenEnabled =
    document.getElementById(
        "greenscreen-enabled"
    );

var selectionModeFixed =
    document.getElementById(
        "selection-mode-fixed"
    );

var selectionModeRandom =
    document.getElementById(
        "selection-mode-random"
    );

var selectionModeStatus =
    document.getElementById(
        "selection-mode-status"
    );

var fixedBackgroundSection =
    document.getElementById(
        "fixed-background-section"
    );

var randomBackgroundSection =
    document.getElementById(
        "random-background-section"
    );


var selectedFilename = null;
var activeBackgrounds = {};
var activeLogo = null;
var currentSelectionMode = "fixed";
var availableBackgroundCount = 0;


/*
 * Generic JSON request helper.
 *
 * Deliberately implemented without fetch/async/await so that
 * the administration page also works on the old iPad.
 */
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

            if (
                request.responseText
            ) {
                try {
                    result =
                        JSON.parse(
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


/*
 * Multipart upload helper.
 */
function uploadFileRequest(
    url,
    file,
    success,
    failure
) {
    var formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    var request =
        new XMLHttpRequest();

    request.open(
        "POST",
        url,
        true
    );

    request.onreadystatechange =
        function () {
            if (
                request.readyState !== 4
            ) {
                return;
            }

            var result = null;

            if (
                request.responseText
            ) {
                try {
                    result =
                        JSON.parse(
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
                    success(
                        result
                    );
                }

                return;
            }

            if (failure) {
                var message =
                    "Upload fehlgeschlagen.";

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
                    "Netzwerkfehler beim Upload."
                );
            }
        };

    request.send(
        formData
    );
}


function libraryImageUrl(
    filename
) {
    return (
        "/background-assets/library/"
        + encodeURIComponent(
            filename
        )
        + "?v="
        + Date.now()
    );
}


function activeImageUrl(
    slot
) {
    return (
        "/background-assets/background_0"
        + slot
        + ".jpg?v="
        + Date.now()
    );
}


function logoImageUrl(
    filename
) {
    return (
        "/logo-assets/"
        + encodeURIComponent(
            filename
        )
        + "?v="
        + Date.now()
    );
}


function refreshSlot(
    slot,
    filename
) {
    var image =
        document.getElementById(
            "slot-image-" + slot
        );

    var name =
        document.getElementById(
            "slot-name-" + slot
        );

    image.src =
        activeImageUrl(
            slot
        );

    name.textContent =
        filename;
}


/*
 * Native <dialog> is not available reliably on old Safari.
 */
function showSelectionDialog() {
    if (
        selectionDialog.showModal
        && typeof selectionDialog.showModal
            === "function"
    ) {
        selectionDialog.showModal();
        return;
    }

    selectionDialog.setAttribute(
        "open",
        "open"
    );

    selectionDialog.style.display =
        "block";
}


function closeSelectionDialog() {
    if (
        selectionDialog.close
        && typeof selectionDialog.close
            === "function"
    ) {
        selectionDialog.close();
        return;
    }

    selectionDialog.removeAttribute(
        "open"
    );

    selectionDialog.style.display =
        "none";
}


function openSelection(
    filename
) {
    if (
        currentSelectionMode !== "fixed"
    ) {
        return;
    }

    selectedFilename =
        filename;

    selectionTitle.textContent =
        filename;

    selectionPreview.src =
        libraryImageUrl(
            filename
        );

    showSelectionDialog();
}


function showModeStatus(
    text,
    isError
) {
    selectionModeStatus.textContent =
        text;

    selectionModeStatus.className =
        "mode-status";

    if (isError) {
        selectionModeStatus.className +=
            " error";
    }
}


function updateModeDisplay() {
    var isRandom =
        currentSelectionMode === "random";

    selectionModeFixed.checked =
        !isRandom;

    selectionModeRandom.checked =
        isRandom;

    if (isRandom) {
        fixedBackgroundSection.className =
            "fixed-background-section hidden";

        randomBackgroundSection.className =
            "random-background-section";

        libraryTitle.textContent =
            "Zufallspool";

        libraryDescription.textContent =
            "Alle Motive dieser Bibliothek können "
            + "zufällig verwendet werden.";
    } else {
        fixedBackgroundSection.className =
            "fixed-background-section";

        randomBackgroundSection.className =
            "random-background-section hidden";

        libraryTitle.textContent =
            "Hintergrund-Bibliothek";

        libraryDescription.textContent =
            "Motiv antippen, um es einem Foto "
            + "fest zuzuordnen.";
    }
}


function saveBackgroundSettings(
    enabled,
    selectionMode,
    success,
    failure
) {
    requestJson(
        "POST",
        "/api/admin/backgrounds/settings",
        {
            enabled: enabled,
            selection_mode: selectionMode
        },
        success,
        failure
    );
}


function loadBackgroundSettings() {
    requestJson(
        "GET",
        "/api/admin/backgrounds/settings?v="
            + Date.now(),
        null,

        function (data) {
            greenscreenEnabled.checked =
                data.enabled === true;

            currentSelectionMode =
                data.selection_mode
                || "fixed";

            updateModeDisplay();

            if (
                currentSelectionMode === "random"
                && availableBackgroundCount < 3
            ) {
                showModeStatus(
                    "Achtung: Für die Zufallsauswahl "
                    + "werden mindestens drei "
                    + "Hintergrundbilder benötigt.",
                    true
                );
            } else {
                showModeStatus(
                    ""
                );
            }

            loadLibrary();
        },

        function () {
            /*
             * Keep usable defaults if the status
             * endpoint cannot be loaded.
             */
            currentSelectionMode =
                "fixed";

            updateModeDisplay();
        }
    );
}


greenscreenEnabled.addEventListener(
    "change",
    function () {
        var enabled =
            greenscreenEnabled.checked;

        saveBackgroundSettings(
            enabled,
            currentSelectionMode,

            function (data) {
                greenscreenEnabled.checked =
                    data.enabled === true;
            },

            function (error) {
                greenscreenEnabled.checked =
                    !enabled;

                window.alert(
                    "Greenscreen-Einstellung "
                    + "konnte nicht geändert werden: "
                    + error
                );
            }
        );
    }
);


function changeSelectionMode(
    newMode
) {
    if (
        newMode === "random"
        && availableBackgroundCount < 3
    ) {
        selectionModeFixed.checked =
            true;

        selectionModeRandom.checked =
            false;

        showModeStatus(
            "Für die Zufallsauswahl müssen "
            + "mindestens drei Hintergrundbilder "
            + "vorhanden sein.",
            true
        );

        return;
    }

    var oldMode =
        currentSelectionMode;

    saveBackgroundSettings(
        greenscreenEnabled.checked,
        newMode,

        function (data) {
            currentSelectionMode =
                data.selection_mode
                || newMode;

            showModeStatus(
                currentSelectionMode === "random"
                ? "Zufallsauswahl ist aktiv."
                : "Feste Zuordnung ist aktiv."
            );

            updateModeDisplay();
            loadLibrary();
        },

        function (error) {
            currentSelectionMode =
                oldMode;

            updateModeDisplay();

            showModeStatus(
                "Auswahlmodus konnte nicht "
                + "geändert werden: "
                + error,
                true
            );
        }
    );
}


selectionModeFixed.addEventListener(
    "change",
    function () {
        if (
            selectionModeFixed.checked
        ) {
            changeSelectionMode(
                "fixed"
            );
        }
    }
);


selectionModeRandom.addEventListener(
    "change",
    function () {
        if (
            selectionModeRandom.checked
        ) {
            changeSelectionMode(
                "random"
            );
        }
    }
);


function refreshActiveLogo() {
    activeLogoImage.src =
        "/active-logo?v="
        + Date.now();

    activeLogoImage.style.display =
        "block";

    activeLogoStatus.textContent =
        "Aktives Logo";
}


function selectLogo(
    filename
) {
    requestJson(
        "POST",
        "/api/admin/logos/select",
        {
            filename: filename
        },

        function () {
            activeLogo =
                filename;

            refreshActiveLogo();
            loadLogoLibrary();
        },

        function (error) {
            window.alert(
                "Logo konnte nicht ausgewählt werden: "
                + error
            );
        }
    );
}


function deleteLogo(
    filename
) {
    var confirmed =
        window.confirm(
            'Logo "'
            + filename
            + '" wirklich löschen?'
        );

    if (!confirmed) {
        return;
    }

    requestJson(
        "DELETE",
        "/api/admin/logos/"
            + encodeURIComponent(
                filename
            ),
        null,

        function () {
            loadLogoLibrary();
        },

        function (error) {
            window.alert(
                error
            );
        }
    );
}


function loadLogoLibrary() {
    requestJson(
        "GET",
        "/api/admin/logos?v="
            + Date.now(),
        null,

        function (data) {
            activeLogo =
                data.active || null;

            while (
                logoLibrary.firstChild
            ) {
                logoLibrary.removeChild(
                    logoLibrary.firstChild
                );
            }

            if (
                !data.items
                || data.items.length === 0
            ) {
                logoLibrary.textContent =
                    "Noch keine Logos vorhanden.";

                return;
            }

            var i;

            for (
                i = 0;
                i < data.items.length;
                i += 1
            ) {
                createLogoItem(
                    data.items[i]
                );
            }
        },

        function () {
            logoLibrary.textContent =
                "Logo-Bibliothek konnte "
                + "nicht geladen werden.";
        }
    );
}


function createLogoItem(
    filename
) {
    var item =
        document.createElement(
            "div"
        );

    item.className =
        "library-item-wrapper";

    var selectButton =
        document.createElement(
            "button"
        );

    selectButton.type =
        "button";

    selectButton.className =
        "library-item";

    var image =
        document.createElement(
            "img"
        );

    image.src =
        logoImageUrl(
            filename
        );

    image.alt =
        filename;

    var caption =
        document.createElement(
            "span"
        );

    caption.textContent =
        filename;

    selectButton.appendChild(
        image
    );

    selectButton.appendChild(
        caption
    );

    var isActive =
        filename === activeLogo;

    if (isActive) {
        item.className +=
            " active-library-item";

        var badge =
            document.createElement(
                "div"
            );

        badge.className =
            "active-badge";

        badge.textContent =
            "AKTIV";

        item.appendChild(
            badge
        );
    }

    selectButton.onclick =
        function () {
            selectLogo(
                filename
            );
        };

    var deleteButton =
        document.createElement(
            "button"
        );

    deleteButton.type =
        "button";

    deleteButton.className =
        "delete-library-item";

    deleteButton.textContent =
        "Löschen";

    deleteButton.disabled =
        isActive;

    if (isActive) {
        deleteButton.title =
            "Das aktive Logo kann "
            + "nicht gelöscht werden.";
    }

    deleteButton.onclick =
        function () {
            deleteLogo(
                filename
            );
        };

    item.appendChild(
        selectButton
    );

    item.appendChild(
        deleteButton
    );

    logoLibrary.appendChild(
        item
    );
}


function rotateBackground(
    filename,
    degrees
) {
    requestJson(
        "POST",
        "/api/admin/backgrounds/"
            + encodeURIComponent(
                filename
            )
            + "/rotate",
        {
            degrees: degrees
        },

        function () {
            loadLibrary();

            var activeSlots =
                getActiveSlots(
                    filename
                );

            var i;

            for (
                i = 0;
                i < activeSlots.length;
                i += 1
            ) {
                refreshSlot(
                    activeSlots[i],
                    filename
                );
            }
        },

        function (error) {
            window.alert(
                "Hintergrund konnte nicht "
                + "gedreht werden: "
                + error
            );
        }
    );
}


function deleteBackground(
    filename
) {
    var confirmed =
        window.confirm(
            'Hintergrund "'
            + filename
            + '" wirklich löschen?'
        );

    if (!confirmed) {
        return;
    }

    requestJson(
        "DELETE",
        "/api/admin/backgrounds/"
            + encodeURIComponent(
                filename
            ),
        null,

        function () {
            loadLibrary();
        },

        function (error) {
            window.alert(
                error
            );
        }
    );
}


function getActiveSlots(
    filename
) {
    var slots = [];
    var key;

    for (
        key in activeBackgrounds
    ) {
        if (
            activeBackgrounds.hasOwnProperty(
                key
            )
            && activeBackgrounds[key]
                === filename
        ) {
            slots.push(
                key
            );
        }
    }

    return slots;
}


function loadLibrary() {
    requestJson(
        "GET",
        "/api/admin/backgrounds?v="
            + Date.now(),
        null,

        function (data) {
            activeBackgrounds =
                data.active || {};

            availableBackgroundCount =
                data.items
                ? data.items.length
                : 0;

            libraryCount.textContent =
                availableBackgroundCount
                + (
                    availableBackgroundCount === 1
                    ? " Motiv"
                    : " Motive"
                );

            while (
                library.firstChild
            ) {
                library.removeChild(
                    library.firstChild
                );
            }

            if (
                !data.items
                || data.items.length === 0
            ) {
                library.textContent =
                    "Noch keine Hintergründe vorhanden.";

                return;
            }

            var i;

            for (
                i = 0;
                i < data.items.length;
                i += 1
            ) {
                createBackgroundItem(
                    data.items[i]
                );
            }

            if (
                currentSelectionMode === "random"
                && availableBackgroundCount < 3
            ) {
                showModeStatus(
                    "Achtung: Es sind weniger als drei "
                    + "Hintergrundbilder vorhanden.",
                    true
                );
            }
        },

        function () {
            library.textContent =
                "Bibliothek konnte nicht "
                + "geladen werden.";
        }
    );
}


function createBackgroundItem(
    filename
) {
    var item =
        document.createElement(
            "div"
        );

    item.className =
        "library-item-wrapper";

    var selectButton =
        document.createElement(
            "button"
        );

    selectButton.type =
        "button";

    selectButton.className =
        "library-item";

    var image =
        document.createElement(
            "img"
        );

    image.src =
        libraryImageUrl(
            filename
        );

    image.alt =
        filename;

    var caption =
        document.createElement(
            "span"
        );

    caption.textContent =
        filename;

    selectButton.appendChild(
        image
    );

    selectButton.appendChild(
        caption
    );

    var activeSlots =
        getActiveSlots(
            filename
        );

    var isActive =
        activeSlots.length > 0;

        var activeSlots =
        getActiveSlots(
            filename
        );

    var isActive =
        activeSlots.length > 0;


    /*
     * First add the image itself.
     */
    item.appendChild(
        selectButton
    );


    if (
        currentSelectionMode === "random"
    ) {
        item.className +=
            " random-pool-item";

        var poolBadge =
            document.createElement(
                "div"
            );

        poolBadge.className =
            "pool-badge";

        poolBadge.textContent =
            "ZUFALLSPOOL";

        item.appendChild(
            poolBadge
        );

        selectButton.onclick =
            function () {
                return false;
            };

    } else {

        if (isActive) {
            item.className +=
                " active-library-item";

            var badge =
                document.createElement(
                    "div"
                );

            badge.className =
                "active-badge";

            badge.textContent =
                "AKTIV: Foto "
                + activeSlots.join(
                    ", "
                );

            item.appendChild(
                badge
            );
        }


        selectButton.onclick =
            function () {
                openSelection(
                    filename
                );
            };


        var assignButton =
            document.createElement(
                "button"
            );

        assignButton.type =
            "button";

        assignButton.className =
            "assign-background-item";

        assignButton.textContent =
            "Zuordnen";

        assignButton.onclick =
            function () {
                openSelection(
                    filename
                );
            };

        item.appendChild(
            assignButton
        );
    }

    var rotateControls =
        document.createElement(
            "div"
        );

    rotateControls.className =
        "rotate-controls";

    var rotateLeftButton =
        document.createElement(
            "button"
        );

    rotateLeftButton.type =
        "button";

    rotateLeftButton.className =
        "rotate-background-item";

    rotateLeftButton.textContent =
        "↶ 90°";

    rotateLeftButton.title =
        "90° nach links drehen";

    rotateLeftButton.onclick =
        function () {
            rotateBackground(
                filename,
                90
            );
        };

    var rotateRightButton =
        document.createElement(
            "button"
        );

    rotateRightButton.type =
        "button";

    rotateRightButton.className =
        "rotate-background-item";

    rotateRightButton.textContent =
        "↷ 90°";

    rotateRightButton.title =
        "90° nach rechts drehen";

    rotateRightButton.onclick =
        function () {
            rotateBackground(
                filename,
                -90
            );
        };

    rotateControls.appendChild(
        rotateLeftButton
    );

    rotateControls.appendChild(
        rotateRightButton
    );

    var deleteButton =
        document.createElement(
            "button"
        );

    deleteButton.type =
        "button";

    deleteButton.className =
        "delete-library-item";

    deleteButton.textContent =
        "Löschen";

    /*
     * The backend currently protects backgrounds that
     * are used by one of the fixed slots. Keep the same
     * rule in the UI, even while random mode is active.
     */
    deleteButton.disabled =
        isActive;

    if (isActive) {
        deleteButton.title =
            "Ein fest zugeordneter Hintergrund "
            + "kann nicht gelöscht werden.";
    }

    deleteButton.onclick =
        function () {
            deleteBackground(
                filename
            );
        };

    item.appendChild(
        selectButton
    );

    item.appendChild(
        deleteButton
    );

    library.appendChild(
        item
    );
}


function selectBackground(
    slot
) {
    if (
        !selectedFilename
        || currentSelectionMode !== "fixed"
    ) {
        return;
    }

    requestJson(
        "POST",
        "/api/admin/backgrounds/select/"
            + slot,
        {
            filename:
                selectedFilename
        },

        function () {
            activeBackgrounds[
                String(slot)
            ] = selectedFilename;

            refreshSlot(
                slot,
                selectedFilename
            );

            closeSelectionDialog();

            loadLibrary();
        },

        function (error) {
            window.alert(
                "Hintergrund konnte nicht "
                + "ausgewählt werden: "
                + error
            );
        }
    );
}


/*
 * Slot buttons inside the selection dialog.
 */
(function () {
    var buttons =
        selectionDialog.querySelectorAll(
            "[data-slot]"
        );

    var i;

    for (
        i = 0;
        i < buttons.length;
        i += 1
    ) {
        (function (button) {
            button.onclick =
                function () {
                    selectBackground(
                        button.getAttribute(
                            "data-slot"
                        )
                    );
                };
        }(buttons[i]));
    }
}());


selectionCancel.onclick =
    function () {
        closeSelectionDialog();
    };


logoUploadForm.onsubmit =
    function (event) {
        event.preventDefault();

        var file =
            logoUploadFile.files[0];

        if (!file) {
            return;
        }

        logoUploadStatus.textContent =
            "Upload läuft …";

        uploadFileRequest(
            "/api/admin/logos/upload",
            file,

            function (data) {
                logoUploadStatus.textContent =
                    "Gespeichert als "
                    + data.filename;

                logoUploadForm.reset();

                loadLogoLibrary();
            },

            function (error) {
                logoUploadStatus.textContent =
                    error;
            }
        );
    };


uploadForm.onsubmit =
    function (event) {
        event.preventDefault();

        var file =
            uploadFile.files[0];

        if (!file) {
            return;
        }

        uploadStatus.textContent =
            "Upload läuft …";

        uploadFileRequest(
            "/api/admin/backgrounds/upload",
            file,

            function (data) {
                uploadStatus.textContent =
                    "Gespeichert als "
                    + data.filename;

                uploadForm.reset();

                loadLibrary();
            },

            function (error) {
                uploadStatus.textContent =
                    error;
            }
        );
    };


/*
 * Initial load.
 *
 * First load the library so that the random-mode
 * minimum of three images can be evaluated.
 */
loadLibrary();
loadLogoLibrary();
loadBackgroundSettings();
