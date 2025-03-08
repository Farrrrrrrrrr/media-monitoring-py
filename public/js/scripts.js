// Client-side functionality for MediaMon application using Firebase Functions

document.addEventListener('DOMContentLoaded', function() {
    // Load default articles on page load
    loadArticles();
    
    // Set up event handlers
    setupEventHandlers();
});

function setupEventHandlers() {
    // Search button click event
    document.getElementById('searchButton').addEventListener('click', function() {
        const searchQuery = document.getElementById('searchInput').value.trim();
        if (searchQuery) {
            searchArticles(searchQuery);
        }
    });
    
    // Search input enter key event
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const searchQuery = this.value.trim();
            if (searchQuery) {
                searchArticles(searchQuery);
            }
        }
    });
    
    // Clear button event
    document.getElementById('clearButton').addEventListener('click', function() {
        document.getElementById('searchInput').value = '';
        document.getElementById('searchNotification').style.display = 'none';
        this.style.display = 'none';
        document.getElementById('resultsTitle').textContent = 'Artikel Terbaru / Latest Articles';
        loadArticles();
    });
    
    // Topic tags click event
    document.querySelectorAll('.topic-tag').forEach(tag => {
        tag.addEventListener('click', function(e) {
            e.preventDefault();
            const topic = this.getAttribute('data-topic');
            document.getElementById('searchInput').value = topic;
            searchArticles(topic);
        });
    });
    
    // Language filter functionality
    const filterButtons = document.querySelectorAll('.filter-btn');
    
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
    
    // Source type filter functionality
    const sourceTypeCheckboxes = document.querySelectorAll('.source-type-checkbox');
    
    sourceTypeCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            filterArticles();
        });
    });
}

function searchArticles(query) {
    // Update UI to show search is active
    document.getElementById('searchNotification').style.display = 'block';
    document.getElementById('searchTerm').textContent = query;
    document.getElementById('clearButton').style.display = 'inline-block';
    document.getElementById('resultsTitle').textContent = 'Hasil Pencarian / Search Results';
    
    // Load articles with the search query
    loadArticles(query);
}

function loadArticles(query = null) {
    // Show loading indicator
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('noArticlesMessage').style.display = 'none';
    document.getElementById('articlesList').innerHTML = '';
    
    // Construct API URL
    const apiUrl = `/api/articles${query ? `?query=${encodeURIComponent(query)}` : ''}`;
    
    // Fetch articles from Firebase Function
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator
            document.getElementById('loadingIndicator').style.display = 'none';
            
            // Check if we have articles
            const articles = data.articles || [];
            if (articles.length === 0) {
                document.getElementById('noArticlesMessage').style.display = 'block';
                updateSentimentCounts([]);
                return;
            }
            
            // Render the articles
            renderArticles(articles);
        })
        .catch(error => {
            console.error('Error fetching articles:', error);
            document.getElementById('loadingIndicator').style.display = 'none';
            document.getElementById('noArticlesMessage').style.display = 'block';
            updateSentimentCounts([]);
        });
}

function renderArticles(articles) {
    // Clear existing articles
    const articlesContainer = document.getElementById('articlesList');
    articlesContainer.innerHTML = '';
    
    // Update sentiment counts
    updateSentimentCounts(articles);
    
    // Render each article
    articles.forEach(article => {
        const publishedDate = new Date(article.published);
        const formattedDate = publishedDate.toLocaleString();
        
        const articleElement = document.createElement('a');
        articleElement.href = `article.html?id=${article.id}`;
        articleElement.className = 'list-group-item list-group-item-action';
        
        if (article.type !== 'news') {
            articleElement.classList.add('social-post', article.type);
        }
        
        articleElement.setAttribute('data-language', article.language);
        articleElement.setAttribute('data-source', article.type);
        
        let sourceIcon = '';
        if (article.type === 'twitter') {
            sourceIcon = '<i class="fab fa-twitter text-info me-2"></i>';
        } else if (article.type === 'facebook') {
            sourceIcon = '<i class="fab fa-facebook text-primary me-2"></i>';
        } else if (article.type === 'instagram') {
            sourceIcon = '<i class="fab fa-instagram text-danger me-2"></i>';
        }
        
        articleElement.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h5 class="mb-1">${sourceIcon}${article.title}</h5>
                <span class="badge bg-${article.sentiment_color}">
                    ${article.sentiment_label} (${article.sentiment_score})
                </span>
            </div>
            <p class="mb-1 text-truncate">${article.summary.replace(/<\/?[^>]+(>|$)/g, "")}</p>
            <small class="text-muted">
                Source: ${article.source} | 
                Published: ${formattedDate}
                <span class="badge bg-light text-dark">${article.language === 'id' ? "Bahasa Indonesia" : "English"}</span>
            </small>
        `;
        
        articlesContainer.appendChild(articleElement);
    });
    
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
}

function updateSentimentCounts(articles) {
    // Count positive, neutral, and negative articles
    const positiveCount = articles.filter(a => a.sentiment_score > 0).length;
    const neutralCount = articles.filter(a => a.sentiment_score === 0).length;
    const negativeCount = articles.filter(a => a.sentiment_score < 0).length;
    
    // Update the UI
    document.getElementById('positiveCount').textContent = positiveCount;
    document.getElementById('neutralCount').textContent = neutralCount;
    document.getElementById('negativeCount').textContent = negativeCount;
}

// Function to filter articles by both language and source type
function filterArticles() {
    const selectedLanguage = document.querySelector('.filter-btn.active').getAttribute('data-language');
    
    // Get selected source types
    const selectedSources = [];
    document.querySelectorAll('.source-type-checkbox:checked').forEach(checkbox => {
        selectedSources.push(checkbox.value);
    });
    
    // Filter articles
    const articles = document.querySelectorAll('.article-list .list-group-item');
    let visibleCount = 0;
    
    articles.forEach(article => {
        const articleLanguage = article.getAttribute('data-language');
        const articleSource = article.getAttribute('data-source');
        
        const languageMatch = selectedLanguage === 'all' || articleLanguage === selectedLanguage;
        const sourceMatch = selectedSources.includes(articleSource);
        
        if (languageMatch && sourceMatch) {
            article.style.display = '';
            visibleCount++;
        } else {
            article.style.display = 'none';
        }
    });
    
    // Show/hide no results message
    document.getElementById('noArticlesMessage').style.display = visibleCount === 0 ? 'block' : 'none';
}
