import os
import gzip
import shutil
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Determine paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")

def resolve_database_path() -> str:
    # 1. If explicit DATABASE_URL is set in environment, check it
    env_url = os.environ.get("DATABASE_URL")
    if env_url and env_url.startswith("sqlite:///"):
        path = env_url.replace("sqlite:///", "")
        if os.path.exists(path) and os.path.getsize(path) > 100000:
            return path

    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

    candidates_db = [
        os.path.join(BASE_DIR, "backend", "data", "retailiq.db"),
        os.path.join(BASE_DIR, "data", "retailiq.db"),
        os.path.join(BASE_DIR, "retailiq.db"),
        os.path.join(BASE_DIR, "api", "retailiq.db"),
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "retailiq.db"),
        os.path.join(os.path.dirname(__file__), "..", "data", "retailiq.db"),
    ]
    candidates_gz = [
        os.path.join(BASE_DIR, "data", "retailiq.db.gz"),
        os.path.join(BASE_DIR, "backend", "data", "retailiq.db.gz"),
        os.path.join(BASE_DIR, "api", "retailiq.db.gz"),
        os.path.join(BASE_DIR, "retailiq.db.gz"),
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "retailiq.db.gz"),
        os.path.join(os.path.dirname(__file__), "..", "data", "retailiq.db.gz"),
    ]

    # In local/standard mode (writable filesystem), use the project DB directly!
    if not is_serverless:
        for cand in candidates_db:
            if os.path.exists(cand) and os.path.getsize(cand) > 100000:
                return cand

    # In serverless/Vercel environment (read-only root), copy to /tmp
    tmp_dir = "/tmp" if os.path.exists("/tmp") else tempfile.gettempdir()
    target_tmp_db = os.path.join(tmp_dir, "retailiq.db")

    if os.path.exists(target_tmp_db) and os.path.getsize(target_tmp_db) > 100000:
        return target_tmp_db

    # Try copying uncompressed candidate
    for cand in candidates_db:
        if os.path.exists(cand) and os.path.getsize(cand) > 100000:
            try:
                shutil.copyfile(cand, target_tmp_db)
                print(f"[RetailIQ DB] Seeded database from {cand} ({os.path.getsize(cand):,} bytes) to {target_tmp_db}")
                return target_tmp_db
            except Exception:
                return cand

    # Try extracting compressed candidate
    for cand in candidates_gz:
        if os.path.exists(cand) and os.path.getsize(cand) > 50000:
            try:
                with gzip.open(cand, "rb") as f_in, open(target_tmp_db, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                print(f"[RetailIQ DB] Decompressed database from {cand} to {target_tmp_db}")
                return target_tmp_db
            except Exception as e:
                print(f"[RetailIQ DB Warning] Decompression failed: {e}")

    return target_tmp_db

db_file = resolve_database_path()
DATABASE_URL = f"sqlite:///{db_file}"
os.environ["DATABASE_URL"] = DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
