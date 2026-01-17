---
title: Google Docs RAG Chatbot
emoji: 📚
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# 📚 Google Docs Knowledge Chatbot

A production-ready RAG (Retrieval-Augmented Generation) chatbot that reads content from Google Docs and answers questions based on the documents. Built with FastAPI, GROQ LLM, and FAISS vector search.

## 🚀 Live Demo

**🌐 Try it now:** [https://huggingface.co/spaces/Redfire-1234/google-doc-chatbot](https://huggingface.co/spaces/Redfire-1234/google-doc-chatbot)

---

## ✨ Features

### **Core Functionality**
- 📁 **Folder-based document access** - Index entire Google Drive folders automatically
- 🔍 **Multi-document search** - Search across all your documents simultaneously
- 💬 **Conversation history** - Remembers last 5 exchanges for context-aware responses
- 🔄 **Smart query rephrasing** - Automatically understands follow-up questions
- 📌 **Source citations** - Shows which documents answered your question
- 🔄 **Real-time updates** - Re-index when documents change

### **Advanced Features**
- 🤖 **Context-aware responses** - Uses conversation history for better understanding
- 🎯 **Ambiguous query handling** - Asks clarifying questions when needed
- ⚡ **Rate limit handling** - Graceful degradation with retry logic
- 📋 **Copy functionality** - Easy copy-paste of bot responses
- 🎨 **Modern UI** - Clean, responsive chat interface
- 🛡️ **Comprehensive error handling** - User-friendly error messages

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI |
| **LLM** | GROQ (Llama-3.3-70b-versatile) |
| **Embeddings** | SentenceTransformers (all-MiniLM-L6-v2) |
| **Vector Database** | FAISS |
| **Document Source** | Google Docs API + Google Drive API |
| **Frontend** | HTML, CSS, Vanilla JavaScript |
| **Deployment** | Hugging Face Spaces (Docker) |

---

## 📖 How to Use

### **1. Index Documents**
Click **"📥 Index All Documents"** to process your Google Drive folder. The system will:
- Fetch all Google Docs from your shared folder
- Split them into semantic chunks (800 characters each)
- Generate embeddings using SentenceTransformers
- Store in FAISS vector database

### **2. Ask Questions**
Type your question in the chat interface. The bot will:
- Search across all indexed documents
- Find the top 3 most relevant chunks
- Generate a grounded answer using GROQ LLM
- Show source citations

### **3. Follow-up Questions**
Ask follow-up questions naturally! The bot:
- Remembers the last 5 exchanges
- Automatically rephrases your question with context
- Understands references like "it", "that", "benefits"

### **4. Re-index When Needed**
Click **"🔄 Re-Index"** when you:
- Add new documents to your folder
- Update existing documents
- Want to refresh the knowledge base

---

## 🏗️ Architecture

```
┌─────────────────┐
│  User Question  │
└────────┬────────┘
         ↓
┌────────────────────────┐
│ Query Clarity Check    │ ← Only on first question
└────────┬───────────────┘
         ↓
┌────────────────────────┐
│ Query Rephrasing       │ ← Adds conversation context
└────────┬───────────────┘
         ↓
┌────────────────────────┐
│ Embedding Generation   │ ← SentenceTransformers
└────────┬───────────────┘
         ↓
┌────────────────────────┐
│ FAISS Vector Search    │ ← Find top-3 relevant chunks
└────────┬───────────────┘
         ↓
┌────────────────────────┐
│ LLM (GROQ)            │ ← Generate grounded answer
└────────┬───────────────┘
         ↓
┌────────────────────────┐
│ Response + Citations   │
└────────────────────────┘
```

---

## 🎯 RAG Pipeline Details

### **1. Document Ingestion**
```python
Google Drive Folder
    ↓
Fetch all Google Docs via API
    ↓
Split into chunks (800 chars, 150 overlap)
    ↓
Generate embeddings (384-dim vectors)
    ↓
Store in FAISS index with metadata
```

### **2. Query Processing**
```python
User Question
    ↓
Check clarity (first question only)
    ↓
Rephrase with conversation context
    ↓
Generate query embedding
    ↓
FAISS similarity search (L2 distance)
    ↓
Retrieve top-3 most similar chunks
```

### **3. Answer Generation**
```python
Retrieved Context + Question + History
    ↓
GROQ LLM (Llama-3.3-70b)
    ↓
Temperature: 0.3 (balanced)
Max tokens: 600
    ↓
Grounded Answer + Source Citations
```

---

## 🔧 Local Development Setup

### **Prerequisites**
- Python 3.11+
- GROQ API key ([Get it here](https://console.groq.com/))
- Google Cloud service account with:
  - Google Docs API enabled
  - Google Drive API enabled

### **Installation**

```bash
# 1. Clone repository
git clone https://github.com/Redfire-1234/google-doc-chatbot.git
cd google-doc-chatbot

# 2. Create virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Create .env file with:
GROQ_API_KEY=your_groq_api_key
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id

# 5. Add your Google Cloud credentials
# Place credentials.json in project root

# 6. Run locally
uvicorn app.main:app --reload --port 8000
```

### **Access locally:**
Open: `http://localhost:8000`

---

## 🔐 Google Cloud Setup

### **1. Create Service Account**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable APIs:
   - Google Docs API
   - Google Drive API
4. Create service account
5. Download JSON credentials
6. Save as `credentials.json`

### **2. Share Google Drive Folder**
1. Create a folder in Google Drive
2. Right-click → Share
3. Add service account email (from `credentials.json`)
4. Give "Viewer" access
5. Copy folder ID from URL:
   ```
   https://drive.google.com/drive/folders/YOUR_FOLDER_ID
   ```

### **3. Add Google Docs**
- Add Google Docs to your shared folder
- They automatically inherit folder permissions
- No need to share individual documents

---

## 📊 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your GROQ API key | `gsk_...` |
| `GOOGLE_DRIVE_FOLDER_ID` | Shared Google Drive folder ID | `1abc123XYZ456` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to credentials.json | `credentials.json` |
| `GOOGLE_CREDENTIALS_BASE64` | Base64 encoded credentials (HF Spaces) | `eyJ0eXA...` |

---

## 🐳 Docker Deployment

### **Build and Run**
```bash
# Build image
docker build -t google-docs-chatbot .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e GOOGLE_DRIVE_FOLDER_ID=your_folder_id \
  -v $(pwd)/credentials.json:/app/credentials.json \
  google-docs-chatbot
```

### **Using Docker Compose**
```yaml
version: '3.8'
services:
  chatbot:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./credentials.json:/app/credentials.json
      - ./data:/app/data
```

---

## 🧪 Edge Cases Handled

| Edge Case | Handling |
|-----------|----------|
| Empty documents | Skipped with warning message |
| Private/unshared docs | Permission error with fix instructions |
| Wrong folder ID | Clear error with setup steps |
| No documents in folder | Helpful message with suggestions |
| Ambiguous queries | Context-aware or asks for clarification |
| Rate limits | Retry logic + user-friendly message |
| Invalid API keys | Authentication error with fix steps |
| Network errors | Connection check message |
| Too short documents | Minimum length warning (50 chars) |
| Deleted documents | Graceful skip with notification |
| Irrelevant questions | "No information" response |

---

## 📈 Performance Metrics

- **Indexing Speed**: ~2-3 seconds per document
- **Query Response Time**: ~1-2 seconds
- **Embedding Dimension**: 384
- **Chunk Size**: 800 characters
- **Chunk Overlap**: 150 characters
- **Top-K Retrieval**: 3 chunks
- **Conversation History**: 5 exchanges (10 messages)

---

## 🔒 Security & Privacy

- ✅ API keys stored as environment variables
- ✅ Credentials never committed to Git
- ✅ Service account with read-only access
- ✅ No data stored permanently (in-memory processing)
- ✅ HTTPS encryption (on HuggingFace Spaces)
- ✅ Rate limiting protection

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Redfire-1234**

- GitHub: [@Redfire-1234](https://github.com/Redfire-1234)
- HuggingFace: [@Redfire-1234](https://huggingface.co/Redfire-1234)

---

## 🙏 Acknowledgments

- **GROQ** for fast LLM inference
- **Hugging Face** for hosting platform
- **Google Cloud** for Docs/Drive APIs
- **SentenceTransformers** for embeddings
- **FAISS** for vector search

---

## 🔗 Links

- **Live Demo**: [https://huggingface.co/spaces/Redfire-1234/google-doc-chatbot](https://huggingface.co/spaces/Redfire-1234/google-doc-chatbot)
- **GitHub Repository**: [https://github.com/Redfire-1234/google-doc-chatbot](https://github.com/Redfire-1234/google-doc-chatbot)
- **Documentation**: See `SETUP_AND_RUN.md` for detailed setup
- **Deployment Guide**: See `HUGGINGFACE_DEPLOYMENT.md`

---

## 📞 Support

If you encounter any issues:

1. Check the [Setup Guide](SETUP_AND_RUN.md)
2. Review [Common Issues](SETUP_AND_RUN.md#troubleshooting)
3. Open an issue on GitHub
4. Contact via HuggingFace Space discussions

---

## 📝 Changelog

### Version 2.0.0 (Current)
- ✅ Folder-based multi-document support
- ✅ Conversation history (5 exchanges)
- ✅ Smart query rephrasing
- ✅ Comprehensive edge case handling
- ✅ Copy message functionality
- ✅ HuggingFace Spaces deployment

### Version 1.0.0
- Initial release with single document support

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by Redfire-1234

</div>
