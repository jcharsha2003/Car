# 🚗 IIA Project — Identification of Uninsured Vehicles
### Information Integration System | IIIT Delhi — M.Tech 3rd Semester

---

## 📋 Project Overview

A full-stack **Information Integration** system that identifies uninsured vehicles on the road by federating **5 independently designed databases** using a **Mediation / Global-As-View (GAV)** architecture. 

This project simulates a **real-world heterogeneous distributed database system**. The 5 databases are hosted across **3 different laptops**, connected over the internet via `ngrok` tunnels.

### Key Features
- 🌐 **True Distributed Architecture** — Master laptop hosts 1 database, Laptop B hosts 2, Laptop C hosts 2. They communicate over the internet (works across different WiFi networks/SIM data).
- 🔍 **ANPR Pipeline** — Upload a vehicle image → YOLOv8 detects vehicle → EasyOCR extracts **license plate only** → queries all 5 remote databases simultaneously.
- 🗄️ **Database Autonomy & Heterogeneity** — Each database was designed in isolation with different column names for the vehicle registration number.
- 🔗 **Federated Integration** — Mediator maps `plate_number` / `registration_id` / `vehicle_reg_no` / `vehicle_identifier` / `vehicle_ref` to a single global key.
- 💻 **SQL Query Page with Federated Writes** — Run SELECT queries across all 5 databases. Run INSERT/UPDATE queries that are automatically forwarded to the correct owning laptop over HTTP.

---

## 🏗️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend & Node Servers** | Python + FastAPI |
| **Frontend** | React + TypeScript + Vite |
| **Databases** | SQLite (5 independent files) |
| **Networking** | ngrok (HTTPS tunnels) |
| **ANPR — Vehicle Detection** | YOLOv8n (Ultralytics) |
| **ANPR — OCR** | EasyOCR |
| **ORM / Integration** | SQLAlchemy + RapidFuzz |

---

## 🚀 Setup & Run (Cross-Network Demo Guide)

This guide shows how to run the project across **3 laptops**, even if they are on different WiFi networks (e.g., mobile hotspots).

### Step 1 — Get the Code (All Laptops)
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### Step 2 — Install ngrok (All Laptops)
This project uses **ngrok** to expose local servers to the internet securely and for free.
1. Create a free account at [ngrok.com](https://ngrok.com)
2. Download and install ngrok for Windows
3. Run: `ngrok config add-authtoken YOUR_TOKEN_HERE`

---

### Step 3 — Start Laptop B (Insurance & Registration DBs)
On Laptop B, open the terminal inside the cloned repo:
```cmd
cd node_backend
start_node_B.bat
```
The script will install dependencies, start the node server on port `8001`, and start an ngrok tunnel.
**Important:** Copy the ngrok URL it prints (e.g., `https://abc1234.ngrok-free.app`) and send it to the Master Laptop.

---

### Step 4 — Start Laptop C (Theft & Ministry DBs)
On Laptop C, open the terminal inside the cloned repo:
```cmd
cd node_backend
start_node_C.bat
```
The script will install dependencies, start the node server on port `8002`, and start an ngrok tunnel.
**Important:** Copy the ngrok URL it prints (e.g., `https://xyz9876.ngrok-free.app`) and send it to the Master Laptop.

---

### Step 5 — Start Master Laptop (Capture DB + Frontend)
On your main laptop, double-click **`start_server.bat`** in the project root.

It will prompt you:
```
Enter Laptop B ngrok URL: https://abc1234.ngrok-free.app
Enter Laptop C ngrok URL: https://xyz9876.ngrok-free.app
```

Paste the URLs provided by Laptop B and C. The script will then:
1. Seed the local capture database with demo data.
2. Install Python and Node.js dependencies.
3. Start the FastAPI backend on port `8000`.
4. Start the React frontend on port `5173`.

**To share the UI with the professor over the internet:**
Open a new terminal on the Master Laptop and run:
```cmd
ngrok http 5173
```
Give that URL to the professor! They can now access the full system from their own device.

---

## 🗄️ Database Schema & Ownership (IIA Concept)

The key IIA concept: **5 databases designed independently** and hosted on different machines.

| Database | Hosted On | Registration Key Column | Organization |
|----------|-----------|------------------------|-------------|
| `capture.db` | **Master Laptop** | `plate_number` | Traffic Surveillance |
| `insurance.db` | **Laptop B** | `registration_id` | National Insurance Registry |
| `registration.db` | **Laptop B** | `vehicle_reg_no` | Regional Transport Office |
| `theft.db` | **Laptop C** | `vehicle_identifier` | Police Crime Records Bureau |
| `ministry.db` | **Laptop C** | `vehicle_ref` | Ministry of Transportation |

The **Mediator** (running on the Master) maps all 5 to a single global attribute: `registration_number` and handles all HTTP communication with Laptop B and C behind the scenes.

---

## 💻 What to Show in a Demo

1. **Upload Car Image (Federated Read):** The master extracts the plate, queries its local DB, makes HTTP requests to Laptop B and C via ngrok, and merges the results into a single view.
2. **SQL Write (Database Isolation):** Open the SQL Query page, switch to WRITE mode. Try to insert a record into `insurance.db`. The UI will indicate that this DB is owned by Laptop B. When you run the query, the Master automatically forwards the INSERT command to Laptop B over the internet!
3. **Cross-DB SQL Queries (Heterogeneity):** Run a SELECT query across "ALL" databases. You will see that the column names are completely different (e.g., `plate_number` vs `registration_id`), proving that the databases were designed independently.

---

## 👥 Team
IIIT Delhi — M.Tech 3rd Semester — IIA (Information Integration and Applications) Project

## 📝 License
Academic project — IIIT Delhi 2026
