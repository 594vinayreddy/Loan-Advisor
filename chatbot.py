"""
chatbot.py — LoanSarthi conversational agent.

Architecture
────────────
                ┌─────────────────────────────────┐
  User query ──►│  LangChain OpenAI Functions Agent│
                │  (gpt-4o or gpt-3.5-turbo)      │
                └────────────┬────────────────────-┘
                             │ decides which tool(s) to call
                    ┌────────┴────────┐
                    │                 │
              ┌─────▼──────┐   ┌──────▼────────┐
              │ RAG Tool   │   │ Rate Tool      │
              │ (ChromaDB) │   │ (SQLite DB)    │
              │ eligibility│   │ live rate      │
              │ criteria,  │   │ comparisons    │
              │ how to     │   │                │
              │ apply, etc)│   │                │
              └────────────┘   └───────────────-┘
"""

from __future__ import annotations
import os
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory

from app.rag_ingest import load_vectorstore
from app.rate_tool import loan_rate_comparison_tool

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are LoanSarthi, a friendly and knowledgeable Indian loan advisor.
You help users navigate home loans, personal loans, and car loans across 12 major Indian banks.

## Your knowledge sources
1. **Static knowledge base** (RAG): Official eligibility criteria, application process, 
   required documents, and terms — sourced from each bank's official .bank.in site.
2. **Live rate database**: Current interest rate ranges, processing fees, and tenure 
   options — updated regularly.

## Guidelines
- Always be accurate. If a field is marked "Not publicly disclosed" or "Pending confirmation",
  tell the user clearly and advise them to confirm directly with the bank.
- Rates in the database are indicative. Always add: "Please confirm current rates with the 
  bank before applying."
- When comparing banks, present information in a clear, structured way.
- For complex eligibility questions, walk the user through the criteria step by step.
- Banks covered: HDFC Bank, ICICI Bank, Axis Bank, SBI, Kotak Mahindra Bank, IndusInd Bank,
  Bank of Baroda, Punjab National Bank (PNB), Canara Bank, IDFC FIRST Bank, Federal Bank,
  AU Small Finance Bank.
- Loan types: Home Loan, Personal Loan, Car Loan (new & pre-owned).
- Education Loan and Business Loan are out of scope — redirect users to the bank directly.

## Tone
- Conversational and helpful, like a trusted friend who knows banking well.
- Use ₹ for Indian Rupees.
- Keep answers concise unless the user asks for full detail.
"""

# ── RAG retrieval tool ────────────────────────────────────────────────────────

_vectorstore = None


def _get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = load_vectorstore()
    return _vectorstore


@tool
def loan_eligibility_rag_tool(query: str) -> str:
    """
    Use this tool to answer questions about loan eligibility criteria, required
    documents, application process, interest rate benchmarks, and terms — for
    any of the 12 covered banks (HDFC, ICICI, Axis, SBI, Kotak, IndusInd,
    Bank of Baroda, PNB, Canara, IDFC FIRST, Federal, AU Small Finance).

    Input: a natural-language question, e.g.:
        "What is the minimum CIBIL score for HDFC personal loan?"
        "How do I apply for SBI home loan?"
        "What documents are needed for ICICI car loan?"
        "What is the age limit for Axis Bank home loan?"

    Returns: relevant excerpts from the official static knowledge base.
    """
    vs = _get_vectorstore()
    docs = vs.similarity_search(query, k=4)

    if not docs:
        return "No relevant information found in the knowledge base for this query."

    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        header = f"[Source {i}: {meta.get('bank', 'General')} — {meta.get('loan_type', '').capitalize()} Loan]"
        parts.append(f"{header}\n{doc.page_content}")

    return "\n\n---\n\n".join(parts)


# ── Agent builder ─────────────────────────────────────────────────────────────

def build_agent(model: str = "gpt-4o", temperature: float = 0.2) -> AgentExecutor:
    """
    Build and return a LangChain OpenAI Functions agent with:
    - RAG tool (ChromaDB static content)
    - Rate comparison tool (SQLite live rates)
    - Sliding window conversation memory (last 10 turns)

    Args:
        model:       OpenAI model name (gpt-4o recommended for tool calling)
        temperature: Lower = more factual, higher = more creative
    """
    llm = ChatOpenAI(model=model, temperature=temperature)

    tools = [
        loan_eligibility_rag_tool,
        loan_rate_comparison_tool,
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=10,  # keep last 10 turns in context
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,  # set False in production to reduce log noise
        max_iterations=5,  # prevent runaway loops
        handle_parsing_errors=True,
    )


# ── Simple CLI for testing ────────────────────────────────────────────────────

def run_cli():
    """Interactive command-line chat — useful for local testing."""
    print("\n🏦  Welcome to LoanSarthi! Type 'exit' to quit.\n")
    agent = build_agent()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("exit", "quit", "bye"):
            print("LoanSarthi: Goodbye! Best of luck with your loan. 🙏")
            break

        if not user_input:
            continue

        result = agent.invoke({"input": user_input})
        print(f"\nLoanSarthi: {result['output']}\n")


if __name__ == "__main__":
    run_cli()