"""Set a throwaway SQLite database before pytest imports the application."""
import os
import tempfile
from pathlib import Path

_test_root=Path(tempfile.mkdtemp(prefix="ghostwaste-pytest-"))
os.environ["GHOSTWASTE_TESTING"]="1"
os.environ["GHOSTWASTE_DB_PATH"]=str(_test_root / "isolated.sqlite3")
os.environ["GHOSTWASTE_AUTO_SCHEMA"]="true"
