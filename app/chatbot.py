"""
chatbot.py — LoanSarthi conversational agent (Groq-powered).

LangChain version: 0.3.x (pinned for stability)
"""

from __future__ import annotations
import os

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

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


# ── Session store ─────────────────────────────────────────────────────────────

_session_histories: dict[str, ChatMessageHistory] = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in _session_histories:
        _session_histories[session_id] = ChatMessageHistory()
    return _session_histories[session_id]


# ── Agent builder ─────────────────────────────────────────────────────────────

def build_agent(
    model: str | None = None,
    temperature: float = 0.2,
) -> RunnableWithMessageHistory:

    groq_model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    llm = ChatGroq(
        model=groq_model,
        temperature=temperature,
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )

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

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=50,
        handle_parsing_errors=True,
    )

    return RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )


# ── CLI for testing ───────────────────────────────────────────────────────────

def run_cli():
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    print(f"\n🏦  Welcome to LoanSarthi! (Model: {model})")
    print("    Type 'exit' to quit.\n")
    agent = build_agent()
    session_id = "cli_session"

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

        result = agent.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}},
        )
        print(f"\nLoanSarthi: {result['output']}\n")


if __name__ == "__main__":
    run_cli()