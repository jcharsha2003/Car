# IIA Distributed Node Backend

This folder contains the lightweight backend needed to run Laptop B and Laptop C as independent databases in the federated system.

## 🌐 Cross-Network Support (ngrok)
This system is designed to work even if Laptop B, Laptop C, and the Master laptop are all on **different WiFi networks** or **mobile hotspots**. We use `ngrok` to create secure public tunnels for the databases.

---

## How to Set Up Laptop B (Insurance & Registration)
1. **Prerequisites**: Install Python and download [ngrok](https://ngrok.com/download). Authenticate ngrok with your free token (`ngrok config add-authtoken YOUR_TOKEN`).
2. Copy this entire `node_backend` folder and the `data` folder to Laptop B.
3. Double-click `start_node_B.bat`.
   - It will install dependencies, start the server on port `8001`, and open an ngrok tunnel.
4. **Important**: The terminal will show an ngrok URL (e.g., `https://abc1234.ngrok-free.app`). 
5. Send that exact URL to the person running the Master Laptop.

---

## How to Set Up Laptop C (Theft & Ministry)
1. **Prerequisites**: Install Python and download [ngrok](https://ngrok.com/download). Authenticate ngrok with your free token.
2. Copy this entire `node_backend` folder and the `data` folder to Laptop C.
3. Double-click `start_node_C.bat`.
   - It will install dependencies, start the server on port `8002`, and open an ngrok tunnel.
4. **Important**: The terminal will show an ngrok URL (e.g., `https://xyz9876.ngrok-free.app`). 
5. Send that exact URL to the person running the Master Laptop.

---

## Interacting with the Node Database Locally
Each node has its own FastAPI docs available locally at `http://localhost:<port>/docs`.
The Master laptop connects to the node securely over the internet using the ngrok URL to perform federated SELECTs and remote writes.
