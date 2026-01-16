# 🚀 Google Docs Knowledge Chatbot - Setup & Run Guide (Folder-Based)

## 🎯 What's New: Folder-Based Approach

**This version uses a MUCH BETTER approach:**
- ✅ Share ONE folder (not individual docs)
- ✅ Add/remove docs anytime
- ✅ Automatic discovery of all docs
- ✅ Search across multiple documents
- ✅ Production-ready scalability

---

## 📁 Project Structure

```
google-docs-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   └── services/
│       ├── __init__.py
│       ├── google_docs.py      # Reads individual docs
│       ├── google_drive.py     # NEW: Lists folder contents
│       ├── chunker.py
│       ├── embeddings.py
│       ├── vector_store.py
│       └── llm.py
├── frontend/
│   ├── index.html
│   └── styles.css
├── data/
│   └── vector_store/
├── requirements.txt
├── Dockerfile
├── .env
├── credentials.json
└── README.md
```

---

## 🔧 Step 1: Prerequisites

### 1.1 Install Python 3.11+
```bash
python --version  # Should be 3.11 or higher
```

### 1.2 Get GROQ API Key
1. Go to https://console.groq.com/
2. Sign up / Log in
3. Create new API key
4. Copy the key (starts with `gsk_...`)

---

## 🗂️ Step 2: Set Up Google Drive Folder (NEW APPROACH)

### 2.1 Create Google Cloud Service Account

1. **Go to Google Cloud Console**: https://console.cloud.google.com/

2. **Create a New Project**
   - Click project dropdown → "New Project"
   - Name: "Google Docs Chatbot"
   - Click "Create"

3. **Enable APIs**
   - Go to: APIs & Services → Library
   - Enable these APIs:
     - **Google Docs API**
     - **Google Drive API** ← Important!

4. **Create Service Account**
   - Go to: APIs & Services → Credentials
   - Click "Create Credentials" → "Service Account"
   - Name: `docs-chatbot-service`
   - Click "Create and Continue"
   - Skip optional steps → "Done"

5. **Create JSON Key**
   - Click on the service account
   - Go to "Keys" tab
   - "Add Key" → "Create new key" → "JSON"
   - **Download and save as `credentials.json`**

6. **Copy Service Account Email**
   - From `credentials.json`, copy the email:
   ```json
   {
     "client_email": "service-account@project.iam.gserviceaccount.com"
   }
   ```

### 2.2 Create and Share Google Drive Folder

**This is the KEY improvement:**

1. **Create a Folder in Google Drive**
   - Go to Google Drive
   - Click "New" → "Folder"
   - Name it: `RAG_Docs` (or whatever you want)

2. **Share the Folder**
   - Right-click the folder → "Share"
   - Paste the service account email
   - Give it **"Viewer"** access (or Editor if you want)
   - Click "Send"

3. **Get Folder ID**
   - Open the folder in Google Drive
   - Look at the URL:
   ```
   https://drive.google.com/drive/folders/1abc123XYZ456
   ```
   - Copy the ID: `1abc123XYZ456`

4. **Add Google Docs to the Folder**
   - Drag and drop or create Google Docs inside this folder
   - **They automatically inherit folder permissions!**
   - No need to share each doc individually

---

## 📦 Step 3: Install Dependencies

### 3.1 Create Virtual Environment
```bash
python -m venv venv

# Activate:
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 3.2 Install Requirements
```bash
pip install -r requirements.txt
```

---

## ⚙️ Step 4: Configuration

### 4.1 Create `.env` File

```bash
GROQ_API_KEY=gsk_your_actual_groq_key_here
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
GOOGLE_DRIVE_FOLDER_ID=1abc123XYZ456
```

**Replace:**
- `gsk_your_actual_groq_key_here` with your GROQ API key
- `1abc123XYZ456` with your Google Drive folder ID

### 4.2 Add `credentials.json`

Place the downloaded JSON file in the project root.

---

## 🏃 Step 5: Run the Application

### Option A: Run Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option B: Run with Docker

```bash
# Build
docker build -t google-docs-chatbot .

# Run
docker run -p 8000:8000 --env-file .env google-docs-chatbot
```

---

## 🌐 Step 6: Access the Application

Open browser: **http://localhost:8000/static/index.html**

---

## 📝 Step 7: Use the Chatbot

### Workflow:

1. **View Documents**
   - Click "📋 View Documents"
   - See all docs in your folder

2. **Index All Documents**
   - Click "📥 Index All Documents"
   - Wait for indexing to complete
   - All docs are now searchable!

3. **Ask Questions**
   - Type questions in the chat
   - Bot searches across ALL documents
   - See which docs answered your question

4. **Update Documents**
   - Add/edit docs in your folder
   - Click "🔄 Re-Index" to update

---

## 🎯 Key Features

### Multi-Document Search
```
Question: "What are the project requirements?"
Answer: Searches across requirements.doc, specs.doc, notes.doc
Sources: Shows which docs contained the answer
```

### Auto-Discovery
```
Add new doc to folder → Re-index → Instantly searchable
```

### Source Attribution
```
Answer includes:
📄 Requirements.doc: "The project must support..."
📄 Meeting_Notes.doc: "Discussed in Q2 planning..."
```

---

## 🧪 Testing the API

### List Documents
```bash
curl http://localhost:8000/documents
```

### Index All
```bash
curl -X POST http://localhost:8000/index-all
```

### Chat
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main topics?"}'
```

### Re-index
```bash
curl -X POST http://localhost:8000/reindex
```

---

## 🐛 Troubleshooting

### Issue 1: "No documents found in folder"

**Check:**
- Is the folder ID correct in `.env`?
- Did you share the folder with the service account?
- Are there any Google Docs in the folder?

**Solution:**
```bash
# Verify folder ID
echo $GOOGLE_DRIVE_FOLDER_ID

# Check credentials
cat credentials.json | grep client_email
```

### Issue 2: "Permission denied"

**Solution:**
- Re-share the folder with the service account email
- Make sure it has at least "Viewer" access
- Check that both Drive API and Docs API are enabled

### Issue 3: "Empty documents"

**Solution:**
- Make sure docs have actual content
- Check that they're Google Docs (not PDF/Word files)
- Google Sheets/Slides won't work - only Google Docs

### Issue 4: Import errors

**Solution:**
```bash
# Make sure you're in project root
pwd  # Should show .../google-docs-chatbot

# Run from root
uvicorn app.main:app --reload
```

---

## 🔄 Typical Workflow

### Initial Setup
```bash
1. Create folder in Drive
2. Share with service account
3. Add docs to folder
4. Run: uvicorn app.main:app --reload
5. Open browser
6. Click "Index All Documents"
7. Start chatting!
```

### Daily Use
```bash
1. Add new doc to folder
2. Click "Re-Index" in UI
3. Ask questions
```

### Updating Docs
```bash
1. Edit doc in Google Drive
2. Click "Re-Index"
3. Changes are reflected immediately
```

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/documents` | GET | List all docs in folder |
| `/index-all` | POST | Index all docs in folder |
| `/index-document` | POST | Index single doc (legacy) |
| `/chat` | POST | Ask question (searches all docs) |
| `/reindex` | POST | Re-index everything |
| `/clear-index` | DELETE | Delete index |

---

## 🎨 Architecture

```
Google Drive Folder
    ↓
[Drive API] → List all docs
    ↓
[Docs API] → Read each doc
    ↓
[Chunker] → Split into chunks
    ↓
[Embeddings] → Convert to vectors
    ↓
[FAISS] → Store in unified index
    ↓
[User Question] → Query embedding
    ↓
[FAISS Search] → Find relevant chunks
    ↓
[LLM] → Generate answer
    ↓
[Response with sources]
```

---

## 🔐 Security Best Practices

### .gitignore
```
.env
credentials.json
data/
__pycache__/
*.pyc
venv/
```

### Permissions
- Use **Viewer** access (read-only)
- Don't commit credentials
- Rotate API keys regularly

---

## 📈 Advanced Features

### Adding More Documents
```bash
# Just drag into the folder!
# Then re-index
```

### Different File Types
```python
# Currently supports: Google Docs
# Future: PDF, Word, Sheets
```

### Custom Folder Structure
```
RAG_Docs/
├── Projects/
│   ├── Project_A.gdoc
│   └── Project_B.gdoc
├── Meetings/
│   ├── Q1_Notes.gdoc
│   └── Q2_Notes.gdoc
└── Documentation/
    └── README.gdoc

# The bot searches ALL of them!
```

---

## ✅ Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] GROQ API key obtained
- [ ] Google Cloud project created
- [ ] **Google Drive API enabled** ← Important!
- [ ] Google Docs API enabled
- [ ] Service account created
- [ ] `credentials.json` downloaded
- [ ] **Folder created in Google Drive**
- [ ] **Folder shared with service account**
- [ ] **Folder ID copied**
- [ ] Google Docs added to folder
- [ ] `.env` configured with folder ID
- [ ] Dependencies installed
- [ ] App running
- [ ] Browser opened

---

## 🎯 Why This Approach is Better

| Old Way | New Way (Folder) |
|---------|------------------|
| Share each doc individually | Share folder once |
| Single document search | Multi-document search |
| Manual tracking | Auto-discovery |
| Static | Dynamic updates |
| Not scalable | Production-ready |

---

**You're ready to go! 🎉**

Drop docs in your folder, index once, search everything!