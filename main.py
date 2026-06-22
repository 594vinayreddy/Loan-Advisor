"""
main.py — Entry point for LoanSarthi.

Usage:
    # Start the API server
    python main.py serve

    # Re-ingest the docx into ChromaDB (run after updating the docx)
    python main.py ingest --force

    # Run the CLI chatbot (for local testing without the API)
    python main.py cli

    # Seed / reset the rate database
    python main.py seed-db
"""

import sys
import os

# Load .env if present
from dotenv import load_dotenv
load_dotenv()

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if cmd == "serve":
        import uvicorn
        uvicorn.run(
            "app.server:app",
            host=os.getenv("APP_HOST", "0.0.0.0"),
            port=int(os.getenv("APP_PORT", 8000)),
            reload=os.getenv("DEBUG", "true").lower() == "true",
        )

    elif cmd == "ingest":
        force = "--force" in sys.argv
        from app.rag_ingest import ingest
        ingest(force=force)

    elif cmd == "cli":
        from app.chatbot import run_cli
        run_cli()

    elif cmd == "seed-db":
        from app.database import init_db, seed_rates
        init_db()
        seed_rates()

    else:
        print(f"Unknown command: {cmd}")
        print("Valid commands: serve | ingest [--force] | cli | seed-db")
        sys.exit(1)


if __name__ == "__main__":
    main()