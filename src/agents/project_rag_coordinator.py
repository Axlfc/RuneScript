import json
import logging
import os

from sentence_transformers import SentenceTransformer

from src.agents.project_rag_ingestion_component import RAGIngestionAgent


class ProjectRAGCoordinator:
    def __init__(self, project_path, use_ollama=True, state=None):
        self.project_path = project_path
        self.vector_store_path = os.path.join(project_path, "vector_store")
        os.makedirs(self.vector_store_path, exist_ok=True)
        self.use_ollama = use_ollama
        self.state = state  # <--- THIS
        if self.state is None:
            logging.warning(
                "ProjectRAGCoordinator was initialized without a state manager. Some logging will be skipped.")
        self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize empty index if it doesn't exist
        if not os.path.exists(os.path.join(self.vector_store_path, "index.faiss")):
            self._create_empty_index()

    def _create_empty_index(self):
        """Create an empty FAISS index."""
        import faiss
        dimension = self.sentence_transformer.get_sentence_embedding_dimension()
        index = faiss.IndexFlatL2(dimension)
        faiss.write_index(index, os.path.join(self.vector_store_path, "index.faiss"))

        # Also create empty metadata
        with open(os.path.join(self.vector_store_path, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump({"chunks": [], "count": 0}, f)

    def embed_current_vault(self):
        """Process all files in the project and embed them for RAG."""
        logging.info("Embedding current project files for RAG...")
        rag_agent = RAGIngestionAgent(self.project_path)
        result = rag_agent.process()

        if result["success"]:
            logging.info(f"Successfully embedded {result['count']} chunks for RAG")
            self.state.log_task(f"Updated RAG knowledge with {result['count']} text chunks")
        else:
            logging.warning(f"Failed to update RAG knowledge: {result['message']}")
            self.state.log_error(f"RAG embedding failed: {result['message']}")

        return result["success"]

    def log_ai_response(self, stage, response):
        """Log AI responses in the vector store."""
        try:
            # Add the AI response to the metadata
            metadata_path = os.path.join(self.vector_store_path, "metadata.json")

            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {"chunks": [], "count": 0}

            # Add this response as a chunk
            chunk = f"AI Response for stage '{stage}': {response[:500]}"  # Truncate very long responses
            metadata["chunks"].append(chunk)
            metadata["count"] = len(metadata["chunks"])

            # Save updated metadata
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            # Update the embeddings
            if metadata["chunks"]:
                import faiss
                embeddings = self.sentence_transformer.encode(metadata["chunks"])
                dimension = embeddings.shape[1]
                index = faiss.IndexFlatL2(dimension)
                index.add(embeddings)
                faiss.write_index(index, os.path.join(self.vector_store_path, "index.faiss"))

            logging.info(f"Added AI response for stage '{stage}' to RAG knowledge")
            return True
        except Exception as e:
            logging.error(f"Failed to log AI response: {e}")
            return False

    def query(self, query: str, top_k: int = 3, as_context: bool = False) -> list:
        """
        Query the embedded chunks for similar context.
        Returns a list of result dicts with 'text' and 'score'.
        If as_context=True, returns a list of formatted text snippets.
        """
        try:
            # Check if index exists
            index_path = os.path.join(self.vector_store_path, "index.faiss")
            metadata_path = os.path.join(self.vector_store_path, "metadata.json")

            if not os.path.exists(index_path) or not os.path.exists(metadata_path):
                logging.warning("FAISS index or metadata not found - creating empty ones")
                self._create_empty_index()
                return []

            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            if not metadata["chunks"]:
                logging.warning("No chunks in metadata - returning empty results")
                return []

            # Load index
            import faiss
            index = faiss.read_index(index_path)

            # Query
            query_vector = self.sentence_transformer.encode([query])
            distances, indices = index.search(query_vector, min(top_k, index.ntotal))

            # Get results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(metadata["chunks"]):
                    results.append({
                        "text": metadata["chunks"][idx],
                        "score": float(distances[0][i])
                    })

            if as_context:
                return [r["text"] for r in results]

            return results
        except Exception as e:
            logging.error(f"Error querying similar context: {e}")
            return []

