import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Shipment, Produce, User, Telemetry, Prediction, PriceRecommendation
from backend.schemas import ShipmentCreate, ShipmentOut, ProduceOut
from backend.auth import get_current_user
from backend.pipeline import process_telemetry_pipeline

router = APIRouter(prefix="/api", tags=["Shipments"])

def format_shipment(s: Shipment) -> dict:
    latest_tel = s.telemetry_records[0] if s.telemetry_records else None
    latest_pred = s.predictions[0] if s.predictions else None
    latest_price = s.price_recommendations[0] if s.price_recommendations else None
    
    return {
        "id": s.id,
        "tracking_number": s.tracking_number,
        "produce_id": s.produce_id,
        "transporter_id": s.transporter_id,
        "origin": s.origin,
        "destination": s.destination,
        "quantity": s.quantity,
        "original_price": s.original_price,
        "status": s.status,
        "start_time": s.start_time,
        "expected_arrival": s.expected_arrival,
        "created_at": s.created_at,
        "produce": s.produce,
        "latest_telemetry": latest_tel,
        "latest_prediction": latest_pred,
        "latest_price_recommendation": latest_price,
        "marketplace_listing": s.marketplace_listing
    }

@router.get("/produce", response_model=List[ProduceOut])
def get_produce_list(db: Session = Depends(get_db)):
    return db.query(Produce).all()

@router.get("/shipments")
def get_shipments(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Shipment)
    if status_filter:
        query = query.filter(Shipment.status == status_filter)
    shipments = query.order_by(Shipment.created_at.desc()).all()
    return [format_shipment(s) for s in shipments]

@router.get("/shipments/{id}")
def get_shipment_by_id(id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    formatted = format_shipment(shipment)
    # Include recent telemetry history for charts
    formatted["telemetry_history"] = [
        {
            "id": t.id,
            "temperature": t.temperature,
            "humidity": t.humidity,
            "transit_hours": t.transit_hours,
            "transit_delay": t.transit_delay,
            "timestamp": t.timestamp.isoformat()
        }
        for t in reversed(shipment.telemetry_records[:20])
    ]
    # Include predictions history
    formatted["prediction_history"] = [
        {
            "id": p.id,
            "remaining_shelf_life_hours": p.remaining_shelf_life_hours,
            "spoilage_risk": p.spoilage_risk,
            "degradation_score": p.degradation_score,
            "confidence_score": p.confidence_score,
            "explanation": p.explanation,
            "created_at": p.created_at.isoformat()
        }
        for p in reversed(shipment.predictions[:20])
    ]
    formatted["alerts"] = [
        {
            "id": a.id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "read_status": a.read_status,
            "created_at": a.created_at.isoformat()
        }
        for a in shipment.alerts[:10]
    ]
    return formatted

@router.post("/shipments")
def create_shipment(
    payload: ShipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "transporter":
        raise HTTPException(status_code=403, detail="Only transporters can create new shipments")

    produce = db.query(Produce).filter(Produce.id == payload.produce_id).first()
    if not produce:
        raise HTTPException(status_code=404, detail="Selected produce does not exist")

    # Generate tracking code
    count = db.query(Shipment).count() + 101
    tracking = f"AGRO{count}"

    now = datetime.utcnow()
    shipment = Shipment(
        tracking_number=tracking,
        produce_id=payload.produce_id,
        transporter_id=current_user.id,
        origin=payload.origin,
        destination=payload.destination,
        quantity=payload.quantity,
        original_price=payload.original_price,
        status="IN_TRANSIT",
        start_time=now,
        expected_arrival=now + timedelta(hours=payload.expected_arrival_hours or 24.0),
        created_at=now
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Initialize baseline telemetry matching produce ideal range
    initial_temp = (produce.ideal_temp_min + produce.ideal_temp_max) / 2.0
    initial_hum = (produce.ideal_humidity_min + produce.ideal_humidity_max) / 2.0
    
    process_telemetry_pipeline(
        db=db,
        shipment_id=shipment.id,
        temperature=initial_temp,
        humidity=initial_hum,
        transit_delay=0.0,
        transit_hours_override=0.5
    )

    return format_shipment(shipment)
