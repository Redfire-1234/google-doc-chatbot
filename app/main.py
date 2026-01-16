from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os

from app.config import get_settings
from app.models import ChatRequest, ChatResponse, IndexRequest, IndexResponse, DocumentInfo
from app.services.google_drive import GoogleDriveService
from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingEngine
from app.services.vector_store import VectorStore
from app.services.llm import LLMService

# Initialize FastAPI app
app = FastAPI(
    title="Google Docs Knowledge Chatbot",
    description="RAG-based chatbot for Google Docs with folder support",
    version="2.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Display clickable link on startup"""
    print("\n" + "="*70)
    print("🚀 Google Docs Knowledge Chatbot is running!")
    print("="*70)
    print("\n📱 Access the application here:")
    print("\n   👉 \033[94m\033[4mhttp://localhost:8000/static/index.html\033[0m\n")
    print("="*70)
    print("\n💡 Quick Tips:")
    print("   • Click 'Index All Documents' to get started")
    print("   • Make sure your Google Drive folder is shared")
    print("   • Press CTRL+C to stop the server")
    print("\n" + "="*70 + "\n")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get settings
settings = get_settings()

# Initialize services
drive_service = GoogleDriveService(settings.google_application_credentials)
chunker = TextChunker(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
embedding_engine = EmbeddingEngine()
llm_service = LLMService(settings.groq_api_key)

# Create data directory
os.makedirs(settings.vector_store_path, exist_ok=True)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Google Docs Knowledge Chatbot API v2.0",
        "features": ["folder-based", "multi-document", "auto-discovery"]
    }


@app.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """
    List all documents in the configured Google Drive folder
    """
    try:
        docs = drive_service.list_documents_in_folder(settings.google_drive_folder_id)
        
        # Check which ones are indexed
        result = []
        for doc in docs:
            indexed = os.path.exists(
                os.path.join(settings.vector_store_path, f"all_docs_index.faiss")
            )
            result.append(DocumentInfo(
                id=doc['id'],
                name=doc['name'],
                modified=doc['modified'],
                indexed=indexed
            ))
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@app.post("/index-all", response_model=IndexResponse)
async def index_all_documents():
    """
    Index ALL documents in the Google Drive folder
    
    This is the recommended approach:
    - Automatically discovers all docs in folder
    - Creates one unified vector store
    - No need to index individually
    """
    try:
        # Get all documents in folder
        docs = drive_service.list_documents_in_folder(settings.google_drive_folder_id)
        
        if not docs:
            raise HTTPException(status_code=404, detail="No documents found in the configured folder")
        
        print(f"Found {len(docs)} documents in folder")
        
        # Initialize vector store
        vector_store = VectorStore(dimension=embedding_engine.dimension)
        total_chunks = 0
        
        # Process each document
        for doc in docs:
            try:
                print(f"Processing: {doc['name']} ({doc['id']})")
                
                # Read document
                text = drive_service.get_document_content(doc['id'])
                
                if not text or len(text.strip()) == 0:
                    print(f"  Skipping empty document: {doc['name']}")
                    continue
                
                # Chunk text
                chunks = chunker.chunk_text(text)
                
                if not chunks:
                    print(f"  No chunks created for: {doc['name']}")
                    continue
                
                print(f"  Created {len(chunks)} chunks")
                
                # Generate embeddings
                embeddings = embedding_engine.encode(chunks)
                
                # Add to vector store with metadata
                metadata = {
                    'doc_id': doc['id'],
                    'doc_name': doc['name'],
                    'modified': doc['modified']
                }
                vector_store.add_documents(chunks, embeddings, metadata)
                
                total_chunks += len(chunks)
                print(f"  Added {len(chunks)} chunks to index")
            
            except Exception as e:
                print(f"  Error processing {doc['name']}: {str(e)}")
                continue
        
        if total_chunks == 0:
            raise HTTPException(status_code=400, detail="No valid content to index")
        
        # Save the unified vector store
        vector_store.save(settings.vector_store_path, "all_docs")
        
        return IndexResponse(
            message=f"Successfully indexed all documents from folder",
            chunks_indexed=total_chunks,
            documents_processed=len(docs)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexing documents: {str(e)}")


@app.post("/index-document", response_model=IndexResponse)
async def index_single_document(request: IndexRequest):
    """
    Index a single document (legacy support)
    
    Note: It's better to use /index-all to index the entire folder
    """
    try:
        if not request.document_id:
            # If no doc ID provided, index all
            return await index_all_documents()
        
        document_id = request.document_id
        
        # Read document
        print(f"Reading document: {document_id}")
        text = drive_service.get_document_content(document_id)
        metadata = drive_service.get_document_metadata(document_id)
        
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Document is empty")
        
        # Chunk text
        chunks = chunker.chunk_text(text)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No valid chunks created")
        
        print(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        embeddings = embedding_engine.encode(chunks)
        
        # Load existing vector store or create new
        vector_store = VectorStore(dimension=embedding_engine.dimension)
        vector_store.load(settings.vector_store_path, "all_docs")
        
        # Add to vector store
        doc_metadata = {
            'doc_id': metadata['id'],
            'doc_name': metadata['name'],
            'modified': metadata['modified']
        }
        vector_store.add_documents(chunks, embeddings, doc_metadata)
        vector_store.save(settings.vector_store_path, "all_docs")
        
        return IndexResponse(
            message=f"Successfully indexed document: {metadata['name']}",
            chunks_indexed=len(chunks),
            documents_processed=1
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexing document: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - searches across ALL indexed documents
    
    Features:
    - Conversation history support (last 5 exchanges)
    - Query clarity checking (only for first question)
    - Automatic query rephrasing with context
    - Context-aware responses
    """
    try:
        question = request.question
        conversation_history = [msg.dict() for msg in request.conversation_history]
        
        # Step 1: Check if query needs clarification (ONLY if no conversation history)
        is_clear, clarification = llm_service.check_query_clarity(question, conversation_history)
        
        if not is_clear and clarification:
            return ChatResponse(
                answer=clarification,
                sources=[],
                is_clarification=True,
                rephrased_query=None
            )
        
        # Step 2: Rephrase query if there's conversation history
        rephrased_query = None
        search_query = question
        
        if conversation_history and len(conversation_history) > 0:
            rephrased = llm_service.rephrase_query(question, conversation_history)
            if rephrased and rephrased.lower() != question.lower():
                rephrased_query = rephrased
                search_query = rephrased
                print(f"Original: {question}")
                print(f"Rephrased: {rephrased}")
        
        # Step 3: Load the unified vector store
        vector_store = VectorStore(dimension=embedding_engine.dimension)
        
        if not vector_store.load(settings.vector_store_path, "all_docs"):
            raise HTTPException(
                status_code=404,
                detail="No documents indexed. Please use /index-all to index your folder first."
            )
        
        # Step 4: Generate query embedding (use rephrased query if available)
        query_embedding = embedding_engine.encode_single(search_query)
        
        # Step 5: Retrieve relevant chunks
        results = vector_store.search(query_embedding, k=settings.top_k_results)
        
        if not results:
            return ChatResponse(
                answer="I couldn't find any relevant information in the indexed documents to answer your question. Could you please rephrase or ask about something else?",
                sources=[],
                is_clarification=False,
                rephrased_query=rephrased_query
            )
        
        # Step 6: Extract chunks and prepare sources
        relevant_chunks = []
        sources = []
        
        for i, (chunk, distance, metadata) in enumerate(results):
            relevant_chunks.append(chunk)
            doc_name = metadata.get('doc_name', 'Unknown Document')
            sources.append(f"📄 {doc_name}: {chunk[:100]}...")
        
        # Step 7: Generate answer with conversation history
        answer = llm_service.generate_answer(
            relevant_chunks, 
            question,  # Use original question for answer generation
            conversation_history
        )
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            is_clarification=False,
            rephrased_query=rephrased_query
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Better error handling
        error_msg = str(e)
        
        # Check for rate limit errors
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait a moment and try again."
            )
        
        # Check for API errors
        if "api" in error_msg.lower() or "authentication" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail="LLM service temporarily unavailable. Please try again later."
            )
        
        raise HTTPException(status_code=500, detail=f"Error processing chat: {error_msg}")


@app.post("/reindex")
async def reindex_all():
    """
    Re-index all documents (useful when docs are updated)
    
    Call this endpoint when:
    - You've updated documents in the folder
    - You've added new documents
    - You want to refresh the index
    """
    try:
        # Clear existing index
        vector_store = VectorStore(dimension=embedding_engine.dimension)
        vector_store.clear()
        
        # Re-index everything
        return await index_all_documents()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error re-indexing: {str(e)}")


@app.delete("/clear-index")
async def clear_index():
    """Delete all indexed data"""
    try:
        index_path = os.path.join(settings.vector_store_path, "all_docs_index.faiss")
        data_path = os.path.join(settings.vector_store_path, "all_docs_data.pkl")
        
        deleted = False
        if os.path.exists(index_path):
            os.remove(index_path)
            deleted = True
        
        if os.path.exists(data_path):
            os.remove(data_path)
            deleted = True
        
        if deleted:
            return {"message": "Successfully cleared all indexed data"}
        else:
            raise HTTPException(status_code=404, detail="No index found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing index: {str(e)}")


# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")