import os

env_content = """SERPER_API_KEY=3c583cc4e32f2d4e0a3fb5a227d3917823efecd8
OPENAI_API_BASE=http://localhost:11434
OPENAI_API_KEY=ollama
STRATEGIST_MODEL=ollama/mistral-nemo:12b-instruct-2407-q4_K_M
RESEARCHER_MODEL=ollama/qwen2.5:7b-instruct
ANALYST_MODEL=ollama/mistral-nemo:12b-instruct-2407-q4_K_M
WRITER_MODEL=ollama/llama3.1:8b
PUBLISHER_MODEL=ollama/llama3.1:8b

# --- Embeddings (Fixed) ---
EMBEDDINGS_PROVIDER=ollama
EMBEDDINGS_OLLAMA_MODEL_NAME=nomic-embed-text
EMBEDDINGS_OLLAMA_BASE_URL=http://localhost:11434

# --- Advanced Memory Configuration ---
# ChromaDB (Vector Store)
# Path relative to project root.
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=research_Assistant_memory

# Neo4j Graph Store
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print(".env updated successfully with ChromaDB + Neo4j Configs")
