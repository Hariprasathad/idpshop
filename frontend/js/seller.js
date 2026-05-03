function switchTab(tabId) {
    // Update active states for sidebar items
    document.querySelectorAll('.sidebar-item').forEach(el => {
        if(el.dataset.target === tabId) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    // Show selected tab content
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
    if (user && user.role === 'seller') {
        const welcomeHeader = document.querySelector('.welcome-header h1');
        if (welcomeHeader) {
            welcomeHeader.textContent = `Welcome back, ${user.name}!`;
        }
    } else if (user) {
        // Redirect if not a seller
        window.location.href = '../user/dashboard.html';
    }
});
function updateOrderStatus(btn) {
    const statusCell = btn.parentElement.previousElementSibling;
    const currentStatus = statusCell.innerText.trim();

    if (currentStatus === 'Processing') {
        statusCell.innerHTML = '<span class="status-badge status-info">Shipped</span>';
        btn.innerHTML = '<i class="fa-solid fa-check-double"></i> Mark Delivered';
        btn.className = 'btn btn-sm btn-primary';
    } else if (currentStatus === 'Shipped') {
        statusCell.innerHTML = '<span class="status-badge status-success">Delivered</span>';
        btn.parentElement.innerHTML = '<span style="color: var(--text-muted); font-size: 0.85rem; font-weight: 500;"><i class="fa-solid fa-check"></i> Completed</span>';
    }
}
