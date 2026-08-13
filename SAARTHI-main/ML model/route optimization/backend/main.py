from __future__ import annotations

import datetime as dt
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .alerts import get_route_alerts
from .cargo import get_cargo_notes
from .config import get_settings
from .graph_data import CITY_POSITIONS, get_all_edges, get_cities
from .llm import generate_explanation
from .ml_weight_adjuster import WeightAdjuster
from .router import dijkstra_route
from .schemas import RouteRequest, RouteResponse, RouteSegment, RouteMode


app = FastAPI(title="Route Optimization Model (Road + Rail + Claude)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

settings = get_settings()

_weight_adjuster: WeightAdjuster | None = None


def _get_weight_adjuster() -> WeightAdjuster | None:
    global _weight_adjuster
    if _weight_adjuster is not None:
        return _weight_adjuster
    # Keep ML optional: only instantiate lazily if used.
    artifact_path = os.path.join(os.path.dirname(__file__), "ml", "artifacts", "weight_adjuster.joblib")
    try:
        _weight_adjuster = WeightAdjuster(artifact_path=artifact_path)
        return _weight_adjuster
    except Exception:
        _weight_adjuster = None
        return None


def _format_mode(mode: str) -> RouteMode:
    if mode == "road":
        return "road"
    if mode == "rail":
        return "rail"
    return "road_rail"


@app.get("/api/graph")
def api_graph() -> dict[str, Any]:
    # Frontend uses city positions + edge list for SVG rendering.
    edges = []
    for e in get_all_edges():
        edges.append(
            {
                "edge_id": e.edge_id,
                "from_city": e.from_city,
                "to_city": e.to_city,
                "edge_type": e.edge_type,
                "label": e.name,
                "distance_km": e.distance_km,
                "time_hours": e.time_hours,
                "cost_inr": e.toll_or_fare_inr,
            }
        )
    return {"cities": get_cities(), "positions": CITY_POSITIONS, "edges": edges}


@app.post("/api/route")
def api_route(req: RouteRequest) -> RouteResponse:
    origin = req.origin.strip()
    destination = req.destination.strip()
    if origin == destination:
        raise HTTPException(status_code=400, detail="Origin and destination must be different.")

    all_edges = get_all_edges()
    mode: RouteMode = _format_mode(req.mode)
    optimize_by = req.optimize_by
    month = req.month if req.month is not None else dt.datetime.now().month

    # Keep original formatting for category matching (frontend sends "Category|Item").
    cargo_key = req.cargo_type.strip()

    used_ml = False
    adjusted_values_fn = None

    weight_adjuster = None
    if req.use_ml:
        weight_adjuster = _get_weight_adjuster()
        if weight_adjuster is not None:
            used_ml = True

            def _adjusted_values_fn(edge):
                return weight_adjuster.adjusted_values(cargo_type=cargo_key, month=month, edge=edge)

            adjusted_values_fn = _adjusted_values_fn

    # Objective weight: either base metric or ML adjusted metric.
    def _objective_for_router(edge):
        if weight_adjuster is None:
            # base objective
            if optimize_by == "time":
                return edge.time_hours
            if optimize_by == "cost":
                return edge.toll_or_fare_inr
            return edge.distance_km
        # ML: objective uses adjusted metric for time/cost, km unchanged.
        if optimize_by == "time":
            return weight_adjuster.adjusted_values(cargo_type=cargo_key, month=month, edge=edge).time_hours
        if optimize_by == "cost":
            return weight_adjuster.adjusted_values(cargo_type=cargo_key, month=month, edge=edge).cost_inr
        return edge.distance_km

    route = dijkstra_route(
        all_edges=all_edges,
        start_city=origin,
        goal_city=destination,
        mode=mode,
        optimize_by=optimize_by,
        weight_fn=_objective_for_router,
        adjusted_values_fn=adjusted_values_fn,
    )

    # Create typed segments for response + alerts/LLM.
    segments: list[RouteSegment] = []
    for s in route.segments:
        segments.append(RouteSegment(**s))

    # Compute rule-based alerts and cargo intelligence.
    # (alerts are derived from road edges only)
    alerts = get_route_alerts(segments=[s.dict() for s in segments])

    cargo_notes = get_cargo_notes(cargo_type=cargo_key, total_time_hours=route.total_time_hours)

    totals = {
        "distance_km": route.total_distance_km,
        "time_hours": route.total_time_hours,
        "cost_inr": route.total_cost_inr,
    }

    resp = RouteResponse(
        origin=origin,
        destination=destination,
        mode=mode,
        optimize_by=optimize_by,
        cargo_type=cargo_key,
        path_cities=route.path_nodes,
        segments=segments,
        totals=totals,
        alerts=alerts,
        cargo_notes=cargo_notes,
        explanation="",
        used_ml=used_ml,
    )

    resp.explanation = generate_explanation(resp=resp, alerts=alerts)
    return resp


# Mount frontend after API routes to avoid route conflicts.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


