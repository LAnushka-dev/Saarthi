from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


EdgeType = Literal["road", "rail"]


@dataclass(frozen=True)
class Edge:
    edge_id: str
    from_city: str
    to_city: str
    edge_type: EdgeType
    name: str  # highway or train name
    distance_km: float
    time_hours: float
    toll_or_fare_inr: float  # toll for road, fare for rail


CITY_POSITIONS: dict[str, dict[str, float]] = {
    "Ahmedabad": {"x": 90, "y": 210},
    "Surat": {"x": 120, "y": 275},
    "Vadodara": {"x": 155, "y": 235},
    "Mumbai": {"x": 185, "y": 310},
    "Pune": {"x": 235, "y": 260},
    "Nashik": {"x": 230, "y": 180},
    "Goa": {"x": 285, "y": 330},
    "Hyderabad": {"x": 340, "y": 235},
    "Bengaluru": {"x": 430, "y": 320},
    "Chennai": {"x": 490, "y": 370},
    "Kolkata": {"x": 540, "y": 180},
    "Patna": {"x": 520, "y": 120},
    "Delhi": {"x": 330, "y": 95},
    "Lucknow": {"x": 420, "y": 145},
    "Kanpur": {"x": 455, "y": 175},
    "Jaipur": {"x": 300, "y": 190},
    "Bhopal": {"x": 210, "y": 135},
    "Indore": {"x": 175, "y": 160},
    "Nagpur": {"x": 310, "y": 135},
    "Ranchi": {"x": 490, "y": 235},
    "Bhubaneswar": {"x": 575, "y": 250},
}


def _rid(a: str, b: str) -> str:
    # Stable edge id for an undirected edge.
    if a <= b:
        return f"{a}__{b}"
    return f"{b}__{a}"


ROAD_EDGES: list[Edge] = [
    Edge(_rid("Ahmedabad", "Surat") + "_road", "Ahmedabad", "Surat", "road", "NH48", 264, 5.2, 650),
    Edge(_rid("Surat", "Vadodara") + "_road", "Surat", "Vadodara", "road", "NH48", 166, 3.4, 420),
    Edge(_rid("Vadodara", "Mumbai") + "_road", "Vadodara", "Mumbai", "road", "NH48", 392, 7.1, 950),
    Edge(_rid("Mumbai", "Pune") + "_road", "Mumbai", "Pune", "road", "NH48", 149, 2.9, 320),
    Edge(_rid("Pune", "Nashik") + "_road", "Pune", "Nashik", "road", "NH60 (Ghoti stretch)", 168, 3.4, 280),
    Edge(_rid("Pune", "Goa") + "_road", "Pune", "Goa", "road", "NH66", 583, 10.7, 1320),
    Edge(_rid("Mumbai", "Goa") + "_road", "Mumbai", "Goa", "road", "NH66", 598, 10.9, 1380),
    Edge(_rid("Pune", "Hyderabad") + "_road", "Pune", "Hyderabad", "road", "NH65", 580, 10.2, 1410),
    Edge(_rid("Pune", "Nagpur") + "_road", "Pune", "Nagpur", "road", "NH48", 632, 11.7, 1600),
    Edge(_rid("Nashik", "Nagpur") + "_road", "Nashik", "Nagpur", "road", "NH3/NH53 (Nagpur-Nashik ghat advisory)", 795, 14.4, 1550),
    Edge(_rid("Nagpur", "Bhopal") + "_road", "Nagpur", "Bhopal", "road", "NH44 (toll work)", 720, 12.8, 1500),
    Edge(_rid("Nagpur", "Hyderabad") + "_road", "Nagpur", "Hyderabad", "road", "NH44", 560, 9.6, 1220),
    Edge(_rid("Nagpur", "Indore") + "_road", "Nagpur", "Indore", "road", "NH47", 720, 12.9, 1330),
    Edge(_rid("Bhopal", "Indore") + "_road", "Bhopal", "Indore", "road", "NH47/NH52", 204, 3.7, 360),
    Edge(_rid("Indore", "Ahmedabad") + "_road", "Indore", "Ahmedabad", "road", "NH47", 370, 6.7, 860),
    Edge(_rid("Indore", "Vadodara") + "_road", "Indore", "Vadodara", "road", "NH48", 242, 4.5, 520),
    Edge(_rid("Ahmedabad", "Delhi") + "_road", "Ahmedabad", "Delhi", "road", "NH48", 940, 16.2, 1850),
    Edge(_rid("Delhi", "Jaipur") + "_road", "Delhi", "Jaipur", "road", "NH48", 281, 5.1, 610),
    Edge(_rid("Jaipur", "Ahmedabad") + "_road", "Jaipur", "Ahmedabad", "road", "NH48", 615, 11.1, 1250),
    Edge(_rid("Jaipur", "Lucknow") + "_road", "Jaipur", "Lucknow", "road", "NH52", 539, 9.7, 980),
    Edge(_rid("Lucknow", "Delhi") + "_road", "Lucknow", "Delhi", "road", "NH48 (Lucknow-Agra corridor)", 545, 9.9, 1000),
    Edge(_rid("Lucknow", "Kanpur") + "_road", "Lucknow", "Kanpur", "road", "NH27 (Kanpur congestion)", 93, 1.9, 160),
    Edge(_rid("Kanpur", "Patna") + "_road", "Kanpur", "Patna", "road", "NH19", 694, 12.7, 1230),
    Edge(_rid("Patna", "Delhi") + "_road", "Patna", "Delhi", "road", "NH19", 1040, 18.1, 2050),
    Edge(_rid("Lucknow", "Patna") + "_road", "Lucknow", "Patna", "road", "NH27 / NH19 link", 860, 15.2, 1760),
    Edge(_rid("Lucknow", "Bhopal") + "_road", "Lucknow", "Bhopal", "road", "NH46", 789, 14.2, 1550),
    Edge(_rid("Hyderabad", "Bengaluru") + "_road", "Hyderabad", "Bengaluru", "road", "NH44", 624, 11.3, 1180),
    Edge(_rid("Bengaluru", "Chennai") + "_road", "Bengaluru", "Chennai", "road", "NH44", 351, 6.2, 640),
    Edge(_rid("Bengaluru", "Nagpur") + "_road", "Bengaluru", "Nagpur", "road", "NH44", 980, 17.6, 1950),
    Edge(_rid("Chennai", "Bhubaneswar") + "_road", "Chennai", "Bhubaneswar", "road", "NH16 (coastal corridor)", 1330, 22.2, 2600),
    Edge(_rid("Bhubaneswar", "Kolkata") + "_road", "Bhubaneswar", "Kolkata", "road", "NH16", 440, 7.5, 690),
    Edge(_rid("Chennai", "Kolkata") + "_road", "Chennai", "Kolkata", "road", "NH16", 1520, 25.1, 2880),
    Edge(_rid("Ranchi", "Nagpur") + "_road", "Ranchi", "Nagpur", "road", "NH39", 610, 10.9, 950),
    Edge(_rid("Ranchi", "Patna") + "_road", "Ranchi", "Patna", "road", "NH20", 545, 9.2, 940),
    Edge(_rid("Ranchi", "Bhubaneswar") + "_road", "Ranchi", "Bhubaneswar", "road", "NH20", 380, 6.7, 520),
    Edge(_rid("Bhubaneswar", "Patna") + "_road", "Bhubaneswar", "Patna", "road", "NH19", 790, 14.2, 1380),
    Edge(_rid("Kolkata", "Ahmedabad") + "_road", "Kolkata", "Ahmedabad", "road", "NH48 (long haul)", 1670, 29.4, 3550),
]


RAIL_EDGES: list[Edge] = [
    Edge(_rid("Delhi", "Mumbai") + "_rail", "Delhi", "Mumbai", "rail", "Rajdhani Express", 1420, 14.5, 3200),
    Edge(_rid("Delhi", "Kolkata") + "_rail", "Delhi", "Kolkata", "rail", "Rajdhani Express", 1520, 15.2, 3400),
    Edge(_rid("Delhi", "Lucknow") + "_rail", "Delhi", "Lucknow", "rail", "Shatabdi (Delhi-Lucknow)", 555, 6.0, 1350),
    Edge(_rid("Delhi", "Jaipur") + "_rail", "Delhi", "Jaipur", "rail", "Shatabdi (Delhi-Jaipur)", 280, 3.5, 820),
    Edge(_rid("Delhi", "Patna") + "_rail", "Delhi", "Patna", "rail", "Rajdhani Express", 1035, 10.8, 2600),
    Edge(_rid("Mumbai", "Chennai") + "_rail", "Mumbai", "Chennai", "rail", "Rajdhani Express", 1320, 21.5, 3000),
    Edge(_rid("Mumbai", "Hyderabad") + "_rail", "Mumbai", "Hyderabad", "rail", "Deccan Queen", 704, 12.0, 2100),
    Edge(_rid("Mumbai", "Nagpur") + "_rail", "Mumbai", "Nagpur", "rail", "Gondwana Express", 820, 14.0, 2400),
    Edge(_rid("Mumbai", "Pune") + "_rail", "Mumbai", "Pune", "rail", "Shatabdi (Mumbai-Pune)", 149, 2.8, 650),
    Edge(_rid("Mumbai", "Vadodara") + "_rail", "Mumbai", "Vadodara", "rail", "Fast Passenger", 392, 8.2, 980),
    # Slightly slower than road corridor in this demo so time-optimization prefers NH60.
    Edge(_rid("Pune", "Nashik") + "_rail", "Pune", "Nashik", "rail", "Intercity Express", 168, 3.9, 520),
    Edge(_rid("Pune", "Hyderabad") + "_rail", "Pune", "Hyderabad", "rail", "Deccan Queen (branch)", 580, 10.2, 1700),
    Edge(_rid("Pune", "Nashik") + "_rail_alt", "Pune", "Nashik", "rail", "Express (via rail hub)", 168, 4.2, 540),
    Edge(_rid("Nashik", "Bhopal") + "_rail", "Nashik", "Bhopal", "rail", "Malwa Express", 865, 15.0, 2250),
    Edge(_rid("Nashik", "Indore") + "_rail", "Nashik", "Indore", "rail", "Express (Malwa belt)", 720, 12.8, 1900),
    Edge(_rid("Nagpur", "Bhopal") + "_rail", "Nagpur", "Bhopal", "rail", "Express", 665, 11.3, 1750),
    Edge(_rid("Nagpur", "Hyderabad") + "_rail", "Nagpur", "Hyderabad", "rail", "Gondwana Express", 560, 9.6, 1650),
    Edge(_rid("Nagpur", "Ranchi") + "_rail", "Nagpur", "Ranchi", "rail", "Express (NH39 route)", 610, 12.0, 1600),
    Edge(_rid("Hyderabad", "Bengaluru") + "_rail", "Hyderabad", "Bengaluru", "rail", "Shatabdi (Hyderabad-Bengaluru)", 624, 8.2, 1850),
    Edge(_rid("Hyderabad", "Chennai") + "_rail", "Hyderabad", "Chennai", "rail", "Charminar Express (demo)", 781, 12.6, 2100),
    Edge(_rid("Bengaluru", "Chennai") + "_rail", "Bengaluru", "Chennai", "rail", "Shatabdi (Bengaluru-Chennai)", 351, 4.5, 980),
    Edge(_rid("Bengaluru", "Nagpur") + "_rail", "Bengaluru", "Nagpur", "rail", "Express", 980, 18.1, 2600),
    Edge(_rid("Bengaluru", "Kolkata") + "_rail", "Bengaluru", "Kolkata", "rail", "Express (via hub)", 1900, 30.0, 4200),
    Edge(_rid("Chennai", "Kolkata") + "_rail", "Chennai", "Kolkata", "rail", "Coromandel Express", 1470, 26.0, 3600),
    Edge(_rid("Chennai", "Bhubaneswar") + "_rail", "Chennai", "Bhubaneswar", "rail", "Intercity Express", 1330, 22.5, 2800),
    Edge(_rid("Bhubaneswar", "Kolkata") + "_rail", "Bhubaneswar", "Kolkata", "rail", "Howrah Express", 440, 7.2, 1350),
    Edge(_rid("Bhubaneswar", "Ranchi") + "_rail", "Bhubaneswar", "Ranchi", "rail", "Express (via Dhanbad)", 510, 9.0, 1450),
    Edge(_rid("Ranchi", "Patna") + "_rail", "Ranchi", "Patna", "rail", "Intercity Express", 545, 8.7, 1300),
    Edge(_rid("Ranchi", "Kolkata") + "_rail", "Ranchi", "Kolkata", "rail", "Express", 680, 13.0, 1750),
    Edge(_rid("Patna", "Lucknow") + "_rail", "Patna", "Lucknow", "rail", "Tejas (Patna-Lucknow)", 360, 4.6, 980),
    Edge(_rid("Lucknow", "Kanpur") + "_rail", "Lucknow", "Kanpur", "rail", "Intercity Express", 93, 2.0, 420),
    Edge(_rid("Lucknow", "Jaipur") + "_rail", "Lucknow", "Jaipur", "rail", "Garib Rath (demo)", 740, 12.5, 1350),
    Edge(_rid("Lucknow", "Ahmedabad") + "_rail", "Lucknow", "Ahmedabad", "rail", "Express (via Delhi)", 1120, 20.0, 2800),
    Edge(_rid("Kanpur", "Delhi") + "_rail", "Kanpur", "Delhi", "rail", "Shatabdi (Kanpur-Delhi)", 440, 5.7, 1050),
    Edge(_rid("Kanpur", "Patna") + "_rail", "Kanpur", "Patna", "rail", "Express", 694, 11.8, 1700),
    Edge(_rid("Ahmedabad", "Mumbai") + "_rail", "Ahmedabad", "Mumbai", "rail", "Sabarmati Express (demo)", 800, 14.2, 2400),
    Edge(_rid("Ahmedabad", "Vadodara") + "_rail", "Ahmedabad", "Vadodara", "rail", "Fast Passenger", 105, 2.1, 320),
    Edge(_rid("Ahmedabad", "Jaipur") + "_rail", "Ahmedabad", "Jaipur", "rail", "Shatabdi (Ahmedabad-Jaipur)", 613, 9.6, 1750),
]


def get_all_edges() -> list[Edge]:
    # Demo dataset: road and rail edges are undirected conceptually.
    return ROAD_EDGES + RAIL_EDGES


def get_cities() -> list[str]:
    return sorted(CITY_POSITIONS.keys())

