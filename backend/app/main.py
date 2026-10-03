"""
FastAPI main application.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api import auth, transactions, dashboard, alerts, investigations, network, ml, admin

app = FastAPI(
    title="Fraud Detection System",
    description="AI-Driven Fraud Detection and Prevention System",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(alerts.router)
app.include_router(investigations.router)
app.include_router(network.router)
app.include_router(ml.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup_event():
    """Initialize database and load ML model on startup."""
    print("Initializing database...")
    init_db()
    print("Database initialized.")

    # Try to load ML model
    from app.ml.predict import get_predictor
    predictor = get_predictor()
    if predictor.loaded:
        print("ML model loaded successfully.")
    else:
        print("WARNING: ML model not loaded. Run training first:")
        print("  cd backend && python -m app.ml.train_model")


@app.get("/")
def root():
    return {"message": "Fraud Detection API", "version": "1.0.0", "status": "running"}


@app.get("/api/health")
def health_check():
    from app.ml.predict import get_predictor
    predictor = get_predictor()
    return {
        "status": "healthy",
        "database": "connected",
        "ml_model": "loaded" if predictor.loaded else "not_loaded",
    }
