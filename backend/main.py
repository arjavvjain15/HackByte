"""
EcoSnap — FastAPI Application Entry Point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env (one level up from backend/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.routes import classify, reports, upvotes, admin

app = FastAPI(
    title="EcoSnap API",
    description="AI-powered civic environmental hazard reporting backend",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow all origins for hackathon — tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(classify.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(upvotes.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


# ── Health Check (for Railway + UptimeRobot keep-alive) ──────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "EcoSnap API"}


@app.get("/", tags=["Health"])
async def root():
    return {"message": "EcoSnap API is running. Visit /docs for API reference."}
