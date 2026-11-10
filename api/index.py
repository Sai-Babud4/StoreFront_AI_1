import os
import sys
import gzip
import shutil
import tempfile
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# TOP-LEVEL APPLICATION ASSIGNMENT FOR VERCEL AST SCANNER
app = FastAPI(
    title="RetailIQ – AI-Powered Inventory Intelligence",
    description="Intelligent Inventory Monitoring and Automated Replenishment Agent",
    version="1.0.0"
)
handler = app

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

for p in [CURRENT_DIR, PARENT_DIR, os.path.join(CURRENT_DIR, "backend"), os.path.join(PARENT_DIR, "backend")]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

# Seed database into writable /tmp for Vercel serverless environment
tmp_dir = "/tmp" if (os.path.exists("/tmp") and os.access("/tmp", os.W_OK)) else tempfile.gettempdir()
target_db = os.path.join(tmp_dir, "retailiq.db")

candidates_db = [
    os.path.join(CURRENT_DIR, "retailiq.db"),
    os.path.join(CURRENT_DIR, "data", "retailiq.db"),
    os.path.join(CURRENT_DIR, "backend", "data", "retailiq.db"),
    os.path.join(PARENT_DIR, "data", "retailiq.db"),
    os.path.join(PARENT_DIR, "backend", "data", "retailiq.db"),
    os.path.join(PARENT_DIR, "retailiq.db"),
]

candidates_gz = [
    os.path.join(CURRENT_DIR, "retailiq.db.gz"),
    os.path.join(CURRENT_DIR, "data", "retailiq.db.gz"),
    os.path.join(CURRENT_DIR, "backend", "data", "retailiq.db.gz"),
    os.path.join(PARENT_DIR, "data", "retailiq.db.gz"),
    os.path.join(PARENT_DIR, "backend", "data", "retailiq.db.gz"),
    os.path.join(PARENT_DIR, "retailiq.db.gz"),
]

if not os.path.exists(target_db) or os.path.getsize(target_db) < 100000:
    seeded = False
    for c in candidates_db:
        if os.path.exists(c) and os.path.getsize(c) > 100000:
            try:
                shutil.copyfile(c, target_db)
                print(f"[RetailIQ Init] Seeded database from {c} ({os.path.getsize(c):,} bytes) to {target_db}")
                seeded = True
                break
            except Exception as e:
                print(f"[RetailIQ Init] Copy error: {e}")
    if not seeded:
        for gz in candidates_gz:
            if os.path.exists(gz) and os.path.getsize(gz) > 50000:
                try:
                    with gzip.open(gz, "rb") as f_in, open(target_db, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    print(f"[RetailIQ Init] Extracted database from {gz} to {target_db} ({os.path.getsize(target_db):,} bytes)")
                    seeded = True
                    break
                except Exception as e:
                    print(f"[RetailIQ Init] Gzip error: {e}")

if os.path.exists(target_db) and os.path.getsize(target_db) > 100000:
    os.environ["DATABASE_URL"] = f"sqlite:///{target_db}"

# Path rewriting middleware to handle Vercel rewrite subtleties
@app.middleware("http")
async def path_normalization_middleware(request: Request, call_next):
    path = request.scope.get("path", "")
    if path.startswith("/api/index.py"):
        request.scope["path"] = path.replace("/api/index.py", "/api") or "/api"
    elif path.startswith("/index.py"):
        request.scope["path"] = path.replace("/index.py", "") or "/"
    return await call_next(request)

# Register core API router on both /api and root level
router_error = None
try:
    try:
        from backend.app.api.endpoints import router as api_router
    except ImportError:
        from app.api.endpoints import router as api_router
        
    app.include_router(api_router, prefix="/api")
    app.include_router(api_router)
    print(f"[RetailIQ Router] Successfully registered API routes!")
except Exception as e:
    import traceback
    router_error = traceback.format_exc()
    print(f"[RetailIQ Router Registration Warning]: {router_error}")

@app.get("/api/health")
@app.get("/health")
def health_endpoint():
    db_size = os.path.getsize(target_db) if os.path.exists(target_db) else 0
    return {
        "status": "healthy" if not router_error else "degraded",
        "service": "RetailIQ AI-Powered Inventory Intelligence",
        "version": "1.0.0",
        "database": {
            "path": target_db,
            "exists": os.path.exists(target_db),
            "size_bytes": db_size
        },
        "router_error": router_error
    }

@app.get("/api/debug")
@app.get("/debug")
def debug_endpoint():
    db_size = os.path.getsize(target_db) if os.path.exists(target_db) else 0
    product_count = None
    sales_count = None
    try:
        import sqlite3
        if os.path.exists(target_db):
            conn = sqlite3.connect(target_db)
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM products")
            product_count = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM sales_transactions")
            sales_count = cur.fetchone()[0]
            conn.close()
    except Exception as e:
        product_count = str(e)

    return {
        "status": "ok",
        "python_version": sys.version,
        "current_dir": CURRENT_DIR,
        "parent_dir": PARENT_DIR,
        "tmp_dir_exists": os.path.exists("/tmp"),
        "target_db": target_db,
        "target_db_size": db_size,
        "products_count": product_count,
        "sales_count": sales_count,
        "router_error": router_error
    }
