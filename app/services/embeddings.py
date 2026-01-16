from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List

class EmbeddingEngine:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize embedding model"""
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Convert texts to embeddings"""
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        """Convert single text to embedding"""
        return self.model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0]