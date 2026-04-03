from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import upload, classify, reports, admin, profile


app = FastAPI(title="EcoSnap API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(upload.router)
app.include_router(classify.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(profile.router)
