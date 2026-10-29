
(() => {
    function initChat() {

        const messages = document.getElementById('pjchat-messages');

        // Hanya jalankan pada halaman detail chat
        if (!messages) return;

        // Elemen popup
        const editDialog = document.getElementById('pjchat-edit-dialog');
        const deleteDialog = document.getElementById('pjchat-delete-dialog');

        // Elemen form
        const editForm = document.getElementById('pjchat-edit-form');
        const deleteForm = document.getElementById('pjchat-delete-form');

        // Elemen khusus edit dan hapus
        const deleteEveryone = document.getElementById('pjchat-delete-everyone');
        const editInput = document.getElementById('pjchat-edit-text');
        const editPreview = document.getElementById('pjchat-edit-preview');
        const editError = document.getElementById('pjchat-edit-error');

        // Otomatis scroll ke pesan terbaru
        messages.scrollTop = messages.scrollHeight;


        // ===================================
        // EDIT PESAN
        // ===================================

        document.querySelectorAll('.js-pjchat-edit').forEach(button => {

            button.addEventListener('click', () => {

                const source = document.getElementById(
                    `pjchat-text-${button.dataset.messageId}`
                );

                if (!source) return;

                const text = source.textContent;

                // Tentukan pesan yang akan diedit
                editForm.action = button.dataset.editUrl;

                // Tampilkan teks lama pada popup
                editInput.value = text;
                editPreview.textContent = text;
                editError.textContent = '';

                // Tutup dropdown
                button.closest('details').open = false;

                // Buka popup Edit
                editDialog.showModal();
                editInput.focus();

            });

        });


        // ===================================
        // HAPUS PESAN
        // ===================================

        document.querySelectorAll('.js-pjchat-delete').forEach(button => {

            button.addEventListener('click', () => {

                // Tentukan pesan yang akan dihapus
                deleteForm.action = button.dataset.deleteUrl;

                // Kedua opsi hanya untuk pesan sendiri
                // yang belum dihapus untuk semua orang
                deleteEveryone.hidden =
                    button.dataset.ownMessage !== 'true';

                // Tutup dropdown
                button.closest('details').open = false;

                // Buka popup Hapus
                deleteDialog.showModal();

            });

        });


        // ===================================
        // VALIDASI EDIT
        // ===================================

        editForm.addEventListener('submit', event => {

            if (!editInput.value.trim()) {

                event.preventDefault();

                editError.textContent =
                    'Pesan tidak boleh kosong.';

                editInput.focus();

            }

        });


        // ===================================
        // TOMBOL TUTUP POPUP
        // ===================================

        document.querySelectorAll('.js-pjchat-close').forEach(button => {

            button.addEventListener('click', () => {
                button.closest('dialog').close();
            });

        });


        // Klik di luar isi dialog untuk menutup
        [editDialog, deleteDialog].forEach(dialog => {

            dialog.addEventListener('click', event => {

                if (event.target === dialog) {
                    dialog.close();
                }

            });

        });


        // ===================================
        // DROPDOWN PANAH PESAN
        // ===================================

        document.querySelectorAll('.pjchat-actions').forEach(details => {

            details.addEventListener('toggle', () => {

                if (!details.open) return;

                // Tutup dropdown lainnya
                document.querySelectorAll(
                    '.pjchat-actions[open]'
                ).forEach(other => {

                    if (other !== details) {
                        other.open = false;
                    }

                });

                // Buka ke atas jika dekat batas bawah chat
                const menu = details.querySelector(
                    '.pjchat-actions-menu'
                );

                const bounds = details.getBoundingClientRect();
                const area = messages.getBoundingClientRect();

                const menuHeight = menu ? menu.offsetHeight : 100;

                const availableBelow = area.bottom - bounds.bottom;
                const availableAbove = bounds.top - area.top;

                details.classList.toggle(
                    'pjchat-menu-up',
                    availableBelow < menuHeight + 12 &&
                    availableAbove > menuHeight + 12
                );

            });

        });


        // Klik di luar dropdown untuk menutup
        document.addEventListener('click', event => {

            if (!event.target.closest('.pjchat-actions')) {

                document.querySelectorAll(
                    '.pjchat-actions[open]'
                ).forEach(details => {

                    details.open = false;

                });

            }

        });

    }

    // Pastikan HTML sudah siap sebelum JavaScript berjalan
    if (document.readyState === 'loading') {

        document.addEventListener(
            'DOMContentLoaded',
            initChat
        );

    } else {

        initChat();

    }

})();


/* ==========================================
   AJAX: AMBIL PESAN TERBARU TANPA RELOAD
   ========================================== */

(() => {
    function initMessagePolling() {
        const messagesArea = document.getElementById("pjchat-messages");

        if (!messagesArea || !messagesArea.dataset.messagesUrl) {
            return;
        }

        const editDialog = document.getElementById("pjchat-edit-dialog");
        const editForm = document.getElementById("pjchat-edit-form");
        const editInput = document.getElementById("pjchat-edit-text");
        const editPreview = document.getElementById("pjchat-edit-preview");
        const editError = document.getElementById("pjchat-edit-error");

        const deleteDialog = document.getElementById("pjchat-delete-dialog");
        const deleteForm = document.getElementById("pjchat-delete-form");
        const deleteEveryone = document.getElementById("pjchat-delete-everyone");

        const editUrlTemplate = messagesArea.dataset.editUrlTemplate;
        const deleteUrlTemplate = messagesArea.dataset.deleteUrlTemplate;

        let isFetching = false;

        function buildUrl(template, messageId) {
            return template.replace("/0/", `/${messageId}/`);
        }

        function makeMessage(data) {
            const wrapper = document.createElement("div");
            wrapper.className = "pjchat-message";
            wrapper.dataset.messageId = String(data.id);

            if (data.is_mine) {
                wrapper.classList.add("pjchat-message--mine");
            }

            const bubble = document.createElement("div");
            bubble.className = "pjchat-bubble";

            if (data.deleted_for_everyone) {
                bubble.classList.add("pjchat-bubble--deleted");
            }

            const content = document.createElement("div");

            if (data.deleted_for_everyone) {
                content.className = "pjchat-deleted-text";

                const symbol = document.createElement("span");
                symbol.textContent = "⊘";

                const label = document.createElement("span");
                label.textContent = data.is_mine
                    ? "Kamu menghapus pesan ini"
                    : "Pesan ini telah dihapus";

                content.append(symbol, label);
            } else {
                content.className = "pjchat-message-text";
                content.id = `pjchat-text-${data.id}`;
                content.textContent = data.text;
            }

            const time = document.createElement("div");
            time.className = "pjchat-message-meta";
            time.textContent = data.created_at;

            const details = document.createElement("details");
            details.className = "pjchat-actions";

            const summary = document.createElement("summary");
            summary.setAttribute("aria-label", "Opsi pesan");
            summary.setAttribute("title", "Opsi pesan");

            const arrow = document.createElement("span");
            arrow.textContent = "⌄";
            summary.appendChild(arrow);

            const menu = document.createElement("div");
            menu.className = "pjchat-actions-menu";

            if (data.is_mine && !data.deleted_for_everyone) {
                const editButton = document.createElement("button");
                editButton.type = "button";
                editButton.className = "pjchat-menu-item js-pjchat-edit";
                editButton.textContent = "Edit pesan";

                editButton.addEventListener("click", () => {
                    editForm.action = buildUrl(editUrlTemplate, data.id);
                    editInput.value = content.textContent;
                    editPreview.textContent = content.textContent;
                    editError.textContent = "";
                    details.open = false;
                    editDialog.showModal();
                    editInput.focus();
                });

                menu.appendChild(editButton);
            }

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className =
                "pjchat-menu-item pjchat-menu-item--danger js-pjchat-delete";
            deleteButton.textContent = "Hapus pesan";

            deleteButton.addEventListener("click", () => {
                deleteForm.action = buildUrl(deleteUrlTemplate, data.id);
                deleteEveryone.hidden =
                    !data.is_mine || bubble.classList.contains("pjchat-bubble--deleted");
                details.open = false;
                deleteDialog.showModal();
            });

            menu.appendChild(deleteButton);
            details.append(summary, menu);

            details.addEventListener("toggle", () => {
                if (!details.open) return;

                messagesArea.querySelectorAll(
                    ".pjchat-actions[open]"
                ).forEach(other => {
                    if (other !== details) {
                        other.open = false;
                    }
                });

                const bounds = details.getBoundingClientRect();
                const area = messagesArea.getBoundingClientRect();
                const menuHeight = menu.offsetHeight;

                details.classList.toggle(
                    "pjchat-menu-up",
                    area.bottom - bounds.bottom < menuHeight + 12 &&
                    bounds.top - area.top > menuHeight + 12
                );
            });

            bubble.append(content, time, details);
            wrapper.appendChild(bubble);

            return wrapper;
        }

        function updateExistingMessage(element, data) {
            const bubble = element.querySelector(".pjchat-bubble");
            const textElement = element.querySelector(".pjchat-message-text");

            if (!bubble) return;

            if (data.deleted_for_everyone) {
                if (!bubble.classList.contains("pjchat-bubble--deleted")) {
                    const replacement = makeMessage(data);
                    element.replaceWith(replacement);
                }
            } else if (textElement && textElement.textContent !== data.text) {
                textElement.textContent = data.text;
            }
        }

        async function refreshMessages() {
            if (isFetching || document.hidden) return;

            isFetching = true;

            try {
                const response = await fetch(messagesArea.dataset.messagesUrl, {
                    method: "GET",
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json"
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const result = await response.json();

                if (!Array.isArray(result.messages)) return;

                const nearBottom =
                    messagesArea.scrollHeight -
                    messagesArea.scrollTop -
                    messagesArea.clientHeight < 120;

                let hasNewMessages = false;

                for (const data of result.messages) {
                    const existing = Array.from(
                        messagesArea.querySelectorAll(
                            ".pjchat-message[data-message-id]"
                        )
                    ).find(element =>
                        element.dataset.messageId === String(data.id)
                    );

                    if (existing) {
                        updateExistingMessage(existing, data);
                    } else {
                        const emptyNotice = messagesArea.querySelector(
                            ".pjchat-no-messages"
                        );

                        if (emptyNotice) {
                            emptyNotice.remove();
                        }

                        messagesArea.appendChild(makeMessage(data));
                        hasNewMessages = true;
                    }
                }

                if (hasNewMessages && nearBottom) {
                    messagesArea.scrollTop = messagesArea.scrollHeight;
                }

            } catch (error) {
                console.warn("Gagal mengambil pesan Chat:", error);
            } finally {
                isFetching = false;
            }
        }

        // Ambil pesan langsung, lalu periksa setiap 4 detik.
        refreshMessages();
        window.addEventListener("pjchat:refresh", refreshMessages);
        setInterval(refreshMessages, 4000);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initMessagePolling);
    } else {
        initMessagePolling();
    }
})();


/* ==========================================
   AJAX: KIRIM PESAN TANPA RELOAD HALAMAN
   ========================================== */

(() => {
    function initAjaxSend() {
        const form = document.querySelector(".pjchat-compose-form");
        const messagesArea = document.getElementById("pjchat-messages");

        if (!form || !messagesArea) {
            return;
        }

        const sendButton = form.querySelector('button[type="submit"]');
        const textInput = form.querySelector('textarea[name="text"]');

        let isSending = false;

        // Area untuk menampilkan pesan kesalahan
        const errorMessage = document.createElement("p");
        errorMessage.className = "pjchat-form-error";
        errorMessage.setAttribute("role", "alert");
        errorMessage.hidden = true;

        form.insertAdjacentElement("afterend", errorMessage);

        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            if (isSending) return;

            if (!textInput || !textInput.value.trim()) {
                errorMessage.textContent = "Pesan tidak boleh kosong.";
                errorMessage.hidden = false;
                textInput?.focus();
                return;
            }

            isSending = true;
            sendButton.disabled = true;
            errorMessage.hidden = true;

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    credentials: "same-origin",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json"
                    }
                });

                const contentType =
                    response.headers.get("content-type") || "";

                if (!contentType.includes("application/json")) {
                    throw new Error(
                        "Server tidak mengembalikan JSON. Coba login ulang."
                    );
                }

                const result = await response.json();

                if (!response.ok || !result.success) {
                    let message = "Pesan gagal dikirim.";

                    if (result.errors?.text) {
                        message = result.errors.text
                            .map(error => error.message)
                            .join(" ");
                    } else if (result.errors) {
                        message = Object.values(result.errors)
                            .flat()
                            .map(error => error.message)
                            .filter(Boolean)
                            .join(" ") || message;
                    }

                    throw new Error(message);
                }

                // Pesan berhasil disimpan di database
                form.reset();
                textInput.focus();

                // Minta polling AJAX memperbarui tampilan
                window.dispatchEvent(new Event("pjchat:refresh"));

            } catch (error) {
                errorMessage.textContent =
                    error.message || "Pesan gagal dikirim. Coba lagi.";
                errorMessage.hidden = false;

                console.error("Gagal mengirim pesan:", error);
            } finally {
                isSending = false;
                sendButton.disabled = false;
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initAjaxSend);
    } else {
        initAjaxSend();
    }
})();


/* ==========================================
   AJAX SIDEBAR - ALL, UNREAD, INBOX
   ========================================== */

(() => {
    function initSidebarPolling() {
        const sidebar = document.querySelector(".pjchat-sidebar");

        if (!sidebar || !sidebar.dataset.sidebarUrl) {
            return;
        }

        let isFetching = false;

        async function refreshSidebar() {
            if (isFetching || document.hidden) return;

            isFetching = true;

            try {
                // Ikuti Search dan filter yang sedang aktif
                const url = new URL(
                    sidebar.dataset.sidebarUrl,
                    window.location.href
                );

                const currentParams = new URLSearchParams(
                    window.location.search
                );

                url.searchParams.set(
                    "q",
                    currentParams.get("q") || ""
                );

                url.searchParams.set(
                    "filter",
                    currentParams.get("filter") || "all"
                );

                const activeConversation =
                    sidebar.dataset.activeConversation;

                if (activeConversation) {
                    url.searchParams.set(
                        "active",
                        activeConversation
                    );
                }

                // Ambil sidebar terbaru dari Django
                const response = await fetch(url.toString(), {
                    method: "GET",
                    credentials: "same-origin",
                    cache: "no-store",
                    headers: {
                        "Accept": "application/json"
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                if (typeof data.html !== "string") {
                    return;
                }

                // Baca HTML terbaru, tanpa reload halaman
                const parser = new DOMParser();
                const documentBaru = parser.parseFromString(
                    data.html,
                    "text/html"
                );

                const sidebarBaru = documentBaru.querySelector(
                    ".pjchat-sidebar"
                );

                if (!sidebarBaru) return;

                // Update angka All dan Unread
                const angkaLama = sidebar.querySelectorAll(
                    ".pjchat-filter-count"
                );

                const angkaBaru = sidebarBaru.querySelectorAll(
                    ".pjchat-filter-count"
                );

                angkaLama.forEach((angka, index) => {
                    if (angkaBaru[index]) {
                        angka.textContent =
                            angkaBaru[index].textContent.trim();
                    }
                });

                // Update daftar percakapan
                const listLama = sidebar.querySelector(
                    ".pjchat-sidebar-list"
                );

                const listBaru = sidebarBaru.querySelector(
                    ".pjchat-sidebar-list"
                );

                if (!listLama || !listBaru) return;

                // Jangan render ulang kalau tidak ada perubahan
                if (listLama.innerHTML !== listBaru.innerHTML) {
                    const posisiScroll = listLama.scrollTop;

                    listLama.innerHTML = listBaru.innerHTML;

                    // Pertahankan posisi scroll sidebar
                    listLama.scrollTop = posisiScroll;
                }

                // Input Search sengaja tidak diganti.
                // Jadi teks yang sedang diketik tidak hilang.

            } catch (error) {
                console.warn(
                    "Gagal memperbarui sidebar Chat:",
                    error
                );
            } finally {
                isFetching = false;
            }
        }

        // Update saat halaman pertama dibuka
        refreshSidebar();

        // Periksa perubahan setiap 4 detik
        setInterval(refreshSidebar, 4000);

        // Perbarui saat tab kembali aktif
        document.addEventListener(
            "visibilitychange",
            () => {
                if (!document.hidden) {
                    refreshSidebar();
                }
            }
        );

        // Perbarui langsung setelah kirim AJAX
        window.addEventListener(
            "pjchat:refresh",
            refreshSidebar
        );
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initSidebarPolling
        );
    } else {
        initSidebarPolling();
    }
})();


/* ==========================================
   AJAX: EDIT DAN HAPUS PESAN TANPA RELOAD
   ========================================== */

(() => {
    function initAjaxEditDelete() {
        const messagesArea = document.getElementById("pjchat-messages");
        const editForm = document.getElementById("pjchat-edit-form");
        const deleteForm = document.getElementById("pjchat-delete-form");
        const editDialog = document.getElementById("pjchat-edit-dialog");
        const deleteDialog = document.getElementById("pjchat-delete-dialog");
        const editError = document.getElementById("pjchat-edit-error");

        if (
            !messagesArea ||
            !editForm ||
            !deleteForm ||
            !editDialog ||
            !deleteDialog ||
            !editError
        ) {
            return;
        }

        let editing = false;
        let deleting = false;

        // Cari bubble berdasarkan ID pesan
        function findMessage(messageId) {
            return Array.from(
                messagesArea.querySelectorAll(
                    ".pjchat-message[data-message-id]"
                )
            ).find(element =>
                element.dataset.messageId === String(messageId)
            );
        }

        // Ambil pesan error dari respons Django
        function getErrorMessage(data, fallback) {
            if (data?.errors) {
                const errors = Object.values(data.errors)
                    .flat()
                    .map(error => error.message)
                    .filter(Boolean);

                if (errors.length) {
                    return errors.join(" ");
                }
            }

            return data?.error || fallback;
        }

        // Kirim form menggunakan AJAX
        async function submitJson(form, formData) {
            const response = await fetch(form.action, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                }
            });

            if (response.status === 403) {
            throw new Error(
                "Akses ditolak. Kamu tidak memiliki izin."
            );
        }

            const contentType =
                response.headers.get("content-type") || "";

            if (!contentType.includes("application/json")) {
                throw new Error(
                    "Server tidak mengembalikan JSON. Periksa sesi login."
                );
            }

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    getErrorMessage(data, "Operasi pesan gagal.")
                );
            }

            return data;
        }

        // Beri tahu polling supaya mengambil pesan terbaru
        function refreshChat() {
            window.dispatchEvent(
                new Event("pjchat:refresh")
            );
        }

        // ===================================
        // AJAX EDIT PESAN
        // ===================================

        editForm.addEventListener("submit", async event => {
            event.preventDefault();

            if (editing) return;

            const input = editForm.querySelector(
                'textarea[name="text"]'
            );

            if (!input || !input.value.trim()) {
                editError.textContent =
                    "Pesan tidak boleh kosong.";

                input?.focus();
                return;
            }

            editing = true;

            const submitButton = editForm.querySelector(
                'button[type="submit"]'
            );

            if (submitButton) {
                submitButton.disabled = true;
            }

            editError.textContent = "";

            try {
                // FormData sudah menyertakan CSRF token
                const result = await submitJson(
                    editForm,
                    new FormData(editForm)
                );

                // Cari pesan yang baru diedit
                const message = findMessage(result.message.id);

                const textElement = message?.querySelector(
                    ".pjchat-message-text"
                );

                // Langsung ubah teks tanpa reload halaman
                if (textElement) {
                    textElement.textContent = result.message.text;
                }

                // Tutup popup Edit
                editDialog.close();

                // Sinkronkan dengan database
                refreshChat();

            } catch (error) {
                editError.textContent =
                    error.message || "Gagal mengedit pesan.";

            } finally {
                editing = false;

                if (submitButton) {
                    submitButton.disabled = false;
                }
            }
        });

        // ===================================
        // AJAX HAPUS PESAN
        // ===================================

        deleteForm.addEventListener("submit", async event => {
            event.preventDefault();

            if (deleting) return;

            // Tombol yang ditekan:
            // "me" atau "everyone"
            const submitter = event.submitter;
            const scope = submitter?.value;

            if (scope !== "me" && scope !== "everyone") {
                return;
            }

            const formData = new FormData(deleteForm);
            formData.set("scope", scope);

            deleting = true;

            const buttons = deleteForm.querySelectorAll(
                'button[type="submit"]'
            );

            buttons.forEach(button => {
                button.disabled = true;
            });

            try {
                const result = await submitJson(
                    deleteForm,
                    formData
                );

                const message = findMessage(result.message_id);

                // ============================
                // HAPUS UNTUK SAYA
                // ============================

                if (result.scope === "me") {
                    // Hilangkan bubble hanya dari layar kita
                    message?.remove();

                    // Jika tidak ada pesan tersisa
                    if (
                        !messagesArea.querySelector(".pjchat-message")
                    ) {
                        const emptyNotice =
                            document.createElement("div");

                        emptyNotice.className =
                            "pjchat-no-messages";

                        emptyNotice.textContent =
                            "Belum ada pesan. Mulai percakapan di bawah.";

                        messagesArea.appendChild(emptyNotice);
                    }
                }

                // ============================
                // HAPUS UNTUK SEMUA ORANG
                // ============================

                else if (
                    result.scope === "everyone" &&
                    message
                ) {
                    const bubble = message.querySelector(
                        ".pjchat-bubble"
                    );

                    const textElement = bubble?.querySelector(
                        ".pjchat-message-text"
                    );

                    if (bubble && textElement) {
                        bubble.classList.add(
                            "pjchat-bubble--deleted"
                        );

                        // Ganti isi bubble dengan keterangan
                        const deletedText =
                            document.createElement("div");

                        deletedText.className =
                            "pjchat-deleted-text";

                        const symbol =
                            document.createElement("span");

                        symbol.setAttribute(
                            "aria-hidden",
                            "true"
                        );

                        symbol.textContent = "⊘";

                        const label =
                            document.createElement("span");

                        label.textContent =
                            "Kamu menghapus pesan ini";

                        deletedText.append(symbol, label);

                        textElement.replaceWith(deletedText);
                    }

                    // Hilangkan opsi Edit
                    message.querySelector(
                        ".js-pjchat-edit"
                    )?.remove();

                    // Pesan tidak boleh dihapus
                    // untuk semua orang berulang kali
                    const deleteButton = message.querySelector(
                        ".js-pjchat-delete"
                    );

                    if (deleteButton) {
                        deleteButton.dataset.ownMessage = "false";
                    }
                }

                // Tutup popup Hapus
                deleteDialog.close();

                // Perbarui data Chat
                refreshChat();

            } catch (error) {
                // Tampilkan error di popup Hapus
                let errorElement = deleteForm.querySelector(
                    ".pjchat-delete-error"
                );

                if (!errorElement) {
                    errorElement =
                        document.createElement("p");

                    errorElement.className =
                        "pjchat-form-error pjchat-delete-error";

                    errorElement.setAttribute(
                        "role",
                        "alert"
                    );

                    deleteForm.querySelector(
                        ".pjchat-delete-choices"
                    )?.insertAdjacentElement(
                        "afterend",
                        errorElement
                    );
                }

                errorElement.textContent =
                    error.message || "Gagal menghapus pesan.";

            } finally {
                deleting = false;

                buttons.forEach(button => {
                    button.disabled = false;
                });
            }
        });

        // Hapus pesan error lama saat popup ditutup
        deleteDialog.addEventListener("close", () => {
            const errorElement = deleteForm.querySelector(
                ".pjchat-delete-error"
            );

            if (errorElement) {
                errorElement.textContent = "";
            }
        });
    }

    // Jalankan setelah HTML siap
    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initAjaxEditDelete
        );
    } else {
        initAjaxEditDelete();
    }
})();
