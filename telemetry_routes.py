from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Telemetry, Shipment
from backend.schemas import TelemetryCreate, TelemetryOut
from backend.pipeline import process_telemetry_pipeline

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

@router.post("", response_model=TelemetryOut)
def record_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == payload.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    result = process_telemetry_pipeline(
        db=db,
        shipment_id=payload.shipment_id,
        temperature=payload.temperature,
        humidity=payload.humidity,
        transit_delay=payload.transit_delay or 0.0,
        transit_hours_override=payload.transit_hours
    )
    return result["telemetry"]

@router.get("/{shipment_id}", response_model=List[TelemetryOut])
def get_shipment_telemetry(shipment_id: int, db: Session = Depends(get_db)):
    records = db.query(Telemetry).filter(Telemetry.shipment_id == shipment_id).order_by(Telemetry.timestamp.desc()).limit(100).all()
    return records
