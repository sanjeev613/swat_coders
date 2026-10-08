from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Shipment, Telemetry, Prediction, PriceRecommendation

router = APIRouter(prefix="/api/inventory", tags=["FIFO Logistics & Virtual Grid"])

# Grid slot definitions for Reefer Truck (2 columns x 4 rows = 8 pallet slots)
# Near Door / Rear Tailgate (Exit) = RED ZONE (Sell within 24-48h)
# Mid Cargo Bay = YELLOW ZONE (Sell within 3-5 days)
# Deep Cargo Front (Chiller) = GREEN ZONE (Hold back / Distant markets)
TRUCK_SLOTS = [
    {"slot_id": "BAY-G1", "row": 0, "col": 0, "zone_name": "Deep Front Chiller Bay", "zone_type": "GREEN_ZONE", "door_distance": 4, "zone_tag": "Green Zone: Hold back / Distant markets"},
    {"slot_id": "BAY-G2", "row": 0, "col": 1, "zone_name": "Deep Front Chiller Bay", "zone_type": "GREEN_ZONE", "door_distance": 4, "zone_tag": "Green Zone: Hold back / Distant markets"},
    {"slot_id": "BAY-Y1", "row": 1, "col": 0, "zone_name": "Mid-Bay Staging A", "zone_type": "YELLOW_ZONE", "door_distance": 3, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "BAY-Y2", "row": 1, "col": 1, "zone_name": "Mid-Bay Staging A", "zone_type": "YELLOW_ZONE", "door_distance": 3, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "BAY-Y3", "row": 2, "col": 0, "zone_name": "Mid-Bay Staging B", "zone_type": "YELLOW_ZONE", "door_distance": 2, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "BAY-Y4", "row": 2, "col": 1, "zone_name": "Mid-Bay Staging B", "zone_type": "YELLOW_ZONE", "door_distance": 2, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "BAY-R1", "row": 3, "col": 0, "zone_name": "Tailgate / Unload Door Ramp", "zone_type": "RED_ZONE", "door_distance": 1, "zone_tag": "Red Zone: Front of truck / Sell within 24-48h"},
    {"slot_id": "BAY-R2", "row": 3, "col": 1, "zone_name": "Tailgate / Unload Door Ramp", "zone_type": "RED_ZONE", "door_distance": 1, "zone_tag": "Red Zone: Front of truck / Sell within 24-48h"},
]

# Storage Room slots (4 rows x 3 cols = 12 pallet racks)
STORAGE_SLOTS = [
    {"slot_id": "RACK-G1", "row": 0, "col": 0, "zone_name": "Deep Cold Air Plenum", "zone_type": "GREEN_ZONE", "door_distance": 4, "zone_tag": "Green Zone: Hold back / Distant markets"},
    {"slot_id": "RACK-G2", "row": 0, "col": 1, "zone_name": "Deep Cold Air Plenum", "zone_type": "GREEN_ZONE", "door_distance": 4, "zone_tag": "Green Zone: Hold back / Distant markets"},
    {"slot_id": "RACK-G3", "row": 0, "col": 2, "zone_name": "Deep Cold Air Plenum", "zone_type": "GREEN_ZONE", "door_distance": 4, "zone_tag": "Green Zone: Hold back / Distant markets"},
    {"slot_id": "RACK-Y1", "row": 1, "col": 0, "zone_name": "Rack Aisle 1", "zone_type": "YELLOW_ZONE", "door_distance": 3, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "RACK-Y2", "row": 1, "col": 1, "zone_name": "Rack Aisle 1", "zone_type": "YELLOW_ZONE", "door_distance": 3, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "RACK-Y3", "row": 1, "col": 2, "zone_name": "Rack Aisle 1", "zone_type": "YELLOW_ZONE", "door_distance": 3, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "RACK-Y4", "row": 2, "col": 0, "zone_name": "Rack Aisle 2", "zone_type": "YELLOW_ZONE", "door_distance": 2, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "RACK-Y5", "row": 2, "col": 1, "zone_name": "Rack Aisle 2", "zone_type": "YELLOW_ZONE", "door_distance": 2, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "RACK-Y6", "row": 2, "col": 2, "zone_name": "Rack Aisle 2", "zone_type": "YELLOW_ZONE", "door_distance": 2, "zone_tag": "Yellow Zone: Standard market distribution"},
    {"slot_id": "RACK-R1", "row": 3, "col": 0, "zone_name": "Loading Dock Front Portal", "zone_type": "RED_ZONE", "door_distance": 1, "zone_tag": "Red Zone: Front of dock / Sell within 24-48h"},
    {"slot_id": "RACK-R2", "row": 3, "col": 1, "zone_name": "Loading Dock Front Portal", "zone_type": "RED_ZONE", "door_distance": 1, "zone_tag": "Red Zone: Front of dock / Sell within 24-48h"},
    {"slot_id": "RACK-R3", "row": 3, "col": 2, "zone_name": "Loading Dock Front Portal", "zone_type": "RED_ZONE", "door_distance": 1, "zone_tag": "Red Zone: Front of dock / Sell within 24-48h"},
]

@router.get("/grid")
def get_fifo_virtual_grid(
    layout_type: str = "truck",  # "truck" or "storage"
    db: Session = Depends(get_db)
):
    """
    Returns virtual grid layout with 3-Zone logistics color-coding:
    - RED ZONE (Sell within 24-48 hours): Front of loading dock or truck.
    - YELLOW ZONE (Sell within 3-5 days): Standard market distribution.
    - GREEN ZONE (Stable shelf life): Can be held back or shipped to more distant markets.
    """
    shipments = db.query(Shipment).filter(Shipment.status != "DELIVERED").all()

    # Sort shipments by FIFO / FEFO Priority:
    # Smallest remaining shelf-life first
    def fifo_sort_key(s: Shipment):
        latest_pred = s.predictions[0] if s.predictions else None
        remaining_hours = latest_pred.remaining_shelf_life_hours if latest_pred else 999.0
        start_ts = s.start_time.timestamp() if s.start_time else 0
        return (remaining_hours, start_ts)

    sorted_shipments = sorted(shipments, key=fifo_sort_key)

    slots_template = TRUCK_SLOTS if layout_type == "truck" else STORAGE_SLOTS
    grid_cells = []

    # Map shipments into slots
    for i, slot in enumerate(slots_template):
        cell_data = {
            "slot_id": slot["slot_id"],
            "row": slot["row"],
            "col": slot["col"],
            "zone_name": slot["zone_name"],
            "zone_type": slot["zone_type"],
            "zone_tag": slot["zone_tag"],
            "door_distance": slot["door_distance"],
            "batch": None,
            "status": "EMPTY"
        }

        if i < len(sorted_shipments):
            s = sorted_shipments[i]
            latest_tel = s.telemetry_records[0] if s.telemetry_records else None
            latest_pred = s.predictions[0] if s.predictions else None
            latest_price = s.price_recommendations[0] if s.price_recommendations else None

            remaining_hours = latest_pred.remaining_shelf_life_hours if latest_pred else 120.0
            risk = latest_pred.spoilage_risk if latest_pred else "LOW"

            # 3-Zone Classification based on calculated shelf life:
            # 🔴 Red Zone: Sell within 24–48 hours (remaining_hours <= 48)
            # 🟡 Yellow Zone: Sell within 3–5 days (48 < remaining_hours <= 120)
            # 🟢 Green Zone: Stable shelf life (remaining_hours > 120)
            if remaining_hours <= 48.0 or risk in ["CRITICAL", "HIGH"]:
                color_code = "RED"
                zone_label = "Red Zone (Sell within 24–48 hours)"
                logistics_instruction = "Must be placed at the very front of the loading dock or truck for immediate unload"
                market_strategy = "Emergency local liquidation & rapid clearance"
            elif remaining_hours <= 120.0:
                color_code = "YELLOW"
                zone_label = "Yellow Zone (Sell within 3–5 days)"
                logistics_instruction = "Standard market distribution; staging in mid-cargo zone"
                market_strategy = "Standard regional mandi distribution"
            else:
                color_code = "GREEN"
                zone_label = "Green Zone (Stable shelf life)"
                logistics_instruction = "Can be held back or shipped to more distant, high-paying markets"
                market_strategy = "Long-haul interstate arbitrage & storage reserve"

            cell_data["status"] = "OCCUPIED"
            cell_data["batch"] = {
                "shipment_id": s.id,
                "tracking_number": s.tracking_number,
                "produce_name": s.produce.name,
                "produce_icon": s.produce.icon,
                "quantity_kg": s.quantity,
                "origin": s.origin,
                "destination": s.destination,
                "start_time": s.start_time.isoformat() if s.start_time else "",
                "temperature": latest_tel.temperature if latest_tel else 4.0,
                "humidity": latest_tel.humidity if latest_tel else 75.0,
                "remaining_shelf_life_hours": remaining_hours,
                "remaining_shelf_life_days": round(remaining_hours / 24.0, 1),
                "spoilage_risk": risk,
                "discount_percentage": latest_price.discount_percentage if latest_price else 0.0,
                "recommended_price": latest_price.recommended_price if latest_price else s.original_price,
                "color_code": color_code,
                "zone_label": zone_label,
                "logistics_instruction": logistics_instruction,
                "market_strategy": market_strategy,
                "fifo_queue_position": i + 1  # 1 = Top of FIFO stack
            }

        grid_cells.append(cell_data)

    # Statistical summary
    occupied_cells = [c for c in grid_cells if c["batch"] is not None]
    red_count = sum(1 for c in occupied_cells if c["batch"]["color_code"] == "RED")
    yellow_count = sum(1 for c in occupied_cells if c["batch"]["color_code"] == "YELLOW")
    green_count = sum(1 for c in occupied_cells if c["batch"]["color_code"] == "GREEN")

    dispatch_queue = [c["batch"] for c in occupied_cells]

    return {
        "layout_type": layout_type,
        "total_slots": len(slots_template),
        "occupied_slots": len(occupied_cells),
        "empty_slots": len(slots_template) - len(occupied_cells),
        "red_zone_batches": red_count,
        "yellow_zone_batches": yellow_count,
        "green_zone_batches": green_count,
        "fifo_dispatch_queue": dispatch_queue,
        "grid_cells": grid_cells,
        "zone_definitions": {
            "RED": {
                "title": "Red Zone (Sell within 24–48 hours)",
                "action": "Must be placed at the very front of the loading dock or truck.",
                "color": "#EF4444"
            },
            "YELLOW": {
                "title": "Yellow Zone (Sell within 3–5 days)",
                "action": "Standard market distribution.",
                "color": "#FBBF24"
            },
            "GREEN": {
                "title": "Green Zone (Stable shelf life)",
                "action": "Can be held back or shipped to more distant, high-paying markets.",
                "color": "#10B981"
            }
        }
    }

@router.post("/dispatch-next")
def dispatch_next_fifo_batch(
    layout_type: str = "truck",
    db: Session = Depends(get_db)
):
    """
    Dispatches the top batch in the FIFO queue (simulates unloading/liquidating).
    """
    grid_info = get_fifo_virtual_grid(layout_type, db)
    queue = grid_info.get("fifo_dispatch_queue", [])

    if not queue:
        raise HTTPException(status_code=400, detail="FIFO Queue is empty. No batches to dispatch.")

    top_batch = queue[0]
    shipment = db.query(Shipment).filter(Shipment.id == top_batch["shipment_id"]).first()
    if shipment:
        shipment.status = "LIQUIDATED" if top_batch["discount_percentage"] > 0 else "DELIVERED"
        db.commit()

    return {
        "success": True,
        "dispatched_batch": top_batch,
        "message": f"Successfully unloaded Batch {top_batch['tracking_number']} ({top_batch['produce_name']}, {top_batch['quantity_kg']} kg) from Red Zone front dock following FIFO sequence."
    }
