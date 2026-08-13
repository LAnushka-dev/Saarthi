from __future__ import annotations

import os
from typing import Any

import httpx

from .config import get_settings
from .schemas import RouteResponse


def _build_fallback_explanation(resp: RouteResponse, blockage_status: str) -> str:
    # Deterministic, non-hallucinating template.
    segs = resp.segments
    route_hint = []
    for s in segs[:5]:
        route_hint.append(f"{s.label} ({s.from_city}→{s.to_city})")
    route_hint_txt = ", ".join(route_hint)
    cargo_notes = resp.cargo_notes[:2]
    cargo_notes_txt = " ".join(cargo_notes) if cargo_notes else ""

    return (
        f"Best route from {resp.origin} to {resp.destination} for {resp.cargo_type}: "
        f"{resp.path_cities[0]}→{resp.path_cities[-1]} via {route_hint_txt}. "
        f"Total time: {resp.totals['time_hours']:.1f} hrs, toll/fare: ₹{resp.totals['cost_inr']:.0f}, "
        f"total distance: {resp.totals['distance_km']:.0f} km. "
        f"Currently: {blockage_status}. {cargo_notes_txt}".strip()
    )


def _anthropic_messages(prompt: str, api_key: str, model: str) -> str:
    # Minimal Claude API call (no SDK dependency).
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": 220,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    with httpx.Client(timeout=20.0) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    # Expected shape: { content: [ { text: "..."} ] }
    content = data.get("content") or []
    if not content:
        return ""
    first = content[0]
    return (first.get("text") or "").strip()


def generate_explanation(resp: RouteResponse, alerts: list[dict[str, str]]) -> str:
    settings = get_settings()
    blockage_status = "currently no highway blockages"
    if alerts:
        blockage_status = "there are active route advisories on selected corridors"

    fallback = _build_fallback_explanation(resp, blockage_status=blockage_status)
    if not settings.anthropic_api_key:
        return fallback

    # Provide only computed facts: segments + totals + cargo notes.
    segment_lines = []
    for s in resp.segments:
        segment_lines.append(
            f"- {s.edge_type.upper()} {s.label}: {s.from_city}→{s.to_city}, {s.time_hours:.1f}h, ₹{s.cost_inr:.0f}"
        )

    alert_lines = []
    for a in alerts:
        alert_lines.append(f"- {a['highway']} ({a['severity']}): {a['message']}")

    cargo_notes_lines = resp.cargo_notes[:6]

    prompt = (
        "You are a logistics assistant for Indian road + rail route planning.\n"
        "Write a short, natural language briefing (2-4 sentences max) using ONLY the facts provided.\n"
        "Do not invent highway names, blockages, or train numbers.\n\n"
        f"Route request:\n- Origin: {resp.origin}\n- Destination: {resp.destination}\n"
        f"- Cargo: {resp.cargo_type}\n- Mode: {resp.mode}\n- Optimize by: {resp.optimize_by}\n\n"
        f"Computed route segments:\n" + "\n".join(segment_lines) + "\n\n"
        f"Totals:\n- Time: {resp.totals['time_hours']:.1f} hours\n"
        f"- Cost: ₹{resp.totals['cost_inr']:.0f}\n- Distance: {resp.totals['distance_km']:.0f} km\n\n"
        f"Route alerts:\n" + ("\n".join(alert_lines) if alert_lines else "- none") + "\n\n"
        f"Cargo intelligence notes:\n" + "\n".join([f"- {n}" for n in cargo_notes_lines]) + "\n\n"
        "Response format example:\n"
        "\"Best route from Nashik to Pune for onions: NH60 via Ghoti, 3.5 hrs, toll cost ₹280, currently no highway blockages.\"\n"
    )

    try:
        return _anthropic_messages(prompt, api_key=settings.anthropic_api_key, model=settings.anthropic_model) or fallback
    except Exception:
        if settings.allow_llm_fallback:
            return fallback
        raise

