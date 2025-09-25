import time
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable

def create_kafka_topics():
    """
    Creates the necessary Kafka topics for the KafkAI project.
    """
    # Configuration
    bootstrap_servers = 'kafka:9092'
    topics = {
        'raw_news': {'num_partitions': 3, 'replication_factor': 1},
        'raw_social_media': {'num_partitions': 3, 'replication_factor': 1},
        'raw_market_data': {'num_partitions': 3, 'replication_factor': 1}
    }
    max_retries = 10
    retry_delay = 10  # seconds

    # Retry connecting to Kafka
    for attempt in range(max_retries):
        try:
            print(f"Connecting to Kafka... (Attempt {attempt + 1}/{max_retries})")
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers,
                client_id='kafka-topic-creator'
            )
            print("Successfully connected to Kafka.")
            break
        except NoBrokersAvailable:
            if attempt < max_retries - 1:
                print(f"Could not connect to Kafka. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Error: Could not connect to Kafka after several retries. Aborting.")
                exit(1)

    # Create topics
    topic_list = []
    for topic_name, config in topics.items():
        topic_list.append(NewTopic(
            name=topic_name,
            num_partitions=config['num_partitions'],
            replication_factor=config['replication_factor']
        ))

    try:
        print(f"Creating topics: {list(topics.keys())}...")
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print("Topics created successfully (or already exist).")
    except TopicAlreadyExistsError:
        print("Topics already exist. No action needed.")
    except Exception as e:
        print(f"An error occurred during topic creation: {e}")
    finally:
        admin_client.close()

if __name__ == "__main__":
    create_kafka_topics()