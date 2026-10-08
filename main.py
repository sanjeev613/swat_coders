import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import engine, Base, get_db
from backend.models import Shipment
from backend.seed_data import seed_database
from backend.ml_engine import calculate_price_recommendation

from backend.routes.auth_routes import router as auth_router
from backend.routes.shipment_routes import router as shipment_router
from backend.routes.telemetry_routes import router as telemetry_router
from backend.routes.prediction_routes import router as prediction_router
from backend.routes.simulation_routes import router as simulation_router
from backend.routes.marketplace_routes import router as marketplace_router
from backend.routes.alert_routes import router as alert_router
from backend.routes.analytics_routes import router as analytics_router
from backend.routes.inventory_routes import router as inventory_router
from backend.routes.market_channel_routes import router as market_channel_router
from backend.routes.weather_routes import router as weather_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    # Seed sample data if empty
    db = next(get_db())
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AgroSense AI-Powered Perishable Cold Chain Monitoring & Smart Liquidation Platform API",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(shipment_router)
app.include_router(telemetry_router)
app.include_router(prediction_router)
app.include_router(simulation_router)
app.include_router(marketplace_router)
app.include_router(alert_router)
app.include_router(analytics_router)
app.include_router(inventory_router)
app.include_router(market_channel_router)
app.include_router(weather_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AgroSense Backend API",
        "version": settings.PROJECT_VERSION
    }

# Explicit Price Recommendation Endpoint matching Section 19
@app.post("/api/price-recommendation/{shipment_id}")
def get_price_recommendation_endpoint(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    latest_pred = shipment.predictions[0] if shipment.predictions else None
    remaining_hours = latest_pred.remaining_shelf_life_hours if latest_pred else 72.0
    risk = latest_pred.spoilage_risk if latest_pred else "LOW"

    rec = calculate_price_recommendation(
        original_price=shipment.original_price,
        remaining_shelf_life_hours=remaining_hours,
        spoilage_risk=risk,
        quantity=shipment.quantity,
        produce_category=shipment.produce.category
    )
    return rec
