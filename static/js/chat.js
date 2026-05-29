/**
 * Chat Logic
 * Handles real-time polling, auto-scroll, and message interactions
 */

document.addEventListener('DOMContentLoaded', function () {
    const chatbox = document.getElementById('chatbox');
    const chatForm = document.getElementById('chatForm');
    const textarea = document.querySelector('textarea[name="content"]');

    // Scroll to bottom initially
    if (chatbox) chatbox.scrollTop = chatbox.scrollHeight;

    // Submit on Enter
    if (textarea) {
        textarea.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const fileInput = document.getElementById('chat-file');
                if (this.value.trim() !== '' || (fileInput && fileInput.files && fileInput.files.length > 0)) {
                    if (chatForm) chatForm.submit();
                }
            }
        });
    }

    // Polling logic for new messages
    if (chatbox) {
        setInterval(async function() {
            try {
                const response = await fetch(window.location.href);
                if (!response.ok) return;
                const html = await response.text();
                
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                const newMessagesContainer = doc.querySelector('.space-y-4');
                const currentMessagesContainer = document.querySelector('.space-y-4');
                
                if (newMessagesContainer && currentMessagesContainer) {
                    if (newMessagesContainer.innerHTML !== currentMessagesContainer.innerHTML) {
                        currentMessagesContainer.innerHTML = newMessagesContainer.innerHTML;
                        // Auto scroll to bottom
                        chatbox.scrollTop = chatbox.scrollHeight;
                    }
                }
            } catch (error) {
                console.error('Chat polling failed:', error);
            }
        }, 3000);
    }

    // Close menus when clicking outside
    document.addEventListener('click', function (event) {
        const optionsMenu = document.getElementById('optionsMenu');
        const emojiMenu = document.getElementById('emojiMenu');
        
        if (optionsMenu && !event.target.closest('#optionsMenu') && !event.target.closest('button[onclick*="optionsMenu"]')) {
            optionsMenu.classList.add('hidden');
        }
        if (emojiMenu && !event.target.closest('#emojiMenu') && !event.target.closest('button[onclick*="emojiMenu"]')) {
            emojiMenu.classList.add('hidden');
        }
    });
});

/**
 * Toggles visibility of chat sub-menus (emoji/options)
 * @param {string} menuId 
 */
function toggleMenu(menuId) {
    const menu = document.getElementById(menuId);
    if (!menu) return;
    const isHidden = menu.classList.contains('hidden');

    // Hide both menus first
    const optionsMenu = document.getElementById('optionsMenu');
    const emojiMenu = document.getElementById('emojiMenu');
    if (optionsMenu) optionsMenu.classList.add('hidden');
    if (emojiMenu) emojiMenu.classList.add('hidden');

    // Toggle the target menu
    if (isHidden) {
        menu.classList.remove('hidden');
    }
}
