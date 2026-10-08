import random
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Shipment, Produce, MarketplaceListing

router = APIRouter(prefix="/api/market-channels", tags=["Multi-Channel Market Price & Buyer Comparison"])

class RouteConsignmentRequest(BaseModel):
    shipment_id: int
    channel_id: str  # 'processing', 'quick_commerce', 'wholesale_mandi'
    channel_name: str
    negotiated_price: float

# Real-time base market index per produce
MARKET_BASE_RATES: Dict[str, Dict[str, float]] = {
    "Tomato": {"retail": 85.0, "processing": 58.0, "mandi_spot": 72.0},
    "Banana": {"retail": 42.0, "processing": 28.0, "mandi_spot": 34.0},
    "Apple": {"retail": 150.0, "processing": 95.0, "mandi_spot": 125.0},
    "Mango": {"retail": 240.0, "processing": 160.0, "mandi_spot": 200.0},
    "Spinach": {"retail": 48.0, "processing": 25.0, "mandi_spot": 38.0},
    "Potato": {"retail": 28.0, "processing": 20.0, "mandi_spot": 24.0},
}

@router.get("/live-feed")
def get_live_market_ticker():
    """
    Simulates live ticker feeds across Quick-Commerce, Wholesale Mandis, and Processing factories.
    """
    now = datetime.utcnow()
    ticker = []
    for produce_name, rates in MARKET_BASE_RATES.items():
        # Add slight natural real-time fluctuation
        fluct = random.uniform(-0.04, 0.04)
        mandi_price = round(rates["mandi_spot"] * (1.0 + fluct), 1)
        retail_price = round(rates["retail"] * (1.0 + (fluct * 0.5)), 1)
        proc_price = round(rates["processing"] * (1.0 + (fluct * 0.2)), 1)

        ticker.append({
            "produce": produce_name,
            "mandi_spot": mandi_price,
            "mandi_change_pct": round(fluct * 100, 1),
            "quick_commerce_bid": retail_price,
            "processing_bid": proc_price,
            "timestamp": now.isoformat()
        })
    return {"live_ticker": ticker}

@router.get("/compare/{shipment_id}")
def compare_market_channels(shipment_id: int, db: Session = Depends(get_db)):
    """
    Generates direct 3-channel comparison table for the farmer:
    1. B2B Food Processing Factory Option
    2. Quick-Commerce Retailer Option (e.g. Blinkit)
    3. Local Wholesale Market Option (APMC Mandi)
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    produce = shipment.produce
    quantity = shipment.quantity
    latest_tel = shipment.telemetry_records[0] if shipment.telemetry_records else None
    latest_pred = shipment.predictions[0] if shipment.predictions else None

    remaining_hours = latest_pred.remaining_shelf_life_hours if latest_pred else 72.0
    risk = latest_pred.spoilage_risk if latest_pred else "LOW"
    temp = latest_tel.temperature if latest_tel else 4.0

    rates = MARKET_BASE_RATES.get(produce.name, {"retail": 80.0, "processing": 50.0, "mandi_spot": 65.0})

    # Option 1: B2B Food Processing Factory Option (e.g. Kissan, Heinz, Dabur)
    # High tolerance for cosmetically imperfect or ripe produce, zero rejection, fast bulk intake
    proc_gross_rate = round(rates["processing"] * random.uniform(0.96, 1.02), 2)
    proc_deductions = 0.0  # Factory handles bulk haulage, no commission
    proc_net_rate = proc_gross_rate
    proc_total_payout = round(proc_net_rate * quantity, 2)
    proc_turnaround_hours = 4.0
    proc_rejection_risk_pct = 2.0  # Processing factories pulp it; cosmetic blemishes accepted

    # Option 2: Quick-Commerce Retailer Option (e.g. Blinkit / Zepto / Instamart)
    # Highest gross price, ultra-fast 2h intake, but STRICT shelf-life and grade threshold
    qc_gross_rate = round(rates["retail"] * random.uniform(0.97, 1.04), 2)
    qc_platform_fee_pct = 4.0
    qc_net_rate = round(qc_gross_rate * (1.0 - (qc_platform_fee_pct / 100.0)), 2)
    qc_total_payout = round(qc_net_rate * quantity, 2)
    qc_turnaround_hours = 2.0
    # Rejection risk escalates sharply if shelf life is low (<24h)
    if remaining_hours < 20.0:
        qc_rejection_risk_pct = 65.0  # Blinkit quality auditors reject soft/overripe produce
    elif remaining_hours < 48.0:
        qc_rejection_risk_pct = 25.0
    else:
        qc_rejection_risk_pct = 4.0

    # Option 3: Local Wholesale Market Option (APMC Mandi Auction Yard)
    # Fluctuating auction price, high commission (6-8%), gate cess, unloading labor, queue delay
    mandi_gross_bid = round(rates["mandi_spot"] * random.uniform(0.92, 1.08), 2)
    mandi_commission_pct = 7.0  # Agent commission
    mandi_labor_per_kg = 1.50   # Unloading & gate fee
    mandi_deductions = round((mandi_gross_bid * (mandi_commission_pct / 100.0)) + mandi_labor_per_kg, 2)
    mandi_net_rate = round(max(5.0, mandi_gross_bid - mandi_deductions), 2)
    # Risk of in-queue spoilage dumping during long 14-18h auction waiting
    if remaining_hours < 24.0:
        mandi_spoilage_dump_risk_pct = 45.0
    elif remaining_hours < 48.0:
        mandi_spoilage_dump_risk_pct = 20.0
    else:
        mandi_spoilage_dump_risk_pct = 8.0
    mandi_turnaround_hours = 16.0
    mandi_total_payout = round(mandi_net_rate * quantity * (1.0 - (mandi_spoilage_dump_risk_pct / 100.0)), 2)

    # Calculate AI Channel Recommendation
    # If remaining shelf-life < 24h: Processing Factory is the only guaranteed zero-spoilage payout!
    # If remaining shelf-life between 24-48h: Quick-Commerce provides highest net return if quick intake available
    # If remaining shelf-life > 72h: Quick-Commerce or Mandi depending on net yield
    if remaining_hours <= 24.0:
        recommended_channel = "b2b_processing"
        recommendation_reason = (
            f"RECOMMENDED OPTION 1 (B2B Processing Factory): Batch {shipment.tracking_number} has only "
            f"{round(remaining_hours, 1)} hours of shelf life remaining. Blinkit has a 65% quality gate rejection "
            f"risk and Mandi auction wait times (16h) will cause ~45% spoilage dump. The processing factory guarantees "
            f"100% batch buyout (₹{proc_total_payout:,.0f}) with zero cosmetic penalty."
        )
    elif remaining_hours <= 48.0:
        if qc_rejection_risk_pct <= 25.0 and (qc_total_payout * 0.75) > proc_total_payout:
            recommended_channel = "quick_commerce"
            recommendation_reason = (
                f"RECOMMENDED OPTION 2 (Quick-Commerce / Blinkit): Remaining shelf life ({round(remaining_hours, 1)}h) "
                f"is sufficient for rapid 2-hour dark store intake. Net realization (₹{qc_net_rate}/kg) yields "
                f"₹{(qc_total_payout - proc_total_payout):,.0f} higher total return than processing pulp."
            )
        else:
            recommended_channel = "b2b_processing"
            recommendation_reason = (
                f"RECOMMENDED OPTION 1 (B2B Processing Factory): Eliminates rejection volatility with instant tanker intake."
            )
    else:
        recommended_channel = "quick_commerce"
        recommendation_reason = (
            f"RECOMMENDED OPTION 2 (Quick-Commerce): Stable cold-chain condition ({round(remaining_hours, 1)}h remaining). "
            f"Direct consumer retail capture provides highest net margin without mandi middlemen commission."
        )

    return {
        "shipment": {
            "id": shipment.id,
            "tracking_number": shipment.tracking_number,
            "produce_name": produce.name,
            "produce_icon": produce.icon,
            "quantity_kg": quantity,
            "origin": shipment.origin,
            "destination": shipment.destination,
            "temperature": temp,
            "remaining_shelf_life_hours": remaining_hours,
            "spoilage_risk": risk
        },
        "recommended_channel_id": recommended_channel,
        "recommendation_reason": recommendation_reason,
        "options": [
            {
                "id": "b2b_processing",
                "name": "B2B Food Processing Factory",
                "tagline": "Puree, Pulp, Ketchup & Juice Processing (e.g. Kissan, Dabur, Tropicana)",
                "icon": "🏭",
                "badge": "ZERO COSMETIC REJECTION",
                "offered_price_per_kg": proc_gross_rate,
                "deductions_per_kg": 0.0,
                "net_price_per_kg": proc_net_rate,
                "total_payout": proc_total_payout,
                "turnaround_time": "3 - 4 hours (Factory Bulk Tanker Intake)",
                "rejection_risk_pct": proc_rejection_risk_pct,
                "quality_threshold": "Grade C / Processing Grade (High brix/sugar tolerance, minor cosmetic defects 100% accepted)",
                "payment_terms": "Direct NEFT / RTGS within 24 hours",
                "logistics_arrangement": "Factory coordinates dedicated bulk collection tanker",
                "is_recommended": recommended_channel == "b2b_processing",
                "pros": ["Zero cosmetic rejection risk", "Guaranteed bulk lot buyout", "Fast 4-hour clearance"],
                "cons": ["Lower unit rate than prime retail shelf"]
            },
            {
                "id": "quick_commerce",
                "name": "Quick-Commerce Retailer (e.g. Blinkit, Zepto)",
                "tagline": "10-Minute Dark Store Direct Intake Network",
                "icon": "⚡",
                "badge": "HIGHEST UNIT PAYOUT",
                "offered_price_per_kg": qc_gross_rate,
                "deductions_per_kg": round(qc_gross_rate * (qc_platform_fee_pct / 100.0), 2),
                "net_price_per_kg": qc_net_rate,
                "total_payout": qc_total_payout,
                "turnaround_time": "1 - 2 hours (Direct Dark Store Dock Intake)",
                "rejection_risk_pct": qc_rejection_risk_pct,
                "quality_threshold": "Grade A Consumer Quality (Requires minimum 24-48h shelf life, firm skin)",
                "payment_terms": "Instant automated escrow clearance upon dock scan",
                "logistics_arrangement": "Nearest micro-fulfillment dark store hub dispatch",
                "is_recommended": recommended_channel == "quick_commerce",
                "pros": ["Highest gross & net realization", "Ultra-fast 2-hour turnaround", "Automated dock escrow payment"],
                "cons": ["Strict firmness check", f"{qc_rejection_risk_pct}% rejection risk if shelf life < 24h"]
            },
            {
                "id": "wholesale_mandi",
                "name": "Local Wholesale Market (APMC Mandi Auction)",
                "tagline": "Regional Wholesale Mandi Yard (e.g. Azadpur / APMC Vashi)",
                "icon": "🏛️",
                "badge": "TRADITIONAL AUCTION SPOT",
                "offered_price_per_kg": mandi_gross_bid,
                "deductions_per_kg": mandi_deductions,
                "net_price_per_kg": mandi_net_rate,
                "total_payout": mandi_total_payout,
                "turnaround_time": "14 - 18 hours (Auction queue waiting & unloading line)",
                "rejection_risk_pct": mandi_spoilage_dump_risk_pct,
                "quality_threshold": "Open auction visual appraisal (Vulnerable to cartel down-bidding for urgent lots)",
                "payment_terms": "Traditional Commission Agent slip (Credit cycle 7–14 days)",
                "logistics_arrangement": "Farmer/Transporter arranges own truck unloading labor",
                "is_recommended": recommended_channel == "wholesale_mandi",
                "pros": ["Open market spot price elasticity", "High trading volume capacity"],
                "cons": ["7% commission + labor deductions", "High 16-hour queue waiting", f"{mandi_spoilage_dump_risk_pct}% risk of dumping unsold stock"]
            }
        ]
    }

@router.post("/route")
def route_consignment_to_channel(
    req: RouteConsignmentRequest,
    db: Session = Depends(get_db)
):
    """
    Executes farmer's channel selection and routes consignment.
    """
    shipment = db.query(Shipment).filter(Shipment.id == req.shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment.status = "LIQUIDATED"

    # Also update or mark marketplace listing
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.shipment_id == shipment.id).first()
    if listing:
        listing.status = "SOLD"
        listing.price = req.negotiated_price

    db.commit()

    return {
        "success": True,
        "shipment_id": shipment.id,
        "tracking_number": shipment.tracking_number,
        "channel_id": req.channel_id,
        "channel_name": req.channel_name,
        "settled_price": req.negotiated_price,
        "total_contract_value": round(req.negotiated_price * shipment.quantity, 2),
        "message": f"Consignment {shipment.tracking_number} ({shipment.quantity} kg of {shipment.produce.name}) successfully routed to {req.channel_name} at ₹{req.negotiated_price}/kg!"
    }
