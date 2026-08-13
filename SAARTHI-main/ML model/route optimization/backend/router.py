from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Callable

from .graph_data import Edge
from .schemas import OptimizeBy, RouteMode


@dataclass(frozen=True)
class RouteResult:
    path_nodes: list[str]
    edge_ids: list[str]
    segments: list[dict]
    total_distance_km: float
    total_time_hours: float
    total_cost_inr: float
    objective_weight: float


def _objective_weight(
    edge: Edge,
    optimize_by: OptimizeBy,
    weight_override: float | None = None,
) -> float:
    if weight_override is not None:
        return weight_override

    if optimize_by == "time":
        return edge.time_hours
    if optimize_by == "cost":
        return edge.toll_or_fare_inr
    return edge.distance_km


def dijkstra_route(
    all_edges: list[Edge],
    start_city: str,
    goal_city: str,
    mode: RouteMode,
    optimize_by: OptimizeBy,
    weight_fn: Callable[[Edge], float] | None = None,
    adjusted_values_fn: Callable[[Edge], dict] | None = None,
) -> RouteResult:
    if start_city == goal_city:
        return RouteResult(
            path_nodes=[start_city],
            edge_ids=[],
            segments=[],
            total_distance_km=0.0,
            total_time_hours=0.0,
            total_cost_inr=0.0,
            objective_weight=0.0,
        )

    allowed_edge_types: set[str]
    if mode == "road":
        allowed_edge_types = {"road"}
    elif mode == "rail":
        allowed_edge_types = {"rail"}
    else:
        allowed_edge_types = {"road", "rail"}

    adj: dict[str, list[Edge]] = {}
    for e in all_edges:
        if e.edge_type not in allowed_edge_types:
            continue
        adj.setdefault(e.from_city, []).append(e)
        adj.setdefault(e.to_city, []).append(e)

    if start_city not in adj or goal_city not in adj:
        raise ValueError("Unknown origin or destination (not in demo graph).")

    # Predecessor map stores (prev_node, edge_used, neighbor_endpoints)
    prev: dict[str, tuple[str, Edge]] = {}
    best: dict[str, float] = {start_city: 0.0}

    heap: list[tuple[float, str]] = [(0.0, start_city)]
    while heap:
        current_w, node = heapq.heappop(heap)
        if node == goal_city:
            break
        if current_w != best.get(node):
            continue

        for e in adj.get(node, []):
            neighbor = e.to_city if node == e.from_city else e.from_city
            if neighbor == node:
                continue

            objective_w = _objective_weight(e, optimize_by)
            if weight_fn is not None:
                objective_w = weight_fn(e)

            new_w = current_w + float(objective_w)
            if new_w < best.get(neighbor, float("inf")):
                best[neighbor] = new_w
                prev[neighbor] = (node, e)
                heapq.heappush(heap, (new_w, neighbor))

    if goal_city not in prev and goal_city != start_city:
        raise ValueError(f"No route found from {start_city} to {goal_city} using mode={mode}.")

    # Reconstruct nodes
    nodes_rev = [goal_city]
    edges_rev: list[Edge] = []
    cursor = goal_city
    while cursor != start_city:
        if cursor not in prev:
            raise ValueError("Route reconstruction failed.")
        pnode, edge_used = prev[cursor]
        nodes_rev.append(pnode)
        edges_rev.append(edge_used)
        cursor = pnode

    path_nodes = list(reversed(nodes_rev))
    edges_used = list(reversed(edges_rev))

    segments: list[dict] = []
    total_distance_km = 0.0
    total_time_hours = 0.0
    total_cost_inr = 0.0
    objective_weight = best.get(goal_city, 0.0)

    for i, e in enumerate(edges_used):
        frm = path_nodes[i]
        to = path_nodes[i + 1]
        adjusted = adjusted_values_fn(e) if adjusted_values_fn is not None else None
        if not adjusted:
            seg_distance = float(e.distance_km)
            seg_time = float(e.time_hours)
            seg_cost = float(e.toll_or_fare_inr)
        else:
            # `adjusted_values_fn` can return either a dict or an object with attributes.
            if isinstance(adjusted, dict):
                seg_distance = float(adjusted.get("distance_km", e.distance_km))
                seg_time = float(adjusted.get("time_hours", e.time_hours))
                seg_cost = float(adjusted.get("cost_inr", e.toll_or_fare_inr))
            else:
                seg_distance = float(getattr(adjusted, "distance_km", e.distance_km))
                seg_time = float(getattr(adjusted, "time_hours", e.time_hours))
                seg_cost = float(getattr(adjusted, "cost_inr", e.toll_or_fare_inr))

        # Keep labels stable but directional.
        segments.append(
            {
                "from_city": frm,
                "to_city": to,
                "edge_type": e.edge_type,
                "label": e.name,
                "distance_km": seg_distance,
                "time_hours": seg_time,
                "cost_inr": seg_cost,
                "edge_id": e.edge_id,
            }
        )
        total_distance_km += seg_distance
        total_time_hours += seg_time
        total_cost_inr += seg_cost

    return RouteResult(
        path_nodes=path_nodes,
        edge_ids=[s["edge_id"] for s in segments],
        segments=segments,
        total_distance_km=total_distance_km,
        total_time_hours=total_time_hours,
        total_cost_inr=total_cost_inr,
        objective_weight=float(objective_weight),
    )

