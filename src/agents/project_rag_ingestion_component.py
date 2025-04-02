import os
import json
import logging
from typing import List, Dict
import glob
from sentence_transformers import SentenceTransformer


class RAGIngestionAgent:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.vector_store_path = os.path.join(project_path, "vector_store")
        os.makedirs(self.vector_store_path, exist_ok=True)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # You can replace with your preferred model
        self.file_extensions = ['.py', '.md', '.txt', '.html', '.js', '.css', '.json']

    def read_project_files(self) -> Dict[str, str]:
        """Read all relevant files from the project directory."""
        file_contents = {}

        # Create a pattern to match all file extensions
        patterns = [f"**/*{ext}" for ext in self.file_extensions]

        for pattern in patterns:
            for filepath in glob.glob(os.path.join(self.project_path, pattern), recursive=True):
                # Skip the vector_store directory
                if "vector_store" in filepath or "__pycache__" in filepath:
                    continue

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        relative_path = os.path.relpath(filepath, self.project_path)
                        file_contents[relative_path] = f.read()
                except Exception as e:
                    logging.warning(f"Failed to read file {filepath}: {e}")

        return file_contents

    def extract_meaningful_chunks(self, file_contents: Dict[str, str]) -> List[str]:
        """
        Use an AI agent to extract meaningful chunks from file contents.
        This could be replaced with rule-based parsing for production use.
        """
        # Prepare the prompt for the AI
        prompt_data = {
            "project_path": self.project_path,
            "files": file_contents
        }

        # Here you would use the self.agent.process_prompt_with_ai("rag_ingestion", prompt_data)
        # For now, we'll implement a simple rule-based chunking
        chunks = []

        for filename, content in file_contents.items():
            # Process Python files
            if filename.endswith('.py'):
                # Extract docstrings and function definitions
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith('def ') or line.strip().startswith('class '):
                        func_name = line.strip()
                        docstring = ""

                        # Look for docstring
                        if i + 1 < len(lines) and '"""' in lines[i + 1] or "'''" in lines[i + 1]:
                            docstring_start = i + 1
                            docstring_end = docstring_start

                            # Find end of docstring
                            for j in range(docstring_start + 1, min(docstring_start + 10, len(lines))):
                                if '"""' in lines[j] or "'''" in lines[j]:
                                    docstring_end = j
                                    break

                            docstring = ' '.join([lines[k].strip() for k in range(docstring_start, docstring_end + 1)])

                        chunks.append(f"From {filename}: {func_name} {docstring}")

            # Process markdown files
            elif filename.endswith('.md'):
                # Split into sections by headers
                sections = []
                current_section = []

                for line in content.split('\n'):
                    if line.startswith('#'):
                        if current_section:
                            sections.append('\n'.join(current_section))
                            current_section = []
                    current_section.append(line)

                if current_section:
                    sections.append('\n'.join(current_section))

                for section in sections:
                    chunks.append(f"From {filename}: {section[:500]}")  # Limit size

            # Other file types - just add the first 500 chars
            else:
                chunks.append(f"From {filename}: {content[:500]}")

        return chunks

    def create_embeddings(self, chunks: List[str]) -> Dict:
        """Create embeddings for the chunks and save them to disk."""
        if not chunks:
            logging.warning("No meaningful chunks found to embed")
            return {"success": False, "message": "No chunks to embed", "count": 0}

        try:
            # Create embeddings
            embeddings = self.model.encode(chunks)

            # Save metadata separately for retrieval
            metadata = {
                "chunks": chunks,
                "count": len(chunks)
            }

            # Save metadata
            metadata_path = os.path.join(self.vector_store_path, "metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            # Save embeddings to FAISS index
            import faiss
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings)
            faiss.write_index(index, os.path.join(self.vector_store_path, "index.faiss"))

            logging.info(f"Successfully saved {len(chunks)} embeddings to FAISS index")
            return {"success": True, "message": f"Saved {len(chunks)} embeddings", "count": len(chunks)}

        except Exception as e:
            logging.error(f"Failed to create embeddings: {e}")
            return {"success": False, "message": str(e), "count": 0}

    def process(self) -> Dict:
        """Main process to read files, extract chunks, and create embeddings."""
        # Read all project files
        file_contents = self.read_project_files()
        logging.info(f"Read {len(file_contents)} files from project")

        if not file_contents:
            logging.warning("No files found in project directory")
            return {"success": False, "message": "No files found", "count": 0}

        # Extract meaningful chunks
        chunks = self.extract_meaningful_chunks(file_contents)
        logging.info(f"Extracted {len(chunks)} meaningful chunks from files")

        # Create and save embeddings
        result = self.create_embeddings(chunks)
        return result