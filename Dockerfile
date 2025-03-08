FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Download NLTK data for TextBlob
RUN python -m textblob.download_corpora lite

# Run the Flask application
CMD ["python", "app.py"]
