/**
 * Authentication & Security Logic
 */

/**
 * Toggles password visibility between 'password' and 'text'
 */
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const eyeIcon = document.getElementById('eye-icon');
    if (!passwordInput || !eyeIcon) return;

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeIcon.classList.remove('fa-eye-slash');
        eyeIcon.classList.add('fa-eye');
    } else {
        passwordInput.type = 'password';
        eyeIcon.classList.remove('fa-eye');
        eyeIcon.classList.add('fa-eye-slash');
    }
}

// Password matching validation
document.addEventListener('DOMContentLoaded', function() {
    const password = document.getElementById('password');
    const confirm = document.getElementById('confirm_password');
    const errorMsg = document.getElementById('password-error');
    const form = document.querySelector('form');

    if (password && confirm) {
        const validatePasswords = () => {
            if (confirm.value === '') {
                errorMsg.classList.add('hidden');
                confirm.classList.remove('border-red-500');
                return true;
            }
            if (password.value !== confirm.value) {
                errorMsg.classList.remove('hidden');
                confirm.classList.add('border-red-500');
                return false;
            } else {
                errorMsg.classList.add('hidden');
                confirm.classList.remove('border-red-500');
                confirm.classList.add('border-green-500');
                return true;
            }
        };

        password.addEventListener('input', validatePasswords);
        confirm.addEventListener('input', validatePasswords);

        // Dynamic Password Requirements Checklist
        const reqLength = document.getElementById('req-length');
        if (reqLength) { // Only run if checklist exists (e.g. register page)
            const updateReq = (id, isValid) => {
                const el = document.getElementById(id);
                if (!el) return;
                const icon = el.querySelector('i');
                if (isValid) {
                    el.classList.add('text-green-600');
                    el.classList.remove('text-gray-500');
                    icon.className = 'fa-solid fa-circle-check text-green-500 text-[10px]';
                } else {
                    el.classList.remove('text-green-600');
                    el.classList.add('text-gray-500');
                    icon.className = 'fa-regular fa-circle text-gray-300 text-[10px]';
                }
            };

            const validateRequirements = () => {
                const val = password.value;
                updateReq('req-length', val.length >= 8);
                updateReq('req-letter', /[a-zA-Z]/.test(val));
                updateReq('req-number', /[0-9]/.test(val));
                updateReq('req-special', /[!@#$%^&*(),.?":{}|<>]/.test(val));
            };

            password.addEventListener('input', validateRequirements);
            // Run once on load in case browser autofills
            validateRequirements();
        }

        if (form) {
            form.addEventListener('submit', function(e) {
                const val = password.value;
                const isStrong = val.length >= 8 && 
                               /[a-zA-Z]/.test(val) && 
                               /[0-9]/.test(val) && 
                               /[!@#$%^&*(),.?":{}|<>]/.test(val);
                               
                if (!validatePasswords()) {
                    e.preventDefault();
                    Swal.fire('خطأ', 'كلمات المرور غير متطابقة!', 'error');
                } else if (reqLength && !isStrong) { 
                    e.preventDefault();
                    Swal.fire('خطأ', 'يرجى استيفاء جميع شروط كلمة المرور القوية', 'error');
                    password.focus();
                }
            });
        }
    }
});
