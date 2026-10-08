from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Alert
from backend.schemas import AlertOut

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertOut])
def get_alerts(
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if unread_only:
        query = query.filter(Alert.read_status == False)
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return alerts

@router.patch("/{id}/read")
def mark_alert_read(id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.read_status = True
    db.commit()
    return {"success": True, "alert_id": id, "read_status": True}

@router.post("/mark-all-read")
def mark_all_alerts_read(db: Session = Depends(get_db)):
    db.query(Alert).filter(Alert.read_status == False).update({"read_status": True})
    db.commit()
    return {"success": True, "message": "All alerts marked as read"}
