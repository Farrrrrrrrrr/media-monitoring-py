from flask import Blueprint, jsonify, request, current_app
from functools import wraps
import datetime
import jwt
import os
from flask_cors import cross_origin

# Create API blueprint
api = Blueprint('api', __name__)

# API authentication
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'status': 'error',
                'message': 'Authentication token is missing',
                'code': 401
            }), 401
            
        try:
            # Decode token
            secret_key = os.environ.get('JWT_SECRET_KEY', 'default-dev-key')
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            
            # You could add user info to request here
            # request.current_user = get_user_by_id(data['user_id'])
            
        except:
            return jsonify({
                'status': 'error',
                'message': 'Invalid authentication token',
                'code': 401
            }), 401
            
        return f(*args, **kwargs)
    
    return decorated

# Standard response format
def api_response(data=None, message=None, status="success", code=200):
    """Generate standardized API response"""
    response = {
        'status': status,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    if message:
        response['message'] = message
        
    if data is not None:
        response['data'] = data
        
    return jsonify(response), code

# API Authentication endpoints
@api.route('/auth/token', methods=['POST'])
def get_token():
    """Get authentication token with API key"""
    api_key = request.json.get('api_key', None)
    
    # Check API key (in production, validate against database)
    valid_api_key = os.environ.get('API_KEY', 'test-api-key')
    
    if api_key != valid_api_key:
        return api_response(
            message="Invalid API key", 
            status="error", 
            code=401
        )
    
    # Generate JWT token
    secret_key = os.environ.get('JWT_SECRET_KEY', 'default-dev-key')
    token = jwt.encode({
        'api_key': api_key,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, secret_key, algorithm="HS256")
    
    return api_response(
        data={'token': token},
        message="Authentication successful"
    )

# Articles API endpoints
@api.route('/articles', methods=['GET'])
@cross_origin()
@token_required
def get_articles():
    """Get articles with optional filtering"""
    from app import fetch_articles
    
    search_query = request.args.get('query', None)
    source_type = request.args.get('source', None)
    language = request.args.get('language', None)
    limit = min(int(request.args.get('limit', 30)), 100)  # Max 100 articles
    
    # Fetch articles
    articles = fetch_articles(search_query)
    
    # Apply filters
    if source_type:
        articles = [a for a in articles if a.get('type') == source_type]
    
    if language:
        articles = [a for a in articles if a.get('language') == language]
    
    # Apply limit
    articles = articles[:limit]
    
    return api_response(
        data=articles,
        message=f"Retrieved {len(articles)} articles"
    )

@api.route('/articles/<article_id>', methods=['GET'])
@cross_origin()
@token_required
def get_article(article_id):
    """Get a specific article by ID"""
    from app import articles
    
    article = articles.get(article_id)
    if not article:
        return api_response(
            message="Article not found", 
            status="error", 
            code=404
        )
    
    return api_response(
        data=article,
        message="Article retrieved successfully"
    )

@api.route('/sources', methods=['GET'])
@cross_origin()
@token_required
def get_sources():
    """Get available news and social media sources"""
    sources = {
        "news": [
            {"id": "kompas", "name": "Kompas", "language": "id"},
            {"id": "tempo", "name": "Tempo", "language": "id"},
            {"id": "republika", "name": "Republika", "language": "id"},
            {"id": "detik", "name": "Detik", "language": "id"},
            {"id": "theguardian", "name": "The Guardian", "language": "en"},
            {"id": "nytimes", "name": "New York Times", "language": "en"}
        ],
        "social_media": [
            {"id": "twitter", "name": "Twitter", "enabled": True},
            {"id": "facebook", "name": "Facebook", "enabled": True},
            {"id": "instagram", "name": "Instagram", "enabled": True}
        ]
    }
    
    return api_response(
        data=sources,
        message="Available sources retrieved"
    )

@api.route('/sentiment', methods=['POST'])
@cross_origin()
@token_required
def analyze_text_sentiment():
    """Analyze sentiment of provided text"""
    from app import analyze_sentiment, contains_indonesian_words, get_sentiment_color
    
    # Get text from request
    text = request.json.get('text', '')
    if not text:
        return api_response(
            message="No text provided", 
            status="error", 
            code=400
        )
    
    # Analyze sentiment
    is_indonesian = contains_indonesian_words(text)
    analysis = analyze_sentiment(text, is_indonesian)
    sentiment_score = analysis.sentiment.polarity
    
    sentiment_label = "Positif" if sentiment_score > 0 else "Negatif" if sentiment_score < 0 else "Netral"
    if not is_indonesian:
        sentiment_label = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
    
    result = {
        'text': text,
        'language': 'id' if is_indonesian else 'en',
        'sentiment_score': round(sentiment_score, 2),
        'sentiment_label': sentiment_label,
        'sentiment_color': get_sentiment_color(sentiment_score)
    }
    
    return api_response(
        data=result,
        message="Sentiment analysis completed"
    )
