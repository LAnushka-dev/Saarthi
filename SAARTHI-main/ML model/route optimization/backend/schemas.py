from typing import Literal

from pydantic import BaseModel, Field


OptimizeBy = Literal["time", "cost", "km"]
RouteMode = Literal["road", "rail", "road_rail"]


class RouteRequest(BaseModel):
    origin: str = Field(..., description="Origin city name")
    destination: str = Field(..., description="Destination city name")
    mode: RouteMode = Field(default="road_rail")
    optimize_by: OptimizeBy = Field(default="time", description="Optimization criterion")
    cargo_type: str = Field(default="onions", description="Cargo type (affects advisories)")
    use_ml: bool = Field(default=False, description="Use ML weight adjuster (if available)")
    month: int | None = Field(default=None, ge=1, le=12, description="Optional route month (1-12)")


class RouteSegment(BaseModel):
    from_city: str
    to_city: str
    edge_type: Literal["road", "rail"]
    label: str
    distance_km: float
    time_hours: float
    cost_inr: float
    edge_id: str


class RouteResponse(BaseModel):
    origin: str
    destination: str
    mode: RouteMode
    optimize_by: OptimizeBy
    cargo_type: str
    path_cities: list[str]
    segments: list[RouteSegment]
    totals: dict
    alerts: list[dict]
    cargo_notes: list[str]
    explanation: str
    used_ml: bool

