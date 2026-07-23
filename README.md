# 🤖 HarshGPT — Production RAG Chatbot

> Ask anything about Harsh Nandan Shukla's projects, internships, and skills — powered by a production-grade Retrieval-Augmented Generation pipeline.

---

**🌐 Live Demo:** [harsh-gpt.streamlit.app](https://harsh-gpt.streamlit.app)  
**📡 API Docs:** [18.205.185.157:8000/docs](http://18.205.185.157:8000/docs)  
**🐳 Docker Hub:** [hnsiitj/harshgpt](https://hub.docker.com/r/hnsiitj/harshgpt)

---

## 📌 What is HarshGPT?

HarshGPT is a **production-grade RAG (Retrieval-Augmented Generation) chatbot** that answers natural-language questions strictly grounded in 5 personal documents — internship reports, project reports, and a resume . It is fully containerised, deployed on AWS EC2, and served via a Streamlit Cloud frontend.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│       STREAMLIT CLOUD (Frontend)        │
│     harsh-gpt.streamlit.app            │
└──────────────────┬──────────────────────┘
                   │  POST /chat
                   ▼
┌─────────────────────────────────────────┐
│        AWS EC2 — t3.small (Ubuntu)      │
│  ┌──────────┐ ┌────────┐ ┌──────────┐  │
│  │  Qdrant  │ │ Redis  │ │ FastAPI  │  │
│  │  :6333   │ │ :6379  │ │  :8000   │  │
│  └──────────┘ └────────┘ └──────────┘  │
│       docker-compose.yml               │
└─────────────────────────────────────────┘
```

---

## ⚙️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **LLM** | GPT-4o mini | 95% cheaper than GPT-4o, sufficient for PDF Q&A |
| **Embeddings** | text-embedding-3-small | Cost-optimised, high quality |
| **Vector DB** | Qdrant (Docker) | Production-grade, $0 local cost, persistent volumes |
| **Framework** | LangChain | Retriever abstractions, prompt chaining |
| **PDF Parsing** | PDFPlumber | Table-aware extraction (vs PyPDF which breaks tables) |
| **Backend** | FastAPI | Async, auto Swagger docs, Pydantic validation |
| **Cache** | Redis | 24hr TTL, MD5-keyed, eliminates repeat API calls |
| **Rate Limiting** | SlowAPI + Redis | 3 req/hour/IP, persists across restarts |
| **Frontend** | Streamlit | Fast UI, chat interface, cloud deployment |
| **Container** | Docker Compose | FastAPI + Qdrant + Redis in single stack |
| **Deploy** | AWS EC2 + Streamlit Cloud | Backend on EC2, frontend on Streamlit Cloud |

---

## 🔄 Pipeline

### Ingestion (one-time)
```
PDFs → PDFPlumberLoader → RecursiveCharacterTextSplitter (500 tokens, 50 overlap)
     → Metadata tagging (source, page, chunk_index)
     → MD5 deterministic chunk IDs (prevents duplicates on re-run)
     → text-embedding-3-small → Qdrant (nested payload)
```

### Query (every request)
```
Question → Rate limit check (Redis)
         → Cache check MD5(query) → HIT: return instantly
         → Smart query router (keyword → auto source filter)
         → Qdrant MMR retrieval (fetch_k=20, k=3, λ=0.5)
         → Build context with source attribution
         → GPT-4o mini (temperature=0, system prompt guardrail)
         → Cache result → Return answer + sources
```

---

## 🚀 Key Features

- **MMR Retrieval** — Maximal Marginal Relevance avoids redundant chunks, balances relevance (70%) and diversity (30%)
- **Smart Query Router** — Auto-detects skills/education keywords → applies resume-only filter automatically
- **Redis Caching** — Same question never hits OpenAI twice; 24-hour TTL
- **Guardrail** — System prompt strictly grounds answers in documents; off-topic questions return a clean fallback
- **Deterministic Chunk IDs** — MD5(source + page + chunk_index) prevents duplicate ingestion on container restart
- **Ingest-on-Startup Check** — Skips ingestion if Qdrant collection exists → saves API credits
- **Persistent Vector Storage** — Docker named volume survives container restarts
- **Rate Limiting** — 3 requests/hour per IP, Redis-backed (survives server restarts)

---

## 📁 Project Structure

```
HarshGPT/
├── backend/
│   ├── Dockerfile
│   └── app/
│       ├── main.py               # FastAPI app, routes, models
│       └── services/
│           ├── ingestion.py      # PDF loading, chunking, Qdrant ingest
│           ├── retriever.py      # Qdrant vectorstore, MMR retriever
│           ├── llm_chain.py      # LangChain chain, guardrail, query router
│           └── cache.py          # Redis get/set with MD5 keying
├── frontend/
│   └── app.py                    # Streamlit chat UI
├── database/                     # PDFs (gitignored — personal data)
├── docker-compose.yml            # Qdrant + Redis + FastAPI
├── requirements.txt
└── .env                          # OPENAI_API_KEY (gitignored)
```

---

## 🛠️ Local Setup

### Prerequisites
- Docker Desktop
- Python 3.12
- OpenAI API key

### 1. Clone the repo
```bash
git clone https://github.com/Harsh-nandanshukla/HarshGPT.git
cd HarshGPT
```

### 2. Add your PDFs
```
database/
├── your_resume.pdf
├── project_report.pdf
└── internship_report.pdf
```

### 3. Create `.env`
```
OPENAI_API_KEY=sk-your-key-here
```

### 4. Run with Docker Compose
```bash
docker-compose up --build
```

This starts Qdrant, Redis, and FastAPI together. Ingestion runs automatically on first startup.

### 5. Run Streamlit frontend
```bash
pip install streamlit requests
streamlit run frontend/app.py
```

**API Docs:** http://localhost:8000/docs  
**Streamlit UI:** http://localhost:8501

---

## 🌐 Deployment

### Backend → AWS EC2

```bash
# SSH into EC2
ssh -i bot.pem ubuntu@<EC2-IP>

# Clone repo
git clone https://github.com/Harsh-nandanshukla/HarshGPT.git
cd HarshGPT

# Upload PDFs (from local machine)
scp -i bot.pem -r ./database ubuntu@<EC2-IP>:~/HarshGPT/

# Create .env
echo "OPENAI_API_KEY=sk-your-key" > .env

# Start everything
docker-compose up -d
```

Open port **8000** in EC2 Security Group inbound rules.

### Frontend → Streamlit Cloud

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select repo → `frontend/app.py` → Python 3.12
4. Add secret: `API_URL = "http://<EC2-IP>:8000/chat"`
5. Deploy

---

## 📡 API Reference

### `POST /chat`

**Request:**
```json
{
  "question": "What are Harsh's technical skills?"
}
```

**Response:**
```json
{
  "answer": "Harsh's technical skills include...",
  "sources": [
    {"source": "Harsh_IITJ_Resume.pdf", "page": 0}
  ]
}
```

**Rate limit:** 3 requests/hour per IP  
**Max question length:** 120 characters

### `GET /health`
```json
{"status": "healthy"}
```

---

## 💸 Cost Analysis

With a $5 OpenAI budget:

| Component | Cost |
|---|---|
| Ingestion (75 chunks, one-time) | ~$0.001 |
| Per query (cache miss) | ~$0.001 |
| Per query (cache hit) | $0.000 |
| Estimated queries on $5 | ~4,000+ |

---

## 🙋 About

Built by **Harsh Nandan Shukla**  
[GitHub](https://github.com/Harsh-nandanshukla) · [LinkedIn](https://www.linkedin.com/in/harsh-shukla-a87b0a2b0)
