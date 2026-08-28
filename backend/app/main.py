from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api import auth_routes, scan_routes, document_routes
from backend.app.core.database import engine, Base
from backend.app.models import schema

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Modern PDF Scanner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(scan_routes.router)
app.include_router(document_routes.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "PDF Scanner Backend"}
