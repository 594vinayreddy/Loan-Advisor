"""
rate_tool.py — LangChain Tool that queries the structured SQLite DB for
live loan rate comparisons.

The tool is given to the LangChain agent so it can decide when to call it
(e.g. "compare home loan rates", "which bank has lowest personal loan rate").
"""

from __future__ import annotations
import json
from typing import Optional
from sqlalchemy.orm import Session
from app.database import LoanRate, SessionLocal


# ── DB query helpers ──────────────────────────────────────────────────────────

def query_rates(
    loan_type: Optional[str] = None,
    bank_name: Optional[str] = None,
    borrower_category: Optional[str] = None,
    sort_by: str = "rate_min_pct",
) -> list[dict]:
    """
    Fetch rates from the DB with optional filters.

    Args:
        loan_type:          "home" | "personal" | "car" (or None for all)
        bank_name:          e.g. "HDFC Bank" (or None for all)
        borrower_category:  e.g. "salaried" (or None for all)
        sort_by:            column name to sort by (default: rate_min_pct)

    Returns:
        List of rate dicts sorted by sort_by.
    """
    db: Session = SessionLocal()
    try:
        q = db.query(LoanRate)
        if loan_type:
            # Fuzzy match: "home loan" → "home"
            lt = loan_type.lower().replace(" loan", "").strip()
            q = q.filter(LoanRate.loan_type == lt)
        if bank_name:
            q = q.filter(LoanRate.bank_name.ilike(f"%{bank_name}%"))
        if borrower_category:
            q = q.filter(LoanRate.borrower_category.ilike(f"%{borrower_category}%"))

        rows = q.order_by(getattr(LoanRate, sort_by, LoanRate.rate_min_pct)).all()
        return [r.to_dict() for r in rows]
    finally:
        db.close()


def compare_rates(loan_type: str) -> str:
    """
    Return a formatted comparison table of rates for a given loan type.
    Intended as the string returned to the LLM by the LangChain Tool.
    """
    rows = query_rates(loan_type=loan_type)
    if not rows:
        return f"No rate data found for loan type: {loan_type}"

    lines = [f"📊 **{loan_type.capitalize()} Loan Rate Comparison** (sorted by lowest rate)\n"]
    lines.append(f"{'Bank':<25} {'Rate Range':<20} {'Max Tenure':<15} {'Processing Fee':<30} {'Notes'}")
    lines.append("-" * 115)

    for r in rows:
        lines.append(
            f"{r['bank']:<25} {r['rate']:<20} {r['max_tenure']:<15} "
            f"{(r['processing_fee'] or 'N/A'):<30} {(r['notes'] or '')[:60]}"
        )
    lines.append(f"\n_Last updated: {rows[0]['last_updated']}_")
    lines.append("_Rates are indicative. Confirm with the bank before applying._")
    return "\n".join(lines)


def get_bank_rate_detail(bank_name: str, loan_type: str) -> str:
    """Return detailed rate info for one bank + loan type."""
    rows = query_rates(loan_type=loan_type, bank_name=bank_name)
    if not rows:
        return f"No rate data found for {bank_name} {loan_type} loan."
    return json.dumps(rows, indent=2)


# ── LangChain Tool wrapper ────────────────────────────────────────────────────

from langchain.tools import tool


@tool
def loan_rate_comparison_tool(query: str) -> str:
    """
    Use this tool when the user asks to compare loan interest rates across banks,
    or wants to know the best/lowest rate for a particular loan type.

    Input format: a natural-language query such as:
        "compare home loan rates"
        "personal loan rates for salaried"
        "car loan rates at HDFC Bank"

    Returns a formatted comparison table from the live rate database.
    """
    q = query.lower()

    # Detect loan type
    if "home" in q:
        loan_type = "home"
    elif "personal" in q:
        loan_type = "personal"
    elif "car" in q or "vehicle" in q or "auto" in q:
        loan_type = "car"
    else:
        # Return all types summary if ambiguous
        parts = []
        for lt in ["home", "personal", "car"]:
            rows = query_rates(loan_type=lt)
            if rows:
                best = rows[0]
                parts.append(f"- **{lt.capitalize()} Loan** — Best rate from {best['bank']}: {best['rate']}")
        return "Here's a quick overview of the best rates available:\n" + "\n".join(parts) + \
               "\n\nAsk me to compare a specific loan type for the full table."

    # Detect specific bank
    banks = [
        "HDFC", "ICICI", "Axis", "SBI", "Kotak", "IndusInd",
        "Bank of Baroda", "Punjab National", "PNB", "Canara",
        "IDFC", "Federal", "AU Small Finance", "AU"
    ]
    bank_filter = next((b for b in banks if b.lower() in q), None)

    if bank_filter:
        return get_bank_rate_detail(bank_filter, loan_type)
    return compare_rates(loan_type)