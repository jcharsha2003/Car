# 🚗 IIA Project — Identification of Uninsured Vehicles
### Information Integration System | IIIT Delhi — M.Tech 3rd Semester

---

## 📋 Project Overview

A full-stack **Information Integration** system that identifies uninsured vehicles on the road by federating **5 independently designed databases** using a **Mediation / Global-As-View (GAV)** architecture.

### Key Features
- 🔍 **ANPR Pipeline** — Upload a vehicle image → YOLOv8 detects vehicle → EasyOCR extracts **license plate only** → queries all 5 databases
- 🗄️ **5 Independent Databases** — designed in isolation with different column names for the same vehicle registration number
- 🔗 **Federated Integration** — Mediator maps `plate_number` / `registration_id` / `vehicle_reg_no` / `vehicle_identifier` / `vehicle_ref` to a single global key
- 💻 **SQL Query Page** — Run SELECT queries against any/all 5 databases with a live results table
- 🌐 **LAN Sharing** — All team members on the same WiFi share one live database in real-time

---

## 🏗️ Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | Python + FastAPI | 3.12 / 0.115 |
| **Frontend** | React + TypeScript + Vite | 19 / 6 / 8 |
| **Database** | SQLite (5 independent DBs) | built-in |
| **ANPR — Vehicle Detection** | YOLOv8n (Ultralytics) | 8.3.14 |
| **ANPR — OCR** | EasyOCR | 1.7.2 |
| **Image Processing** | OpenCV | 4.10 |
| **ORM** | SQLAlchemy | 2.0.35 |
| **Fuzzy Matching** | RapidFuzz + Levenshtein | 3.10 / 0.26 |
| **HTTP Client** | httpx | 0.27 |
| **Charts** | Recharts | 3.10 |

---

## 📁 Project Structure

```
iia_project/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # DB paths, CORS, schema mapping config
│   │   ├── api/                # REST API routes
│   │   │   ├── routes_vehicle.py      # Vehicle scan / lookup endpoints
│   │   │   ├── routes_integration.py  # Schema info + SQL Query endpoints
│   │   │   └── routes_reports.py      # Ministry report endpoints
│   │   ├── detection/          # ANPR pipeline
│   │   │   ├── anpr_pipeline.py       # YOLOv8 + plate detection + OCR
│   │   │   └── ocr_engine.py          # EasyOCR — license plate only
│   │   ├── integration/        # Information Integration core
│   │   │   ├── mediator.py            # Federated mediator
│   │   │   ├── schema_mapper.py       # GAV schema mapping
│   │   │   ├── schema_matcher.py      # Multi-signal schema matching
│   │   │   ├── entity_resolver.py     # Plate normalization + fuzzy match
│   │   │   └── source_registry.py     # Source health monitoring
│   │   └── sources/            # Data source wrappers (one per DB)
│   │       ├── capture_source.py
│   │       ├── insurance_source.py
│   │       ├── registration_source.py
│   │       ├── theft_source.py
│   │       └── ministry_source.py
│   └── requirements.txt        # Python dependencies
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx          # Stats overview
│   │   │   ├── ScanVehicle.tsx        # Image upload + ANPR page
│   │   │   ├── SqlQueryPage.tsx       # SQL query editor page (NEW)
│   │   │   ├── SearchVehicle.tsx      # Search by plate
│   │   │   ├── DataSources.tsx        # 5 DB schema viewer
│   │   │   ├── IntegrationView.tsx    # GAV mapping + schema matching
│   │   │   └── MinistryReports.tsx    # Report uninsured vehicles
│   │   ├── components/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── UnifiedVehicleView.tsx # Global vehicle info card
│   │   │   └── StatusBadge.tsx
│   │   └── api.ts              # API client (auto-reads LAN IP from .env)
│   └── package.json
├── data/                       # SQLite database files (created by seed script)
│   ├── capture.db              # Traffic camera captures
│   ├── insurance.db            # Insurance records
│   ├── registration.db         # RTO registration records
│   ├── theft.db                # Police theft/security records
│   └── ministry.db             # Ministry of Transportation reports
├── scripts/
│   └── seed_databases.py       # Populate all 5 DBs with demo data
├── start_server.bat            # One-click Windows launcher (detects LAN IP)
├── .gitignore
└── README.md
```

---

## ⚙️ Prerequisites

Make sure the following are installed on the **server laptop**:

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.10 or higher | https://python.org/downloads |
| **Node.js** | 18 or higher | https://nodejs.org |
| **Git** | any | https://git-scm.com |

> Friends who only **view** the app need **nothing installed** — just a browser.

---

## 🚀 Setup & Run (Step by Step)

### Step 1 — Clone the repository

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

---

### Step 2 — Backend Setup (Python / FastAPI)

```bash
# Navigate to the backend folder
cd backend

# (Recommended) Create a virtual environment
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
```

> ⚠️ `easyocr` and `ultralytics` are large packages (~1–2 GB). First install takes 5–10 minutes.

---

### Step 3 — Seed the Databases

```bash
# From the project root (iia_project/ folder)
cd ..
python scripts/seed_databases.py
```

This creates and populates all 5 SQLite databases in the `data/` folder with 10 demo vehicles.

**Demo vehicles seeded:**

| Plate | Status |
|-------|--------|
| UP32AB1234 | ✅ INSURED |
| UP32CD5678 | ⚠️ INSURANCE EXPIRED |
| MH02EF9012 | ❌ UNINSURED |
| DL01GH3456 | 🚨 STOLEN |
| KA03IJ7890 | 🗑️ SCRAPPED |
| HR26PQ7788 | ⚠️ SUSPICIOUS |

---

### Step 4 — Start the Backend Server

```bash
# From the backend/ folder
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at: **http://localhost:8000**  
Interactive API docs at: **http://localhost:8000/docs**

---

### Step 5 — Frontend Setup (React / Vite)

Open a **new terminal window**:

```bash
# Navigate to the frontend folder
cd frontend

# Install Node.js dependencies
npm install

# Create the environment config file
# Windows PowerShell:
echo "VITE_API_BASE=http://localhost:8000" > .env
# Or just create frontend/.env manually with:
#   VITE_API_BASE=http://localhost:8000

# Start the frontend dev server
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

### ✅ Quick Summary (all commands together)

```bash
# 1. Clone
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# 2. Backend install
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 3. Seed databases
cd ..
python scripts/seed_databases.py

# 4. Start backend (keep this terminal open)
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Frontend (new terminal)
cd frontend
npm install
echo "VITE_API_BASE=http://localhost:8000" > .env
npm run dev
```

---

## 🌐 Sharing with Friends on the Same WiFi (LAN Demo)

You can share the running app with teammates on the **same WiFi network** — no installation needed on their devices.

### Option A — One-click (Windows)
Double-click **`start_server.bat`** — it auto-detects your IP, installs dependencies, seeds DBs, and starts both servers. It prints the shareable URL.

### Option B — Manual

**1. Find your LAN IP:**
```powershell
# Windows
ipconfig | findstr "IPv4"
# Example output: 192.168.1.105
```

**2. Update frontend `.env`:**
```
VITE_API_BASE=http://192.168.1.105:8000
```

**3. Start frontend with network binding:**
```bash
npm run dev -- --host 0.0.0.0
```

**4. Tell friends to open:**
```
http://192.168.1.105:5173
```

> **Firewall fix** (run once as Administrator if friends can't connect):
> ```powershell
> netsh advfirewall firewall add rule name="IIA Backend" dir=in action=allow protocol=TCP localport=8000
> netsh advfirewall firewall add rule name="IIA Frontend" dir=in action=allow protocol=TCP localport=5173
> ```

---

## 📄 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicle/{plate}` | Full integrated vehicle view (all 5 DBs) |
| POST | `/api/vehicle/scan` | Upload image → ANPR → plate extraction |
| POST | `/api/sql-query` | Run SELECT query on any/all databases |
| GET | `/api/sql-query/tables` | Get schema of all 5 databases |
| GET | `/api/data-sources` | Schema info from all 5 sources |
| GET | `/api/integration/schema` | GAV mapping + schema matching results |
| GET | `/api/statistics` | Dashboard statistics |
| POST | `/api/reports/` | Create Ministry of Transportation report |
| GET | `/api/health` | Health check |

Full interactive docs: **http://localhost:8000/docs**

---

## 🗄️ Database Schema (IIA Concept)

The key IIA concept: **5 databases designed independently** — same vehicle, different column names:

| Database | Table | Registration Key Column | Organization |
|----------|-------|------------------------|-------------|
| `capture.db` | `vehicle_capture` | **`plate_number`** | Traffic Surveillance |
| `insurance.db` | `insurance_records` | **`registration_id`** | National Insurance Registry |
| `registration.db` | `vehicle_registration` | **`vehicle_reg_no`** | Regional Transport Office |
| `theft.db` | `vehicle_security_records` | **`vehicle_identifier`** | Police Crime Records Bureau |
| `ministry.db` | `transport_reports` | **`vehicle_ref`** | Ministry of Transportation |

The **Mediator** maps all 5 to a single global attribute: `registration_number`

---

## 💻 SQL Query Examples

Use the **SQL Query** page (`/query`) or the API directly:

```sql
-- All captured vehicles (Capture DB)
SELECT plate_number, detected_vehicle_type, detected_color, capture_location
FROM vehicle_capture LIMIT 20

-- Active insurance policies (Insurance DB)
SELECT registration_id, insurer_name, policy_expiry_date, insurance_status
FROM insurance_records WHERE insurance_status = 'ACTIVE'

-- Registered vehicles (Registration DB)
SELECT vehicle_reg_no, owner_name, manufacturer, model_name, registration_status
FROM vehicle_registration

-- Stolen vehicles (Theft DB)
SELECT vehicle_identifier, case_type, reported_date, police_reference
FROM vehicle_security_records WHERE case_type = 'STOLEN'

-- Ministry reports (Ministry DB)
SELECT vehicle_ref, report_type, reason, severity, report_status
FROM transport_reports ORDER BY report_date DESC
```

---

## 🏛️ Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │            React Frontend (Vite)             │
                    │  /scan (Image+ANPR)  |  /query (SQL Editor) │
                    └──────────────────┬──────────────────────────┘
                                       │ HTTP / REST
                    ┌──────────────────▼──────────────────────────┐
                    │           FastAPI Backend (Python)           │
                    │                                              │
                    │   ┌──────────────────────────────────────┐  │
                    │   │      ANPR Pipeline                   │  │
                    │   │  YOLOv8 → Plate Region → EasyOCR     │  │
                    │   └──────────────┬───────────────────────┘  │
                    │                  │ plate number              │
                    │   ┌──────────────▼───────────────────────┐  │
                    │   │      Mediator (GAV Integration)      │  │
                    │   │  plate_number = registration_number  │  │
                    │   └──┬──────┬──────┬──────┬─────────┬───┘  │
                    └──────┼──────┼──────┼──────┼─────────┼──────┘
                           │      │      │      │         │
                    ┌──────▼─┐ ┌──▼───┐ ┌▼─────┐ ┌──────▼─┐ ┌──▼──────┐
                    │capture │ │insur-│ │regis-│ │ theft  │ │ministry │
                    │  .db   │ │ance  │ │trat. │ │  .db   │ │  .db    │
                    │plate_  │ │.db   │ │.db   │ │vehicle_│ │vehicle_ │
                    │number  │ │reg_id│ │reg_no│ │identif.│ │  ref    │
                    └────────┘ └──────┘ └──────┘ └────────┘ └─────────┘
```

---

## 👥 Team

IIIT Delhi — M.Tech 3rd Semester — IIA (Information Integration and Applications) Project

---

## 📝 License

Academic project — IIIT Delhi 2026
