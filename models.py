import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="transporter")  # "transporter" or "retailer"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    shipments = relationship("Shipment", back_populates="transporter")
    purchases = relationship("MarketplaceListing", back_populates="buyer")


class Produce(Base):
    __tablename__ = "produce"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=False)  # "Fruit" or "Vegetable"
    initial_shelf_life_hours = Column(Float, nullable=False)
    base_price = Column(Float, nullable=False)  # in ₹/kg
    ideal_temp_min = Column(Float, default=2.0)
    ideal_temp_max = Column(Float, default=6.0)
    ideal_humidity_min = Column(Float, default=70.0)
    ideal_humidity_max = Column(Float, default=85.0)
    icon = Column(String(20), default="📦")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    shipments = relationship("Shipment", back_populates="produce")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(50), unique=True, index=True, nullable=False)
    produce_id = Column(Integer, ForeignKey("produce.id"), nullable=False)
    transporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)  # in kg
    original_price = Column(Float, nullable=False)  # ₹/kg
    status = Column(String(50), default="IN_TRANSIT")  # IN_TRANSIT, DELIVERED, LIQUIDATED, SPOILED
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    expected_arrival = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    produce = relationship("Produce", back_populates="shipments")
    transporter = relationship("User", back_populates="shipments")
    telemetry_records = relationship("Telemetry", back_populates="shipment", cascade="all, delete-orphan", order_by="Telemetry.timestamp.desc()")
    predictions = relationship("Prediction", back_populates="shipment", cascade="all, delete-orphan", order_by="Prediction.created_at.desc()")
    price_recommendations = relationship("PriceRecommendation", back_populates="shipment", cascade="all, delete-orphan", order_by="PriceRecommendation.created_at.desc()")
    alerts = relationship("Alert", back_populates="shipment", cascade="all, delete-orphan", order_by="Alert.created_at.desc()")
    marketplace_listing = relationship("MarketplaceListing", back_populates="shipment", uselist=False, cascade="all, delete-orphan")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    temperature = Column(Float, nullable=False)  # in °C
    humidity = Column(Float, nullable=False)     # in %
    transit_hours = Column(Float, default=0.0)
    transit_delay = Column(Float, default=0.0)   # in hours
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    shipment = relationship("Shipment", back_populates="telemetry_records")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    remaining_shelf_life_hours = Column(Float, nullable=False)
    spoilage_risk = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    degradation_score = Column(Float, nullable=False)    # 0.0 to 100.0 or rate factor
    confidence_score = Column(Float, nullable=False)     # percentage e.g. 92.5
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    shipment = relationship("Shipment", back_populates="predictions")


class PriceRecommendation(Base):
    __tablename__ = "price_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    original_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, nullable=False)  # e.g. 35.0
    recommended_price = Column(Float, nullable=False)    # original_price * (1 - discount/100)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="ACTIVE")        # ACTIVE, APPLIED, REJECTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    shipment = relationship("Shipment", back_populates="price_recommendations")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # TEMPERATURE_SPIKE, TRANSIT_DELAY, HIGH_RISK, SHELF_LIFE_CRITICAL, MARKETPLACE_OFFER
    severity = Column(String(50), nullable=False)    # WARNING, HIGH_RISK, CRITICAL, INFO
    message = Column(Text, nullable=False)
    read_status = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    shipment = relationship("Shipment", back_populates="alerts")


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False, unique=True)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    discount_percentage = Column(Float, nullable=False)
    status = Column(String(50), default="AVAILABLE")  # AVAILABLE, SOLD, EXPIRED, CANCELLED
    listed_at = Column(DateTime, default=datetime.datetime.utcnow)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    purchased_at = Column(DateTime, nullable=True)

    shipment = relationship("Shipment", back_populates="marketplace_listing")
    buyer = relationship("User", back_populates="purchases")
