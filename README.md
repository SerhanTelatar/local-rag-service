# Local LLM Document Question-Answering Service

A RAG (Retrieval-Augmented Generation) based service that allows you to ask questions about your documents using a locally running LLM (Ollama).

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Features

- 📄 **Multiple Document Support**: Process PDF, TXT, Markdown and DOCX files
- 🔍 **Semantic Search**: Embedding-based similarity search with Sentence-Transformers
- 🤖 **Local LLM**: Runs completely locally with Ollama, your data stays private
- ⚡ **Fast API**: Async, high-performance REST API with FastAPI
- 🎨 **Modern Interface**: User-friendly web interface

## 📋 Requirements

- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- 8GB+ RAM (for embedding model)

## 🚀 Installation

### 1. Ollama Setup

Download and install [Ollama](https://ollama.ai/) for your operating system.

Download a model:
```bash
ollama pull llama3.1:8b
```

### 2. Project Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/local-rag-service.git
cd local-rag-service

# Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Start the Service

```bash
# Make sure Ollama is running
ollama serve

# In a new terminal, start the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at `http://localhost:8000`.

## 📖 Usage

### Web Interface

Go to `http://localhost:8000` in your browser:

1. Upload a document from the left panel (PDF, TXT, MD, DOCX)
2. Type your question in the input field
3. Click "Ask" or press Enter
4. View the answer and source documents

### API Usage

#### Health Check
```bash
curl http://localhost:8000/api/health
```

#### Upload Document
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/document.pdf"
```

#### Ask Question
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the document about?"}'
```

### API Documentation

Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

## 🏗️ Project Structure

```
local-rag-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI main application
│   ├── config.py            # Configuration
│   ├── api/
│   │   └── routes.py        # API endpoints
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── services/
│       ├── llm_service.py   # Ollama integration
│       ├── document_service.py  # Document processing
│       └── vector_service.py    # ChromaDB operations
├── tests/                   # Unit tests
├── static/                  # Frontend files
├── documents/               # Uploaded documents
├── chroma_db/              # Vector database
├── requirements.txt
└── README.md
```

## 🔧 Configuration

You can configure via environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | http://localhost:11434 | Ollama server address |
| `OLLAMA_MODEL` | llama3.1:8b | LLM model to use |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Embedding model |
| `CHUNK_SIZE` | 500 | Document chunk size |
| `TOP_K_RESULTS` | 3 | Number of search results |

## 🧪 Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=html
```

## 🛠️ Technologies Used

| Technology | Why? |
|------------|------|
| **FastAPI** | Async support, automatic OpenAPI documentation, type safety |
| **Ollama** | Easy setup, OpenAI-compatible API, wide model support |
| **ChromaDB** | Lightweight, Python-native, persistent storage |
| **Sentence-Transformers** | Free, runs locally, high-quality embeddings |
| **PyMuPDF** | Fast and reliable PDF processing |

## 📊 Architecture

```
┌─────────────┐     ┌─────────────────────────────────────────┐
│  Web UI     │────▶│              FastAPI                     │
└─────────────┘     │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
                    │  │ Document │ │  Vector  │ │   LLM    │ │
                    │  │ Service  │ │  Service │ │  Service │ │
                    │  └────┬─────┘ └────┬─────┘ └────┬─────┘ │
                    └───────┼────────────┼────────────┼───────┘
                            │            │            │
                    ┌───────▼───┐ ┌──────▼─────┐ ┌────▼────┐
                    │ Documents │ │  ChromaDB  │ │ Ollama  │
                    └───────────┘ └────────────┘ └─────────┘
```

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
