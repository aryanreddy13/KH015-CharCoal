# Sanjivani - Agentic Disaster Relief & Emergency Resource Coordinator

**Sanjivani** is an intelligent, multi-agency disaster operations management and resource coordination platform. It integrates autonomous agent pipelines, geospatial risk assessment, realtime telemetry dispatching, and a mobile-first citizen incident reporting portal.

---

## 🌟 Key Features (Phase 1 Implemented)

1. **Authority Command Center (`/dashboard`)**:
   - High-density dark-mode emergency operations center interface.
   - Interactive GIS Leaflet map featuring all 5 operational disaster sectors with severity-coded pulsating markers.
   - Real-time KPI telemetry: Active Sectors, Critical Zones, Available Units, Active Convoys, Total Casualties.
   - Real-time Zone Inspector with individual resource requirement manifests and en-route convoys.
   - Live Emergency Alerts stream and System Audit Trail.
2. **Citizen Reporter Interface (`/report`)**:
   - Mobile-first, streamlined incident submission form.
   - One-touch GPS location acquisition.
   - Trapped/injured counts, resource checklist, and instant "PENDING REVIEW" submission status.
3. **Simulation Test Harness**:
   - `START SIMULATION`: Mobilizes available units and begins agentic loops.
   - `INJECT EMERGENCY`: Simulates sudden flash flood surges and victim increases in Zone A.
   - `SIMULATE ROAD BLOCK`: Simulates arterial highway debris blockages and calculates ETA delays.
4. **Realtime WebSocket Protocol (`/ws/dashboard`)**:
   - Instant live updates across browser tabs without page reloads.
5. **Multi-Database & Zero-Config Resilience**:
   - Works with PostgreSQL or automatically falls back to local SQLite if PostgreSQL is not active.

---

## 🏗️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic v2, WebSockets, Uvicorn
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, React Router v6, Lucide Icons, Leaflet / React-Leaflet, Recharts
- **Database**: PostgreSQL (or SQLite fallback `disaster.db`)

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

---

### Step 1: Start the Backend Server

1. Open a terminal in the `backend/` directory:
```bash
cd backend
```

2. (Optional) Create and activate a Python virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables (defaults to SQLite fallback automatically):
```bash
cp .env.example .env
```

5. Launch the backend API and WebSocket hub:
```bash
python run.py
```
*The backend will automatically create tables and seed initial demo data.*
*Backend API URL: `http://localhost:8000`*
*Interactive API Docs: `http://localhost:8000/docs`*

---

### Step 2: Start the Frontend Application

1. Open a new terminal in the `frontend/` directory:
```bash
cd frontend
```

2. Install npm packages:
```bash
npm install
```

3. Launch the Vite dev server:
```bash
npm run dev
```
*Frontend URL: `http://localhost:5173`*

---

## 📱 Application URLs

| Interface | URL | Description |
|---|---|---|
| **Authority Command Center** | `http://localhost:5173/dashboard` | Main operations dashboard for emergency commanders |
| **Operational Zones** | `http://localhost:5173/zones` | Geospatial sector viewer and zone inspector |
| **Resource Inventory** | `http://localhost:5173/resources` | Agency asset catalog with capacity details |
| **Active Allocations** | `http://localhost:5173/allocations` | Convoy routing, distance, and ETAs |
| **Citizen Reports** | `http://localhost:5173/reports` | Feed of submitted field incidents |
| **Alerts Broadcast** | `http://localhost:5173/alerts` | Active priority alerts and warning issuer |
| **Audit Trail** | `http://localhost:5173/audit` | Immutable system event log |
| **Citizen Reporter App** | `http://localhost:5173/report` | Mobile-first citizen hazard submission portal |
| **API Documentation** | `http://localhost:8000/docs` | Swagger / OpenAPI REST documentation |

---

## 🏛️ Initial Demo Zones Data

- **Zone A (Riverfront & Metro)**: Flood | Severity 9.6 | 350 Affected | Critical | Needs: Rescue (9.8), Medical (9.4), Food (7.1)
- **Zone B (Foothills & Industrial)**: Earthquake | Severity 9.1 | 280 Affected | Critical | Needs: Medical (9.5), Shelter (9.0)
- **Zone C (Coastal Highway)**: Flood | Severity 7.4 | 150 Affected | High | Needs: Food (7.8), Water (7.2)
- **Zone D (Eastern Ridge)**: Cyclone | Severity 5.8 | 100 Affected | Moderate | Needs: Shelter (6.0), Medical (5.5)
- **Zone E (South Agricultural)**: Flood | Severity 3.2 | 50 Affected | Low | Needs: Food (3.5), Water (3.0)

---

## 🧩 Architectural Phasing Roadmap

- **Phase 1 (Complete)**: Foundational full-stack application, 12 database models, 5 seeded zones, REST & WebSocket layers, Command Center, Citizen Reporter, Simulation Engine.
- **Phase 2**: Needs Assessment Agent with structured LLM parsing & multi-variable Priority Scoring.
- **Phase 3**: Optimization Allocation Agent (Linear Programming) & Real-time ETA Routing Engine.
- **Phase 4**: Multi-Agency Conflict Resolution & Live Resource Movement Telemetry.
- **Phase 5**: Mobile Offline-First Local Storage, Camera EXIF GPS extraction, and Geofencing.
- **Phase 6**: Multimodal Dispatches (SMS, Voice IVR, Automated agency webhook bridges).
