"""
rag_ingest.py — Parses the LoanSarthi static content docx and indexes it
into ChromaDB using FREE local embeddings (sentence-transformers).

Embedding model: all-MiniLM-L6-v2 (runs locally, no API key, no cost)
  - Downloads ~90MB on first run, then cached locally forever
  - Excellent quality for retrieval tasks, very fast on CPU
Vector store: ChromaDB running in Docker (HTTP client)

Prerequisites:
    1. docker run -d -p 8001:8000 --name chromadb chromadb/chroma:0.6.0
    2. No API key needed for embeddings!

Run once (or after updating the docx):
    python main.py ingest
    python main.py ingest --force
"""

import os
from typing import List

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document as LCDocument
import chromadb

CHROMA_HOST       = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT       = int(os.getenv("CHROMA_PORT", "8001"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "loansarthi_static")
DOCX_PATH         = os.getenv("STATIC_CONTENT_PATH", "./data/loansarthi_static_content.docx")
# Free local model — downloads once (~90MB), then cached at ~/.cache/huggingface/
EMBEDDING_MODEL   = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _table_to_markdown(table: Table) -> str:
    rows = []
    for i, row in enumerate(table.rows):
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        rows.append("| " + " | ".join(cells) + " |")
        if i == 0:
            rows.append("|" + "|".join(["---"] * len(cells)) + "|")
    return "\n".join(rows)


def _iter_block_items(doc: Document):
    from docx.oxml.ns import qn
    parent = doc.element.body
    for child in parent.iterchildren():
        if child.tag == qn("w:p"):
            yield "para", Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield "table", Table(child, doc)


def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    parts = []
    for kind, obj in _iter_block_items(doc):
        if kind == "para":
            text = obj.text.strip()
            if text:
                parts.append(text)
        elif kind == "table":
            parts.append(_table_to_markdown(obj))
    return "\n\n".join(parts)


def _detect_bank_and_loan(text: str):
    banks = [
        "HDFC Bank", "ICICI Bank", "Axis Bank", "State Bank of India", "SBI",
        "AU Small Finance Bank", "Kotak Mahindra Bank", "IndusInd Bank",
        "Federal Bank", "Bank of Baroda", "Punjab National Bank", "PNB",
        "Canara Bank", "IDFC FIRST Bank",
    ]
    loan_types = {
        "home loan": "home",
        "personal loan": "personal",
        "car loan": "car",
    }
    bank_found = next((b for b in banks if b.lower() in text.lower()), "general")
    loan_found = next((v for k, v in loan_types.items() if k in text.lower()), "general")
    return bank_found, loan_found


def _get_chroma_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)


def _get_embeddings() -> HuggingFaceEmbeddings:
    """
    Returns a local sentence-transformers embedding model.
    First call downloads ~90MB to ~/.cache/huggingface/ — subsequent calls
    load from cache instantly. No API key or internet needed after first run.
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


# ── Main ingest ───────────────────────────────────────────────────────────────

def ingest(force: bool = False):
    client = _get_chroma_client()

    try:
        col = client.get_collection(CHROMA_COLLECTION)
        count = col.count()
        if count > 0 and not force:
            print(f"ℹ️   Collection '{CHROMA_COLLECTION}' already has {count} chunks — skipping ingest.")
            print("    Pass force=True to re-ingest.")
            return
        elif force:
            client.delete_collection(CHROMA_COLLECTION)
            print(f"🗑️   Deleted existing collection '{CHROMA_COLLECTION}'.")
    except Exception:
        pass

    print(f"📄  Reading docx: {DOCX_PATH}")
    raw_text = extract_text_from_docx(DOCX_PATH)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: List[str] = splitter.split_text(raw_text)
    print(f"✂️   Created {len(chunks)} chunks.")

    documents: List[LCDocument] = []
    for i, chunk in enumerate(chunks):
        bank, loan_type = _detect_bank_and_loan(chunk)
        documents.append(
            LCDocument(
                page_content=chunk,
                metadata={
                    "chunk_id":  i,
                    "bank":      bank,
                    "loan_type": loan_type,
                    "source":    "loansarthi_static_content.docx",
                },
            )
        )

    print(f"🔢  Embedding with '{EMBEDDING_MODEL}' (local, free) and storing in ChromaDB …")
    print("    (First run downloads ~90MB — please wait)")
    embeddings = _get_embeddings()

    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        client=client,
        collection_name=CHROMA_COLLECTION,
    )
    print(f"✅  Ingested {len(documents)} chunks into collection '{CHROMA_COLLECTION}'.")


def load_vectorstore() -> Chroma:
    embeddings = _get_embeddings()
    client = _get_chroma_client()
    return Chroma(
        client=client,
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
    )


if __name__ == "__main__":
    ingest(force=False)