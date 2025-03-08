from flask import Flask, render_template, request
import feedparser
from textblob import TextBlob
import uuid
import datetime
from urllib.parse import urlparse, quote
import requests
import json
import re
import os
import tweepy
from facebook_scraper import get_posts
import instaloader

app = Flask(__name__)

# In-memory storage for articles (in a real app, you'd use a database)
articles = {}

# Social media API configuration
class SocialMediaConfig:
    # Twitter API credentials
    TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY', '')
    TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET', '')
    TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN', '')
    TWITTER_ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET', '')
    
    # Facebook credentials (for facebook-scraper)
    FACEBOOK_EMAIL = os.environ.get('FACEBOOK_EMAIL', '')
    FACEBOOK_PASSWORD = os.environ.get('FACEBOOK_PASSWORD', '')
    
    # Instagram credentials
    INSTAGRAM_USERNAME = os.environ.get('INSTAGRAM_USERNAME', '')
    INSTAGRAM_PASSWORD = os.environ.get('INSTAGRAM_PASSWORD', '')

    # Social media sources enabled status
    TWITTER_ENABLED = bool(TWITTER_API_KEY and TWITTER_API_SECRET)
    FACEBOOK_ENABLED = bool(FACEBOOK_EMAIL and FACEBOOK_PASSWORD)
    INSTAGRAM_ENABLED = bool(INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD)

def fetch_twitter_posts(search_query=None, count=10):
    """Fetch tweets related to a search query"""
    if not SocialMediaConfig.TWITTER_ENABLED:
        print("Twitter API credentials not configured")
        return []
    
    try:
        # Set up Twitter API client
        auth = tweepy.OAuthHandler(
            SocialMediaConfig.TWITTER_API_KEY, 
            SocialMediaConfig.TWITTER_API_SECRET
        )
        auth.set_access_token(
            SocialMediaConfig.TWITTER_ACCESS_TOKEN, 
            SocialMediaConfig.TWITTER_ACCESS_SECRET
        )
        api = tweepy.API(auth)
        
        # Search for tweets
        tweets = []
        if search_query:
            # Search tweets with query
            search_results = api.search_tweets(q=search_query, count=count, tweet_mode='extended')
            tweets.extend(search_results)
        else:
            # Get home timeline tweets if no query
            home_tweets = api.home_timeline(count=count, tweet_mode='extended')
            tweets.extend(home_tweets)
        
        # Process tweets into our article format
        twitter_articles = []
        for tweet in tweets:
            # Extract text (handling both normal and extended tweets)
            if hasattr(tweet, 'full_text'):
                text = tweet.full_text
            else:
                text = tweet.text
            
            # Skip retweets to avoid duplication
            if hasattr(tweet, 'retweeted_status'):
                continue
                
            # Perform sentiment analysis
            is_indonesian = contains_indonesian_words(text)
            analysis = analyze_sentiment(text, is_indonesian)
            sentiment_score = analysis.sentiment.polarity
            
            sentiment_label = "Positif" if sentiment_score > 0 else "Negatif" if sentiment_score < 0 else "Netral"
            if not is_indonesian:
                sentiment_label = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
            
            article_id = f"twitter_{tweet.id}"
            
            # Create article object
            article = {
                'id': article_id,
                'title': f"@{tweet.user.screen_name}: {text[:50]}...",
                'summary': text,
                'link': f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}",
                'published': tweet.created_at,
                'source': 'Twitter',
                'sentiment_score': round(sentiment_score, 2),
                'sentiment_label': sentiment_label,
                'sentiment_color': get_sentiment_color(sentiment_score),
                'language': 'id' if is_indonesian else 'en',
                'user': tweet.user.screen_name,
                'profile_image': tweet.user.profile_image_url_https,
                'type': 'twitter'
            }
            
            # Store in our articles dict and return list
            articles[article_id] = article
            twitter_articles.append(article)
            
        return twitter_articles
        
    except Exception as e:
        print(f"Error fetching Twitter data: {e}")
        return []

def fetch_facebook_posts(search_query=None, pages=None, count=5):
    """Fetch Facebook posts from specific pages or search"""
    if not SocialMediaConfig.FACEBOOK_ENABLED:
        print("Facebook credentials not configured")
        return []
    
    if pages is None:
        # Default Indonesian news pages to monitor
        pages = ['detikcom', 'kompascom', 'tribunnews']
    
    facebook_articles = []
    
    try:
        # For each page, get recent posts
        for page in pages:
            try:
                # Get posts from the page
                posts = list(get_posts(
                    page, 
                    pages=1,
                    credentials=(SocialMediaConfig.FACEBOOK_EMAIL, SocialMediaConfig.FACEBOOK_PASSWORD),
                    options={"posts_per_page": count}
                ))
                
                # Process posts
                for post in posts:
                    # Skip posts without text
                    if not post.get('text'):
                        continue
                    
                    text = post.get('text')
                    
                    # If search query provided, skip non-matching posts
                    if search_query and search_query.lower() not in text.lower():
                        continue
                    
                    # Perform sentiment analysis
                    is_indonesian = contains_indonesian_words(text)
                    analysis = analyze_sentiment(text, is_indonesian)
                    sentiment_score = analysis.sentiment.polarity
                    
                    sentiment_label = "Positif" if sentiment_score > 0 else "Negatif" if sentiment_score < 0 else "Netral"
                    if not is_indonesian:
                        sentiment_label = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
                    
                    article_id = f"facebook_{post.get('post_id')}"
                    
                    # Get publication date
                    pub_date = post.get('time')
                    if not pub_date:
                        pub_date = datetime.datetime.now()
                    
                    # Create article object
                    article = {
                        'id': article_id,
                        'title': f"Facebook: {text[:50]}...",
                        'summary': text,
                        'link': post.get('post_url'),
                        'published': pub_date,
                        'source': f"Facebook/{page}",
                        'sentiment_score': round(sentiment_score, 2),
                        'sentiment_label': sentiment_label,
                        'sentiment_color': get_sentiment_color(sentiment_score),
                        'language': 'id' if is_indonesian else 'en',
                        'user': page,
                        'type': 'facebook'
                    }
                    
                    # Store and append
                    articles[article_id] = article
                    facebook_articles.append(article)
                    
            except Exception as e:
                print(f"Error fetching posts from Facebook page {page}: {e}")
                continue
                
        return facebook_articles
        
    except Exception as e:
        print(f"Error with Facebook scraper: {e}")
        return []

def fetch_instagram_posts(search_query=None, accounts=None, count=5):
    """Fetch Instagram posts from specific accounts or hashtag search"""
    if not SocialMediaConfig.INSTAGRAM_ENABLED:
        print("Instagram credentials not configured")
        return []
    
    if accounts is None:
        # Default Indonesian news accounts
        accounts = ['detikcom', 'kompascom', 'tribunnews']
    
    instagram_articles = []
    
    try:
        # Set up Instagram loader
        loader = instaloader.Instaloader()
        
        # Login if credentials provided
        if SocialMediaConfig.INSTAGRAM_USERNAME and SocialMediaConfig.INSTAGRAM_PASSWORD:
            try:
                loader.login(SocialMediaConfig.INSTAGRAM_USERNAME, SocialMediaConfig.INSTAGRAM_PASSWORD)
            except Exception as e:
                print(f"Instagram login failed: {e}")
        
        # Process based on search type
        if search_query and search_query.startswith('#'):
            # Search by hashtag
            hashtag = search_query.replace('#', '')
            posts = loader.get_hashtag_posts(hashtag)
            
            # Limit number of posts
            post_count = 0
            for post in posts:
                if post_count >= count:
                    break
                
                try:
                    # Get post text
                    text = post.caption if post.caption else "No caption"
                    
                    # Perform sentiment analysis
                    is_indonesian = contains_indonesian_words(text)
                    analysis = analyze_sentiment(text, is_indonesian)
                    sentiment_score = analysis.sentiment.polarity
                    
                    sentiment_label = "Positif" if sentiment_score > 0 else "Negatif" if sentiment_score < 0 else "Netral"
                    if not is_indonesian:
                        sentiment_label = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
                    
                    article_id = f"instagram_{post.shortcode}"
                    
                    # Create article object
                    article = {
                        'id': article_id,
                        'title': f"Instagram: {text[:50]}...",
                        'summary': text,
                        'link': f"https://www.instagram.com/p/{post.shortcode}/",
                        'published': post.date_local,
                        'source': f"Instagram/{post.owner_username}",
                        'sentiment_score': round(sentiment_score, 2),
                        'sentiment_label': sentiment_label,
                        'sentiment_color': get_sentiment_color(sentiment_score),
                        'language': 'id' if is_indonesian else 'en',
                        'user': post.owner_username,
                        'type': 'instagram'
                    }
                    
                    # Store and append
                    articles[article_id] = article
                    instagram_articles.append(article)
                    post_count += 1
                    
                except Exception as e:
                    print(f"Error processing Instagram post: {e}")
                    continue
                    
        else:
            # Get posts from specified accounts
            for username in accounts:
                try:
                    profile = instaloader.Profile.from_username(loader.context, username)
                    posts = profile.get_posts()
                    
                    post_count = 0
                    for post in posts:
                        if post_count >= count:
                            break
                            
                        text = post.caption if post.caption else "No caption"
                        
                        # If search query provided, skip non-matching posts
                        if search_query and search_query.lower() not in text.lower():
                            continue
                        
                        # Perform sentiment analysis
                        is_indonesian = contains_indonesian_words(text)
                        analysis = analyze_sentiment(text, is_indonesian)
                        sentiment_score = analysis.sentiment.polarity
                        
                        sentiment_label = "Positif" if sentiment_score > 0 else "Negatif" if sentiment_score < 0 else "Netral"
                        if not is_indonesian:
                            sentiment_label = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
                        
                        article_id = f"instagram_{post.shortcode}"
                        
                        # Create article object
                        article = {
                            'id': article_id,
                            'title': f"Instagram: {text[:50]}...",
                            'summary': text,
                            'link': f"https://www.instagram.com/p/{post.shortcode}/",
                            'published': post.date_local,
                            'source': f"Instagram/{username}",
                            'sentiment_score': round(sentiment_score, 2),
                            'sentiment_label': sentiment_label,
                            'sentiment_color': get_sentiment_color(sentiment_score),
                            'language': 'id' if is_indonesian else 'en',
                            'user': username,
                            'type': 'instagram'
                        }
                        
                        # Store and append
                        articles[article_id] = article
                        instagram_articles.append(article)
                        post_count += 1
                        
                except Exception as e:
                    print(f"Error fetching Instagram posts from {username}: {e}")
                    continue
                    
        return instagram_articles
        
    except Exception as e:
        print(f"Error with Instagram loader: {e}")
        return []

def fetch_articles(search_query=None):
    """
    Fetch articles from RSS feeds and social media, then analyze sentiment
    If search_query is provided, search for that topic
    """
    all_articles = []
    
    # Default feeds with Indonesian sources
    default_feeds = [
        # Indonesian news sources
        "https://www.kompas.com/rss/",
        "https://rss.tempo.co/",
        "https://www.republika.co.id/rss/",
        "https://www.detik.com/rss",
        # International sources
        "https://www.theguardian.com/world/rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
    ]
    
    # If we have a search query, build a list of targeted feeds
    feeds = []
    if search_query:
        # Clear existing articles when performing a new search
        articles.clear()
        
        # Detect if the search query might be in Indonesian
        is_indonesian_query = contains_indonesian_words(search_query)
        
        # Google News RSS search (Indonesian version if detected)
        if is_indonesian_query:
            google_news = f"https://news.google.com/rss/search?q={quote(search_query)}&hl=id-ID&gl=ID&ceid=ID:id"
        else:
            google_news = f"https://news.google.com/rss/search?q={quote(search_query)}&hl=en-US&gl=US&ceid=US:en"
        feeds.append(google_news)
        
        # Indonesian specific search
        indonesian_search = f"https://news.google.com/rss/search?q={quote(search_query)}+Indonesia&hl=id-ID&gl=ID&ceid=ID:id"
        feeds.append(indonesian_search)
        
        # Add topic-specific feeds from major news sources
        topic_feeds = {
            "technology": [
                "https://www.theverge.com/rss/index.xml",
                "https://feeds.wired.com/wired/index",
                # Indonesian tech sources
                "https://www.techno.id/rss",
                "https://tekno.kompas.com/rss/"
            ],
            "politics": [
                "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
                # Indonesian politics sources
                "https://nasional.kompas.com/rss/",
                "https://rss.tempo.co/nasional"
            ],
            "business": [
                "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
                # Indonesian business sources
                "https://ekonomi.kompas.com/rss/",
                "https://www.cnbcindonesia.com/rss"
            ],
            "health": [
                "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
                # Indonesian health sources
                "https://health.kompas.com/rss/",
                "https://www.klikdokter.com/rss"
            ],
            "teknologi": [  # Indonesian word for technology
                "https://tekno.kompas.com/rss/",
                "https://www.techno.id/rss"
            ],
            "politik": [  # Indonesian word for politics
                "https://nasional.kompas.com/rss/",
                "https://rss.tempo.co/nasional"
            ],
            "bisnis": [  # Indonesian word for business
                "https://ekonomi.kompas.com/rss/",
                "https://www.cnbcindonesia.com/rss"
            ],
            "kesehatan": [  # Indonesian word for health
                "https://health.kompas.com/rss/",
                "https://www.klikdokter.com/rss"
            ]
        }
        
        # Check if search query matches any of our predefined topics (in English or Indonesian)
        for topic, topic_feed_list in topic_feeds.items():
            if re.search(r'\b' + re.escape(topic) + r'\b', search_query.lower()):
                feeds.extend(topic_feed_list)
    else:
        feeds = default_feeds
    
    # Process each feed
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:10]:  # Limit to 10 articles per feed
                try:
                    # Skip if article with the same title exists
                    # Make sure we have a title
                    if not hasattr(entry, 'title'):
                        continue
                    
                    # Ensure title is a string
                    title = entry.title
                    if not isinstance(title, str):
                        title = str(title)
                    
                    if any(a['title'] == title for a in all_articles):
                        continue
                        
                    # Generate a unique ID for each article
                    article_id = str(uuid.uuid4())
                    
                    # Get publication date or use current time if not available
                    pub_date = entry.get('published_parsed', None)
                    if pub_date:
                        try:
                            pub_date = datetime.datetime(*pub_date[:6])
                        except Exception:
                            pub_date = datetime.datetime.now()
                    else:
                        pub_date = datetime.datetime.now()
                        
                    # Perform sentiment analysis
                    # TextBlob doesn't work well for Indonesian, but we'll use it as a fallback
                    is_indonesian = contains_indonesian_words(title)
                    analysis = analyze_sentiment(title, is_indonesian)
                    sentiment_score = analysis.sentiment.polarity
                    sentiment_label = "Positif" if sentiment_score > 0 else "Negatif" if sentiment_score < 0 else "Netral"
                    
                    if not is_indonesian:  # Use English labels for non-Indonesian content
                        sentiment_label = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
                    
                    # Extract source name from feed URL or entry
                    link = getattr(entry, 'link', feed_url)
                    if not isinstance(link, str):
                        link = str(link)
                        
                    source_url = link
                    source = urlparse(source_url).netloc.replace('www.', '').split('.')[0].capitalize()
                    
                    # Better source detection, with special handling for Indonesian sources
                    if source == 'News' or source == 'Google':
                        # Try to extract real source from entry source or title
                        if hasattr(entry, 'source'):
                            entry_source = getattr(entry, 'source')
                            if isinstance(entry_source, str):
                                source = entry_source
                        elif isinstance(title, str) and ' - ' in title:
                            # Many titles end with " - Source Name"
                            source = title.split(' - ')[-1]
                    
                    # Check for common Indonesian sources and clean up names
                    indonesian_sources = {
                        'kompas': 'Kompas', 
                        'detik': 'Detik', 
                        'tempo': 'Tempo',
                        'republika': 'Republika', 
                        'liputan6': 'Liputan 6',
                        'tribunnews': 'Tribun News',
                        'cnbcindonesia': 'CNBC Indonesia',
                        'klikdokter': 'Klik Dokter'
                    }
                    
                    for key, value in indonesian_sources.items():
                        if key in source.lower():
                            source = value
                            break
                    
                    # Determine language of article
                    language = 'id' if is_indonesian else 'en'
                    
                    # Get summary, with a fallback
                    summary = getattr(entry, 'summary', 'No summary available')
                    if not isinstance(summary, str):
                        summary = str(summary)
                    
                    article = {
                        'id': article_id,
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'published': pub_date,
                        'source': source,
                        'sentiment_score': round(sentiment_score, 2),
                        'sentiment_label': sentiment_label,
                        'sentiment_color': get_sentiment_color(sentiment_score),
                        'language': language,
                        'type': 'news' # Mark as news article type
                    }
                    
                    articles[article_id] = article
                    all_articles.append(article)
                except Exception as e:
                    print(f"Error processing entry: {e}")
                    continue  # Skip this problematic entry
        except Exception as e:
            print(f"Error fetching from {feed_url}: {e}")
    
    # Add social media content
    try:
        # Fetch from Twitter if enabled
        twitter_articles = fetch_twitter_posts(search_query)
        all_articles.extend(twitter_articles)
        
        # Fetch from Facebook if enabled
        facebook_articles = fetch_facebook_posts(search_query)
        all_articles.extend(facebook_articles)
        
        # Fetch from Instagram if enabled
        instagram_articles = fetch_instagram_posts(search_query)
        all_articles.extend(instagram_articles)
    except Exception as e:
        print(f"Error fetching social media content: {e}")
    
    return sorted(all_articles, key=lambda x: x['published'], reverse=True)

def contains_indonesian_words(text):
    """
    Simple check if text might be Indonesian by looking for common Indonesian words
    A more sophisticated approach would use a language detection library
    """
    # First, check if the input is a string
    if not isinstance(text, str):
        try:
            text = str(text)
        except:
            return False
    
    # Ensure we have a non-empty string
    if not text:
        return False
    
    common_indonesian_words = [
        'dan', 'atau', 'yang', 'di', 'ini', 'itu', 'dengan', 'untuk', 'dalam', 'tidak',
        'pada', 'dari', 'jika', 'maka', 'akan', 'oleh', 'saya', 'kamu', 'mereka', 'kami',
        'indonesia', 'jakarta', 'adalah', 'bisa', 'dapat', 'tahun', 'menurut', 'tentang'
    ]
    
    try:
        # Convert to lowercase and split into words
        words = text.lower().split()
        
        # Check if any common Indonesian words are in the text
        for word in words:
            if word in common_indonesian_words:
                return True
    except Exception:
        # If any error occurs in processing, assume it's not Indonesian
        return False
    
    return False

def analyze_sentiment(text, is_indonesian=False):
    """
    Analyze sentiment of text
    For Indonesian text, we'd use a specialized model, but TextBlob as fallback
    """
    # Ensure we have a valid string
    if not isinstance(text, str) or not text:
        return TextBlob("")  # Return neutral sentiment for empty text
        
    try:
        # In a real implementation, you could use a proper Indonesian sentiment model
        # For now, we'll use TextBlob for both languages
        return TextBlob(text)
    except Exception:
        # If TextBlob fails, return a neutral sentiment
        return TextBlob("")

def get_sentiment_color(score):
    """Return a color based on sentiment score"""
    if score > 0.3:
        return "success"  # very positive - green
    elif score > 0:
        return "info"     # somewhat positive - blue
    elif score > -0.3:
        return "warning"  # somewhat negative - yellow
    else:
        return "danger"   # very negative - red

@app.route('/')
def home():
    """Home page - display list of articles with sentiment analysis"""
    search_query = request.args.get('query', None)
    article_list = fetch_articles(search_query)
    return render_template('index.html', articles=article_list, request=request)

@app.route('/article/<article_id>')
def article_detail(article_id):
    """Article detail page"""
    if article_id not in articles:
        # If we don't have the article in memory, re-fetch all articles
        search_query = request.args.get('query', None)
        fetch_articles(search_query)
    
    article = articles.get(article_id, None)
    if not article:
        return "Article not found", 404
        
    return render_template('article.html', article=article)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
