# Yerel LLM ile Doküman Soru-Cevap Servisi

Yerel çalışan bir LLM (Ollama) kullanarak dokümanlarınız üzerinden soru-cevap yapmanızı sağlayan RAG (Retrieval-Augmented Generation) tabanlı bir servistir.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Özellikler

- 📄 **Çoklu Doküman Desteği**: PDF, TXT, Markdown ve DOCX dosyalarını işler
- 🔍 **Semantik Arama**: Sentence-Transformers ile embedding tabanlı benzerlik araması
- 🤖 **Yerel LLM**: Ollama ile tamamen yerel çalışır, verileriniz sizde kalır
- ⚡ **Hızlı API**: FastAPI ile async, yüksek performanslı REST API
- 🎨 **Modern Arayüz**: Kullanıcı dostu web arayüzü

## 📋 Gereksinimler

- Python 3.10+
- [Ollama](https://ollama.ai/) kurulu ve çalışır durumda
- 8GB+ RAM (embedding modeli için)

## 🚀 Kurulum

### 1. Ollama Kurulumu

[Ollama](https://ollama.ai/) sitesinden işletim sisteminize uygun sürümü indirip kurun.

Model indirme:
```bash
ollama pull llama3.1:8b
```

### 2. Proje Kurulumu

```bash
# Repo'yu klonlayın
git clone https://github.com/yourusername/local-rag-service.git
cd local-rag-service

# Sanal ortam oluşturun
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 3. Servisi Başlatma

```bash
# Ollama'nın çalıştığından emin olun
ollama serve

# Yeni terminalde servisi başlatın
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Servis `http://localhost:8000` adresinde çalışmaya başlayacaktır.

## 📖 Kullanım

### Web Arayüzü

Tarayıcınızda `http://localhost:8000` adresine gidin:

1. Sol panelden doküman yükleyin (PDF, TXT, MD, DOCX)
2. Soru alanına sorunuzu yazın
3. "Sor" butonuna tıklayın veya Enter'a basın
4. Cevabı ve kaynak dokümanları görüntüleyin

### API Kullanımı

#### Sağlık Kontrolü
```bash
curl http://localhost:8000/api/health
```

#### Doküman Yükleme
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/document.pdf"
```

#### Soru Sorma
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Doküman ne hakkında?"}'
```

### API Dokümantasyonu

Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

## 🏗️ Proje Yapısı

```
local-rag-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI ana uygulama
│   ├── config.py            # Yapılandırma
│   ├── api/
│   │   └── routes.py        # API endpoint'leri
│   ├── models/
│   │   └── schemas.py       # Pydantic modelleri
│   └── services/
│       ├── llm_service.py   # Ollama entegrasyonu
│       ├── document_service.py  # Doküman işleme
│       └── vector_service.py    # ChromaDB işlemleri
├── tests/                   # Unit testler
├── static/                  # Frontend dosyaları
├── documents/               # Yüklenen dokümanlar
├── chroma_db/              # Vektör veritabanı
├── requirements.txt
└── README.md
```

## 🔧 Yapılandırma

Ortam değişkenleri veya `.env` dosyası ile yapılandırabilirsiniz:

| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| `OLLAMA_BASE_URL` | http://localhost:11434 | Ollama sunucu adresi |
| `OLLAMA_MODEL` | llama3.1:8b | Kullanılacak LLM modeli |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Embedding modeli |
| `CHUNK_SIZE` | 500 | Doküman parça boyutu |
| `TOP_K_RESULTS` | 3 | Arama sonuç sayısı |

## 🧪 Testler

```bash
# Tüm testleri çalıştır
pytest tests/ -v

# Coverage raporu ile
pytest tests/ -v --cov=app --cov-report=html
```

## 🛠️ Kullanılan Teknolojiler

| Teknoloji | Neden? |
|-----------|--------|
| **FastAPI** | Async desteği, otomatik OpenAPI dokümantasyonu, tip güvenliği |
| **Ollama** | Kolay kurulum, OpenAI uyumlu API, geniş model desteği |
| **ChromaDB** | Hafif, Python-native, kalıcı depolama |
| **Sentence-Transformers** | Ücretsiz, yerel çalışır, yüksek kaliteli embedding'ler |
| **PyMuPDF** | Hızlı ve güvenilir PDF işleme |

## 📊 Mimari

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

## 📝 Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın
