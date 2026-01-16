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
        try:
            docs = drive_service.list_documents_in_folder(settings.google_drive_folder_id)
        except Exception as e:
            error_msg = str(e)
            
            # Handle permission/access errors
            if "403" in error_msg or "Permission denied" in error_msg:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Permission Denied",
                        "message": "Cannot access Google Drive folder. Please ensure:",
                        "steps": [
                            "1. The folder is shared with your service account email",
                            "2. Service account has at least 'Viewer' access",
                            "3. Check GOOGLE_DRIVE_FOLDER_ID in your .env file",
                            "4. Both Google Drive API and Google Docs API are enabled"
                        ],
                        "service_account_help": "Find your service account email in credentials.json under 'client_email'"
                    }
                )
            
            # Handle folder not found
            elif "404" in error_msg or "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Folder Not Found",
                        "message": "The specified Google Drive folder does not exist.",
                        "steps": [
                            "1. Check your GOOGLE_DRIVE_FOLDER_ID in .env file",
                            "2. Verify the folder exists in Google Drive",
                            "3. Make sure you copied the correct folder ID from the URL"
                        ],
                        "example": "Folder URL: https://drive.google.com/drive/folders/YOUR_FOLDER_ID"
                    }
                )
            
            raise
        
        if not docs:
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "No Documents Found",
                    "message": "The folder exists but contains no Google Docs.",
                    "steps": [
                        "1. Add Google Docs to your shared folder",
                        "2. Make sure they are Google Docs (not PDFs or Word files)",
                        "3. Check that documents aren't in subfolders"
                    ]
                }
            )
        
        print(f"Found {len(docs)} documents in folder")
        
        # Initialize vector store
        vector_store = VectorStore(dimension=embedding_engine.dimension)
        total_chunks = 0
        processed_docs = 0
        failed_docs = []
        
        # Process each document
        for doc in docs:
            try:
                print(f"Processing: {doc['name']} ({doc['id']})")
                
                # Read document
                try:
                    text = drive_service.get_document_content(doc['id'])
                except Exception as e:
                    error_msg = str(e)
                    
                    # Document is private/not shared
                    if "403" in error_msg or "Permission denied" in error_msg:
                        failed_docs.append({
                            "name": doc['name'],
                            "error": "Permission denied - document not shared with service account"
                        })
                        print(f"  ⚠️  Skipping {doc['name']}: Permission denied")
                        continue
                    
                    # Document deleted or invalid
                    elif "404" in error_msg:
                        failed_docs.append({
                            "name": doc['name'],
                            "error": "Document not found or deleted"
                        })
                        print(f"  ⚠️  Skipping {doc['name']}: Not found")
                        continue
                    
                    raise
                
                # Handle empty documents
                if not text or len(text.strip()) == 0:
                    failed_docs.append({
                        "name": doc['name'],
                        "error": "Document is empty"
                    })
                    print(f"  ⚠️  Skipping empty document: {doc['name']}")
                    continue
                
                # Check minimum content length
                if len(text.strip()) < 50:
                    failed_docs.append({
                        "name": doc['name'],
                        "error": f"Document too short ({len(text)} characters, minimum 50 required)"
                    })
                    print(f"  ⚠️  Skipping {doc['name']}: Too short")
                    continue
                
                # Chunk text
                chunks = chunker.chunk_text(text)
                
                if not chunks:
                    failed_docs.append({
                        "name": doc['name'],
                        "error": "Could not create valid chunks from document"
                    })
                    print(f"  ⚠️  No chunks created for: {doc['name']}")
                    continue
                
                print(f"  Created {len(chunks)} chunks")
                
                # Generate embeddings with retry logic
                max_retries = 3
                retry_delay = 2
                
                for attempt in range(max_retries):
                    try:
                        embeddings = embedding_engine.encode(chunks)
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            print(f"  Retry {attempt + 1}/{max_retries} for embeddings...")
                            import time
                            time.sleep(retry_delay)
                        else:
                            failed_docs.append({
                                "name": doc['name'],
                                "error": f"Failed to generate embeddings after {max_retries} attempts"
                            })
                            print(f"  ❌ Failed to generate embeddings for: {doc['name']}")
                            continue
                
                # Add to vector store with metadata
                metadata = {
                    'doc_id': doc['id'],
                    'doc_name': doc['name'],
                    'modified': doc['modified']
                }
                vector_store.add_documents(chunks, embeddings, metadata)
                
                total_chunks += len(chunks)
                processed_docs += 1
                print(f"  ✅ Added {len(chunks)} chunks to index")
            
            except Exception as e:
                failed_docs.append({
                    "name": doc['name'],
                    "error": str(e)
                })
                print(f"  ❌ Error processing {doc['name']}: {str(e)}")
                continue
        
        if total_chunks == 0:
            error_detail = {
                "error": "No Content Indexed",
                "message": "All documents failed to index.",
                "failed_documents": failed_docs,
                "steps": [
                    "1. Check that documents have actual content",
                    "2. Ensure documents are shared with service account",
                    "3. Verify documents are Google Docs (not PDFs/Word)"
                ]
            }
            raise HTTPException(status_code=400, detail=error_detail)
        
        # Save the unified vector store
        vector_store.save(settings.vector_store_path, "all_docs")
        
        response_detail = {
            "message": f"Successfully indexed documents from folder",
            "chunks_indexed": total_chunks,
            "documents_processed": processed_docs,
            "total_documents": len(docs)
        }
        
        # Add warning if some docs failed
        if failed_docs:
            response_detail["warnings"] = {
                "failed_documents": failed_docs,
                "message": f"{len(failed_docs)} document(s) failed to index"
            }
        
        return IndexResponse(**response_detail)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Internal Server Error",
                "message": str(e),
                "steps": [
                    "1. Check server logs for details",
                    "2. Verify all environment variables are set",
                    "3. Ensure credentials.json is valid"
                ]
            }
        )


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
        # Better error handling with rate limit detection
        error_msg = str(e)
        
        # Check for rate limit errors (GROQ API)
        if "rate_limit" in error_msg.lower() or "429" in error_msg or "too many requests" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate Limit Exceeded",
                    "message": "Too many requests to the AI service. Please wait a moment.",
                    "retry_after": "30 seconds",
                    "steps": [
                        "1. Wait 30 seconds before trying again",
                        "2. Reduce the frequency of your requests",
                        "3. Consider upgrading your GROQ API plan for higher limits"
                    ]
                }
            )
        
        # Check for API authentication errors
        if "api" in error_msg.lower() or "authentication" in error_msg.lower() or "401" in error_msg:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "AI Service Unavailable",
                    "message": "Cannot connect to AI service. Please check your API key.",
                    "steps": [
                        "1. Verify GROQ_API_KEY in your .env file",
                        "2. Ensure the API key is valid and active",
                        "3. Check if your GROQ account has credits",
                        "4. Try regenerating your API key at console.groq.com"
                    ]
                }
            )
        
        # Check for embedding/model errors
        if "model" in error_msg.lower() or "embedding" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Model Service Error",
                    "message": "Error generating embeddings or processing text.",
                    "steps": [
                        "1. The embedding service may be temporarily down",
                        "2. Try again in a few moments",
                        "3. Check your internet connection"
                    ]
                }
            )
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Chat Processing Error",
                "message": error_msg,
                "steps": [
                    "1. Try asking your question differently",
                    "2. If problem persists, check server logs",
                    "3. Verify all services are running properly"
                ]
            }
        )


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
