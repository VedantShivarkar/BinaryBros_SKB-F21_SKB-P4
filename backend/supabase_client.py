"""
=============================================================================
Amrit Vaayu dMRV — Supabase Client Initialization
=============================================================================
Establishes a secure, singleton connection to the Supabase PostgreSQL
instance using environment variables. This module is imported by all route
handlers that need database access.

Usage:
    from supabase_client import supabase
    response = supabase.table("Farmers").select("*").execute()
=============================================================================
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Load environment variables from the project-root `.env` file.
# The `override=False` ensures system-level env vars take precedence,
# which is critical for containerized / CI-CD deployments.
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=False)

# ---------------------------------------------------------------------------
# Read Supabase credentials from environment
# ---------------------------------------------------------------------------
SUPABASE_URL: str | None = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str | None = os.environ.get("SUPABASE_KEY")

# ---------------------------------------------------------------------------
# Validate that both credentials are present before attempting connection.
# Fail loudly at import-time rather than at first query — this prevents
# silent runtime errors deep inside request handlers.
# ---------------------------------------------------------------------------
if not SUPABASE_URL or not SUPABASE_KEY:
    print(
        "\n[FATAL] Missing Supabase credentials.\n"
        "  → Ensure SUPABASE_URL and SUPABASE_KEY are set in your .env file\n"
        "  → Refer to .env.example for the expected format.\n",
        file=sys.stderr,
    )
    # We do NOT call sys.exit() here so that the module can still be imported
    # during testing or schema-generation workflows where Supabase isn't needed.
    supabase: Client | None = None
else:
    # ----- Initialize the Supabase client singleton -----
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"[OK] Supabase client initialized → {SUPABASE_URL[:40]}…")
