# 🧠 KafkAI: The Real-Time AI Brain

KafkAI is a Retrieval-Augmented Generation (RAG) system where the "retrieval" knowledge base is updated in real-time from Kafka streams, giving a Large Language Model (LLM) up-to-the-second context.

This project demonstrates how to build a complete end-to-end RAG pipeline that ingests, processes, and queries real-time data streams.

## How It Works

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

1.  **Producers**: A service (e.g., `news-producer`) fetches data from an external API and publishes it to a `raw_news` Kafka topic.
2.  **Stream Processing (ksqlDB)**: ksqlDB processes the raw data, cleans it, and structures it into a unified `processed_facts` topic.
3.  **Real-Time Vectorizer**: A Python service consumes these facts, uses a Sentence Transformer model to create vector embeddings, and upserts them into a ChromaDB vector database.
4.  **Q&A Application**: A Streamlit web app allows users to ask questions. The app queries ChromaDB for relevant context, combines it with the user's question, and sends it to an LLM (like GPT) to generate a context-aware answer.

## Prerequisites

*   **Docker and Docker Compose**: To run the containerized services.
*   **API Keys**: You will need API keys for the data sources you want to use.
    *   [NewsAPI.io](https://newsapi.org/) for the news producer.
    *   [OpenAI](https://platform.openai.com/signup/) for the Q&A application.

## 🚀 Getting Started

### 1. Configure Environment Variables

First, create a `.env` file by copying the example file:

```bash
cp .env.example .env
```

Next, open the `.env` file and add your API keys:

```
# .env
NEWS_API_KEY=your_news_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Launch the Application

Run the entire application stack using Docker Compose:

```bash
docker compose up -d
```

This command will build the custom service images and start all containers in detached mode.

*(Note: If you encounter permission errors, you may need to run the command with `sudo`)*

### 3. Apply the ksqlDB Processing Logic

The `ksqldb-server` needs to be told how to process the streams. You can do this by executing the `processing.sql` script via the `ksqldb-cli`:

```bash
docker compose exec ksqldb-cli ksql http://ksqldb-server:8088 < ksql/processing.sql
```

This only needs to be done once after the first time you start the services.

### 4. Use the Q&A Application

The system is now running!

*   The `news-producer` will start fetching news and publishing it to Kafka.
*   The `vectorizer` will start consuming processed facts and adding them to ChromaDB.

Open your web browser and navigate to the Streamlit application:

**URL**: `http://localhost:8501`

You can now ask questions related to the news being ingested.

## Services

| Service         | Description                                        | Access Point                |
| --------------- | -------------------------------------------------- | --------------------------- |
| **qna-app**     | The Streamlit web interface for asking questions.  | `http://localhost:8501`     |
| **chromadb**    | The vector database storing the knowledge.         | `http://localhost:8000`     |
| **ksqldb-server** | The stream processing engine.                      | `http://localhost:8088`     |
| **kafka**       | The message broker.                                | `localhost:9092`            |
| **news-producer** | Fetches news and sends it to Kafka.                | (Runs in background)        |
| **vectorizer**  | Creates vector embeddings and stores them.         | (Runs in background)        |

## Stopping the Application

To stop all the running services, use the following command:

```bash
docker compose down
```
To also remove the persistent data volumes (Kafka data, ChromaDB index), add the `-v` flag:
```bash
docker compose down -v
```