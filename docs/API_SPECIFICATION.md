# PS20 REST & WebSocket API Specification

## Base URL
- Local Backend: `http://localhost:8000/api`
- WebSocket: `ws://localhost:8000/ws/dashboard`

## Endpoints

### Health & Summary
- `GET /api/health` -> System health & database connection status
- `GET /api/summary` -> Dashboard KPIs (Active zones, Critical zones, Available resources, Allocations, Total affected)

### Zones
- `GET /api/zones` -> List all 5 disaster zones with nested resource needs
- `GET /api/zones/{id}` -> Full detail on single zone (Allocations, Reports, Alerts)

### Resources & Needs
- `GET /api/resources` -> Inventory of all agency assets (Rescue teams, Medical units, Food rations, Shelters)
- `GET /api/resources/{id}` -> Specific resource location and status
- `GET /api/needs` -> Granular resource requirements ranked by priority score
- `GET /api/allocations` -> Active resource dispatches, destinations, and ETAs

### Agencies
- `GET /api/agencies` -> Registered operational agencies

### Reports & Alerts
- `GET /api/reports` -> Citizen and operator disaster reports
- `POST /api/reports` -> Submit new citizen emergency report
- `GET /api/alerts` -> Active emergency alerts
- `POST /api/alerts` -> Issue command center alert

### Audit Trail
- `GET /api/audit-logs` -> Immutable timeline of all system actions

### Simulation Triggers
- `POST /api/simulation/start` -> Start agentic telemetry & resource mobilization
- `POST /api/simulation/emergency` -> Inject flash flood / sudden casualty surge
- `POST /api/simulation/road-block` -> Simulate corridor blockage and ETA delays

### WebSocket Protocol (`/ws/dashboard`)
Broadcasts typed JSON packets:
```json
{
  "event": "ZONE_UPDATED | REPORT_RECEIVED | RESOURCE_UPDATED | ALLOCATION_UPDATED | ALERT_CREATED | ETA_UPDATED | SIMULATION_EVENT | AUDIT_LOG_CREATED",
  "data": { ... },
  "timestamp": "2026-09-11T13:00:00Z"
}
```
