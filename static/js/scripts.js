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
            articles.forEach(article => {
                const articleLanguage = article.getAttribute('data-language');
                
                if (language === 'all' || language === articleLanguage) {
                    article.style.display = '';
                } else {
                    article.style.display = 'none';
                }
            });
        });
    });
});
