import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

# app.py runs init_db()/seed_db() at import time, so point the DB at a
# throwaway file before importing it. spendly.db is never touched.
_import_dir = tempfile.mkdtemp()
db.DB_PATH = os.path.join(_import_dir, "import.db")

from app import app as flask_app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    db.seed_db()
    flask_app.config["TESTING"] = True
    return flask_app.test_client()
