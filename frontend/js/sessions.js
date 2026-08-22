var sessionCount =
    document.getElementById(
        "session-count"
    );

var collageCount =
    document.getElementById(
        "collage-count"
    );

var archiveSize =
    document.getElementById(
        "archive-size"
    );

var newestSession =
    document.getElementById(
        "newest-session"
    );

var sessionList =
    document.getElementById(
        "session-list"
    );

var deleteAllButton =
    document.getElementById(
        "delete-all-button"
    );

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
            if (
                request.readyState !== 4
            ) {
                return;
            }

            var data = null;

            if (request.responseText) {
                try {
                    data = JSON.parse(
                        request.responseText
                    );
                } catch (error) {
                    data = null;
                }
            }

            if (
                request.status >= 200
                && request.status < 300
            ) {
                success(data);
                return;
            }

            if (failure) {
                failure(
                    data
                    && data.detail
                    ? data.detail
                    : "HTTP "
                        + request.status
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

    request.send();
}


function formatDate(value) {
    if (!value) {
        return "–";
    }

    var date =
        new Date(value);

    if (isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}


function formatSize(bytes) {
    if (
        bytes === null
        || bytes === undefined
    ) {
        return "–";
    }

    if (bytes < 1024 * 1024) {
        return Math.round(
            bytes / 1024
        ) + " KB";
    }

    return (
        (
            bytes
            / 1024
            / 1024
        ).toFixed(1)
        + " MB"
    );
}


function renderSessions(items) {
    sessionList.innerHTML = "";

    if (!items.length) {
        sessionList.textContent =
            "Keine Sessions vorhanden.";

        return;
    }

    for (
        var index = 0;
        index < items.length;
        index += 1
    ) {
        var item =
            items[index];

        var card =
            document.createElement(
                "article"
            );

        card.className =
            "session-card";

        var info =
            document.createElement(
                "div"
            );

        info.className =
            "session-info";

        var title =
            document.createElement(
                "strong"
            );

        title.textContent =
            formatDate(
                item.created_at
            );

        info.appendChild(
            title
        );

        var details =
            document.createElement(
                "div"
            );

        details.className =
            "session-details";

        details.textContent =
            item.photo_count
            + " Fotos · "
            + formatSize(
                item.size_bytes
            );

        info.appendChild(
            details
        );

        card.appendChild(
            info
        );

        var actions =
            document.createElement(
                "div"
            );

        actions.className =
            "session-actions";

        if (item.has_collage) {
            var viewLink =
                document.createElement(
                    "a"
                );

            viewLink.href =
                "/api/admin/sessions/"
                + encodeURIComponent(
                    item.session_id
                )
                + "/collage";

            viewLink.target =
                "_blank";

            viewLink.textContent =
                "Collage ansehen";

            actions.appendChild(
                viewLink
            );
        }

        var deleteButton =
            document.createElement(
                "button"
            );

        deleteButton.type =
            "button";

        deleteButton.textContent =
            "Session löschen";

        deleteButton.setAttribute(
            "data-session-id",
            item.session_id
        );

        deleteButton.onclick =
            function () {
                var sessionId =
                    this.getAttribute(
                        "data-session-id"
                    );

                deleteSession(
                    sessionId
                );
            };

        actions.appendChild(
            deleteButton
        );

        card.appendChild(
            actions
        );

        sessionList.appendChild(
            card
        );
    }
}


deleteAllButton.onclick =
    function () {
        var confirmed =
            window.confirm(
                "Alle alten Sessions wirklich löschen?\n\n"
                + "Dabei werden alle gespeicherten "
                + "Fotos und Collagen gelöscht.\n\n"
                + "Die aktuelle Session bleibt erhalten.\n\n"
                + "Dieser Vorgang kann nicht "
                + "rückgängig gemacht werden."
            );

        if (!confirmed) {
            return;
        }

        deleteAllButton.disabled =
            true;

        deleteAllButton.textContent =
            "Wird gelöscht …";

        requestJson(
            "DELETE",
            "/api/admin/sessions",

            function (data) {
                deleteAllButton.disabled =
                    false;

                deleteAllButton.textContent =
                    "Alle alten Sessions löschen";

                window.alert(
                    data.deleted_count
                    + " Session(s) wurden gelöscht."
                );

                loadSessions();
            },

            function (error) {
                deleteAllButton.disabled =
                    false;

                deleteAllButton.textContent =
                    "Alle alten Sessions löschen";

                window.alert(
                    "Sessions konnten nicht "
                    + "gelöscht werden: "
                    + error
                );
            }
        );
    };


loadSessions();

function loadSessions() {
    requestJson(
        "GET",
        "/api/admin/sessions?v="
            + Date.now(),

        function (data) {
            sessionCount.textContent =
                data.summary.session_count;

            collageCount.textContent =
                data.summary.collage_count;

            archiveSize.textContent =
                data.summary.size_mb
                + " MB";

            newestSession.textContent =
                formatDate(
                    data.summary.newest
                );

            renderSessions(
                data.items
            );
        },

        function (error) {
            sessionList.textContent =
                "Sessions konnten nicht "
                + "geladen werden: "
                + error;
        }
    );
}


function deleteSession(
    sessionId
) {
    if (
        !window.confirm(
            "Diese Session wirklich löschen?"
        )
    ) {
        return;
    }

    requestJson(
        "DELETE",
        "/api/admin/sessions/"
            + encodeURIComponent(
                sessionId
            ),

        function () {
            loadSessions();
        },

        function (error) {
            window.alert(
                "Session konnte nicht "
                + "gelöscht werden: "
                + error
            );
        }
    );
}


loadSessions();
