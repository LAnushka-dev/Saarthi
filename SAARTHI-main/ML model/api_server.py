"""
FastAPI Inference Server for Saarthi ML Models
================================================
Endpoints:
  POST /api/crop-query          → Model 1: Crop-State Knowledge Engine
  POST /api/forecast            → Model 2: Production Forecasting
  POST /api/zone-balance        → Model 3: Surplus/Deficit by zone
  GET  /api/alerts              → Model 3: Active zone alerts (all zones)
  GET  /api/available-crops     → Model 1: What's harvestable this month
  GET  /api/state-crops/{state} → Model 1: Best crops for a state

Run with:
  uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

Call from Next.js:
  const res = await fetch("http://localhost:8000/api/crop-query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: "Best basmati source in October?" })
  })
"""

from __future__ import annotations
import datetime
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn")
    HAS_FASTAPI = False

from model1_crop_knowledge import CropKnowledgeEngine
from model2_production_forecast import ProductionForecaster
from model3_surplus_deficit import SurplusDeficitModel, ZONES

# ---------------------------------------------------------------------------
# Startup: initialise models once
# ---------------------------------------------------------------------------

knowledge_engine = CropKnowledgeEngine(use_embeddings=False)
forecaster = ProductionForecaster(epochs=150).fit_all()
surplus_model = SurplusDeficitModel()

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

if HAS_FASTAPI:
    class CropQueryRequest(BaseModel):
        question: str
        current_month: Optional[int] = None    # 1-12
        top_k: int = 5

    class ForecastRequest(BaseModel):
        crop: str
        state: str
        target_year: Optional[int] = None
        rainfall_mm: Optional[float] = None
        temp_anomaly: Optional[float] = None

    class ZoneBalanceRequest(BaseModel):
        zone_id: int
        crop_productions: dict[str, float]    # {"wheat": 18400, "rice": 4800}

    class AllZonesRequest(BaseModel):
        production_map: dict[int, dict[str, float]]   # {zone_id: {crop: mt}}

    # ------------------------------------------------------------------
    app = FastAPI(
        title="Saarthi ML API",
        description="AI layer for India's agricultural marketplace",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://saarthi.vercel.app"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @app.get("/health")
    def health():
        return {"status": "ok", "models_loaded": ["crop_knowledge", "production_forecaster", "surplus_deficit"]}

    # ------------------------------------------------------------------
    # Model 1: Crop-State Knowledge Engine
    # ------------------------------------------------------------------

    @app.post("/api/crop-query")
    def crop_query(req: CropQueryRequest):
        """
        Answer natural-language queries about crop-state relationships.

        Example:
          { "question": "Which state has Grade A basmati right now?", "current_month": 10 }
        """
        month = req.current_month or datetime.datetime.now().month
        result = knowledge_engine.query(req.question, current_month=month, top_k=req.top_k)
        return result.to_dict()

    @app.get("/api/available-crops")
    def available_crops(month: Optional[int] = None):
        """
        Return all crops currently in peak harvest season.
        Defaults to current calendar month.
        """
        m = month or datetime.datetime.now().month
        crops = knowledge_engine.available_crops_now(m)
        return {
            "month": m,
            "crops": [c.to_dict() for c in crops],
            "count": len(crops),
        }

    @app.get("/api/state-crops/{state}")
    def state_crops(state: str):
        """Return all Grade-A crops known for a given state."""
        crops = knowledge_engine.best_crops_for_state(state)
        if not crops:
            raise HTTPException(status_code=404, detail=f"No Grade-A crops found for state: {state}")
        return {
            "state": state,
            "grade_a_crops": [c.to_dict() for c in crops],
            "count": len(crops),
        }

    # ------------------------------------------------------------------
    # Model 2: Production Forecasting
    # ------------------------------------------------------------------

    @app.post("/api/forecast")
    def forecast(req: ForecastRequest):
        """
        Forecast crop production for next season.

        Example:
          { "crop": "wheat", "state": "Punjab", "target_year": 2025, "rainfall_mm": 620 }
        """
        year = req.target_year or (datetime.datetime.now().year + 1)
        result = forecaster.predict(
            crop=req.crop,
            state=req.state,
            target_year=year,
            rainfall_mm=req.rainfall_mm,
            temp_anomaly=req.temp_anomaly,
        )
        return result.to_dict()

    # ------------------------------------------------------------------
    # Model 3: Surplus / Deficit
    # ------------------------------------------------------------------

    @app.post("/api/zone-balance")
    def zone_balance(req: ZoneBalanceRequest):
        """
        Compute surplus/deficit for a single zone given production inputs.

        Example:
          { "zone_id": 6, "crop_productions": { "wheat": 18400, "basmati rice": 4800 } }
        """
        if req.zone_id not in ZONES:
            raise HTTPException(status_code=404, detail=f"Zone {req.zone_id} not found. Valid: 1-15")
        summary = surplus_model.compute_zone_balance(req.zone_id, req.crop_productions)
        return summary.to_dict()

    @app.post("/api/zone-balance/all")
    def all_zone_balances(req: AllZonesRequest):
        """Compute balance for multiple zones in one call."""
        # Convert string keys back to int (JSON serialises dict keys as strings)
        int_map = {int(k): v for k, v in req.production_map.items()}
        summaries = surplus_model.compute_all_zones(int_map)
        return {
            "zones": [s.to_dict() for s in summaries],
            "total_zones": len(summaries),
        }

    @app.get("/api/alerts")
    def get_alerts(production_map: Optional[str] = None):
        """
        Return active CRITICAL/WARNING zone alerts.

        Pass production_map as a URL-safe JSON string, or use the POST version.
        If omitted, returns a demo alert using sample data.
        """
        import json as _json

        if production_map:
            try:
                pm = {int(k): v for k, v in _json.loads(production_map).items()}
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid production_map JSON")
        else:
            # Demo data
            pm = {
                6: {"wheat": 18400, "basmati rice": 4800},
                3: {"rice": 14200, "potato": 7800},
                9: {"onion": 4200, "tomato": 1800, "sugarcane": 98000},
            }

        summaries = surplus_model.compute_all_zones(pm)
        alerts = surplus_model.get_alerts(summaries)
        return {"alerts": alerts, "alert_count": len(alerts)}

    # ------------------------------------------------------------------
    # Combined pipeline: Forecast → Zone Balance (convenience endpoint)
    # ------------------------------------------------------------------

    @app.post("/api/pipeline/forecast-and-balance")
    def forecast_and_balance(zone_id: int, crops: list[str]):
        """
        Run Model 2 → Model 3 pipeline for a zone in one call.
        Forecasts production for each crop then computes the zone balance.
        """
        if zone_id not in ZONES:
            raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")

        zone = ZONES[zone_id]
        production_map: dict[str, float] = {}
        forecasts_out = []

        for crop in crops:
            state = zone.states[0] if zone.states else "India"
            year = datetime.datetime.now().year + 1
            fc = forecaster.predict(crop, state, year)
            if fc.predicted_production_mt > 0:
                production_map[crop] = fc.predicted_production_mt
            forecasts_out.append(fc.to_dict())

        balance = surplus_model.compute_zone_balance(zone_id, production_map)
        return {
            "zone_id": zone_id,
            "forecasts": forecasts_out,
            "balance": balance.to_dict(),
        }

    if __name__ == "__main__":
        import uvicorn
        uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)

else:
    print("Install FastAPI to run the server: pip install fastapi uvicorn")
