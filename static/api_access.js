/**
 * API Documentation Helper
 * Provides utility functions for API documentation pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add API status indicator
    const apiStatusElement = document.getElementById('api-status');
    if (apiStatusElement) {
        checkApiStatus(apiStatusElement);
    }
    
    // Handle API key request form
    const apiKeyForm = document.getElementById('api-key-request-form');
    if (apiKeyForm) {
        apiKeyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitApiKeyRequest();
        });
    }
    
    // Highlight current documentation section
    highlightCurrentSection();
});

/**
 * Check if the API is operational
 * @param {HTMLElement} statusElement - Element to update with status
 */
function checkApiStatus(statusElement) {
    fetch('/api/v1/health')
        .then(response => {
            if (response.ok) {
                statusElement.innerHTML = '<span class="badge bg-success">Operational</span>';
            } else {
                statusElement.innerHTML = '<span class="badge bg-warning">Degraded</span>';
            }
        })
        .catch(() => {
            statusElement.innerHTML = '<span class="badge bg-danger">Offline</span>';
        });
}

/**
 * Highlight the current section in the documentation
 */
function highlightCurrentSection() {
    const path = window.location.pathname;
    const navLinks = document.querySelectorAll('.api-nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
            link.setAttribute('aria-current', 'page');
        }
    });
}

/**
 * Handle API key request form submission
 */
function submitApiKeyRequest() {
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const purposeInput = document.getElementById('purpose');
    
    const requestData = {
        name: nameInput.value,
        email: emailInput.value,
        purpose: purposeInput.value
    };
    
    const resultElement = document.getElementById('api-request-result');
    resultElement.innerHTML = '<div class="alert alert-info">Processing your request...</div>';
    
    // This would normally submit to a backend endpoint
    // For now, just show a success message
    setTimeout(() => {
        resultElement.innerHTML = '<div class="alert alert-success">' +
            '<strong>Request received!</strong> We will contact you soon with your API credentials.' +
            '</div>';
    }, 1500);
}
