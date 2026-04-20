// AW Client Portal — Common JS

function showLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'flex';
    }
}

function hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

// Auto-dismiss flash messages after 4 seconds
document.addEventListener('DOMContentLoaded', function() {
    const loader = document.getElementById('loader');
    if (loader) loader.style.display = 'none';

    const messages = document.getElementById('flash-messages');
    if (messages) {
        setTimeout(function() {
            messages.style.transition = 'opacity 0.3s ease';
            messages.style.opacity = '0';
            setTimeout(function() { messages.remove(); }, 300);
        }, 4000);
    }
});

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(amount);
}
