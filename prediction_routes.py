from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Shipment, Prediction
from backend.ml_engine import calculate_shelf_life_and_risk

router = APIRouter(prefix="/api", tags=["AI Predictions"])

@router.get("/predictions/{shipment_id}")
def get_shipment_predictions(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    predictions = db.query(Prediction).filter(Prediction.shipment_id == shipment_id).order_by(Prediction.created_at.desc()).all()
    latest_pred = predictions[0] if predictions else None
    latest_tel = shipment.telemetry_records[0] if shipment.telemetry_records else None

    # Calculate explainable factors based on current parameters
    if latest_tel:
        explain_data = calculate_shelf_life_and_risk(
            produce_name=shipment.produce.name,
            initial_shelf_life_hours=shipment.produce.initial_shelf_life_hours,
            current_temp=latest_tel.temperature,
            current_humidity=latest_tel.humidity,
            transit_hours=latest_tel.transit_hours,
            transit_delay=latest_tel.transit_delay
        )
        factors = explain_data.get("factors", [])
    else:
        factors = ["Initial cold chain baseline maintained."]

    return {
        "shipment_id": shipment_id,
        "produce_name": shipment.produce.name,
        "latest_prediction": latest_pred,
        "factors": factors,
        "history": predictions[:15]
    }

@router.post("/predict/{shipment_id}")
def trigger_prediction(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    latest_tel = shipment.telemetry_records[0] if shipment.telemetry_records else None
    temp = latest_tel.temperature if latest_tel else 4.0
    hum = latest_tel.humidity if latest_tel else 75.0
    transit_h = latest_tel.transit_hours if latest_tel else 18.0
    delay = latest_tel.transit_delay if latest_tel else 0.0

    pred_res = calculate_shelf_life_and_risk(
        produce_name=shipment.produce.name,
        initial_shelf_life_hours=shipment.produce.initial_shelf_life_hours,
        current_temp=temp,
        current_humidity=hum,
        transit_hours=transit_h,
        transit_delay=delay
    )

    pred = Prediction(
        shipment_id=shipment.id,
        remaining_shelf_life_hours=pred_res["remaining_shelf_life_hours"],
        spoilage_risk=pred_res["spoilage_risk"],
        degradation_score=pred_res["degradation_score"],
        confidence_score=pred_res["confidence_score"],
        explanation=pred_res["explanation"]
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)

    return {
        "prediction": pred,
        "factors": pred_res["factors"],
        "ideal_temp_range": pred_res["ideal_temp_range"],
        "ideal_humidity_range": pred_res["ideal_humidity_range"]
    }
