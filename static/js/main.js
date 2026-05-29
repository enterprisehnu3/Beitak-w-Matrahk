/**
 * Global App Logic
 * Handles PWA registration and general UI enhancements
 */

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker Registered'))
            .catch(err => console.log('Service Worker Failed', err));
    });
}

// Global UI consistency (e.g., active links, hover effects)
document.addEventListener('DOMContentLoaded', function() {
    // Star Rating Logic
    const starContainer = document.getElementById('star-rating-container');
    if (starContainer) {
        const labels = starContainer.querySelectorAll('.star-label');

        function updateStars(selectedValue) {
            labels.forEach(label => {
                const val = parseInt(label.dataset.value);
                if (val <= selectedValue) {
                    label.classList.remove('text-gray-300');
                    label.classList.add('text-yellow-500');
                } else {
                    label.classList.remove('text-yellow-500');
                    label.classList.add('text-gray-300');
                }
            });
        }

        labels.forEach(label => {
            label.addEventListener('click', function() {
                updateStars(parseInt(this.dataset.value));
            });

            label.addEventListener('mouseenter', function() {
                updateStars(parseInt(this.dataset.value));
            });
        });

        starContainer.addEventListener('mouseleave', function() {
            const checked = starContainer.querySelector('input[name="rating"]:checked');
            if (checked) {
                updateStars(parseInt(checked.value));
            } else {
                labels.forEach(l => {
                    l.classList.remove('text-yellow-500');
                    l.classList.add('text-gray-300');
                });
            }
        });
    }
});
