from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="transporter", pattern="^(transporter|retailer)$")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

# --- Produce Schemas ---
class ProduceOut(BaseModel):
    id: int
    name: str
    category: str
    initial_shelf_life_hours: float
    base_price: float
    ideal_temp_min: float
    ideal_temp_max: float
    ideal_humidity_min: float
    ideal_humidity_max: float
    icon: str

    class Config:
        from_attributes = True

# --- Telemetry Schemas ---
class TelemetryCreate(BaseModel):
    shipment_id: int
    temperature: float = Field(..., ge=-10.0, le=60.0)
    humidity: float = Field(..., ge=0.0, le=100.0)
    transit_hours: Optional[float] = 0.0
    transit_delay: Optional[float] = 0.0

class TelemetryOut(BaseModel):
    id: int
    shipment_id: int
    temperature: float
    humidity: float
    transit_hours: float
    transit_delay: float
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Prediction Schemas ---
class PredictionOut(BaseModel):
    id: int
    shipment_id: int
    remaining_shelf_life_hours: float
    spoilage_risk: str
    degradation_score: float
    confidence_score: float
    explanation: str
    created_at: datetime
    factors: Optional[List[str]] = None

    class Config:
        from_attributes = True

# --- Price Recommendation Schemas ---
class PriceRecommendationOut(BaseModel):
    id: int
    shipment_id: int
    original_price: float
    discount_percentage: float
    recommended_price: float
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Alert Schemas ---
class AlertOut(BaseModel):
    id: int
    shipment_id: int
    alert_type: str
    severity: str
    message: str
    read_status: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Marketplace Listing Schemas ---
class MarketplaceListingOut(BaseModel):
    id: int
    shipment_id: int
    quantity: float
    price: float
    discount_percentage: float
    status: str
    listed_at: datetime
    buyer_id: Optional[int] = None
    purchased_at: Optional[datetime] = None
    # Joined shipment information for rich marketplace display
    produce_name: Optional[str] = None
    produce_category: Optional[str] = None
    produce_icon: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    current_location: Optional[str] = None
    original_price: Optional[float] = None
    remaining_shelf_life_hours: Optional[float] = None
    spoilage_risk: Optional[str] = None
    discount_reason: Optional[str] = None

    class Config:
        from_attributes = True

# --- Shipment Schemas ---
class ShipmentCreate(BaseModel):
    produce_id: int
    origin: str
    destination: str
    quantity: float = Field(..., gt=0)
    original_price: float = Field(..., gt=0)
    expected_arrival_hours: Optional[float] = 24.0

class ShipmentOut(BaseModel):
    id: int
    tracking_number: str
    produce_id: int
    transporter_id: int
    origin: str
    destination: str
    quantity: float
    original_price: float
    status: str
    start_time: datetime
    expected_arrival: Optional[datetime]
    created_at: datetime
    produce: Optional[ProduceOut] = None
    latest_telemetry: Optional[TelemetryOut] = None
    latest_prediction: Optional[PredictionOut] = None
    latest_price_recommendation: Optional[PriceRecommendationOut] = None
    marketplace_listing: Optional[MarketplaceListingOut] = None

    class Config:
        from_attributes = True

# --- Simulation Request Schemas ---
class TemperatureSpikeRequest(BaseModel):
    shipment_id: Optional[int] = None
    target_temperature: Optional[float] = 18.0
    humidity: Optional[float] = 75.0

class TransitDelayRequest(BaseModel):
    shipment_id: Optional[int] = None
    delay_hours: float = 8.0

class CustomTelemetryRequest(BaseModel):
    shipment_id: int
    temperature: float
    humidity: float
    transit_delay: Optional[float] = 0.0

# --- Analytics Schemas ---
class AnalyticsOverview(BaseModel):
    total_shipments: int
    successful_deliveries: int
    at_risk_shipments: int
    spoilage_incidents: int
    products_saved_kg: float
    average_discount_pct: float
    estimated_loss_avoided: float
    total_inventory_value: float
    liquidation_revenue: float
