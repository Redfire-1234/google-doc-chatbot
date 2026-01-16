from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List

class TextChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into semantic chunks"""
        if not text or len(text.strip()) == 0:
            return []
        
        chunks = self.splitter.split_text(text)
        # Filter out very small chunks
        chunks = [chunk for chunk in chunks if len(chunk.strip()) > 50]
        return chunks