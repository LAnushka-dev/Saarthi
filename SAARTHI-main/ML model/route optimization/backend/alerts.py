from __future__ import annotations

from typing import Any


ALERT_RULES: list[dict[str, Any]] = [
    {
        "pattern": "NH3",
        "highway": "NH3 ghat advisory",
        "severity": "medium",
        "message": "NH3 ghat stretches may have slower gradients and intermittent traffic. Keep buffer time and avoid peak-hour departures.",
    },
    {
        "pattern": "NH27",
        "highway": "NH27 Kanpur congestion",
        "severity": "high",
        "message": "NH27 near Kanpur can see congestion and stop-go delays. Consider an off-peak run or a rail segment if available.",
    },
    {
        "pattern": "NH44 (toll work)",
        "highway": "NH44 toll-work delays",
        "severity": "medium",
        "message": "NH44 has active toll/work pockets that can add queueing time. Prefer lanes with faster throughput.",
    },
    {
        "pattern": "NH60",
        "highway": "NH60 Ghoti stretch",
        "severity": "low",
        "message": "NH60 (Ghoti stretch) may have localized lane/turn slowdowns. Drivers should watch for temporary diversions.",
    },
    {
        "pattern": "NH16",
        "highway": "NH16 coastal corridor",
        "severity": "medium",
        "message": "NH16 coastal corridor can be affected by works and sea-side traffic patterns. Keep an eye on live updates and weather.",
    },
]


def _get(seg: Any, key: str) -> Any:
    if isinstance(seg, dict):
        return seg.get(key)
    return getattr(seg, key, None)


def get_route_alerts(segments: list[Any]) -> list[dict[str, str]]:
    used = []
    # We match the segment label (highway/train name). This prevents inventing highways.
    for seg in segments:
        if _get(seg, "edge_type") != "road":
            continue
        for rule in ALERT_RULES:
            if rule["pattern"] in (_get(seg, "label") or ""):
                used.append(
                    {
                        "highway": rule["highway"],
                        "severity": rule["severity"],
                        "message": rule["message"],
                    }
                )
    # De-duplicate by highway name.
    deduped: list[dict[str, str]] = []
    seen = set()
    for item in used:
        key = item["highway"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped

