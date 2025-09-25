FROM python:3.9-slim

WORKDIR /app

# First, copy and install requirements to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then, copy the application code
COPY vectorizer.py .

# The model will be downloaded on first run and cached in the container.
# For production, you might want to pre-download the model into the image.
CMD ["python", "vectorizer.py"]