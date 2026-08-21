const library =
    document.getElementById(
        "background-library"
    );

const uploadForm =
    document.getElementById(
        "upload-form"
    );

const uploadFile =
    document.getElementById(
        "upload-file"
    );

const uploadStatus =
    document.getElementById(
        "upload-status"
    );

const selectionDialog =
    document.getElementById(
        "selection-dialog"
    );

const selectionPreview =
    document.getElementById(
        "selection-preview"
    );

const selectionTitle =
    document.getElementById(
        "selection-title"
    );

const selectionCancel =
    document.getElementById(
        "selection-cancel"
    );

const logoLibrary =
    document.getElementById(
        "logo-library"
    );

const activeLogoImage =
    document.getElementById(
        "active-logo-image"
    );

const activeLogoStatus =
    document.getElementById(
        "active-logo-status"
    );

const logoUploadForm =
    document.getElementById(
        "logo-upload-form"
    );

const logoUploadFile =
    document.getElementById(
        "logo-upload-file"
    );

const logoUploadStatus =
    document.getElementById(
        "logo-upload-status"
    );

const greenscreenEnabled =
    document.getElementById(
        "greenscreen-enabled"
    );

let selectedFilename = null;

async function loadBackgroundSettings() {
    const response = await fetch(
        "/api/admin/backgrounds/settings",
        {
            cache: "no-store",
        }
    );

    if (!response.ok) {
        return;
    }

    const data =
        await response.json();

    greenscreenEnabled.checked =
        data.enabled === true;
}


greenscreenEnabled.addEventListener(
    "change",
    async () => {
        const enabled =
            greenscreenEnabled.checked;

        const response = await fetch(
            "/api/admin/backgrounds/settings",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                body: JSON.stringify({
                    enabled: enabled,
                }),
            }
        );

        if (!response.ok) {
            greenscreenEnabled.checked =
                !enabled;

            alert(
                "Greenscreen-Einstellung "
                + "konnte nicht geändert werden."
            );
        }
    }
);

function libraryImageUrl(
    filename
) {
    return (
        "/background-assets/library/"
        + encodeURIComponent(filename)
        + "?v="
        + Date.now()
    );
}


function activeImageUrl(
    slot
) {
    return (
        `/background-assets/background_0${slot}.jpg`
        + `?v=${Date.now()}`
    );
}


function refreshSlot(
    slot,
    filename
) {
    const image =
        document.getElementById(
            `slot-image-${slot}`
        );

    const name =
        document.getElementById(
            `slot-name-${slot}`
        );

    image.src =
        activeImageUrl(slot);

    name.textContent =
        filename;
}


function openSelection(
    filename
) {
    selectedFilename =
        filename;

    selectionTitle.textContent =
        filename;

    selectionPreview.src =
        libraryImageUrl(
            filename
        );

    selectionDialog.showModal();
}

function logoImageUrl(
    filename
) {
    return (
        "/logo-assets/"
        + encodeURIComponent(filename)
        + "?v="
        + Date.now()
    );
}


function refreshActiveLogo() {
    activeLogoImage.src =
        "/active-logo?v="
        + Date.now();

    activeLogoImage.style.display =
        "block";

    activeLogoStatus.textContent =
        "Aktives Logo";
}


async function selectLogo(
    filename
) {
    const response = await fetch(
        "/api/admin/logos/select",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json",
            },

            body: JSON.stringify({
                filename: filename,
            }),
        }
    );

    if (!response.ok) {
        alert(
            "Logo konnte nicht ausgewählt werden."
        );

        return;
    }

    refreshActiveLogo();
}


async function loadLogoLibrary() {
    const response = await fetch(
        "/api/admin/logos",
        {
            cache: "no-store",
        }
    );

    if (!response.ok) {
        logoLibrary.textContent =
            "Logo-Bibliothek konnte nicht "
            + "geladen werden.";

        return;
    }

    const data =
        await response.json();

    logoLibrary.replaceChildren();

    if (data.items.length === 0) {
        logoLibrary.textContent =
            "Noch keine Logos vorhanden.";

        return;
    }

    for (
        const filename
        of data.items
    ) {
        const button =
            document.createElement(
                "button"
            );

        button.type =
            "button";

        button.className =
            "library-item";

        const image =
            document.createElement(
                "img"
            );

        image.src =
            logoImageUrl(
                filename
            );

        image.alt =
            filename;

        const caption =
            document.createElement(
                "span"
            );

        caption.textContent =
            filename;

        button.append(
            image,
            caption
        );

        button.addEventListener(
            "click",
            () => {
                selectLogo(
                    filename
                );
            }
        );

        logoLibrary.appendChild(
            button
        );
    }
}

logoUploadForm.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const file =
            logoUploadFile.files[0];

        if (!file) {
            return;
        }

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        logoUploadStatus.textContent =
            "Upload läuft …";

        const response = await fetch(
            "/api/admin/logos/upload",
            {
                method: "POST",
                body: formData,
            }
        );

        if (!response.ok) {
            const data =
                await response.json();

            logoUploadStatus.textContent =
                data.detail
                ?? "Upload fehlgeschlagen.";

            return;
        }

        const data =
            await response.json();

        logoUploadStatus.textContent =
            `Gespeichert als ${data.filename}`;

        logoUploadForm.reset();

        await loadLogoLibrary();
    }
);


async function loadLibrary() {
    const response = await fetch(
        "/api/admin/backgrounds",
        {
            cache: "no-store",
        }
    );

    if (!response.ok) {
        library.textContent =
            "Bibliothek konnte nicht geladen werden.";

        return;
    }

    const data =
        await response.json();

    library.replaceChildren();

    for (
        const filename
        of data.items
    ) {
        const button =
            document.createElement(
                "button"
            );

        button.type =
            "button";

        button.className =
            "library-item";

        const image =
            document.createElement(
                "img"
            );

        image.src =
            libraryImageUrl(
                filename
            );

        image.alt =
            filename;

        const caption =
            document.createElement(
                "span"
            );

        caption.textContent =
            filename;

        button.append(
            image,
            caption
        );

        button.addEventListener(
            "click",
            () => {
                openSelection(
                    filename
                );
            }
        );

        library.appendChild(
            button
        );
    }
}


async function selectBackground(
    slot
) {
    if (!selectedFilename) {
        return;
    }

    const response = await fetch(
        `/api/admin/backgrounds/select/${slot}`,
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json",
            },

            body: JSON.stringify({
                filename:
                    selectedFilename,
            }),
        }
    );

    if (!response.ok) {
        alert(
            "Hintergrund konnte nicht "
            + "ausgewählt werden."
        );

        return;
    }

    refreshSlot(
        slot,
        selectedFilename
    );

    selectionDialog.close();
}


for (
    const button
    of selectionDialog.querySelectorAll(
        "[data-slot]"
    )
) {
    button.addEventListener(
        "click",
        () => {
            selectBackground(
                button.dataset.slot
            );
        }
    );
}


selectionCancel.addEventListener(
    "click",
    () => {
        selectionDialog.close();
    }
);


uploadForm.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        const file =
            uploadFile.files[0];

        if (!file) {
            return;
        }

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        uploadStatus.textContent =
            "Upload läuft …";

        const response = await fetch(
            "/api/admin/backgrounds/upload",
            {
                method: "POST",
                body: formData,
            }
        );

        if (!response.ok) {
            const data =
                await response.json();

            uploadStatus.textContent =
                data.detail
                ?? "Upload fehlgeschlagen.";

            return;
        }

        const data =
            await response.json();

        uploadStatus.textContent =
            `Gespeichert als ${data.filename}`;

        uploadForm.reset();

        await loadLibrary();
    }
);


loadLibrary();
loadLogoLibrary();
loadBackgroundSettings();
