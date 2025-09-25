-- ksqlDB Stream Processing Logic for KafkAI

-- Set properties for the session
SET 'auto.offset.reset' = 'earliest';

-- 1. Create a STREAM on the raw_news Kafka topic
-- The raw data is in JSON format. We define the schema here.
CREATE STREAM IF NOT EXISTS raw_news_stream (
    source VARCHAR,
    timestamp VARCHAR,
    content VARCHAR,
    metadata STRUCT<
        url VARCHAR,
        author VARCHAR,
        source_name VARCHAR
    >
) WITH (
    KAFKA_TOPIC='raw_news',
    VALUE_FORMAT='JSON'
);

-- 2. Transform and create the processed_facts stream
-- This stream will contain the cleaned, structured data.
-- We generate a unique fact_id and structure the data for the vectorizer.
CREATE STREAM IF NOT EXISTS processed_facts_stream
WITH (
    KAFKA_TOPIC='processed_facts',
    VALUE_FORMAT='JSON',
    PARTITIONS=3
) AS SELECT
    -- Generate a unique ID for each fact
    GENERATE_UUID() AS fact_id,
    -- Standardize the source
    LCASE(source) AS source,
    -- Use the 'content' field as the main text for vectorization
    content AS fact_text,
    -- Convert the timestamp string to a BIGINT (Unix timestamp)
    UNIX_TIMESTAMP() AS timestamp,
    -- Pass along relevant metadata
    MAP(
        'url' := metadata->url,
        'original_timestamp' := timestamp -- Keep the original timestamp string
    ) AS metadata
FROM
    raw_news_stream
-- Filter out any records where the content is null or empty
WHERE content IS NOT NULL AND LCASE(content) != 'null'
EMIT CHANGES;

-- The `processed_facts_stream` will now continuously receive data
-- from `raw_news_stream`, transform it, and publish it to the
-- `processed_facts` Kafka topic. The Real-Time Vectorizer will
-- consume from this topic.