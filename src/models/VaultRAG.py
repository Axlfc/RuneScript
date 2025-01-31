import os
import faiss
import pickle
import numpy as np
import torch
import logging
from typing import Optional, List, Dict, Tuple, Union
from datetime import datetime
import json
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS


class VaultRAG:
    def __init__(self, session_id: str, base_path: str = "data"):
        """
        Initialize VaultRAG with improved error handling and organization.

        Args:
            session_id: Unique identifier for the session
            base_path: Base directory for storing data
        """
        self.session_id = session_id
        self.base_path = base_path
        self.vector_store_path = os.path.join(base_path, "conversations", session_id, "vector_store")
        os.makedirs(self.vector_store_path, exist_ok=True)

        # File paths
        self.index_file = os.path.join(self.vector_store_path, 'index.faiss')
        self.pkl_path = os.path.join(self.vector_store_path, "index.pkl")
        self.metadata_path = os.path.join("data", "conversations", session_id, "metadata.json")
        self.vault_path = os.path.join("data", "conversations", session_id, "vault.md")

        # Initialize model
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.model.to(self.device)
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        # Initialize FAISS index
        self.index = self._load_or_create_index()
        # Initialize stores
        self.documents = []
        self.document_embeddings = {}
        self.document_ids = []
        self.embeddings = []
        self.load_metadata()

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=512,
            chunk_overlap=256
        )

    def _load_or_create_index(self) -> faiss.Index:
        """Load existing FAISS index or create a new one."""
        try:
            if os.path.exists(self.index_file):
                index = faiss.read_index(self.index_file)
                logging.info(f"Loaded existing FAISS index from {self.index_file}")
                return index
            else:
                dimension = self.model.get_sentence_embedding_dimension()
                index = faiss.IndexFlatL2(dimension)
                faiss.write_index(index, self.index_file)
                logging.info(f"Created new FAISS index with dimension {dimension}")
                return index
        except Exception as e:
            logging.error(f"Error in _load_or_create_index: {e}")
            dimension = self.model.get_sentence_embedding_dimension()
            return faiss.IndexFlatL2(dimension)

    def load_metadata(self):
        """Load existing metadata or create new if doesn't exist"""
        try:
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                    if 'embeddings' in metadata:
                        self.embeddings = metadata['embeddings']
                        self.document_ids = [emb['document_id'] for emb in metadata['embeddings']]
                        # Reconstruct FAISS index from stored embeddings
                        if self.embeddings:
                            embeddings_array = np.array([emb['vector'] for emb in metadata['embeddings']], dtype=np.float32)
                            self.index.add(embeddings_array)
                            print(f"INFO: Loaded {len(self.embeddings)} embeddings from metadata")
            else:
                self.save_metadata()
                print("INFO: Created new metadata file")
        except Exception as e:
            print(f"ERROR: Failed to load metadata: {str(e)}")
            self.embeddings = []
            self.save_metadata()

    def save_metadata(self):
        """Save current embeddings to metadata file"""
        try:
            os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)
            metadata = {
                'embeddings': self.embeddings
            }
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"INFO: Saved {len(self.embeddings)} embeddings to metadata")
        except Exception as e:
            print(f"ERROR: Failed to save metadata: {str(e)}")

    def _create_embedding(self, text: str) -> np.ndarray:
        """
        Create an embedding for the given text.

        Args:
            text: Text to embed

        Returns:
            numpy.ndarray: The embedding vector
        """
        try:
            # Log the input text for debugging
            logging.info(f"Creating embedding for text: {text[:100]}...")  # Log first 100 characters

            # Ensure text is a valid string
            if not isinstance(text, str):
                raise ValueError(f"Provided text is not a valid string. Received: {type(text)}")

            if not text.strip():
                raise ValueError("Empty text provided for embedding")

            # Convert text to embedding
            embedding = self.model.encode(text, convert_to_tensor=False)

            # Ensure embedding is a numpy array with correct shape
            if isinstance(embedding, (list, np.ndarray)):
                embedding = np.array(embedding).astype('float32')
                if len(embedding.shape) == 1:
                    embedding = embedding.reshape(1, -1)
                return embedding
            else:
                raise ValueError(f"Unexpected embedding type: {type(embedding)}")

        except Exception as e:
            logging.error(f"Error creating embedding: {e}")
            raise

    def store_embedding(self, document_id, content):
        """Store an embedding for a document"""
        try:
            print(f"INFO: Storing embedding for document_id: {document_id}")
            print(f"INFO: Content type: {type(content)}, Content length: {len(content)}")

            # Ensure content is in text form
            if isinstance(content, list):
                content = ' '.join(map(str, content))

            # Generate embedding as numpy array
            embedding = self.model.encode([content], convert_to_numpy=True)[0]

            # Reshape embedding for FAISS compatibility and add to index
            self.index.add(embedding.reshape(1, -1))

            # Prepare metadata with embedding as a list to ensure compatibility
            embedding_data = {
                'document_id': document_id,
                'vector': embedding.tolist(),  # Convert to list for JSON compatibility
                'timestamp': datetime.now().isoformat()
            }

            # Append metadata to the embeddings list (must be a list of dicts)
            if isinstance(self.embeddings, list):  # Ensure embeddings is a list
                self.embeddings.append(embedding_data)
            else:
                print("ERROR: 'self.embeddings' should be a list.")
                return  # Exit if embeddings is not in the correct format

            # Ensure document IDs are tracked in list form
            if isinstance(self.document_ids, list):
                self.document_ids.append(document_id)
            else:
                print("ERROR: 'self.document_ids' should be a list.")
                return  # Exit if document_ids is not in the correct format

            # Save updated metadata
            self.save_metadata()
            print(f"INFO: Successfully stored embedding for {document_id}")

        except Exception as e:
            print(f"ERROR: Failed to store embedding: {str(e)}")


    def save_pickle_data(self) -> None:
        """Save document data to pickle file."""
        try:
            pickle_data = {
                'documents': self.documents,
                'embeddings': self.document_embeddings
            }
            with open(self.pkl_path, 'wb') as f:
                pickle.dump(pickle_data, f)
        except Exception as e:
            logging.error(f"Error saving pickle data: {e}")

    def query(self, query_embedding, top_k=3):
        if self.index is None or self.index.ntotal == 0:
            print("FAISS index is empty.")
            return []

        distances, indices = self.index.search(query_embedding, top_k)
        print(f"Indices returned by FAISS: {indices}")
        print(f"Length of self.document_ids: {len(self.document_ids)}")
        results = []
        for i, idx_list in enumerate(indices):
            for j, idx in enumerate(idx_list):
                if idx < len(self.document_ids):
                    doc_id = self.document_ids[idx]
                    results.append((doc_id, distances[i][j]))
                else:
                    print(f"Index out of range: {idx}")
        return results

    def update_embeddings(self, doc_name=None):
        # Load content from vault
        with open(self.vault_path, 'r', encoding='utf-8') as f:
            content = f.read()
        try:
            print("INFO: Updating embeddings...")

            # Split content into chunks
            chunks = self.chunk_content(content)

            # Generate embeddings for each chunk
            self.embeddings = self.model.encode(chunks, convert_to_numpy=True)
            self.document_ids = [f'vault_content_{i}' for i in range(len(chunks))]

            # Initialize FAISS index
            embedding_dimension = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(embedding_dimension)
            self.index.add(self.embeddings)

            print(f"Embeddings updated. Total documents: {len(self.document_ids)}")
            return True

        except Exception as e:
            print(f"ERROR: Failed to update embeddings: {str(e)}")

    def chunk_content(self, content, chunk_size=500):
        # Split content into chunks of specified size
        words = content.split()
        return [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

    @staticmethod
    def cosine_similarity(embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        return np.dot(embedding_a, embedding_b) / (
                np.linalg.norm(embedding_a) * np.linalg.norm(embedding_b)
        )