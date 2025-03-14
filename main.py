import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Import your actual Flask application
    # Adjust this import to match your actual app's structure
    from app import app
    
    if __name__ == "__main__":
        # This is used when running locally
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
        
except Exception as e:
    logger.error(f"Error starting application: {str(e)}")
    # Log detailed exception information for debugging
    logger.exception("Exception details:")
    sys.exit(1)
