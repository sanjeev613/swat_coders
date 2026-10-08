from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import MarketplaceListing, Shipment, User
from backend.auth import get_current_user

router = APIRouter(prefix="/api/marketplace", tags=["Marketplace"])

def format_listing(item: MarketplaceListing) -> dict:
    shipment = item.shipment
    produce = shipment.produce if shipment else None
    latest_pred = shipment.predictions[0] if shipment and shipment.predictions else None
    latest_price = shipment.price_recommendations[0] if shipment and shipment.price_recommendations else None

    return {
        "id": item.id,
        "shipment_id": item.shipment_id,
        "tracking_number": shipment.tracking_number if shipment else "",
        "produce_name": produce.name if produce else "Produce",
        "produce_category": produce.category if produce else "General",
        "produce_icon": produce.icon if produce else "📦",
        "quantity": item.quantity,
        "price": item.price,
        "original_price": shipment.original_price if shipment else item.price,
        "discount_percentage": item.discount_percentage,
        "status": item.status,
        "listed_at": item.listed_at,
        "origin": shipment.origin if shipment else "Unknown",
        "destination": shipment.destination if shipment else "Unknown",
        "current_location": f"En-route to {shipment.destination}" if shipment else "In Transit",
        "remaining_shelf_life_hours": latest_pred.remaining_shelf_life_hours if latest_pred else 24.0,
        "spoilage_risk": latest_pred.spoilage_risk if latest_pred else "MEDIUM",
        "discount_reason": latest_price.reason if latest_price else "Dynamic liquidation deal based on cold-chain assessment",
        "buyer_id": item.buyer_id,
        "purchased_at": item.purchased_at
    }

@router.get("")
def get_marketplace_listings(
    status_filter: Optional[str] = "AVAILABLE",
    db: Session = Depends(get_db)
):
    query = db.query(MarketplaceListing)
    if status_filter:
        query = query.filter(MarketplaceListing.status == status_filter)
    listings = query.order_by(MarketplaceListing.listed_at.desc()).all()
    return [format_listing(l) for l in listings]

@router.post("/{id}/accept")
def accept_marketplace_offer(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.id == id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Marketplace listing not found")

    if listing.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="This deal is no longer available.")

    listing.status = "SOLD"
    listing.buyer_id = current_user.id
    listing.purchased_at = datetime.utcnow()

    # Update associated shipment status to LIQUIDATED
    shipment = listing.shipment
    if shipment:
        shipment.status = "LIQUIDATED"

    db.commit()
    db.refresh(listing)

    return {
        "success": True,
        "message": f"Successfully secured liquidation order for {listing.quantity} kg of {shipment.produce.name} at ₹{listing.price}/kg!",
        "listing": format_listing(listing)
    }
