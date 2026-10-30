"""Index the existing Kepler handbook into pgvector (document_chunks).

Run this from the `backend` folder (or use the project Python path). This is
intended as a small helper for onboarding current `data/` files into the
vector store.
"""
import os
import sys

# Ensure package imports work when running the script directly
# This script is typically run from the repo root:
#   python backend/scripts/index_existing.py
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_ROOT = os.path.join(REPO_ROOT, "backend")
sys.path.insert(0, BACKEND_ROOT)

from app.services.ingest import index_document
from app.core.config import settings

DATA_FILE = os.path.abspath(
    os.path.join(REPO_ROOT, "data", "Kepler College_Student Handbook.txt")
)

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        print('Handbook file not found at', DATA_FILE)
        sys.exit(1)
    print('Indexing', DATA_FILE)
    doc_id = index_document(DATA_FILE, doc_name='Kepler College Student Handbook')
    print('Indexed as doc_id=', doc_id)
