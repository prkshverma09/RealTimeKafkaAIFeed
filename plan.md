# KafkAI: Implementation Plan

This document breaks down the implementation of the KafkAI project into actionable tasks, based on the `spec.md` design document.

## Phase 1: Core Infrastructure Setup

**Goal:** Get the fundamental components of the data pipeline running.

*   **Task 1.1: Setup Docker Compose Environment**
    *   Create a `docker-compose.yml` file.
    *   Add services for:
        *   Zookeeper
        *   Kafka Broker
        *   ksqlDB Server
        *   ChromaDB
    *   Configure networking so services can communicate.
    *   Define volumes for data persistence (Kafka data, ChromaDB data).

*   **Task 1.2: Create Kafka Topics**
    *   Write a script or a simple service that runs on startup to create the necessary Kafka topics:
        *   `raw_news`
        *   `raw_social_media`
        *   `raw_market_data`
    *   This can be a simple Python script using `kafka-python` or a shell script using Kafka's command-line tools.

## Phase 2: Data Ingestion and Processing

**Goal:** Implement the flow of data from external sources into a processed, unified Kafka topic.

*   **Task 2.1: Implement Data Producer(s)**
    *   Create a Python script for at least one data source (e.g., a news API like NewsAPI.io).
    *   The script will:
        *   Fetch data from the API periodically.
        *   Transform the data into the predefined JSON format.
        *   Publish the JSON messages to the `raw_news` Kafka topic.
    *   Containerize this producer as a Docker service in the `docker-compose.yml`.

*   **Task 2.2: Define ksqlDB Stream Processing Logic**
    *   Write a ksqlDB script (`.sql` file) that:
        *   Creates a `STREAM` on the `raw_news` topic.
        *   Creates a new, unified stream named `processed_facts_stream` with the target schema (`fact_id`, `source`, `fact_text`, `timestamp`, `metadata`).
        *   Uses `CREATE STREAM ... AS SELECT ...` to transform the raw data and populate the new stream. This will automatically create and publish to the `processed_facts` topic.
    *   Document how to apply this script to the running ksqlDB server.

## Phase 3: Real-Time Vectorization

**Goal:** Consume processed facts, convert them to vectors, and store them in the vector database.

*   **Task 3.1: Implement the Real-Time Vectorizer Service**
    *   Create a Python service that:
        *   Connects to Kafka as a consumer on the `processed_facts` topic.
        *   Uses a sentence-transformer library (e.g., `sentence-transformers`) to load a pre-trained model (`all-MiniLM-L6-v2`).
        *   For each message, generates a vector embedding from the `fact_text`.
        *   Connects to the ChromaDB client.
        *   Upserts the vector, the `fact_id`, and associated metadata into a ChromaDB collection.
    *   Containerize this service in the `docker-compose.yml`.

## Phase 4: Q&A Application and Final Integration

**Goal:** Build the user-facing application and connect it to the backend.

*   **Task 4.1: Implement the Q&A Application**
    *   Create a Streamlit application in Python.
    *   Build the UI: a title, a text input box for questions, and a "Submit" button.
    *   Implement the backend logic for the RAG pipeline:
        1.  When the user submits a question, generate an embedding for it (using the same model as the vectorizer).
        2.  Query the ChromaDB collection with the question's embedding to retrieve the top-k relevant text chunks.
        3.  Format the retrieved text chunks and the user's question into a prompt for the LLM.
        4.  Call the OpenAI API (or another LLM provider) with the prompt.
        5.  Display the returned answer in the Streamlit UI.
    *   Containerize this application in the `docker-compose.yml`.

*   **Task 4.2: Full System Test**
    *   Run the entire stack using `docker-compose up`.
    *   Verify that data flows from the producer to Kafka.
    *   Check the `processed_facts` topic in Kafka to see the transformed data.
    *   Query ChromaDB's API to ensure vectors are being added.
    *   Ask a question in the Q&A app related to the ingested data and verify that the answer is relevant and context-aware.

## Phase 5: Documentation and Cleanup

**Goal:** Finalize the project for usability and handoff.

*   **Task 5.1: Create a `README.md`**
    *   Add a clear and concise `README.md` at the root of the project.
    *   Include:
        *   A project description.
        *   Prerequisites (Docker, API keys).
        *   Instructions on how to configure API keys (e.g., using a `.env` file).
        *   A single command to launch the entire application (`docker-compose up -d`).
        *   Instructions on how to use the application and verify its components.

*   **Task 5.2: Code Cleanup and Final Review**
    *   Review all code for clarity, comments, and adherence to best practices.
    *   Ensure all services have proper error handling.
    *   Remove any hardcoded secrets.

---

### Technology Stack Summary:

*   **Orchestration:** Docker, Docker Compose
*   **Messaging:** Apache Kafka
*   **Stream Processing:** ksqlDB
*   **Vector Database:** ChromaDB
*   **Backend/Services:** Python
*   **Frontend:** Streamlit
*   **AI/ML:** OpenAI API, Sentence-Transformers library