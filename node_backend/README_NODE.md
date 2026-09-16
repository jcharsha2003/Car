# IIA Distributed Node Backend

This folder contains the lightweight backend needed to run Laptop B and Laptop C as independent databases in the federated system.

## How to Set Up Laptop B (Insurance & Registration)
1. Copy this entire `node_backend` folder and the `data` folder to Laptop B.
2. Install Python.
3. Double-click `start_node_B.bat`.
   - It will install dependencies and start the server on port `8001`.
4. Note the IPv4 Address shown in the terminal.
5. On the Master Laptop, open `backend/app/config.py` (or `.env`) and update `NODE_B_URL` to point to Laptop B's IP.
   - Example: `NODE_B_URL = "http://192.168.1.15:8001"`

## How to Set Up Laptop C (Theft & Ministry)
1. Copy this entire `node_backend` folder and the `data` folder to Laptop C.
2. Install Python.
3. Double-click `start_node_C.bat`.
   - It will install dependencies and start the server on port `8002`.
4. Note the IPv4 Address shown in the terminal.
5. On the Master Laptop, open `backend/app/config.py` (or `.env`) and update `NODE_C_URL` to point to Laptop C's IP.
   - Example: `NODE_C_URL = "http://192.168.1.20:8002"`

## Interacting with the Node Database
Each node has its own FastAPI docs available at `http://localhost:<port>/docs`.
You can use the endpoints to inspect schemas, execute local SQL write queries, and perform federated SELECTs (called from the Master).
