"""
main.py — Entry point for LoanSarthi.

Usage:
    python main.py serve
    python main.py ingest [--force]
    python main.py cli
    python main.py seed-db
"""

import sys
import os

# ── Fix module resolution ─────────────────────────────────────────────────────
# Add the project root to sys.path so that "from app.xxx import yyy" works
# regardless of which directory you launch from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Load .env ─────────────────────────────────────────────────────────────────
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