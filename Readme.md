# 🏦 LoanSarthi

**LoanSarthi** is an AI-powered loan advisory chatbot for the Indian banking market. It helps users compare loan eligibility criteria, interest rates, and application processes across 12 major Indian banks — through a natural conversational interface.

---

## Features

- **Conversational AI** — Powered by Groq's `llama-3.3-70b-versatile` via LangChain
- **RAG Pipeline** — Static knowledge base (eligibility, documents, terms) ingested from official bank sources and retrieved via ChromaDB + HuggingFace sentence-transformers
- **Live Rate Database** — SQLite-backed structured store for real-time interest rate comparisons across banks
- **Multi-turn sessions** — Conversation history maintained per `session_id`
- **REST API** — FastAPI server with `/chat`, `/rates`, `/rates/compare`, and `/health` endpoints

---

## Banks Covered

| Bank | Home Loan | Personal Loan | Car Loan |
|---|---|---|---|
| HDFC Bank | ✅ | ✅ | ✅ |
| ICICI Bank | ✅ | ✅ | ✅ |
| Axis Bank | ✅ | ✅ | ✅ |
| State Bank of India (SBI) | ✅ | ✅ | ✅ |
| Kotak Mahindra Bank | ⏳ | ✅ | ✅ |
| IndusInd Bank | ✅ | ✅ | ✅ |
| Bank of Baroda | ✅ | ✅ | ✅ |
| Punjab National Bank (PNB) | ⏳ | ✅ | ⏳ |
| Canara Bank | ✅ | ✅ | ✅ |
| IDFC FIRST Bank | ✅ | ✅ | ⏳ |
| Federal Bank | ✅ | ⏳ | ⏳ |
| AU Small Finance Bank | ✅ | ✅ | ✅ |

✅ Confirmed from official source &nbsp;|&nbsp; ⏳ Pending — scheduled for next data pass

> Education Loan and Business/MSME Loan are out of scope for this phase.

---

## Architecture

```
User
 │
 ▼
FastAPI  (app/server.py)
 │
 ▼
LangChain Agent  (app/chatbot.py)
 ├── loan_eligibility_rag_tool  ──► ChromaDB (Docker :8001)
 │                                    └── HuggingFace all-MiniLM-L6-v2
 └── loan_rate_comparison_tool ──► SQLite  (data/loan_rates.db)
```

**Embedding model:** `all-MiniLM-L6-v2` (local, free, ~90MB, no API key needed)  
**LLM:** Groq `llama-3.3-70b-versatile` (requires `GROQ_API_KEY`)  
**Vector store:** ChromaDB running in Docker  
**Structured data:** SQLite via SQLAlchemy

---

## Project Structure

```
LoanAdvicer/
├── main.py                        # Entry point (serve / ingest / cli / seed-db)
├── Requirements.txt
├── .env                           # Not committed — see below
├── .gitignore
├── data/
│   └── loansarthi_static_content.docx   # ← Place this file here (gitignored)
└── app/
    ├── __init__.py
    ├── server.py                  # FastAPI routes
    ├── chatbot.py                 # LangChain agent + session management
    ├── rag_ingest.py              # Docx → chunks → ChromaDB
    ├── rate_tool.py               # SQLite rate query + LangChain tool
    └── database.py                # SQLAlchemy models + seed data
```

---

## Prerequisites

- Python 3.12+
- Docker (for ChromaDB)
- A Groq API key — get one free at [console.groq.com](https://console.groq.com)

---

## Setup

### 1. Clone and install dependencies

```bash
git clone Loan-Advisor 
cd LoanAdvicer

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r Requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here

# Optional overrides (defaults shown)
GROQ_MODEL=llama-3.3-70b-versatile
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION=loansarthi_static
STATIC_CONTENT_PATH=./data/loansarthi_static_content.docx
DATABASE_URL=sqlite:///./data/loan_rates.db
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
```

### 3. Start ChromaDB

```bash
docker run -d -p 8001:8000 --name chromadb chromadb/chroma:0.6.0
```

### 4. Place the static content file

Copy `loansarthi_static_content.docx` into the `data/` directory:

```
data/loansarthi_static_content.docx
```

> This file is gitignored and must be provided manually at runtime.

### 5. Initialise the database and ingest content

```bash
# Seed the rate database
python main.py seed-db

# Ingest the docx into ChromaDB (downloads ~90MB embedding model on first run)
python main.py ingest
```

---

## Running LoanSarthi

### API server

```bash
python main.py serve
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### CLI (for testing)

```bash
python main.py cli
```

---

## API Reference

### `POST /chat`

Send a message and receive a reply. Each `session_id` maintains its own conversation history.

```json
// Request
{
  "session_id": "user_123",
  "message": "What is the minimum CIBIL score for an HDFC home loan?"
}

// Response
{
  "session_id": "user_123",
  "reply": "For an HDFC home loan, the minimum CIBIL score is 650..."
}
```

### `GET /rates?loan_type=home&bank_name=SBI`

Query the live rate database with optional filters: `loan_type`, `bank_name`, `borrower_category`.

### `GET /rates/compare/{loan_type}`

Returns a formatted comparison table for `home`, `personal`, or `car`.

### `DELETE /chat/{session_id}`

Clears conversation history for a session.

### `GET /health`

```json
{ "status": "ok", "service": "LoanSarthi" }
```

---

## Re-ingesting Content

If you update the docx, force a full re-ingest:

```bash
python main.py ingest --force
```

> **Note:** After switching embedding models, always run `ingest --force` — embedding spaces are incompatible across models.

---

## Updating Loan Rates

The seed data in `app/database.py` contains indicative rates as of June 2026. To update:

1. Edit the `SEED_RATES` list in `app/database.py`, or
2. Write an ETL job that fetches fresh rates and upserts rows into the `loan_rates` table via SQLAlchemy.

---

## Known Limitations & Gaps

- Interest rates in the database are **indicative** — always advise users to confirm with the bank before applying.
- Some eligibility fields (especially CIBIL minimums at smaller banks) are **not publicly disclosed** by the bank. These are marked clearly in responses.
- Kotak Mahindra Bank home loan data is **pending** research.
- Federal Bank car loan, PNB home/car loan, and IDFC FIRST car loan data are **pending** official confirmation.
- Session history is stored **in-memory** — it is lost on server restart. For production, replace `ChatMessageHistory` with a Redis-backed store.

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Groq `llama-3.3-70b-versatile` |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (local, free) |
| Orchestration | LangChain 0.3.x |
| Vector Store | ChromaDB (Docker) |
| Structured DB | SQLite + SQLAlchemy |
| API | FastAPI + Uvicorn |
| Document parsing | python-docx |

---

## Disclaimer

LoanSarthi is an informational tool only. All rates, eligibility criteria, and terms are indicative and sourced from publicly available bank information. Always verify details directly with the bank before making any financial decisions.
