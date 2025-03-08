// Client-side functionality for article detail page

document.addEventListener('DOMContentLoaded', function() {
    // Get article ID from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const articleId = urlParams.get('id');
    
    if (!articleId) {
        window.location.href = '/';
        return;
    }
    
    // Show loading indicator
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'text-center my-5';
    loadingIndicator.innerHTML = `
        <div class="spinner-border" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">Loading article details...</p>
    `;
    document.querySelector('.card-body').prepend(loadingIndicator);
    
    // Fetch article details from Firebase Function
    fetch(`/api/article/${articleId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Article not found');
            }
            return response.json();
        })
        .then(article => {
            // Remove loading indicator
            loadingIndicator.remove();
            
            // Display article details
            displayArticleDetails(article);
        })
        .catch(error => {
            console.error('Error loading article:', error);
            loadingIndicator.innerHTML = `
                <div class="alert alert-danger">
                    <h4>Error loading article</h4>
                    <p>${error.message}</p>
                    <a href="/" class="btn btn-primary">Back to Home</a>
                </div>
            `;
        });
});

function displayArticleDetails(article) {
    // Set document title
    document.title = article.title + ' - MediaMon';
    
    // Set UI language based on article language
    const isIndonesian = article.language === 'id';
    
    // Update breadcrumb
    document.getElementById('breadcrumbLabel').textContent = isIndonesian ? 'Detail Artikel' : 'Article Detail';
    
    // Update article details
    document.getElementById('articleSource').textContent = article.source;
    document.getElementById('articleTitle').textContent = article.title;
    document.getElementById('articleDate').textContent = 
        (isIndonesian ? 'Diterbitkan pada ' : 'Published on ') + 
        new Date(article.published).toLocaleString();
    
    // Update sentiment badge
    const sentimentBadge = document.getElementById('articleSentiment');
    sentimentBadge.textContent = `${article.sentiment_label} (${article.sentiment_score})`;
    sentimentBadge.className = `badge bg-${article.sentiment_color} me-2`;
    
    // Update language badge
    document.getElementById('articleLanguage').textContent = 
        isIndonesian ? 'Bahasa Indonesia' : 'English';
    
    // Update summary
    document.getElementById('summaryLabel').textContent = isIndonesian ? 'Ringkasan:' : 'Summary:';
    document.getElementById('articleSummary').innerHTML = article.summary;
    
    // Update sentiment analysis
    document.getElementById('sentimentLabel').textContent = 
        isIndonesian ? 'Analisis Sentimen:' : 'Sentiment Analysis:';
    
    const sentimentBar = document.getElementById('sentimentBar');
    sentimentBar.style.width = `${(article.sentiment_score + 1) / 2 * 100}%`;
    sentimentBar.className = `progress-bar bg-${article.sentiment_color}`;
    sentimentBar.textContent = article.sentiment_score;
    sentimentBar.setAttribute('aria-valuenow', article.sentiment_score);
    
    // Update sentiment labels
    document.getElementById('negativeLabel').textContent = 
        `${isIndonesian ? 'Sangat Negatif' : 'Very Negative'} (-1.0)`;
    document.getElementById('neutralLabel').textContent = 
        `${isIndonesian ? 'Netral' : 'Neutral'} (0.0)`;
    document.getElementById('positiveLabel').textContent = 
        `${isIndonesian ? 'Sangat Positif' : 'Very Positive'} (1.0)`;
    
    // Update action buttons
    document.getElementById('articleLink').textContent = 
        isIndonesian ? 'Baca Artikel Lengkap' : 'Read Full Article';
    document.getElementById('articleLink').href = article.link;
    
    document.getElementById('backButton').textContent = 
        isIndonesian ? 'Kembali ke Daftar' : 'Back to List';
}
