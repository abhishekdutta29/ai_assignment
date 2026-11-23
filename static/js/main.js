// KnowledgeLens - Core Client Main Script

document.addEventListener('DOMContentLoaded', () => {
    // Theme toggle
    const themeBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    const htmlElem = document.documentElement;

    const savedTheme = localStorage.getItem('kl_theme') || 'dark';
    htmlElem.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const current = htmlElem.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            htmlElem.setAttribute('data-theme', next);
            localStorage.setItem('kl_theme', next);
            updateThemeIcon(next);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeIcon) return;
        if (theme === 'dark') {
            themeIcon.className = 'fa-solid fa-sun';
        } else {
            themeIcon.className = 'fa-solid fa-moon';
        }
    }

    // Global toast system
    window.showToast = function(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    };
});
