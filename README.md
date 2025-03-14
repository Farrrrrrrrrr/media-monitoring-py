# Media Monitoring for Indonesian News

A media monitoring application that fetches news articles from various sources, analyzes sentiment, and displays the results in a responsive dashboard. The application has a special focus on Indonesian news sources.

## Features

- Fetches news from multiple Indonesian and international sources
- Performs sentiment analysis on article titles
- Detects Indonesian language content
- Provides a bilingual interface (Indonesian and English)
- Allows filtering by language
- Responsive design that works on mobile and desktop

## API Documentation

The MediaMon project includes comprehensive API documentation that can be accessed through the following URLs when the application is running:

1. **API Documentation** - `/api/docs`
   - Detailed description of all available endpoints
   - Request/response formats and examples
   - Authentication instructions

2. **Swagger UI** - `/api/swagger`
   - Interactive API testing interface
   - Try out API calls directly from your browser
   - Explore the full API capabilities

3. **Integration Examples** - `/api/integration`
   - Code samples in multiple languages (Python, JavaScript, PHP, Java)
   - Step-by-step integration tutorials
   - Authentication examples

When the application is deployed to Google App Engine, these pages will be available at:
- https://your-app-name.appspot.com/api/docs
- https://your-app-name.appspot.com/api/swagger
- https://your-app-name.appspot.com/api/integration

## Deployment Options

### 1. Firebase Functions and Hosting (Recommended)

This method allows free hosting with Firebase Functions.

**Requirements:**
- Node.js and npm
- Firebase CLI
- Firebase Account

**Setup:**

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in the project directory
firebase init

# Deploy to Firebase
firebase deploy
```

### 2. As a Flask Web Application

This method requires a Python server but offers real-time data fetching.

**Requirements:**
- Python 3.8+
- Flask and other dependencies (see requirements.txt)

**Setup:**

```bash
# Install dependencies
pip install -r requirements.txt

# Download TextBlob corpora
python -m textblob.download_corpora lite

# Run the Flask application
python app.py
```

The application will be available at http://localhost:5000

### 3. Using Docker

For easy containerization and consistent environments.

```bash
# Build and run with Docker
docker-compose up --build
```

## Project Structure

- `app.py`: Flask application for local development
- `functions/`: Firebase Functions for serverless deployment
- `public/`: Static files for Firebase Hosting
- `static/`: CSS, JS, and other static files for Flask
- `templates/`: Flask HTML templates
- `firebase.json`: Firebase configuration

## Customization

- Add more RSS feeds in `app.py` or `functions/main.py`
- Modify the sentiment analysis for better Indonesian language support 
- Customize the UI in public/ or templates/ directories
