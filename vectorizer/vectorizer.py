import json
import time
import chromadb
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from sentence_transformers import SentenceTransformer

def create_kafka_consumer(topic):
    """
    Creates and returns a Kafka consumer for the given topic.
    Retries connection if brokers are not available.
    """
    bootstrap_servers = 'kafka:9092'
    max_retries = 10
    retry_delay = 10

    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                auto_offset_reset='earliest',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            print(f"Successfully connected to Kafka topic '{topic}'.")
            return consumer
        except NoBrokersAvailable:
            if attempt < max_retries - 1:
                print(f"Could not connect to Kafka. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Error: Could not connect to Kafka after several retries. Aborting.")
                return None

def connect_to_chromadb():
    """
    Connects to the ChromaDB server and returns a client instance.
    """
    host = 'chromadb'
    port = 8000
    max_retries = 10
    retry_delay = 10

    for attempt in range(max_retries):
        try:
            client = chromadb.HttpClient(host=host, port=port)
            # Ping the server to check the connection
            client.heartbeat()
            print("Successfully connected to ChromaDB.")
            return client
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Could not connect to ChromaDB: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Error: Could not connect to ChromaDB after several retries. Aborting.")
                return None

def main():
    """
    Main function to run the vectorizer service.
    """
    # 1. Load Sentence Transformer model
    print("Loading Sentence Transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Model loaded.")

    # 2. Connect to ChromaDB
    chroma_client = connect_to_chromadb()
    if not chroma_client:
        return

    # 3. Create or get a ChromaDB collection
    collection_name = "kafkai_facts"
    print(f"Getting or creating ChromaDB collection: '{collection_name}'")
    collection = chroma_client.get_or_create_collection(name=collection_name)
    print("Collection ready.")

    # 4. Connect to Kafka
    consumer = create_kafka_consumer('processed_facts')
    if not consumer:
        return

    # 5. Consume messages, vectorize, and upsert
    print("Starting to consume messages from 'processed_facts' topic...")
    for message in consumer:
        try:
            fact = message.value
            fact_id = fact.get('FACT_ID')
            fact_text = fact.get('FACT_TEXT')

            if not fact_id or not fact_text:
                print(f"Skipping message with missing data: {fact}")
                continue

            # Generate embedding
            embedding = model.encode(fact_text).tolist()

            # Prepare metadata
            metadata = {
                "source": fact.get("SOURCE"),
                "text": fact_text,
                "timestamp": fact.get("TIMESTAMP"),
                "url": fact.get("METADATA", {}).get("url", "")
            }

            # Upsert into ChromaDB
            collection.upsert(
                ids=[fact_id],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            print(f"Successfully vectorized and stored fact: {fact_id}")

        except Exception as e:
            print(f"An error occurred while processing a message: {e}")

if __name__ == "__main__":
    main()