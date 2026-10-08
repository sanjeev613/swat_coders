from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Shipment, MarketplaceListing
from backend.schemas import TemperatureSpikeRequest, TransitDelayRequest, CustomTelemetryRequest
from backend.pipeline import process_telemetry_pipeline

router = APIRouter(prefix="/api/simulate", tags=["Simulation"])

def get_target_shipment(db: Session, shipment_id: int = None) -> Shipment:
    if shipment_id:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    else:
        shipment = db.query(Shipment).filter(Shipment.tracking_number == "AGRO102").first()
    if not shipment:
        # Fallback to the first available shipment
        shipment = db.query(Shipment).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="No active shipments available for simulation")
    return shipment

@router.post("/temperature-spike")
def simulate_temperature_spike(
    payload: TemperatureSpikeRequest = None,
    db: Session = Depends(get_db)
):
    shipment_id = payload.shipment_id if payload else None
    shipment = get_target_shipment(db, shipment_id)

    target_temp = payload.target_temperature if payload and payload.target_temperature else 18.0
    humidity = payload.humidity if payload and payload.humidity else 75.0

    result = process_telemetry_pipeline(
        db=db,
        shipment_id=shipment.id,
        temperature=target_temp,
        humidity=humidity,
        transit_delay=0.0,
        transit_hours_override=18.0
    )

    return {
        "success": True,
        "scenario": "TEMPERATURE_SPIKE",
        "shipment_id": shipment.id,
        "tracking_number": shipment.tracking_number,
        "produce": shipment.produce.name,
        "temperature": target_temp,
        "humidity": humidity,
        "remaining_shelf_life_hours": result["prediction"].remaining_shelf_life_hours,
        "spoilage_risk": result["prediction"].spoilage_risk,
        "discount_percentage": result["price_recommendation"].discount_percentage,
        "recommended_price": result["price_recommendation"].recommended_price,
        "explanation": result["prediction"].explanation,
        "alerts_count": len(result["alerts"]),
        "marketplace_updated": bool(result["marketplace_listing"])
    }

@router.post("/transit-delay")
def simulate_transit_delay(
    payload: TransitDelayRequest,
    db: Session = Depends(get_db)
):
    shipment = get_target_shipment(db, payload.shipment_id)
    latest_tel = shipment.telemetry_records[0] if shipment.telemetry_records else None
    current_temp = latest_tel.temperature if latest_tel else 14.0
    current_hum = latest_tel.humidity if latest_tel else 75.0

    result = process_telemetry_pipeline(
        db=db,
        shipment_id=shipment.id,
        temperature=current_temp,
        humidity=current_hum,
        transit_delay=payload.delay_hours,
        transit_hours_override=(latest_tel.transit_hours if latest_tel else 18.0) + payload.delay_hours
    )

    return {
        "success": True,
        "scenario": "TRANSIT_DELAY",
        "shipment_id": shipment.id,
        "tracking_number": shipment.tracking_number,
        "delay_hours": payload.delay_hours,
        "remaining_shelf_life_hours": result["prediction"].remaining_shelf_life_hours,
        "spoilage_risk": result["prediction"].spoilage_risk,
        "discount_percentage": result["price_recommendation"].discount_percentage,
        "recommended_price": result["price_recommendation"].recommended_price
    }

@router.post("/custom")
def simulate_custom_telemetry(
    payload: CustomTelemetryRequest,
    db: Session = Depends(get_db)
):
    shipment = get_target_shipment(db, payload.shipment_id)
    latest_tel = shipment.telemetry_records[0] if shipment.telemetry_records else None
    current_transit = latest_tel.transit_hours if latest_tel else 18.0

    result = process_telemetry_pipeline(
        db=db,
        shipment_id=shipment.id,
        temperature=payload.temperature,
        humidity=payload.humidity,
        transit_delay=payload.transit_delay or 0.0,
        transit_hours_override=current_transit
    )

    return {
        "success": True,
        "scenario": "CUSTOM_TELEMETRY",
        "shipment_id": shipment.id,
        "tracking_number": shipment.tracking_number,
        "temperature": payload.temperature,
        "humidity": payload.humidity,
        "transit_delay": payload.transit_delay,
        "remaining_shelf_life_hours": result["prediction"].remaining_shelf_life_hours,
        "spoilage_risk": result["prediction"].spoilage_risk,
        "discount_percentage": result["price_recommendation"].discount_percentage,
        "recommended_price": result["price_recommendation"].recommended_price,
        "explanation": result["prediction"].explanation
    }

@router.post("/reset")
def reset_normal_conditions(
    payload: dict = None,
    db: Session = Depends(get_db)
):
    shipment_id = payload.get("shipment_id") if payload else None
    shipment = get_target_shipment(db, shipment_id)
    produce = shipment.produce

    normal_temp = (produce.ideal_temp_min + produce.ideal_temp_max) / 2.0
    normal_hum = (produce.ideal_humidity_min + produce.ideal_humidity_max) / 2.0

    # Clean existing marketplace listing if reset back to safe
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.shipment_id == shipment.id).first()
    if listing and listing.status == "AVAILABLE":
        db.delete(listing)
        db.flush()

    result = process_telemetry_pipeline(
        db=db,
        shipment_id=shipment.id,
        temperature=normal_temp,
        humidity=normal_hum,
        transit_delay=0.0,
        transit_hours_override=18.0
    )

    return {
        "success": True,
        "scenario": "RESET_NORMAL",
        "shipment_id": shipment.id,
        "tracking_number": shipment.tracking_number,
        "temperature": normal_temp,
        "humidity": normal_hum,
        "remaining_shelf_life_hours": result["prediction"].remaining_shelf_life_hours,
        "spoilage_risk": result["prediction"].spoilage_risk,
        "discount_percentage": result["price_recommendation"].discount_percentage,
        "recommended_price": result["price_recommendation"].recommended_price
    }
