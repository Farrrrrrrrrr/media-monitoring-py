"""
API Key and Rate Limit Management for MediaMon

This module provides API key management and rate limiting for the MediaMon API.
"""
import time
import uuid
from flask import request, jsonify, g
from functools import wraps
from firebase_admin import firestore

class APIKeyManager:
    """Handle API key management and validation"""
    def __init__(self, db=None):
        # In-memory store for API keys when no database is provided
        self.db = db
        self.keys = {}
    
    def generate_key(self, user_id, name, permissions=None):
        """Generate a new API key for a user"""
        if permissions is None:
            permissions = ['read']
        
        key = str(uuid.uuid4())
        key_data = {
            'key': key,
            'user_id': user_id,
            'name': name,
            'permissions': permissions,
            'created_at': time.time(),
            'last_used': None
        }
        
        # Store the key
        if self.db:
            # Use database storage in production
            self.db.collection('api_keys').document(key).set(key_data)
        else:
            # In-memory storage for development
            self.keys[key] = key_data
        
        return key
    
    def validate_key(self, key):
        """Validate an API key and return its data"""
        if self.db:
            # Database lookup
            key_doc = self.db.collection('api_keys').document(key).get()
            if key_doc.exists:
                key_data = key_doc.to_dict()
                # Update last_used timestamp
                self.db.collection('api_keys').document(key).update({
                    'last_used': time.time()
                })
                return key_data
        else:
            # In-memory lookup
            if key in self.keys:
                self.keys[key]['last_used'] = time.time()
                return self.keys[key]
        
        return None
    
    def revoke_key(self, key):
        """Revoke an API key"""
        if self.db:
            self.db.collection('api_keys').document(key).delete()
        else:
            if key in self.keys:
                del self.keys[key]

class RateLimiter:
    """Handle API rate limiting"""
    def __init__(self, db=None):
        self.db = db
        self.requests = {}  # In-memory request tracking
        self.limits = {
            'default': {
                'requests': 100,  # Requests per window
                'window': 60 * 60  # 1 hour window in seconds
            },
            'free_tier': {
                'requests': 50,
                'window': 60 * 60
            },
            'standard_tier': {
                'requests': 200,
                'window': 60 * 60
            },
            'premium_tier': {
                'requests': 1000,
                'window': 60 * 60
            }
        }
    
    def is_allowed(self, api_key, tier='default'):
        """Check if request is allowed based on rate limits"""
        now = time.time()
        
        if self.db:
            # Use Firestore for tracking in production
            try:
                # Get usage document
                usage_ref = self.db.collection('rate_limits').document(api_key)
                usage_doc = usage_ref.get()
                
                if usage_doc.exists:
                    # Get existing usage data
                    usage_data = usage_doc.to_dict()
                    requests_timestamps = usage_data.get('requests', [])
                    
                    # Clean up old requests outside the window
                    limit = self.limits.get(tier, self.limits['default'])
                    window = limit['window']
                    requests_timestamps = [t for t in requests_timestamps if t > now - window]
                    
                    # Check if under limit
                    if len(requests_timestamps) >= limit['requests']:
                        return False
                    
                    # Record this request
                    requests_timestamps.append(now)
                    usage_ref.set({'requests': requests_timestamps, 'last_updated': now})
                else:
                    # First request for this key, create new document
                    usage_ref.set({'requests': [now], 'last_updated': now})
                
                return True
            except Exception as e:
                print(f"Error checking rate limit: {e}")
                # Fallback to in-memory tracking if DB fails
                return self._check_in_memory(api_key, tier, now)
        else:
            # Use in-memory tracking for development
            return self._check_in_memory(api_key, tier, now)
    
    def _check_in_memory(self, api_key, tier, now):
        """Check rate limit using in-memory tracking"""
        # Initialize tracking for new keys
        if api_key not in self.requests:
            self.requests[api_key] = []
        
        # Clear old requests outside the window
        limit = self.limits.get(tier, self.limits['default'])
        window = limit['window']
        self.requests[api_key] = [t for t in self.requests[api_key] if t > now - window]
        
        # Check if under limit
        if len(self.requests[api_key]) >= limit['requests']:
            return False
        
        # Record this request
        self.requests[api_key].append(now)
        return True
    
    def reset_for_key(self, api_key):
        """Reset rate limiting for a specific key"""
        if self.db:
            try:
                self.db.collection('rate_limits').document(api_key).delete()
            except Exception as e:
                print(f"Error resetting rate limit: {e}")
        
        # Also reset in-memory tracking
        if api_key in self.requests:
            self.requests[api_key] = []
    
    def reset_all(self):
        """Reset all rate limiting data"""
        if self.db:
            try:
                # Delete all rate limit documents
                batch = self.db.batch()
                docs = self.db.collection('rate_limits').stream()
                for doc in docs:
                    batch.delete(doc.reference)
                batch.commit()
            except Exception as e:
                print(f"Error resetting all rate limits: {e}")
        
        # Reset in-memory tracking
        self.requests = {}

# Create API management utilities for Flask with database
def create_api_manager(db=None):
    api_key_manager = APIKeyManager(db)
    rate_limiter = RateLimiter(db)
    
    # Flask decorators for API routes
    def require_api_key(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Get API key from request
            api_key = None
            if 'X-API-Key' in request.headers:
                api_key = request.headers['X-API-Key']
            
            if not api_key:
                return jsonify({
                    'status': 'error',
                    'message': 'API key is required',
                    'code': 401
                }), 401
            
            # Validate key
            key_data = api_key_manager.validate_key(api_key)
            if not key_data:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid API key',
                    'code': 401
                }), 401
            
            # Store key data in flask g object for route access
            g.api_key_data = key_data
            
            # Check rate limits
            tier = key_data.get('tier', 'default')
            if not rate_limiter.is_allowed(api_key, tier):
                return jsonify({
                    'status': 'error',
                    'message': 'Rate limit exceeded',
                    'code': 429
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated
    
    def admin_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # This decorator should be used after require_api_key
            if not hasattr(g, 'api_key_data'):
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required',
                    'code': 401
                }), 401
            
            # Check if user has admin permission
            if 'admin' not in g.api_key_data.get('permissions', []):
                return jsonify({
                    'status': 'error',
                    'message': 'Admin permission required',
                    'code': 403
                }), 403
                
            return f(*args, **kwargs)
        
        return decorated
    
    return {
        'key_manager': api_key_manager,
        'rate_limiter': rate_limiter,
        'require_api_key': require_api_key,
        'admin_required': admin_required
    }

# Example usage in Flask application:
"""
from flask import Flask
from firebase_admin import firestore

app = Flask(__name__)
db = firestore.client()

# Create API manager with database connection
api_manager = create_api_manager(db)
key_manager = api_manager['key_manager']
require_api_key = api_manager['require_api_key']
admin_required = api_manager['admin_required']

@app.route('/api/protected')
@require_api_key
def protected_endpoint():
    # Access key data
    api_key_data = g.api_key_data
    return jsonify({"message": f"Hello, {api_key_data['name']}"})

@app.route('/api/admin')
@require_api_key
@admin_required
def admin_endpoint():
    return jsonify({"message": "Admin access granted"})
"""
