# AgroSense — AI-Powered Perishable Cold Chain Monitoring & Smart Liquidation Platform

> **A 100% software-based AgriTech platform** designed to eliminate perishable fruits and vegetables waste during transit through explainable bio-respiration degradation modeling, automated dynamic discounting, and real-time retailer liquidation.

---

## 1. Project Overview

**AgroSense** is a full-stack, enterprise-grade cold chain monitoring and autonomous liquidation platform. In modern agricultural logistics, millions of tonnes of produce spoil before reaching wholesale mandis or retail shelves due to undetected temperature excursions, humidity imbalance, or transit delays. 

Instead of waiting for consignments to arrive spoiled at destinations—resulting in a 100% financial and biological loss—AgroSense continuously simulates and monitors cold-chain telemetry, projects remaining shelf life via an explainable biological model, triggers progressive dynamic liquidation discounts, and immediately lists at-risk batches on a retailer marketplace for rapid local clearance.

**Zero Hardware Requirement:** This platform is 100% software-based. No Arduino, Raspberry Pi, ESP32, or physical IoT devices are required; all climate dynamics and sensor telemetry are simulated and persisted through REST APIs and an interactive simulation dashboard.

---

## 2. Problem Statement

1. **High In-Transit Spoilage Rates:** In emerging and developed markets alike, 25%–40% of fresh produce (tomatoes, leafy greens, mangoes, bananas) is lost in transit due to cold-chain refrigeration malfunctions or highway bottlenecks.
2. **Delayed Reaction:** Transporters only discover spoilage upon destination unloading, when produce is already rotten and has zero commercial salvage value.
3. **Information Asymmetry:** Nearby supermarket chains and local grocery retailers have high daily demand but lack visibility into consignments currently in transit that need expedited liquidation at discounted rates.
4. **Black-Box AI Skepticism:** Logistics managers reject black-box neural networks for food shelf-life decisions because decisions cannot be explained during technical or regulatory audits.

---

## 3. Proposed Solution

AgroSense solves this through a closed-loop automated pipeline:

```
[ Cold Chain Consignment (e.g. AGRO102 Tomatoes) ]
                     │
                     ▼
[ Sensor Telemetry Simulator (Temp, Humidity, Transit Delay) ]
                     │
                     ▼ (Persisted to Live Database)
[ Explainable AI Degradation Engine (Q10 Respiration Kinetics) ]
                     │
                     ▼
[ Dynamic Spoilage Risk Calculation (LOW / MEDIUM / HIGH / CRITICAL) ]
                     │
                     ▼
[ Automated Dynamic Liquidation Pricing Engine (e.g. -35% OFF) ]
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
[ Real-Time Alert System ]  [ Retailer Marketplace Auto-Listing ]
         │                       │
         ▼                       ▼
[ Transporter Notification ] [ Retailer One-Click Offer Acceptance ]
```

---

## 4. Architecture

AgroSense is structured with a decoupled, clean three-tier architecture:

```
┌────────────────────────────────────────────────────────┐
│                   React 19 Frontend                    │
│   TypeScript • Tailwind CSS • Recharts • Lucide Icons  │
│   - Transporter Dashboard & Shipment Detail Graphs    │
│   - Dedicated Climate & Delay Simulator Dashboard     │
│   - Retailer Marketplace & Instant Offer Acceptance   │
│   - AI Explainability White-Box Exploration Center    │
└───────────────────────────▲────────────────────────────┘
                            │ REST JSON APIs
                            ▼
┌────────────────────────────────────────────────────────┐
│                 Python FastAPI Backend                 │
│   - Role-Based Access Control (Transporter / Retailer) │
│   - Autonomous Pipeline Coordinator                   │
│   - Q10 Respiration & VPD Transpiration Models         │
│   - Dynamic Liquidation Pricing Logic                  │
└───────────────────────────▲────────────────────────────┘
                            │ SQLAlchemy ORM
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Live Database Layer                  │
│   - SQLite (Zero-config out of the box)                │
│   - PostgreSQL / Supabase Compatible via DATABASE_URL  │
│   - Fully Normalized 8-Table Relational Schema         │
└────────────────────────────────────────────────────────┘
```

---

## 5. Technology Stack

- **Frontend:**
  - **React 19** with **TypeScript**
  - **Vite 8** for rapid hot-module reloading and bundle building
  - **Tailwind CSS v4** for clean, responsive, dark AgriTech design aesthetics
  - **Recharts** for temperature/humidity time series, degradation curves, and risk trajectories
  - **Lucide React** for icons
- **Backend:**
  - **Python 3.10+** with **FastAPI**
  - **Uvicorn** ASGI server
  - **SQLAlchemy 2.0** ORM for relational persistence
  - **Pydantic v2** for strict data validation
  - **PyJWT & Bcrypt** for secure role-based authentication
  - **Scikit-learn & NumPy** for computational statistical modeling
- **Database:**
  - **SQLite** default out of the box (zero installation necessary)
  - **PostgreSQL / Supabase** supported by changing `DATABASE_URL` in `.env`

---

## 6. Database Schema

The database consists of 8 fully-relational, normalized tables:

1. **`users`**:
   - `id` (PK, Integer)
   - `name` (String)
   - `email` (String, Unique)
   - `password_hash` (String)
   - `role` (String: `transporter` or `retailer`)
   - `created_at` (DateTime)

2. **`produce`**:
   - `id` (PK, Integer)
   - `name` (String, Unique: Tomato, Banana, Apple, Mango, Spinach, Potato)
   - `category` (String: Fruit / Vegetable)
   - `initial_shelf_life_hours` (Float)
   - `base_price` (Float in ₹/kg)
   - `ideal_temp_min`, `ideal_temp_max`, `ideal_humidity_min`, `ideal_humidity_max` (Float)
   - `icon` (String)

3. **`shipments`**:
   - `id` (PK, Integer)
   - `tracking_number` (String, Unique e.g. AGRO102)
   - `produce_id` (FK -> `produce.id`)
   - `transporter_id` (FK -> `users.id`)
   - `origin`, `destination` (String)
   - `quantity` (Float in kg)
   - `original_price` (Float in ₹/kg)
   - `status` (String: `IN_TRANSIT`, `DELIVERED`, `LIQUIDATED`, `SPOILED`)
   - `start_time`, `expected_arrival`, `created_at` (DateTime)

4. **`telemetry`**:
   - `id` (PK, Integer)
   - `shipment_id` (FK -> `shipments.id`)
   - `temperature` (Float in °C)
   - `humidity` (Float in %)
   - `transit_hours` (Float)
   - `transit_delay` (Float in hours)
   - `timestamp` (DateTime)

5. **`predictions`**:
   - `id` (PK, Integer)
   - `shipment_id` (FK -> `shipments.id`)
   - `remaining_shelf_life_hours` (Float)
   - `spoilage_risk` (String: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
   - `degradation_score` (Float, 0.0 to 100.0)
   - `confidence_score` (Float, percentage)
   - `explanation` (Text)
   - `created_at` (DateTime)

6. **`price_recommendations`**:
   - `id` (PK, Integer)
   - `shipment_id` (FK -> `shipments.id`)
   - `original_price` (Float)
   - `discount_percentage` (Float)
   - `recommended_price` (Float)
   - `reason` (Text)
   - `status` (String: `ACTIVE`, `APPLIED`, `REJECTED`)
   - `created_at` (DateTime)

7. **`alerts`**:
   - `id` (PK, Integer)
   - `shipment_id` (FK -> `shipments.id`)
   - `alert_type` (String: `TEMPERATURE_SPIKE`, `TRANSIT_DELAY`, `HIGH_RISK`, `SHELF_LIFE_CRITICAL`, `MARKETPLACE_OFFER`)
   - `severity` (String: `INFO`, `WARNING`, `HIGH_RISK`, `CRITICAL`)
   - `message` (Text)
   - `read_status` (Boolean)
   - `created_at` (DateTime)

8. **`marketplace_listings`**:
   - `id` (PK, Integer)
   - `shipment_id` (FK -> `shipments.id`, Unique)
   - `quantity` (Float)
   - `price` (Float)
   - `discount_percentage` (Float)
   - `status` (String: `AVAILABLE`, `SOLD`, `EXPIRED`, `CANCELLED`)
   - `listed_at` (DateTime)
   - `buyer_id` (FK -> `users.id`, Nullable)
   - `purchased_at` (DateTime, Nullable)

---

## 7. AI & Degradation Logic (Explainable White-Box Model)

The AI engine uses deterministic biological respiration kinetics and transpiration mechanics:

### A. Q10 Biological Respiration Acceleration
Based on Van 't Hoff's biological kinetics, produce respiration rate accelerates exponentially with temperature rise:
$$\text{Thermal Multiplier} = Q_{10}^{\frac{\Delta T}{8.0}}$$
Where $\Delta T = \max(0, T_{\text{current}} - T_{\text{optimal\_max}})$ and $Q_{10}$ is produce-specific (2.2 for Tomatoes, 2.8 for Spinach, 1.8 for Apples).

### B. Vapor Pressure Deficit (VPD) Penalty
When relative humidity drops below recommended thresholds, skin transpiration accelerates water loss and wilting:
$$\text{Humidity Penalty} = 1.0 + \frac{\Delta RH}{50.0}$$

### C. Transit Delay Compounding
Unplanned road delay hours are added directly to the effective shelf-life consumption:
$$\text{Effective Hours Consumed} = (\text{Transit Hours} \times \text{Thermal Multiplier} \times \text{Humidity Penalty}) + (\text{Transit Delay} \times 2.2)$$
$$\text{Remaining Shelf Life} = \max(1.0, \text{Initial Shelf Life} - \text{Effective Hours Consumed})$$

### D. Dynamic Spoilage Risk Categorization
- **🟢 LOW:** Remaining shelf life $> 72\text{ hours}$ (Degradation score $< 35\%$)
- **🟡 MEDIUM:** Remaining shelf life between $48\text{ and }72\text{ hours}$ (Degradation score $35\% - 60\%$)
- **🟠 HIGH:** Remaining shelf life between $18\text{ and }48\text{ hours}$ (Degradation score $60\% - 80\%$)
- **🔴 CRITICAL:** Remaining shelf life $< 18\text{ hours}$ (Degradation score $\ge 80\%$)

### E. Automatic Dynamic Liquidation Pricing Rules
- $> 72\text{ hours remaining:}$ 0% – 5% discount
- $48 - 72\text{ hours remaining:}$ 10% discount
- $24 - 48\text{ hours remaining:}$ 25% discount
- $12 - 24\text{ hours remaining:}$ 35% – 50% discount (**35% discount for 18h Tomato scenario**)
- $< 12\text{ hours remaining:}$ 60% – 70% emergency liquidation discount

*Disclaimer: The shelf-life prediction is an explainable simulation prototype designed for logistical decision support and does not constitute a certified food-safety laboratory certification.*

---

## 8. Documented REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new user account (transporter or retailer) |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT Bearer access token |
| `GET` | `/api/auth/me` | Fetch currently logged in user profile |
| `GET` | `/api/produce` | Get list of all produce types and biological thresholds |
| `GET` | `/api/shipments` | List all consignments with latest telemetry and predictions |
| `POST` | `/api/shipments` | Transporters create a new shipment |
| `GET` | `/api/shipments/{id}` | Get shipment details with 20 historical graph data points |
| `POST` | `/api/telemetry` | Record telemetry data and execute autonomous pipeline |
| `GET` | `/api/telemetry/{shipment_id}` | Fetch historical telemetry points for a shipment |
| `POST` | `/api/predict/{shipment_id}` | Trigger re-prediction and generate explainability factors |
| `GET` | `/api/predictions/{shipment_id}`| Get latest prediction and breakdown factor reasons |
| `POST` | `/api/simulate/temperature-spike` | **Simulate temperature spike (18°C) for demo scenario** |
| `POST` | `/api/simulate/transit-delay` | Simulate highway checkpoint transit delay |
| `POST` | `/api/simulate/custom` | Apply custom slider adjustments (temp, humidity, delay) |
| `POST` | `/api/simulate/reset` | Reset consignment to safe baseline cold storage |
| `POST` | `/api/price-recommendation/{shipment_id}` | Query dynamic pricing engine recommendation |
| `GET` | `/api/marketplace` | Fetch active liquidation deals for retailers |
| `POST` | `/api/marketplace/{id}/accept` | Retailers claim and purchase discounted consignment |
| `GET` | `/api/alerts` | List real-time cold chain spoilage alerts |
| `PATCH` | `/api/alerts/{id}/read` | Mark individual alert as read |
| `POST` | `/api/alerts/mark-all-read` | Mark all alerts as read |
| `GET` | `/api/inventory/grid` | **Generate virtual Reefer Truck or Cold Storage FIFO grid** |
| `POST` | `/api/inventory/dispatch-next` | **Pop and dispatch highest priority batch from FIFO stack** |
| `GET` | `/api/market-channels/live-feed` | **Simulated live wholesale mandi, retail, and factory spot ticker** |
| `GET` | `/api/market-channels/compare/{id}` | **Direct 3-buyer comparison matrix (Processing vs Quick-Commerce vs Mandi)** |
| `POST` | `/api/market-channels/route` | **Confirm sale and route consignment to chosen buyer channel** |
| `GET` | `/api/analytics/overview` | Fetch economic metrics, loss avoided, and distributions |
| `GET` | `/api/health` | Backend service health probe |

---

## 9. Installation Instructions

### Prerequisites
- **Python 3.10+**
- **Node.js v18+** & **npm**

### Step 1: Clone or Navigate to the Workspace
```bash
cd c:\davinci\agrosensor
```

### Step 2: Set Up Python Backend Virtual Environment
```bash
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# Install backend dependencies:
pip install -r backend/requirements.txt
```

### Step 3: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 10. Environment Variables

Create a `.env` file in the project root (a template is available in `.env.example`):

```ini
# Secret key for JWT token hashing
SECRET_KEY=agrosense_dev_secret_key_993427810_safe_for_local_testing

# Database URL (Default: local SQLite; or PostgreSQL/Supabase):
DATABASE_URL=sqlite:///./agrosense.db

# Or for Supabase PostgreSQL:
# DATABASE_URL=postgresql://postgres.yourproject:yourpassword@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

ENV=development
API_PORT=8000
FRONTEND_PORT=5173
```

---

## 11. How to Run the Backend

From the project root:
```bash
.\venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend will start at: **`http://127.0.0.1:8000`**
Interactive Swagger API docs available at: **`http://127.0.0.1:8000/docs`**

*Note: Database tables and initial seed data (6 produce types, 10 realistic shipments, demo users) are created automatically on initial startup.*

---

## 12. How to Run the Frontend

From the `frontend` directory:
```bash
cd frontend
npm run dev
```
The Vite development server will start at: **`http://localhost:5173`**

---

## 13. Demo Instructions (The Required 3-Minute Hackathon Demo)

1. **Launch the Web Application:** Open `http://localhost:5173` in your browser.
2. **Observe Initial Baseline State (Shipment AGRO102):**
   - Produce: **Tomato** (500 kg, Chennai → Coimbatore)
   - Temperature: **4°C** | Humidity: **75%**
   - Remaining Shelf Life: **5 Days** (120 Hours)
   - Spoilage Risk: **LOW** (🟢)
   - Current Price: **₹100/kg**
3. **Execute the Demo Trigger:**
   - Click the prominent **[Simulate Temperature Spike (18°C)]** button located in the top banner (or inside the Telemetry tab).
4. **Watch the Automated Pipeline Execute (in ~1-2 seconds):**
   - Telemetry (18°C) is saved to the database.
   - AI recalculates degradation rate via Q10 thermal acceleration.
   - Remaining shelf life visibly drops: **5 Days → 18 Hours**!
   - Spoilage risk updates: **LOW → HIGH** (🟠).
   - Dynamic liquidation engine recommends: **35% Discount**.
   - Price updates: **₹100/kg → ₹65/kg**.
   - Spoilage alert is generated: *"Estimated shelf life is approximately 18 hours. Consider immediate liquidation."*
   - Marketplace listing is automatically generated for local retailers.
5. **Switch Role to Retailer:**
   - In the top-right role switcher, click **[Retailer]**.
   - Navigate to the **Marketplace** tab.
   - See the lot: **Fresh Tomatoes (500 kg, 18 hours remaining, ₹65/kg, 35% OFF)** with reason: *"Temperature spike detected during transportation."*
   - Click **[Accept Offer]**. Order is claimed and consignment transitions to **LIQUIDATED**.
6. **Inspect Impact Analytics:**
   - Click the **Analytics** tab to view the **💰 Estimated Loss Avoided: ₹32,500+** metric and distribution charts.
7. **Explainability Audit:**
   - Click **Why this Prediction?** or navigate to **AI Predictions** to inspect the mathematical breakdown showing temperature delta (+14°C above limit), cellular respiration multiplier, and technical evaluation disclosures.
8. **Reset Scenario:**
   - Click **[Reset Normal (4°C / 5 Days)]** to return AGRO102 to baseline conditions at any time.

---

## 14. Security Considerations

- **Zero Client Credential Leakage:** No database passwords, JWT secrets, or cloud keys are present in frontend JavaScript code or bundles.
- **Backend Environment Isolation:** All secrets loaded strictly via backend `.env` through `backend/config.py`.
- **Password Protection:** Passwords securely hashed with bcrypt using auto-generated salts.
- **Role-Based Authorization:** Transporters cannot accept liquidation offers; retailers cannot tamper with transporter sensor telemetry.
- **Pydantic Validation:** All incoming sensor payloads strictly bounded (-10°C to 60°C temperature, 0% to 100% humidity).

---

## 15. Limitations

- **Simulated Environment:** Sensor telemetry is simulated via REST APIs and web sliders rather than physical IoT hardware (by design according to competition specifications).
- **Prototype Food Safety Scope:** Predictions model biological respiration and shelf life for logistical planning; they do not replace certified pathogen laboratory assays.
- **Network Connectivity Assumption:** Assumes cold-chain vehicles maintain cellular connectivity to stream telemetry.

---

## 16. Future Enhancements

- **Machine Learning Transition:** Plug in XGBoost or Random Forest regression models trained on USDA/FAO perishability datasets using the existing modular `ml_engine.py` interface.
- **Route Weather Integration:** Connect OpenWeatherMap APIs to predict ambient heatwaves along highway transit routes before temperature spikes occur.
- **Automated Mandi Bidding:** Implement automated multi-retailer reverse auctions for distressed consignments.
- **Geofenced Push Notifications:** WhatsApp and SMS alerts to supermarket procurement managers within a 30 km radius of the arriving vehicle.

---

## 18. Micro-Climate Weather API & Heatwave Emergency Mitigation

AgroSense features a live **Micro-Climate Weather Station** integrated directly with the Open-Meteo High-Resolution Forecasting API (`https://api.open-meteo.com/v1/forecast`), requiring zero external API keys:

1. **Farmer GPS Coordinates & Agricultural Belts:**
   - Transporters and farmers can query micro-climate conditions by custom GPS coordinates (`navigator.geolocation`) or pick from pre-configured agricultural production corridors (e.g. *Nashik Agri-Zone*, *Coimbatore Cold Corridor*, *Agra Potato Belt*, *Shimla Valley*).
   - Real-time endpoints: `GET /api/weather/hubs`, `GET /api/weather/current?latitude={lat}&longitude={lon}`.
2. **Autonomous Heatwave Detection ($\ge 35^\circ\text{C}$):**
   - If ambient temperatures exceed $35^\circ\text{C}$ or peak daily forecasts reach heatwave thresholds, the platform triggers a `HEATWAVE_WARNING` or `EXTREME_HEATWAVE` alert.
3. **Automatic 30% Shelf-Life Reduction:**
   - Under extreme micro-climate heat, biological cellular respiration rates surge exponentially. The platform automatically applies a **30% penalty** to remaining shelf life (`remaining_shelf_life_hours * 0.70`).
4. **Steeper, Faster Liquidation Pricing Strategy:**
   - To prevent catastrophic 100% loss from heat rot, the pricing engine applies an accelerated clearance discount (e.g. +18% emergency markdown, capping at 75% OFF) and immediately publishes the consignment to the retailer marketplace to empty inventory within a 4-hour window before heat spoils it.
   - Endpoint: `POST /api/weather/simulate-heatwave`

---

## 19. Acceptance Test Verification Checklist

- [x] **Frontend works:** React 19 + TypeScript + Vite + Tailwind CSS responsive UI
- [x] **Backend works:** Python FastAPI REST APIs running on port 8000
- [x] **Database works:** Relational SQLite / PostgreSQL database persistence verified
- [x] **User authentication works:** Secure registration, login, JWT tokens, and RBAC
- [x] **Shipment creation works:** Transporter add-shipment modal with automatic tracking numbers
- [x] **Telemetry API works:** Telemetry recorded and queried via `/api/telemetry`
- [x] **Telemetry is persisted:** All slider and spike values committed to the database
- [x] **Shelf-life prediction works:** Explainable Q10 respiration degradation algorithm
- [x] **Spoilage risk calculated:** LOW, MEDIUM, HIGH, CRITICAL states computed
- [x] **AI explanation displayed:** "Why?" modal and dedicated Explainability page
- [x] **Price recommendation works:** Dynamic pricing engine based on remaining hours
- [x] **Marketplace updates automatically:** Distressed shipments immediately listed
- [x] **Alerts are persisted:** Critical and Warning alerts stored in `alerts` table
- [x] **Retailer receives notification:** In-app notification feed and deal acceptance
- [x] **Temperature spike demo works:** 1-click execution for technical evaluation
- [x] **5 days → approximately 18 hours is demonstrated:** Exact scenario supported
- [x] **Price changes automatically:** ₹100/kg → ₹65/kg (35% OFF)
- [x] **FIFO/FEFO Visual Logistics Grid:** 3-Zone truck/cold storage loading layout (Red/Yellow/Green zones)
- [x] **Multi-Channel Market Comparison:** Direct comparison matrix across B2B Processing, Quick-Commerce (Blinkit), and Local Wholesale Mandis
- [x] **Temperature & Humidity Sliders:** Granular telemetry adjustment with real-time feedback
- [x] **Micro-Climate Weather API:** Live Open-Meteo GPS weather fetching for local micro-climates
- [x] **Heatwave 30% Shelf-Life Reduction:** Automatic 30% reduction and steeper liquidation discount recalculation
- [x] **No secrets exposed in frontend:** Clean API proxy and backend `.env` isolation
- [x] **Application is responsive:** Mobile-friendly layouts and navigation
- [x] **README is included:** Comprehensive technical guide
