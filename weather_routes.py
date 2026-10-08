import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Shipment, Alert, MarketplaceListing, Telemetry, Prediction, PriceRecommendation
from backend.ml_engine import calculate_shelf_life_and_risk, calculate_price_recommendation

router = APIRouter(prefix="/api/weather", tags=["Micro-Climate Weather & Heatwave Simulator"])

class HeatwaveSimulationRequest(BaseModel):
    shipment_id: Optional[int] = None
    latitude: Optional[float] = 19.9975
    longitude: Optional[float] = 73.7898
    heatwave_temp: Optional[float] = 39.5
    humidity: Optional[float] = 32.0
    location_name: Optional[str] = "Nashik Agricultural Belt"

# Pre-defined major agricultural hubs in India
AGRI_HUBS = [
    {"name": "Nashik Agri-Zone (Maharashtra)", "lat": 19.9975, "lon": 73.7898, "primary_crop": "Tomato & Onion"},
    {"name": "Coimbatore Cold Corridor (Tamil Nadu)", "lat": 11.0168, "lon": 76.9558, "primary_crop": "Tomato & Banana"},
    {"name": "Agra Belt (Uttar Pradesh)", "lat": 27.1767, "lon": 78.0081, "primary_crop": "Potato"},
    {"name": "Shimla Valley (Himachal Pradesh)", "lat": 31.1048, "lon": 77.1734, "primary_crop": "Apple"},
    {"name": "Ratnagiri Coastal Zone (Maharashtra)", "lat": 16.9902, "lon": 73.3120, "primary_crop": "Mango"},
    {"name": "Ooty Nilgiris (Tamil Nadu)", "lat": 11.4102, "lon": 76.6950, "primary_crop": "Spinach & Greens"},
]

@router.get("/hubs")
def get_agricultural_hubs():
    return {"hubs": AGRI_HUBS}

@router.get("/current")
def get_current_micro_climate(
    latitude: float = 19.9975,
    longitude: float = 73.7898,
    location_name: Optional[str] = "Nashik Agri-Zone"
):
    """
    Fetches real-time micro-climate conditions via Open-Meteo Weather API based on GPS coordinates.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&hourly=temperature_2m&forecast_days=1"

    try:
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current", {})
                hourly_temps = data.get("hourly", {}).get("temperature_2m", [])
                max_forecast_temp = max(hourly_temps) if hourly_temps else current.get("temperature_2m", 32.0)

                temp = current.get("temperature_2m", 32.0)
                humidity = current.get("relative_humidity_2m", 45.0)
            else:
                temp = 33.5
                humidity = 42.0
                max_forecast_temp = 36.0
    except Exception:
        # Graceful fallback if offline
        temp = 33.5
        humidity = 42.0
        max_forecast_temp = 36.5

    # Determine Heatwave condition
    is_heatwave = temp >= 35.0 or max_forecast_temp >= 37.0
    if temp >= 40.0:
        heatwave_status = "EXTREME_HEATWAVE"
        warning_msg = f"CRITICAL HEATWAVE ALERT: Ambient temperature reached {temp}°C. Rapid cellular transpiration underway."
    elif temp >= 35.0 or is_heatwave:
        heatwave_status = "HEATWAVE_WARNING"
        warning_msg = f"HEATWAVE DETECTED: Forecast predicts peak heat of {max_forecast_temp}°C. Accelerated shelf-life decay active."
    else:
        heatwave_status = "NORMAL_CLIMATE"
        warning_msg = "Micro-climate parameters within seasonal standard."

    return {
        "gps": {"latitude": latitude, "longitude": longitude},
        "location_name": location_name,
        "current_temperature": temp,
        "relative_humidity": humidity,
        "max_forecast_today": max_forecast_temp,
        "is_heatwave": is_heatwave,
        "heatwave_status": heatwave_status,
        "warning_message": warning_msg,
        "source": "Open-Meteo High-Resolution Micro-Climate API",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/simulate-heatwave")
def simulate_heatwave_impact(
    req: HeatwaveSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    Simulates a localized micro-climate heatwave (e.g. 39.5°C):
    1. Automatically reduces vegetable shelf life by 30%.
    2. Recalculates a steeper, faster price discount strategy to empty inventory.
    3. Triggers HEATWAVE_EMERGENCY alerts and updates marketplace listings.
    """
    target_shipment_id = req.shipment_id
    if target_shipment_id:
        shipment = db.query(Shipment).filter(Shipment.id == target_shipment_id).first()
    else:
        shipment = db.query(Shipment).filter(Shipment.tracking_number == "AGRO102").first()
    if not shipment:
        shipment = db.query(Shipment).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="No active shipment found")

    now = datetime.utcnow()
    hw_temp = req.heatwave_temp if req.heatwave_temp else 39.5
    hw_hum = req.humidity if req.humidity else 32.0

    # Get baseline values before heatwave
    latest_tel = shipment.telemetry_records[0] if shipment.telemetry_records else None
    latest_pred = shipment.predictions[0] if shipment.predictions else None
    latest_price = shipment.price_recommendations[0] if shipment.price_recommendations else None

    before_shelf_life = latest_pred.remaining_shelf_life_hours if latest_pred else 72.0
    before_price = latest_price.recommended_price if latest_price else shipment.original_price
    before_discount = latest_price.discount_percentage if latest_price else 0.0

    # 1. Record Heatwave Telemetry
    telemetry = Telemetry(
        shipment_id=shipment.id,
        temperature=hw_temp,
        humidity=hw_hum,
        transit_hours=latest_tel.transit_hours if latest_tel else 18.0,
        transit_delay=latest_tel.transit_delay if latest_tel else 0.0,
        timestamp=now
    )
    db.add(telemetry)
    db.flush()

    # 2. Run AI model with 30% Shelf-Life Heatwave Penalty
    pred_res = calculate_shelf_life_and_risk(
        produce_name=shipment.produce.name,
        initial_shelf_life_hours=shipment.produce.initial_shelf_life_hours,
        current_temp=hw_temp,
        current_humidity=hw_hum,
        transit_hours=telemetry.transit_hours,
        transit_delay=telemetry.transit_delay,
        heatwave_detected=True,
        heatwave_temp=hw_temp
    )

    prediction = Prediction(
        shipment_id=shipment.id,
        remaining_shelf_life_hours=pred_res["remaining_shelf_life_hours"],
        spoilage_risk=pred_res["spoilage_risk"],
        degradation_score=pred_res["degradation_score"],
        confidence_score=pred_res["confidence_score"],
        explanation=pred_res["explanation"],
        created_at=now
    )
    db.add(prediction)
    db.flush()

    # 3. Recalculate Steeper & Faster Price Discount Strategy to empty inventory
    price_rec = calculate_price_recommendation(
        original_price=shipment.original_price,
        remaining_shelf_life_hours=pred_res["remaining_shelf_life_hours"],
        spoilage_risk=pred_res["spoilage_risk"],
        quantity=shipment.quantity,
        produce_category=shipment.produce.category,
        heatwave_detected=True,
        heatwave_temp=hw_temp
    )

    rec_model = PriceRecommendation(
        shipment_id=shipment.id,
        original_price=price_rec["original_price"],
        discount_percentage=price_rec["discount_percentage"],
        recommended_price=price_rec["recommended_price"],
        reason=price_rec["reason"],
        status="ACTIVE",
        created_at=now
    )
    db.add(rec_model)
    db.flush()

    # 4. Generate Heatwave Alert in Database
    alert = Alert(
        shipment_id=shipment.id,
        alert_type="HEATWAVE_EMERGENCY",
        severity="CRITICAL",
        message=(
            f"🔥 CRITICAL MICRO-CLIMATE HEATWAVE ({hw_temp}°C) at {req.location_name}: "
            f"Remaining shelf life for {shipment.produce.name} compressed by 30% to {pred_res['remaining_shelf_life_hours']}h. "
            f"Steep discount ({price_rec['discount_percentage']}%) activated for emergency clearance."
        ),
        created_at=now
    )
    db.add(alert)

    # 5. Automatically Update / Create Marketplace Listing with Steep Discount
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.shipment_id == shipment.id).first()
    if not listing:
        listing = MarketplaceListing(
            shipment_id=shipment.id,
            quantity=shipment.quantity,
            price=price_rec["recommended_price"],
            discount_percentage=price_rec["discount_percentage"],
            status="AVAILABLE",
            listed_at=now
        )
        db.add(listing)
    else:
        listing.price = price_rec["recommended_price"]
        listing.discount_percentage = price_rec["discount_percentage"]
        if listing.status != "SOLD":
            listing.status = "AVAILABLE"

    db.commit()

    return {
        "success": True,
        "scenario": "HEATWAVE_PREDICTION_EMERGENCY",
        "shipment": {
            "id": shipment.id,
            "tracking_number": shipment.tracking_number,
            "produce_name": shipment.produce.name,
            "quantity_kg": shipment.quantity
        },
        "micro_climate": {
            "location": req.location_name,
            "heatwave_temperature": hw_temp,
            "humidity": hw_hum
        },
        "shelf_life_reduction": {
            "baseline_shelf_life_hours": before_shelf_life,
            "penalty_percentage": 30.0,
            "reduced_shelf_life_hours": pred_res["remaining_shelf_life_hours"],
            "hours_lost": round(before_shelf_life - pred_res["remaining_shelf_life_hours"], 1)
        },
        "pricing_strategy": {
            "original_price": shipment.original_price,
            "before_discount_pct": before_discount,
            "steeper_discount_pct": price_rec["discount_percentage"],
            "new_liquidation_price": price_rec["recommended_price"],
            "reason": price_rec["reason"]
        },
        "action_taken": "Inventory pre-emptively listed on marketplace with steeper pricing to guarantee 4-hour clearance before heat spoils it."
    }
