/**
 * Favorites Management
 * Handles adding/removing listings from user favorites
 */

async function toggleFavorite(listingId, btnElement = null) {
    try {
        const resp = await fetch(`/toggle_favorite/${listingId}`, { method: 'POST' });
        const data = await resp.json();
        const btn = btnElement || document.getElementById(`fav-btn-${listingId}`) || document.getElementById('fav-btn');
        if (!btn) return;
        
        const icon = btn.querySelector('i');
        if (data.status === 'added') {
            btn.classList.add('text-red-500', 'bg-red-50');
            btn.classList.remove('text-gray-400', 'bg-white');
            if (icon) icon.classList.replace('fa-regular', 'fa-solid');
        } else {
            btn.classList.remove('text-red-500', 'bg-red-50');
            btn.classList.add('text-gray-400', 'bg-white');
            if (icon) icon.classList.replace('fa-solid', 'fa-regular');
        }
    } catch (err) {
        console.error('Error toggling favorite:', err);
    }
}

/**
 * Removes a favorite card from the UI with animation
 * Used in favorites_page.html
 */
function removeCard(listingId) {
    const card = document.getElementById(`fav-card-${listingId}`);
    if (card) {
        card.style.opacity = '0';
        card.style.transform = 'scale(0.95)';
        setTimeout(() => {
            card.remove();
            if (document.querySelectorAll('[id^="fav-card-"]').length === 0) {
                location.reload(); // Refresh to show empty state if last card removed
            }
        }, 300);
    }
}
