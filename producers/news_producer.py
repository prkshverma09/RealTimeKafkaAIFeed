import os
import json
import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from newsapi import NewsApiClient
from dotenv import load_dotenv

load_dotenv()

def create_kafka_producer():
    """
    Creates and returns a Kafka producer.
    Retries connection if brokers are not available.
    """
    bootstrap_servers = 'kafka:9092'
    max_retries = 10
    retry_delay = 10  # seconds

    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Successfully connected to Kafka.")
            return producer
        except NoBrokersAvailable:
            if attempt < max_retries - 1:
                print(f"Could not connect to Kafka. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Error: Could not connect to Kafka after several retries. Aborting.")
                return None

def fetch_and_produce_news():
    """
    Fetches news from NewsAPI and produces it to a Kafka topic.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        print("Error: NEWS_API_KEY environment variable not set.")
        return

    newsapi = NewsApiClient(api_key=api_key)
    producer = create_kafka_producer()

    if not producer:
        return

    while True:
        try:
            print("Fetching top headlines from NewsAPI...")
            top_headlines = newsapi.get_top_headlines(
                q='technology',
                language='en',
                country='us'
            )

            articles = top_headlines.get('articles', [])
            print(f"Found {len(articles)} articles.")

            for article in articles:
                message = {
                    'source': 'news-api',
                    'timestamp': article.get('publishedAt'),
                    'content': article.get('title'),
                    'metadata': {
                        'url': article.get('url'),
                        'author': article.get('author'),
                        'source_name': article.get('source', {}).get('name')
                    }
                }
                producer.send('raw_news', value=message)
                print(f"Produced message: {message['content']}")

            producer.flush()
            print("Finished producing batch. Waiting for 60 seconds...")
            time.sleep(60) # Fetch news every 60 seconds

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(30) # Wait before retrying in case of an API error

if __name__ == "__main__":
    fetch_and_produce_news()