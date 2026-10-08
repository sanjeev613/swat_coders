from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models import User, Produce, Shipment, Telemetry, Prediction, PriceRecommendation, Alert, MarketplaceListing
from backend.auth import hash_password
from backend.pipeline import process_telemetry_pipeline

def seed_database(db: Session):
    # Check if already seeded
    if db.query(Produce).count() > 0:
        return

    print("[AgroSense] Seeding initial database...")

    # 1. Create Users
    transporter = User(
        name="Apex Cold Chain Logistics",
        email="transporter@agrosense.com",
        password_hash=hash_password("password123"),
        role="transporter"
    )
    retailer = User(
        name="FreshBazaar Supermarkets",
        email="retailer@agrosense.com",
        password_hash=hash_password("password123"),
        role="retailer"
    )
    db.add_all([transporter, retailer])
    db.commit()
    db.refresh(transporter)
    db.refresh(retailer)

    # 2. Create Produce Types
    produce_list = [
        Produce(
            name="Tomato",
            category="Vegetable",
            initial_shelf_life_hours=120.0,  # 5 days
            base_price=100.0,
            ideal_temp_min=4.0,
            ideal_temp_max=6.0,
            ideal_humidity_min=70.0,
            ideal_humidity_max=85.0,
            icon="🍅"
        ),
        Produce(
            name="Banana",
            category="Fruit",
            initial_shelf_life_hours=168.0,  # 7 days
            base_price=40.0,
            ideal_temp_min=12.0,
            ideal_temp_max=15.0,
            ideal_humidity_min=85.0,
            ideal_humidity_max=90.0,
            icon="🍌"
        ),
        Produce(
            name="Apple",
            category="Fruit",
            initial_shelf_life_hours=720.0,  # 30 days
            base_price=140.0,
            ideal_temp_min=1.0,
            ideal_temp_max=4.0,
            ideal_humidity_min=90.0,
            ideal_humidity_max=95.0,
            icon="🍎"
        ),
        Produce(
            name="Mango",
            category="Fruit",
            initial_shelf_life_hours=144.0,  # 6 days
            base_price=220.0,
            ideal_temp_min=11.0,
            ideal_temp_max=13.0,
            ideal_humidity_min=85.0,
            ideal_humidity_max=90.0,
            icon="🥭"
        ),
        Produce(
            name="Spinach",
            category="Vegetable",
            initial_shelf_life_hours=96.0,   # 4 days
            base_price=50.0,
            ideal_temp_min=1.0,
            ideal_temp_max=3.0,
            ideal_humidity_min=95.0,
            ideal_humidity_max=98.0,
            icon="🥬"
        ),
        Produce(
            name="Potato",
            category="Vegetable",
            initial_shelf_life_hours=1440.0, # 60 days
            base_price=25.0,
            ideal_temp_min=7.0,
            ideal_temp_max=10.0,
            ideal_humidity_min=85.0,
            ideal_humidity_max=90.0,
            icon="🥔"
        )
    ]
    db.add_all(produce_list)
    db.commit()

    produce_map = {p.name: p for p in db.query(Produce).all()}

    # 3. Create 10 Shipments
    now = datetime.utcnow()
    shipment_data = [
        # AGRO102 is the designated primary demo shipment
        {
            "code": "AGRO102",
            "produce": "Tomato",
            "quantity": 500.0,
            "origin": "Chennai",
            "destination": "Coimbatore",
            "price": 100.0,
            "temp": 4.0,
            "hum": 75.0,
            "transit_h": 18.0,
            "delay": 0.0,
            "history": [(3.8, 74), (4.1, 75), (4.0, 75), (4.2, 76), (4.0, 75)]
        },
        {
            "code": "AGRO101",
            "produce": "Banana",
            "quantity": 1200.0,
            "origin": "Jalgaon",
            "destination": "Mumbai",
            "price": 40.0,
            "temp": 13.5,
            "hum": 88.0,
            "transit_h": 12.0,
            "delay": 0.0,
            "history": [(13.0, 87), (13.2, 88), (13.5, 88)]
        },
        {
            "code": "AGRO103",
            "produce": "Apple",
            "quantity": 800.0,
            "origin": "Shimla",
            "destination": "New Delhi",
            "price": 140.0,
            "temp": 2.5,
            "hum": 92.0,
            "transit_h": 22.0,
            "delay": 0.0,
            "history": [(2.0, 91), (2.3, 92), (2.5, 92)]
        },
        {
            "code": "AGRO104",
            "produce": "Mango",
            "quantity": 450.0,
            "origin": "Ratnagiri",
            "destination": "Pune",
            "price": 250.0,
            "temp": 12.0,
            "hum": 86.0,
            "transit_h": 8.0,
            "delay": 0.0,
            "history": [(11.8, 85), (12.0, 86)]
        },
        {
            "code": "AGRO105",
            "produce": "Spinach",
            "quantity": 300.0,
            "origin": "Ooty",
            "destination": "Bangalore",
            "price": 50.0,
            "temp": 2.2,
            "hum": 96.0,
            "transit_h": 6.0,
            "delay": 0.0,
            "history": [(2.0, 95), (2.2, 96)]
        },
        {
            "code": "AGRO106",
            "produce": "Potato",
            "quantity": 2500.0,
            "origin": "Agra",
            "destination": "Lucknow",
            "price": 25.0,
            "temp": 8.5,
            "hum": 88.0,
            "transit_h": 14.0,
            "delay": 0.0,
            "history": [(8.0, 87), (8.5, 88)]
        },
        {
            "code": "AGRO107",
            "produce": "Tomato",
            "quantity": 750.0,
            "origin": "Nashik",
            "destination": "Surat",
            "price": 80.0,
            "temp": 12.5,
            "hum": 72.0,
            "transit_h": 14.0,
            "delay": 4.0,
            "history": [(7.0, 75), (10.0, 74), (12.5, 72)]
        },
        {
            "code": "AGRO108",
            "produce": "Spinach",
            "quantity": 200.0,
            "origin": "Hosur",
            "destination": "Chennai",
            "price": 45.0,
            "temp": 15.0,
            "hum": 68.0,
            "transit_h": 10.0,
            "delay": 6.0,
            "history": [(4.0, 92), (9.0, 80), (15.0, 68)]
        },
        {
            "code": "AGRO109",
            "produce": "Mango",
            "quantity": 600.0,
            "origin": "Vijayawada",
            "destination": "Hyderabad",
            "price": 220.0,
            "temp": 11.5,
            "hum": 87.0,
            "transit_h": 9.0,
            "delay": 0.0,
            "history": [(11.0, 86), (11.5, 87)]
        },
        {
            "code": "AGRO110",
            "produce": "Banana",
            "quantity": 950.0,
            "origin": "Theni",
            "destination": "Madurai",
            "price": 38.0,
            "temp": 13.8,
            "hum": 89.0,
            "transit_h": 5.0,
            "delay": 0.0,
            "history": [(13.5, 88), (13.8, 89)]
        }
    ]

    for item in shipment_data:
        p_obj = produce_map[item["produce"]]
        shipment = Shipment(
            tracking_number=item["code"],
            produce_id=p_obj.id,
            transporter_id=transporter.id,
            origin=item["origin"],
            destination=item["destination"],
            quantity=item["quantity"],
            original_price=item["price"],
            status="IN_TRANSIT",
            start_time=now - timedelta(hours=item["transit_h"]),
            expected_arrival=now + timedelta(hours=12)
        )
        db.add(shipment)
        db.commit()
        db.refresh(shipment)

        # Seed historical points
        for i, (h_temp, h_hum) in enumerate(item["history"]):
            t_time = now - timedelta(hours=(item["transit_h"] - (i * (item["transit_h"] / max(1, len(item["history"]))))))
            db.add(Telemetry(
                shipment_id=shipment.id,
                temperature=h_temp,
                humidity=h_hum,
                transit_hours=round(item["transit_h"] - (len(item["history"]) - 1 - i) * 3, 1),
                transit_delay=0.0,
                timestamp=t_time
            ))
        db.commit()

        # Run pipeline for current condition
        process_telemetry_pipeline(
            db=db,
            shipment_id=shipment.id,
            temperature=item["temp"],
            humidity=item["hum"],
            transit_delay=item["delay"],
            transit_hours_override=item["transit_h"]
        )

    print("[AgroSense] Database successfully seeded with 6 produce types, 10 shipments, and active telemetry!")
