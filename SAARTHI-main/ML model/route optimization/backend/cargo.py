from __future__ import annotations

def _split_cargo(cargo_type: str) -> tuple[str, str | None]:
    """
    Frontend sends cargo as: "Category|Item" (e.g. "Perishable Goods|Fruits, vegetables").
    Keep it tolerant: if no '|', treat entire string as category.
    """
    raw = (cargo_type or "").strip()
    if "|" not in raw:
        return raw, None
    category, item = raw.split("|", 1)
    return category.strip(), item.strip() or None


def get_cargo_notes(cargo_type: str, total_time_hours: float) -> list[str]:
    category, item = _split_cargo(cargo_type)
    cat = category.lower()

    notes: list[str] = []
    perish_limit: float | None = None

    if "perishable" in cat:
        perish_limit = 12
        notes += [
            "Perishable cargo: prioritize `time` optimization and minimize handoffs/halts.",
            "Use insulated/ventilated packaging as appropriate and avoid long idle periods on alert corridors.",
        ]
    elif "non-perishable" in cat:
        perish_limit = 36
        notes += [
            "Non-perishable cargo: `cost` optimization is usually acceptable unless alerts are severe.",
            "Plan buffers around congestion advisories to protect delivery slots.",
        ]
    elif "fragile" in cat:
        perish_limit = 30
        notes += [
            "Fragile goods: avoid rough/ghat-heavy segments if possible; add careful loading/unloading time.",
            "Prefer fewer transfers; consistent handling reduces breakage risk.",
        ]
    elif "hazardous" in cat or "hazmat" in cat:
        perish_limit = 24
        notes += [
            "Hazmat: ensure permits, compliant packaging, and approved routes (no shortcuts through restricted areas).",
            "Maintain safety buffers; avoid densely congested pockets when possible.",
        ]
    elif cat == "livestock":
        perish_limit = 18
        notes += [
            "Livestock: schedule regular rest/water breaks and avoid heat-stress windows.",
            "Minimize stop-go congestion exposure; stable timelines reduce animal stress.",
        ]
    elif "heavy" in cat or "bulk" in cat:
        perish_limit = 40
        notes += [
            "Heavy/bulk cargo: verify axle-load limits, ghat gradients, and bridge restrictions on the selected corridor.",
            "Prefer highways with predictable toll plazas and wide shoulders for safety.",
        ]
    elif "high-value" in cat or "high value" in cat:
        perish_limit = 24
        notes += [
            "High-value cargo: prefer reliable routes with secure stops and minimal deviations.",
            "Avoid extended nighttime halts; plan secure parking and tracking.",
        ]
    elif "general cargo" in cat or cat == "general":
        perish_limit = 30
        notes += ["General cargo: choose the most reliable route and keep transfer buffers for handoffs."]
    elif "oversized" in cat:
        perish_limit = 48
        notes += [
            "Oversized cargo: verify permits, escort requirements, and turning/clearance constraints.",
            "Avoid dense city cores; plan for daylight movement where mandated.",
        ]
    elif "liquid" in cat:
        perish_limit = 24
        notes += [
            "Liquid cargo: check tank integrity, slosh control, and temperature constraints (especially milk).",
            "Avoid aggressive driving segments; smoother corridors reduce surge risk.",
        ]
    else:
        perish_limit = 30
        notes += ["Choose the most reliable route available and keep transfer buffers for handoffs."]

    if item:
        notes.insert(0, f"Cargo selected: {category} - {item}.")

    if perish_limit is not None and total_time_hours > perish_limit:
        notes.append(f"Route duration ({total_time_hours:.1f}h) exceeds the typical {perish_limit:.0f}h planning window for this cargo category.")

    return notes

