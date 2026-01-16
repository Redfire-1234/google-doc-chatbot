import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Dict

class VectorStore:
    def __init__(self, dimension: int = 384):
        """Initialize FAISS index"""
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.chunks = []
        self.metadata = []  # Store chunk metadata (doc_id, doc_name, etc.)
        self.document_id = None
    
    def add_documents(self, chunks: List[str], embeddings: np.ndarray, doc_metadata: Dict = None):
        """Add document chunks and their embeddings to the index"""
        if embeddings.shape[0] != len(chunks):
            raise ValueError("Number of embeddings must match number of chunks")
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype('float32')
        
        # Add to FAISS index
        self.index.add(embeddings)
        self.chunks.extend(chunks)
        
        # Add metadata for each chunk
        for _ in chunks:
            self.metadata.append(doc_metadata or {})
    
    def search(self, query_embedding: np.ndarray, k: int = 3) -> List[Tuple[str, float, Dict]]:
        """Search for top-k similar chunks"""
        if self.index.ntotal == 0:
            return []
        
        # Ensure query is float32 and 2D
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunks):
                results.append((
                    self.chunks[idx],
                    float(distances[0][i]),
                    self.metadata[idx]
                ))
        
        return results
    
    def save(self, path: str, store_id: str = "all_docs"):
        """Save index and chunks to disk"""
        os.makedirs(path, exist_ok=True)
        
        # Save FAISS index
        index_path = os.path.join(path, f"{store_id}_index.faiss")
        faiss.write_index(self.index, index_path)
        
        # Save chunks and metadata
        data_path = os.path.join(path, f"{store_id}_data.pkl")
        with open(data_path, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata
            }, f)
    
    def load(self, path: str, store_id: str = "all_docs"):
        """Load index and chunks from disk"""
        index_path = os.path.join(path, f"{store_id}_index.faiss")
        data_path = os.path.join(path, f"{store_id}_data.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(data_path):
            return False
        
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        
        # Load chunks and metadata
        with open(data_path, 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.metadata = data.get('metadata', [])
        
        return True
    
    def exists(self, path: str, store_id: str = "all_docs") -> bool:
        """Check if index exists"""
        index_path = os.path.join(path, f"{store_id}_index.faiss")
        data_path = os.path.join(path, f"{store_id}_data.pkl")
        return os.path.exists(index_path) and os.path.exists(data_path)
    
    def clear(self):
        """Clear the vector store"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = []
        self.metadata = []