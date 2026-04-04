"""
EcoSnap — FastAPI Application Entry Point
Merged backend: AI Pipeline + Auth + Profiles + Upload + Admin + Reports
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import classify, reports, admin, upvotes, upload, profile

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="EcoSnap API",
    version="2.0.0",
    description="AI-powered civic hazard reporting platform — Cloud Vision + Supabase",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check (public) ─────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "2.0.0"}


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(classify.router,  prefix="/api")
app.include_router(reports.router,   prefix="/api")
app.include_router(upvotes.router,   prefix="/api")
app.include_router(admin.router,     prefix="/api")
app.include_router(upload.router,    prefix="/api")
app.include_router(profile.router,   prefix="/api")
