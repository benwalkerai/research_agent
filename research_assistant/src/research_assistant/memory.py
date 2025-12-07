import os
import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from neo4j import GraphDatabase
import logging

# Configure Logger
logger = logging.getLogger(__name__)

class Neo4jConnection:
    """Singleton for Neo4j Driver to prevent connection leaks."""
    _driver = None

    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            try:
                cls._driver = GraphDatabase.driver(uri, auth=(user, password))
                cls._driver.verify_connectivity()
                logger.info("✅ Neo4j Driver Connected")
            except Exception as e:
                logger.error(f"⚠️ Neo4j Connection Failed: {e}")
                cls._driver = None
        return cls._driver

    @classmethod
    def close(cls):
        if cls._driver:
            cls._driver.close()
            cls._driver = None
            logger.info("Neo4j Driver Closed")

class CustomCrewMemory:
    def __init__(self):
        # --- ChromaDB Setup (Vector / Short Term) ---
        chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        
        # Configure Embeddings to match CrewAI's config (Ollama/Nomic)
        # This ensures the vectors we search against are in the same space as the agent's thoughts.
        ollama_base = os.getenv("EMBEDDINGS_OLLAMA_BASE_URL", "http://localhost:11434")
        model_name = os.getenv("EMBEDDINGS_OLLAMA_MODEL_NAME", "nomic-embed-text")
        
        self.embedding_fn = OllamaEmbeddingFunction(
            url=ollama_base,
            model_name=model_name
        )

        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        
        self.collection = self.chroma_client.get_or_create_collection(
            name=os.getenv("CHROMA_COLLECTION_NAME", "research_assistant_memory"),
            embedding_function=self.embedding_fn
        )

        # --- Neo4j Setup (Graph / Long Term) ---
        self.driver = Neo4jConnection.get_driver()

    def save(self, value: str, metadata: dict = None, agent: str = "Assistant"):
        """
        Saves a memory to both Vector Store (context) and Graph (relationships).
        """
        if not metadata: metadata = {}
        metadata['agent'] = agent
        
        # 1. Save to Vector Store
        try:
            # Check if exists (dedup logic could be added here)
            self.collection.add(
                documents=[value],
                metadatas=[metadata],
                ids=[f"{agent}_{os.urandom(8).hex()}"]
            )
            # logger.info(f"💾 Saved to Vector Memory")
        except Exception as e:
            logger.error(f"❌ ChromaDB Save Error: {e}")

        # 2. Save to Graph Store
        if self.driver:
            query = """
            MERGE (a:Agent {name: $agent})
            CREATE (m:Memory {content: $content, timestamp: datetime()})
            MERGE (a)-[:REMEMBERED]->(m)
            """
            try:
                with self.driver.session() as session:
                    session.run(query, agent=agent, content=value)
                # logger.info(f"🕸️ Linked in Knowledge Graph")
            except Exception as e:
                logger.error(f"❌ Neo4j Save Error: {e}")

    def search(self, query: str, limit: int = 3):
        """
        Retrieves context from Vector Store.
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            logger.error(f"❌ Memory Search Error: {e}")
            return []

    def close(self):
        # We generally don't close the singleton driver on individual instance close 
        # unless handling shutdown signal.
        pass
