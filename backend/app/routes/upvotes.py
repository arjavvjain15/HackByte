"""
EcoSnap — Upvote Router (stub)
Upvote logic has been consolidated into app/routes/reports.py.
This file is kept for router registration but adds no routes.
"""
from fastapi import APIRouter

router = APIRouter(tags=["Upvotes"])
# All upvote endpoints are in reports.py:
# POST /api/reports/{id}/upvote
# GET  /api/reports/{id}/upvote-status
