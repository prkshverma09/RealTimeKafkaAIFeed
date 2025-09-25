import os
import streamlit as st
import chromadb
import openai
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = os.getenv("CHROMA_PORT", 8000)
COLLECTION_NAME = "kafkai_facts"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- LOAD MODELS ---
# Use a caching mechanism for Streamlit to load models only once
@st.cache_resource
def load_models():
    """Loads the Sentence Transformer model."""
    print("Loading Sentence Transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Model loaded.")
    return model

@st.cache_resource
def get_chroma_client():
    """Returns a ChromaDB client connected to the server."""
    print(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return client

# --- RAG-LLM FUNCTIONS ---
def retrieve_context(query, model, chroma_client, n_results=5):
    """
    Retrieves relevant context from ChromaDB for a given query.
    """
    try:
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        query_embedding = model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results['documents'][0]
    except Exception as e:
        st.error(f"Error retrieving context from ChromaDB: {e}")
        return []

def generate_response(query, context):
    """
    Generates a response from the LLM using the retrieved context.
    """
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY is not set. Cannot generate response.")
        return "Error: OpenAI API key is not configured."

    openai.api_key = OPENAI_API_KEY

    system_prompt = (
        "You are KafkAI, an AI assistant with access to real-time information. "
        "Your knowledge is augmented by a continuous stream of facts. "
        "Answer the user's question based on the provided context. "
        "If the context doesn't contain the answer, say so. "
        "Be concise and helpful."
    )

    prompt = f"""
    Context from real-time data stream:
    ---
    {context}
    ---
    Question: {query}
    Answer:
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message['content']
    except Exception as e:
        st.error(f"Error calling OpenAI API: {e}")
        return "Sorry, I encountered an error while generating a response."

# --- STREAMLIT UI ---
st.set_page_config(page_title="KafkAI", page_icon="🧠")
st.title("🧠 KafkAI: The Real-Time AI Brain")
st.markdown("Ask me anything! My knowledge base is updated in real-time from a Kafka stream.")

# Load resources
embedding_model = load_models()
chroma_client = get_chroma_client()

# User input
user_query = st.text_input("Your question:", key="query_input")

if st.button("Ask KafkAI"):
    if user_query:
        with st.spinner("Thinking..."):
            # 1. Retrieve context
            st.subheader("1. Retrieving Context...")
            retrieved_docs = retrieve_context(user_query, embedding_model, chroma_client)

            if retrieved_docs:
                context_str = "\n- ".join(retrieved_docs)
                st.info(f"**Found {len(retrieved_docs)} relevant facts:**\n- {context_str}")

                # 2. Generate response
                st.subheader("2. Generating Answer...")
                answer = generate_response(user_query, context_str)
                st.success(answer)
            else:
                st.warning("Could not find any relevant real-time context. Answering from general knowledge.")
                # Optional: Fallback to LLM without context
                answer = generate_response(user_query, "No specific context found.")
                st.success(answer)
    else:
        st.warning("Please enter a question.")