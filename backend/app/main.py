import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.session import Base, engine, SessionLocal
from app.database.seeder import seed_database
from app.api import api_router
from app.websocket.connection_manager import manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sanjivani_backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and auto-seed initial demo dataset
    logger.info("Initializing Sanjivani Disaster Database schema...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        logger.error(f"Error while running initial database seed: {e}")
    finally:
        db.close()
    
    logger.info("Sanjivani Command Center Backend successfully started.")
    yield
    logger.info("Sanjivani Command Center Backend shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic Disaster Relief & Emergency Resource Coordinator Backend API",
    version="1.0.0-phase1",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Include REST API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static directory for uploaded evidence photographs
static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
(static_dir / "uploads").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Realtime WebSocket Endpoint
@app.websocket("/ws/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """
    Live WebSocket channel for streaming dashboard updates:
    ZONE_UPDATED, REPORT_RECEIVED, RESOURCE_UPDATED, ALLOCATION_UPDATED,
    ALERT_CREATED, ETA_UPDATED, SIMULATION_EVENT, AUDIT_LOG_CREATED
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open and receive client heartbeats/pings
            data = await websocket.receive_text()
            # Client can send ping
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        manager.disconnect(websocket)

@app.get("/")
def root():
    return {
        "system": "Sanjivani - Agentic Disaster Relief & Emergency Resource Coordinator",
        "status": "ONLINE",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
        "websocket": "/ws/dashboard",
    }
