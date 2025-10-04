import { NextResponse } from 'next/server';
import { ChromaClient } from 'chromadb';
import OpenAI from 'openai';
import { pipeline } from '@xenova/transformers';

// Configuration
const CHROMA_HOST = process.env.CHROMA_HOST || 'http://chromadb:8000';
const COLLECTION_NAME = 'kafkai_facts';
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

// Initialize clients
const chroma = new ChromaClient({ path: CHROMA_HOST });
const openai = new OpenAI({ apiKey: OPENAI_API_KEY });

// Load the sentence-transformer model
// Use a singleton pattern to ensure the pipeline is loaded only once
class PipelineSingleton {
    static instance: any = null;

    static async getInstance() {
        if (this.instance === null) {
            this.instance = pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');
        }
        return this.instance;
    }
}

// Handler for POST requests
export async function POST(request: Request) {
  try {
    const { query } = await request.json();

    if (!query) {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 });
    }

    // 1. Retrieve context from ChromaDB
    const pipe = await PipelineSingleton.getInstance();
    const queryEmbedding = await pipe(query, { pooling: 'mean', normalize: true });
    const collection = await chroma.getCollection({ name: COLLECTION_NAME });
    const results = await collection.query({
      queryEmbeddings: [Array.from(queryEmbedding.data)],
      nResults: 5,
    });
    const context = results.documents[0].join('\n- ');

    // 2. Generate response from OpenAI
    const systemPrompt = `You are KafkAI, an AI assistant with access to real-time information. Your knowledge is augmented by a continuous stream of facts. Answer the user's question based on the provided context. If the context doesn't contain the answer, say so. Be concise and helpful.`;
    const userPrompt = `Context from real-time data stream:\n---\n- ${context}\n---\nQuestion: ${query}\nAnswer:`;

    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      temperature: 0.7,
    });

    const answer = response.choices[0].message?.content;

    return NextResponse.json({ answer });
  } catch (error) {
    console.error('Error processing chat request:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}