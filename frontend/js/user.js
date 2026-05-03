function switchTab(tabId) {
    // Highlight active sidebar
    document.querySelectorAll('.sidebar-link').forEach(el => {
        el.classList.remove('active');
        if (el.dataset.target === tabId) {
            el.classList.add('active');
        }
    });

    // Show selected tab
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
    });

    const targetTab = document.getElementById('tab-' + tabId);
    if (targetTab) {
        targetTab.classList.add('active');
    }
}

// Check authentication on load
document.addEventListener('DOMContentLoaded', () => {
    const user = checkAuth();
    if (user) {
        const welcomeTitle = document.querySelector('#tab-dashboard h1');
        if (welcomeTitle) {
            welcomeTitle.textContent = `Welcome ${user.name}`;
        }
    }
});
