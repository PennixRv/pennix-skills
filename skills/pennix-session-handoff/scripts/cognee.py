"""Formal handoff uses the Pennix Cognee memory owner's native client."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pennix-cognee-memory" / "scripts"))
from cognee_client import CogneeClient, CogneeError, handoff_content
