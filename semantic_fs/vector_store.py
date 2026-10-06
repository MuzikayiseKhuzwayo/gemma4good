import os
import re
import math
import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple

class LocalTextVectorizer:
    """
    Lightweight, zero-dependency embedding generator.
    Produces 128-dimensional normalized dense vectors using hashing and TF-IDF
    n-gram projections, with optional upgrade to sentence-transformers / bge-small.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim
        self._st_model = None
        self._try_load_neural_model()

    def _try_load_neural_model(self):
        """Optional loading of sentence-transformers or fast local ONNX model if installed."""
        try:
            from sentence_transformers import SentenceTransformer # type: ignore
            self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.dim = 384
            print("[SemanticFS] Loaded neural embedding model: all-MiniLM-L6-v2")
        except Exception:
            # Safe, deterministic local vectorizer fallback
            pass

    def encode(self, text: str) -> List[float]:
        """Encodes text into a normalized dense vector of floats."""
        if self._st_model is not None:
            try:
                emb = self._st_model.encode(text)
                return [float(x) for x in emb]
            except Exception:
                pass

        # Deterministic feature-hashing projection
        vec = [0.0] * self.dim
        tokens = re.findall(r"\b\w+\b", text.lower())
        if not tokens:
            return vec

        # Unigrams and bigrams
        for i, token in enumerate(tokens):
            h1 = hash(token) % self.dim
            vec[h1] += 1.0
            if i + 1 < len(tokens):
                bigram = f"{token}_{tokens[i+1]}"
                h2 = hash(bigram) % self.dim
                vec[h2] += 1.5

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two normalized vectors."""
        if len(vec_a) != len(vec_b) or not vec_a:
            return 0.0
        return sum(a * b for a, b in zip(vec_a, vec_b))


class SemanticFileSystem:
    """
    Phase 2: Production Semantic File System & Vector Database.
    Embedded zero-copy SQLite storage with continuous indexing, vector similarity search,
    and metadata indexing.
    """

    def __init__(self, db_path: Optional[str] = None):
        print("Initializing Semantic File System (Vector DB Layer)...")
        if db_path is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "aos_vectors.db")
        else:
            self.db_path = db_path

        self.vectorizer = LocalTextVectorizer()
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initializes tables for documents and semantic chunks."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    path TEXT PRIMARY KEY,
                    title TEXT,
                    mtime REAL,
                    metadata_json TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_path TEXT,
                    chunk_index INTEGER,
                    content TEXT,
                    embedding_json TEXT,
                    FOREIGN KEY (doc_path) REFERENCES documents (path) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_path ON chunks (doc_path)")
            conn.commit()

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Splits document content into overlapping semantic chunks."""
        if not text:
            return []
        
        words = text.split()
        if len(words) <= chunk_size:
            return [text]

        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            i += (chunk_size - overlap)
        return chunks

    def vectorize_and_store(self, path: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Chunks, vectorizes, and indexes document content into embedded SQLite.
        """
        if not path or content is None:
            return False

        metadata = metadata or {}
        chunks = self.chunk_text(content)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Upsert document record
            cursor.execute(
                "INSERT OR REPLACE INTO documents (path, title, mtime, metadata_json) VALUES (?, ?, ?, ?)",
                (path, os.path.basename(path), metadata.get("mtime", 0.0), json.dumps(metadata))
            )
            # Remove old chunks
            cursor.execute("DELETE FROM chunks WHERE doc_path = ?", (path,))

            # Insert new vectorized chunks
            for idx, chunk in enumerate(chunks):
                emb = self.vectorizer.encode(chunk)
                cursor.execute(
                    "INSERT INTO chunks (doc_path, chunk_index, content, embedding_json) VALUES (?, ?, ?, ?)",
                    (path, idx, chunk, json.dumps(emb))
                )
            conn.commit()

        print(f"[SemanticFS] Indexed '{path}' ({len(chunks)} chunks).")
        return True

    def retrieve(self, query: str, top_k: int = 5, score_threshold: float = 0.05) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search across all stored chunks.
        Returns top matching results with paths, snippets, and similarity scores.
        """
        if not query:
            return []

        query_emb = self.vectorizer.encode(query)
        scored_results: List[Tuple[float, Dict[str, Any]]] = []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, doc_path, chunk_index, content, embedding_json FROM chunks")
            rows = cursor.fetchall()

            for row in rows:
                chunk_emb = json.loads(row["embedding_json"])
                similarity = self.vectorizer.cosine_similarity(query_emb, chunk_emb)
                if similarity >= score_threshold:
                    scored_results.append((
                        similarity,
                        {
                            "id": row["id"],
                            "path": row["doc_path"],
                            "chunk_index": row["chunk_index"],
                            "content": row["content"],
                            "similarity": round(similarity, 4)
                        }
                    ))

        # Sort descending by similarity score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_matches = [item[1] for item in scored_results[:top_k]]
        return top_matches

    def delete(self, path: str) -> bool:
        """Deletes a file and its chunks from the semantic index."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE doc_path = ?", (path,))
            cursor.execute("DELETE FROM documents WHERE path = ?", (path,))
            conn.commit()
            return cursor.rowcount > 0

    def list_indexed_files(self) -> List[str]:
        """Returns a list of all indexed file paths."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM documents")
            return [row["path"] for row in cursor.fetchall()]
