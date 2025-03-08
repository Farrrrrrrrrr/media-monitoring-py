// Client-side functionality for MediaMon application

document.addEventListener('DOMContentLoaded', function() {
    // Automatically refresh the dashboard every 5 minutes
    const AUTO_REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes in milliseconds
    
    // Only set up auto-refresh on the home page
    if (window.location.pathname === '/') {
        setTimeout(function() {
            window.location.reload();
        }, AUTO_REFRESH_INTERVAL);
    }
    
    // Add animation to the sentiment score badges
    const badges = document.querySelectorAll('.badge');
    badges.forEach(badge => {
        badge.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
        });
        badge.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Language filter functionality
    const filterButtons = document.querySelectorAll('.filter-btn');
    const articles = document.querySelectorAll('.article-list .list-group-item');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const language = this.getAttribute('data-language');
            
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter articles
            filterArticles();
        });
    });
    
    // Source type checkboxes
    const sourceTypeCheckboxes = document.querySelectorAll('.source-type-checkbox');
    sourceTypeCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            filterArticles();
        });
    });
    
    // Function to filter articles by both language and source type
    function filterArticles() {
        const selectedLanguage = document.querySelector('.filter-btn.active').getAttribute('data-language');
        
        // Get selected source types
        const selectedSources = Array.from(document.querySelectorAll('.source-type-checkbox:checked'))
            .map(checkbox => checkbox.value);
            
        // Filter articles
        const articles = document.querySelectorAll('.article-list .list-group-item');
        articles.forEach(article => {
            const articleLanguage = article.getAttribute('data-language');
            const articleSource = article.getAttribute('data-source');
            
            const languageMatch = selectedLanguage === 'all' || articleLanguage === selectedLanguage;
            const sourceMatch = selectedSources.includes(articleSource);
            
            if (languageMatch && sourceMatch) {
                article.style.display = '';
            } else {
                article.style.display = 'none';
            }
        });
    }
});
