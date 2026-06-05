/**
 * Alerts & Notifications Logic
 * Handles SweetAlert2 toasts and confirmation dialogs
 */

document.addEventListener("DOMContentLoaded", function () {
    const flashItems = document.querySelectorAll(".flash-item");
    flashItems.forEach((item, index) => {
        const category = item.getAttribute("data-category");
        const message = item.getAttribute("data-message");

        setTimeout(() => {
            Swal.mixin({
                toast: true,
                position: "top-end",
                showConfirmButton: false,
                timer: 4000,
                timerProgressBar: true,
                showCloseButton: true,
                customClass: { popup: "colored-toast" }
            }).fire({
                icon: category === "success" ? "success" :
                    category === "danger" ? "error" :
                        category === "warning" ? "warning" : "info",
                title: message
            });
        }, index * 500);
    });
});

/**
 * Replaces native confirm() with a styled SweetAlert2 dialog
 * @param {HTMLFormElement|HTMLButtonElement} targetEl - The form or button that triggered the confirm
 * @param {string} title - Modal title
 * @param {string} text - Modal description
 * @param {string} icon - SweetAlert2 icon type
 */
function swalConfirm(targetEl, title, text, icon) {
    if (typeof event !== "undefined") event.preventDefault();
    let formEl = targetEl;
    let clickedButton = null;
    if (targetEl && (targetEl.tagName === 'BUTTON' || targetEl.tagName === 'INPUT' || targetEl.tagName === 'A')) {
        clickedButton = targetEl;
        formEl = targetEl.form;
    }
    Swal.fire({
        title: title || "هل أنت متأكد؟",
        text: text || "",
        icon: icon || "warning",
        showCancelButton: true,
        confirmButtonColor: "#2563eb",
        cancelButtonColor: "#6b7280",
        confirmButtonText: '<i class="fa-solid fa-check ml-1"></i> نعم، متأكد',
        cancelButtonText: '<i class="fa-solid fa-xmark ml-1"></i> إلغاء',
        reverseButtons: true,
        customClass: {
            popup: "swal-rtl",
            confirmButton: "swal2-confirm-btn",
            cancelButton: "swal2-cancel-btn"
        }
    }).then((result) => {
        if (result.isConfirmed && formEl) {
            if (clickedButton && clickedButton.name) {
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = clickedButton.name;
                hiddenInput.value = clickedButton.value;
                formEl.appendChild(hiddenInput);
            }
            formEl.submit();
        }
    });
    return false;
}
