import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database.database import init_db
from backend.api.run import router as run_router
from backend.api.debug import router as debug_router
from backend.api.history import router as history_router
from backend.api.stats import router as stats_router
from backend.api.settings_api import router as settings_router

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize Database tables
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_SUBTITLE,
    version=settings.VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(run_router)
app.include_router(debug_router)
app.include_router(history_router)
app.include_router(stats_router)
app.include_router(settings_router)

# Health Check Endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "ai_status": "active" if (os.getenv("AI_API_KEY") or os.getenv("GEMINI_API_KEY") or settings.AI_API_KEY) else "fallback_mode"
    }

# SPA Template / Static route
TEMPLATES_DIR = BASE_DIR / "templates"
INDEX_PATH = TEMPLATES_DIR / "index.html"

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    # Allow API requests through
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    if INDEX_PATH.exists():
        return HTMLResponse(content=INDEX_PATH.read_text(encoding="utf-8"))
    
    return HTMLResponse(content="<h1>AI Code Sandbox Server Running</h1><p>Index template not found.</p>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8080, reload=True)
