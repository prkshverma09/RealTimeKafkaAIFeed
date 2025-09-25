# KafkAI: The Real-Time AI Brain - Design Document

## 1. Overview

KafkAI is a Retrieval-Augmented Generation (RAG) system that leverages real-time data streams from Apache Kafka to provide a Large Language Model (LLM) with up-to-the-second information. This allows the LLM to answer questions about events as they happen, overcoming the knowledge cut-off limitation of pre-trained models.

## 2. System Architecture

The system is composed of the following key components:

```
+----------------+      +----------------+      +-----------------+
| Data Producers |----->| Apache Kafka   |----->| ksqlDB          |
| (e.g., APIs)   |      | (Raw Topics)   |      | (Stream Proc.)  |
+----------------+      +----------------+      +-----------------+
                                                     |
                                                     v
+-----------------+      +-----------------+      +----------------------+
| Q&A Application |<---->| Vector Database |<-----| Real-Time Vectorizer |
| (Chatbot UI)    |      | (e.g., Pinecone)|      | (Kafka Consumer)     |
+-----------------+      +-----------------+      +----------------------+
       |
       v
+-----------------+
| LLM             |
| (e.g., GPT-4)   |
+-----------------+
```

### 2.1. Data Flow

1.  **Data Ingestion:** Various data producers (e.g., news APIs, social media feeds, financial data providers) publish data into specific Kafka topics.
2.  **Stream Processing:** ksqlDB consumes messages from the raw Kafka topics, performs transformations (filtering, cleaning, schema unification), and publishes the processed data into a unified "facts" topic.
3.  **Vectorization and Indexing:** A dedicated Kafka consumer, the "Real-Time Vectorizer," consumes the processed "facts." For each fact, it generates a vector embedding using a sentence-transformer model and upserts it into a vector database.
4.  **Question Answering:** A user asks a question through the Q&A application.
5.  **Context Retrieval:** The application generates an embedding for the user's question and queries the vector database to find the most relevant facts (context).
6.  **Augmented Generation:** The application sends the user's question along with the retrieved context to an LLM.
7.  **Response:** The LLM generates an answer based on the provided context and its own internal knowledge, and the application displays it to the user.

## 3. Component Deep Dive

### 3.1. Data Producers

*   **Responsibilities:** Ingest data from external sources and publish it to Kafka.
*   **Implementation:** These will be small, independent services (e.g., Python scripts).
*   **Data Format:** JSON. Each message will have a consistent schema with fields like `source`, `timestamp`, `content`, and `metadata`.
    *   Example for a news feed: `{"source": "news-api", "timestamp": "2023-10-27T10:00:00Z", "content": "New AI breakthrough announced.", "metadata": {"url": "http://example.com/news/123"}}`

### 3.2. Apache Kafka

*   **Responsibilities:** Act as the central message bus for real-time data.
*   **Topics:**
    *   `raw_news`: For raw data from news APIs.
    *   `raw_social_media`: For raw data from social media feeds.
    *   `raw_market_data`: For raw financial data.
    *   `processed_facts`: A unified topic for cleaned and structured data from ksqlDB.
*   **Data Retention:** A retention policy of 24 hours for raw topics and 7 days for the processed topic.

### 3.3. ksqlDB

*   **Responsibilities:** Real-time stream processing.
*   **Queries:**
    1.  **Create Streams:** Define streams on top of the raw Kafka topics.
    2.  **Transform and Unify:** Create a new stream (`processed_facts`) from the raw streams. This will involve:
        *   Filtering out irrelevant or low-quality data.
        *   Unifying the data structure into a common format.
        *   Potentially performing simple data enrichment.
*   **Output Schema (`processed_facts` topic):**
    *   `fact_id`: `VARCHAR` (Primary Key)
    *   `source`: `VARCHAR`
    *   `fact_text`: `VARCHAR`
    *   `timestamp`: `BIGINT` (Unix timestamp)
    *   `metadata`: `MAP<STRING, STRING>`

### 3.4. Real-Time Vectorizer

*   **Responsibilities:** Consume from `processed_facts`, generate embeddings, and store them.
*   **Technology Stack:** Python, using the `kafka-python` library for consumption and a chosen sentence-transformer model (e.g., `all-MiniLM-L6-v2`) for embedding.
*   **Logic:**
    1.  Consume a message from the `processed_facts` topic.
    2.  Extract the `fact_text`.
    3.  Use the embedding model to generate a vector from the `fact_text`.
    4.  Upsert the vector along with the `fact_id` and other metadata into the vector database.

### 3.5. Vector Database

*   **Responsibilities:** Store and index vector embeddings for efficient similarity search.
*   **Choice:** We will start with **ChromaDB** for its simplicity and ease of setup. We can later migrate to a more scalable solution like Pinecone or Weaviate if needed.
*   **Schema/Index:**
    *   `id`: The `fact_id` from the Kafka message.
    *   `vector`: The generated embedding.
    *   `metadata`: A dictionary containing `source`, `fact_text`, `timestamp`, etc. This allows for filtering and displaying the original text.

### 3.6. Q&A Application

*   **Responsibilities:** Provide a user interface, orchestrate the RAG process.
*   **Technology Stack:** Python with **Streamlit** for a simple web interface.
*   **Logic:**
    1.  Accept a user question from the text input.
    2.  Generate an embedding for the question using the same model as the Vectorizer.
    3.  Query the vector database to get the top-k most similar facts.
    4.  Construct a prompt for the LLM, including the retrieved facts as context.
    5.  Send the prompt to the LLM (e.g., using the OpenAI API).
    6.  Display the LLM's response to the user.

### 3.7. LLM

*   **Choice:** We will use a model from the **OpenAI API** (e.g., `gpt-3.5-turbo` or `gpt-4`) for its strong reasoning capabilities. The specific model can be configured.

## 4. Scalability and Reliability

*   **Kafka:** Kafka is inherently scalable and fault-tolerant. We can add more brokers and partitions as the data volume grows.
*   **Producers/Vectorizer:** These are stateless services and can be scaled horizontally by running multiple instances.
*   **Vector Database:** ChromaDB can be run in a client/server mode. For very large scale, we would need to migrate to a managed, distributed vector database.
*   **ksqlDB:** Can be scaled by adding more ksqlDB server instances.

## 5. Security

*   All API keys (OpenAI, data source APIs) will be managed via environment variables or a secret management system.
*   Kafka topics can be secured with ACLs if deployed in a production environment.
*   The Q&A application will not store user data.

## 6. MLOps / DevOps

*   **Containerization:** All services (Producers, Vectorizer, Q&A App) will be containerized using Docker for consistent deployment.
*   **Orchestration:** Docker Compose will be used for local development to spin up the entire stack (Kafka, Zookeeper, ksqlDB, ChromaDB, and our custom services).
*   **CI/CD:** A simple CI/CD pipeline (e.g., using GitHub Actions) can be set up to build and push Docker images.