from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models import Shipment, Produce, Telemetry, Prediction, PriceRecommendation, Alert, MarketplaceListing
from backend.ml_engine import calculate_shelf_life_and_risk, calculate_price_recommendation

def process_telemetry_pipeline(
    db: Session,
    shipment_id: int,
    temperature: float,
    humidity: float,
    transit_delay: float = 0.0,
    transit_hours_override: float = None
) -> dict:
    """
    Executes the complete AgroSense cold-chain monitoring pipeline:
    1. Persists Telemetry to Database
    2. Runs Explainable Degradation Model
    3. Persists AI Prediction
    4. Evaluates Alert Triggers & Persists Alerts
    5. Computes Dynamic Price Recommendation & Persists
    6. Automatically creates or updates Marketplace Listing
    7. Generates Retailer Notifications
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise ValueError(f"Shipment with id {shipment_id} not found")

    produce = shipment.produce
    now = datetime.utcnow()

    # Calculate transit hours
    if transit_hours_override is not None:
        transit_hours = transit_hours_override
    else:
        elapsed = (now - shipment.start_time).total_seconds() / 3600.0
        transit_hours = max(1.0, elapsed)

    # 1. Save Telemetry
    telemetry = Telemetry(
        shipment_id=shipment.id,
        temperature=temperature,
        humidity=humidity,
        transit_hours=round(transit_hours, 1),
        transit_delay=round(transit_delay, 1),
        timestamp=now
    )
    db.add(telemetry)
    db.flush()

    # 2. Run AI Degradation Engine
    pred_result = calculate_shelf_life_and_risk(
        produce_name=produce.name,
        initial_shelf_life_hours=produce.initial_shelf_life_hours,
        current_temp=temperature,
        current_humidity=humidity,
        transit_hours=transit_hours,
        transit_delay=transit_delay
    )

    prediction = Prediction(
        shipment_id=shipment.id,
        remaining_shelf_life_hours=pred_result["remaining_shelf_life_hours"],
        spoilage_risk=pred_result["spoilage_risk"],
        degradation_score=pred_result["degradation_score"],
        confidence_score=pred_result["confidence_score"],
        explanation=pred_result["explanation"],
        created_at=now
    )
    db.add(prediction)
    db.flush()

    # 3. Dynamic Price Recommendation
    price_rec = calculate_price_recommendation(
        original_price=shipment.original_price,
        remaining_shelf_life_hours=pred_result["remaining_shelf_life_hours"],
        spoilage_risk=pred_result["spoilage_risk"],
        quantity=shipment.quantity,
        produce_category=produce.category
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

    # 4. Alert Checks
    alerts_created = []

    # Check Temperature spike
    if temperature > produce.ideal_temp_max:
        temp_alert = Alert(
            shipment_id=shipment.id,
            alert_type="TEMPERATURE_SPIKE",
            severity="WARNING" if temperature <= produce.ideal_temp_max + 6 else "HIGH_RISK",
            message=f"Temperature ({round(temperature, 1)}°C) has exceeded the preferred range ({produce.ideal_temp_min}°C–{produce.ideal_temp_max}°C) for {produce.name}.",
            created_at=now
        )
        db.add(temp_alert)
        alerts_created.append(temp_alert)

    # Check Transit Delay
    if transit_delay > 0:
        delay_alert = Alert(
            shipment_id=shipment.id,
            alert_type="TRANSIT_DELAY",
            severity="WARNING",
            message=f"Shipment {shipment.tracking_number} delayed by {round(transit_delay, 1)} hours.",
            created_at=now
        )
        db.add(delay_alert)
        alerts_created.append(delay_alert)

    # Check Spoilage Risk / Shelf life thresholds
    if pred_result["remaining_shelf_life_hours"] <= 20.0 or pred_result["spoilage_risk"] == "CRITICAL":
        crit_alert = Alert(
            shipment_id=shipment.id,
            alert_type="SHELF_LIFE_CRITICAL",
            severity="CRITICAL",
            message=f"Estimated shelf life is approximately {round(pred_result['remaining_shelf_life_hours'], 0)} hours. Consider immediate liquidation.",
            created_at=now
        )
        db.add(crit_alert)
        alerts_created.append(crit_alert)
    elif pred_result["remaining_shelf_life_hours"] <= 48.0 or pred_result["spoilage_risk"] == "HIGH":
        risk_alert = Alert(
            shipment_id=shipment.id,
            alert_type="HIGH_RISK",
            severity="HIGH_RISK",
            message=f"Estimated shelf life has fallen below 48 hours ({round(pred_result['remaining_shelf_life_hours'], 1)}h remaining).",
            created_at=now
        )
        db.add(risk_alert)
        alerts_created.append(risk_alert)

    # 5. Automatic Marketplace Listing Update
    # When remaining shelf life is low (<48h) or discount > 0, list on marketplace automatically
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.shipment_id == shipment.id).first()
    if price_rec["discount_percentage"] > 0 or pred_result["spoilage_risk"] in ["HIGH", "CRITICAL"]:
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

        # Retailer notification alert
        retailer_alert = Alert(
            shipment_id=shipment.id,
            alert_type="MARKETPLACE_OFFER",
            severity="INFO",
            message=f"New Liquidation Offer: {produce.name} ({shipment.quantity} kg) now at ₹{price_rec['recommended_price']}/kg ({price_rec['discount_percentage']}% OFF).",
            created_at=now
        )
        db.add(retailer_alert)
        alerts_created.append(retailer_alert)

    db.commit()

    return {
        "telemetry": telemetry,
        "prediction": prediction,
        "price_recommendation": rec_model,
        "marketplace_listing": listing,
        "alerts": alerts_created
    }
