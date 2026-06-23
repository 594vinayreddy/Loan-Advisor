"""
server.py — FastAPI server exposing the LoanSarthi chatbot via:

  POST /chat          — single-turn REST endpoint (stateless, session_id-based)
  GET  /rates         — query the live rate DB directly
  GET  /rates/compare — formatted rate comparison for a loan type
  GET  /health        — health check

Session management: conversation history is stored per session_id using
LangChain's RunnableWithMessageHistory + in-memory ChatMessageHistory.
For production, replace with Redis-backed message history.

Run with:
    uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations
import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import init_db, seed_rates, get_db
from app.rag_ingest import ingest
from app.chatbot import build_agent
from app.rate_tool import query_rates, compare_rates

# Single shared agent instance (history is managed per session_id internally)
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


# ── Startup ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀  LoanSarthi starting up …")
    init_db()
    seed_rates()
    ingest(force=False)  # no-op if vector store already exists
    get_agent()          # warm up the agent on startup
    print("✅  Ready.")
    yield
    print("👋  LoanSarthi shutting down.")


app = FastAPI(
    title="LoanSarthi API",
    description="Loan advisory chatbot for Indian banks — RAG + live rate DB",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "user_123",
                "message": "What is the minimum CIBIL score for an HDFC home loan?"
            }
        }


class ChatResponse(BaseModel):
    session_id: str
    reply: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "LoanSarthi"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Send a message to LoanSarthi and get a reply.
    Each session_id maintains its own conversation history.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    agent = get_agent()

    try:
        result = agent.invoke(
            {"input": req.message},
            config={"configurable": {"session_id": req.session_id}},
        )
        return ChatResponse(session_id=req.session_id, reply=result["output"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.delete("/chat/{session_id}")
def clear_session(session_id: str):
    """Clear conversation history for a session."""
    from app.chatbot import _session_histories
    if session_id in _session_histories:
        del _session_histories[session_id]
        return {"message": f"Session '{session_id}' cleared."}
    return {"message": f"Session '{session_id}' not found."}


@app.get("/rates")
def get_rates(
        loan_type: Optional[str] = None,
        bank_name: Optional[str] = None,
        borrower_category: Optional[str] = None,
):
    rows = query_rates(
        loan_type=loan_type,
        bank_name=bank_name,
        borrower_category=borrower_category,
    )
    return {"count": len(rows), "rates": rows}


@app.get("/rates/compare/{loan_type}")
def get_rate_comparison(loan_type: str):
    valid = {"home", "personal", "car"}
    if loan_type.lower() not in valid:
        raise HTTPException(status_code=400, detail=f"loan_type must be one of: {valid}")
    return {"comparison": compare_rates(loan_type.lower())}


@app.get("/banks")
def list_banks():
    return {
        "banks": [
            "HDFC Bank", "ICICI Bank", "Axis Bank", "State Bank of India (SBI)",
            "AU Small Finance Bank", "Kotak Mahindra Bank", "IndusInd Bank",
            "Federal Bank", "Bank of Baroda", "Punjab National Bank (PNB)",
            "Canara Bank", "IDFC FIRST Bank",
        ],
        "loan_types": ["Home Loan", "Personal Loan", "Car Loan (New & Pre-Owned)"],
        "out_of_scope": ["Education Loan", "Business / MSME Loan"],
    }