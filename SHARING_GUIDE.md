# 🚗 IIA Project — Sharing Guide (LAN Demo)

## Overview

This app runs entirely on **one laptop** (the "server"). Your two friends just open a browser — **no installation needed on their devices**.

---

## Step 1 — Run on the Server Laptop (YOUR laptop)

Double-click **`start_server.bat`** inside the `iia_project` folder.

This script will:
1. ✅ Detect your WiFi IP automatically
2. ✅ Install Python + Node dependencies
3. ✅ Seed the databases (first run only)
4. ✅ Start the FastAPI backend (`0.0.0.0:8000`)
5. ✅ Start the Vite frontend (`0.0.0.0:5173`)
6. ✅ Print the URL your friends should open

**Make sure your laptop is connected to the same WiFi as your friends.**

---

## Step 2 — Friends Open the App

After the script runs, look for this output:

```
YOUR FRIENDS (on same WiFi):
  Open Chrome/Firefox and go to:
  http://192.168.x.x:5173
```

Send that URL to your friends via WhatsApp/message.

They just open Chrome → type the URL → done. ✅

---

## Step 3 — Live Data Sharing

- All 5 databases (`.db` files) live on **your laptop**
- When any of you inserts a record through the web app, **everyone sees it instantly**
- This is a true multi-user shared system on LAN

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Friends can't reach the URL | Make sure Windows Firewall allows port 5173 and 8000 (see below) |
| Backend not starting | Check the red window — likely a Python package error |
| "Scan failed" on image | Backend is starting up / EasyOCR loading. Wait 10 seconds and retry |
| LAN IP shows as localhost | You're not on WiFi — connect to WiFi and re-run `start_server.bat` |

### Allow ports through Windows Firewall (run once as admin)

Open PowerShell as Administrator and run:
```powershell
netsh advfirewall firewall add rule name="IIA Backend" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="IIA Frontend" dir=in action=allow protocol=TCP localport=5173
```

---

## Pages in the App

| Page | URL | What it does |
|------|-----|-------------|
| Dashboard | `/` | Stats overview |
| **Scan Vehicle** | `/scan` | Upload car image → ANPR extracts license plate → global view |
| Search Vehicle | `/search` | Search by plate or owner |
| **SQL Query** | `/query` | Type any SELECT query across the 5 databases |
| Data Sources | `/sources` | Shows all 5 DB schemas |
| Integration View | `/integration` | GAV schema mapping, instance matching |
| Ministry Reports | `/reports` | Report uninsured/stolen vehicles |

---

## Demo Vehicles (pre-seeded in the databases)

| Plate | Status | Description |
|-------|--------|-------------|
| UP32AB1234 | ✅ INSURED | Valid, insured |
| UP32CD5678 | ⚠️ EXPIRED | Insurance expired |
| MH02EF9012 | ❌ UNINSURED | No insurance record |
| DL01GH3456 | 🚨 STOLEN | Reported stolen |
| KA03IJ7890 | 🗑️ SCRAPPED | Vehicle scrapped |
| HR26PQ7788 | ⚠️ SUSPICIOUS | Suspicious |

---

## SQL Query Examples to Show Sir

```sql
-- 1. Global view: all captures with registration info
SELECT vc.plate_number, vr.owner_name, vr.manufacturer, vr.model_name
FROM vehicle_capture vc
JOIN ... -- Use the Query page for cross-DB queries per DB

-- 2. All active insurance policies
SELECT registration_id, insurer_name, policy_expiry_date
FROM insurance_records
WHERE insurance_status = 'ACTIVE'

-- 3. Stolen vehicles
SELECT vehicle_identifier, case_type, reported_date, police_reference
FROM vehicle_security_records
WHERE case_type = 'STOLEN'

-- 4. Ministry reports (uninsured)
SELECT vehicle_ref, report_type, reason, severity
FROM transport_reports
WHERE report_type = 'UNINSURED_VEHICLE'
```

---

## Architecture Summary (for explanation)

```
5 Independent SQLite Databases (designed in isolation)
     capture.db    →  plate_number
     insurance.db  →  registration_id       ← same car, different column names
     registration.db → vehicle_reg_no
     theft.db      →  vehicle_identifier
     ministry.db   →  vehicle_ref

         ↓ GAV Schema Mapping (Global-As-View)
         ↓ Mediator (Federated Architecture)
         ↓
     FastAPI Backend (Python)
         ↓
     React Frontend (Vite)
```

The key IIA concept: **same vehicle registration number stored under 5 different column names** in 5 independently designed databases — the mediator maps them all to a single global key `registration_number`.
