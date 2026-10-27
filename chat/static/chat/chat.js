
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
