"""
Model 3: Surplus & Deficit Prediction
=======================================
Computes for each agri-zone:
    Surplus/Deficit = Predicted Production − Zone Consumption Need

If a zone is heading into deficit, the platform triggers early
procurement alerts to vendors and suggests inter-zone routes.

Zones follow India's agro-climatic zone classification (broadly):
  Zone 1  Western Himalayas (J&K, HP, Uttarakhand)
  Zone 2  Eastern Himalayas (NE states, Sikkim, WB hills)
  Zone 3  Lower Gangetic Plain (WB, Bihar)
  Zone 4  Middle Gangetic Plain (UP East, Jharkhand)
  Zone 5  Upper Gangetic Plain (UP West, Delhi, Haryana)
  Zone 6  Trans-Gangetic Plain (Punjab, Chandigarh)
  Zone 7  Eastern Plateau & Hills (Chhattisgarh, Odisha)
  Zone 8  Central Plateau & Hills (MP, Rajasthan SE)
  Zone 9  Western Plateau & Hills (Maharashtra, Telangana)
  Zone 10 Southern Plateau & Hills (Karnataka, Tamil Nadu)
  Zone 11 East Coast Plains & Hills (AP, Odisha coast)
  Zone 12 West Coast Plains & Ghats (Kerala, Goa, coastal Karnataka)
  Zone 13 Gujarat Plains & Hills
  Zone 14 Western Dry Region (Rajasthan W, Kutch)
  Zone 15 Islands (A&N, Lakshadweep)
"""

from __future__ import annotations
import math
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum

# ---------------------------------------------------------------------------
# Zone meta-data
# ---------------------------------------------------------------------------

@dataclass
class Zone:
    zone_id: int
    name: str
    states: list[str]
    population_m: float          # millions
    kcal_per_capita_day: float = 2100.0   # ICMR recommendation
    key_crops: list[str] = field(default_factory=list)

    @property
    def annual_caloric_need_bn_kcal(self) -> float:
        """Zone's total annual caloric requirement in billion kcal."""
        return self.population_m * 1e6 * self.kcal_per_capita_day * 365 / 1e9

    @property
    def grain_equivalent_mt(self) -> float:
        """Convert caloric need to approximate grain-equivalent metric tonnes.
        Assumes ~3,500 kcal/kg for food grain mix (rice, wheat, pulses).
        """
        return self.annual_caloric_need_bn_kcal * 1e9 / (3500 * 1000)


ZONES: dict[int, Zone] = {
    1:  Zone(1,  "Western Himalayas",       ["J&K", "Himachal Pradesh", "Uttarakhand"],      26.0,  key_crops=["apple","wheat","maize"]),
    2:  Zone(2,  "Eastern Himalayas",        ["Assam", "Meghalaya", "Arunachal Pradesh", "Nagaland", "Manipur", "Mizoram", "Tripura", "Sikkim"], 52.0, key_crops=["rice","tea","ginger"]),
    3:  Zone(3,  "Lower Gangetic Plain",     ["West Bengal", "Bihar"],                       154.0, key_crops=["rice","jute","potato"]),
    4:  Zone(4,  "Middle Gangetic Plain",    ["Uttar Pradesh (East)", "Jharkhand"],          110.0, key_crops=["rice","wheat","maize"]),
    5:  Zone(5,  "Upper Gangetic Plain",     ["Uttar Pradesh (West)", "Haryana", "Delhi"],   105.0, key_crops=["wheat","sugarcane","potato"]),
    6:  Zone(6,  "Trans-Gangetic Plain",     ["Punjab", "Chandigarh", "Haryana (NW)"],       32.0,  key_crops=["wheat","basmati rice","cotton"]),
    7:  Zone(7,  "Eastern Plateau & Hills",  ["Chhattisgarh", "Odisha", "Jharkhand (W)"],    72.0,  key_crops=["rice","pulses","minor millets"]),
    8:  Zone(8,  "Central Plateau & Hills",  ["Madhya Pradesh", "Rajasthan (SE)"],            90.0,  key_crops=["soybean","wheat","gram"]),
    9:  Zone(9,  "Western Plateau & Hills",  ["Maharashtra", "Telangana"],                   154.0, key_crops=["cotton","sugarcane","soybean","onion"]),
    10: Zone(10, "Southern Plateau & Hills", ["Karnataka", "Tamil Nadu (N)"],                98.0,  key_crops=["ragi","rice","groundnut"]),
    11: Zone(11, "East Coast Plains",        ["Andhra Pradesh", "Odisha (coast)"],            60.0,  key_crops=["rice","tobacco","chilli"]),
    12: Zone(12, "West Coast & Ghats",       ["Kerala", "Goa", "Karnataka (coast)"],          40.0,  key_crops=["coconut","banana","pepper","rubber"]),
    13: Zone(13, "Gujarat Plains",           ["Gujarat"],                                     63.0,  key_crops=["cotton","groundnut","castor"]),
    14: Zone(14, "Western Dry Region",       ["Rajasthan (W)", "Gujarat (Kutch)"],            30.0,  key_crops=["bajra","moth bean","mustard"]),
    15: Zone(15, "Islands",                  ["Andaman & Nicobar", "Lakshadweep"],             0.5,  key_crops=["coconut","rice"]),
}

# ---------------------------------------------------------------------------
# Caloric value map: MT of crop -> billion kcal
# ---------------------------------------------------------------------------

KCAL_PER_KG: dict[str, float] = {
    "wheat":         3400,
    "rice":          3600,
    "basmati rice":  3600,
    "maize":         3600,
    "sorghum":       3290,
    "bajra":         3610,
    "gram":          3630,
    "soybean":       4460,
    "potato":        770,
    "tomato":        180,
    "onion":         400,
    "sugarcane":     270,
    "cotton":        0,     # non-food
    "groundnut":     5670,
    "mustard":       5000,
    "banana":        890,
    "apple":         520,
    "orange":        470,
    "mango":         600,
    "grapes":        690,
    "chilli":        400,
    "turmeric":      350,
}

def mt_to_bn_kcal(crop: str, production_mt: float) -> float:
    kcal_per_kg = KCAL_PER_KG.get(crop.lower(), 2000.0)  # default 2000 kcal/kg
    return production_mt * 1000 * kcal_per_kg / 1e9

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class AlertLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING  = "WARNING"
    STABLE   = "STABLE"
    SURPLUS  = "SURPLUS"

@dataclass
class ZoneCropBalance:
    zone_id: int
    zone_name: str
    crop: str
    predicted_production_mt: float
    consumption_need_mt: float       # derived from population need allocated to this crop
    surplus_deficit_mt: float        # positive = surplus, negative = deficit
    surplus_deficit_pct: float       # relative to need
    caloric_contribution_bn_kcal: float
    alert_level: AlertLevel
    procurement_recommendation: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["alert_level"] = self.alert_level.value
        return d


@dataclass
class ZoneSummary:
    zone_id: int
    zone_name: str
    states: list[str]
    population_m: float
    overall_caloric_need_bn_kcal: float
    total_caloric_production_bn_kcal: float
    caloric_balance_bn_kcal: float        # positive = surplus
    caloric_sufficiency_pct: float        # 100% = exactly meets need
    alert_level: AlertLevel
    crop_balances: list[ZoneCropBalance]
    inter_zone_recommendations: list[str]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["alert_level"] = self.alert_level.value
        d["crop_balances"] = [c.to_dict() for c in self.crop_balances]
        return d


# ---------------------------------------------------------------------------
# Consumption allocation: how much of each crop does each zone "need"?
# ---------------------------------------------------------------------------

CROP_DIET_SHARE: dict[str, float] = {
    # Share of total caloric need attributable to each crop category
    "wheat":    0.22,
    "rice":     0.30,
    "pulses":   0.08,  # gram, dal etc.
    "vegetables": 0.05,  # potato, onion, tomato combined
    "fruits":   0.03,
    "oilseeds": 0.07,
    "others":   0.25,
}

CROP_TO_DIET_CATEGORY: dict[str, str] = {
    "wheat":        "wheat",
    "basmati rice": "rice",
    "rice":         "rice",
    "gram":         "pulses",
    "soybean":      "oilseeds",
    "groundnut":    "oilseeds",
    "mustard":      "oilseeds",
    "potato":       "vegetables",
    "tomato":       "vegetables",
    "onion":        "vegetables",
    "banana":       "fruits",
    "mango":        "fruits",
    "apple":        "fruits",
    "orange":       "fruits",
    "grapes":       "fruits",
}

def _crop_consumption_need_mt(zone: Zone, crop: str) -> float:
    """Estimate MT of crop the zone needs to satisfy its population."""
    category = CROP_TO_DIET_CATEGORY.get(crop.lower(), "others")
    diet_share = CROP_DIET_SHARE.get(category, 0.05)
    kcal_needed = zone.annual_caloric_need_bn_kcal * 1e9 * diet_share
    kcal_per_kg = KCAL_PER_KG.get(crop.lower(), 2000.0)
    return kcal_needed / (kcal_per_kg * 1000)  # MT

# ---------------------------------------------------------------------------
# Surplus/Deficit Model
# ---------------------------------------------------------------------------

class SurplusDeficitModel:
    """
    Given a dict of {(crop, zone_id): predicted_production_mt},
    computes the balance for every zone and raises alerts.

    In production, predicted_production_mt comes from Model 2 outputs.
    """

    # Alert thresholds (deficit %)
    CRITICAL_THRESHOLD = -20.0
    WARNING_THRESHOLD  = -5.0
    SURPLUS_THRESHOLD  =  10.0

    def compute_zone_balance(
        self,
        zone_id: int,
        crop_productions: dict[str, float],   # {crop: predicted_mt}
    ) -> ZoneSummary:
        zone = ZONES[zone_id]
        caloric_need = zone.annual_caloric_need_bn_kcal
        total_caloric_prod = 0.0
        crop_balances: list[ZoneCropBalance] = []

        for crop, prod_mt in crop_productions.items():
            need_mt = _crop_consumption_need_mt(zone, crop)
            surplus_mt = prod_mt - need_mt
            surplus_pct = (surplus_mt / need_mt * 100) if need_mt > 0 else 0.0
            cal_bn = mt_to_bn_kcal(crop, prod_mt)
            total_caloric_prod += cal_bn
            alert = self._crop_alert(surplus_pct)
            rec = self._procurement_recommendation(crop, zone, surplus_mt, surplus_pct)

            crop_balances.append(ZoneCropBalance(
                zone_id=zone_id,
                zone_name=zone.name,
                crop=crop,
                predicted_production_mt=round(prod_mt, 1),
                consumption_need_mt=round(need_mt, 1),
                surplus_deficit_mt=round(surplus_mt, 1),
                surplus_deficit_pct=round(surplus_pct, 1),
                caloric_contribution_bn_kcal=round(cal_bn, 2),
                alert_level=alert,
                procurement_recommendation=rec,
            ))

        caloric_balance = total_caloric_prod - caloric_need
        sufficiency_pct = (total_caloric_prod / caloric_need * 100) if caloric_need > 0 else 0.0
        overall_alert = self._overall_alert(sufficiency_pct)
        inter_zone_recs = self._inter_zone_recommendations(zone, crop_balances, sufficiency_pct)

        return ZoneSummary(
            zone_id=zone_id,
            zone_name=zone.name,
            states=zone.states,
            population_m=zone.population_m,
            overall_caloric_need_bn_kcal=round(caloric_need, 2),
            total_caloric_production_bn_kcal=round(total_caloric_prod, 2),
            caloric_balance_bn_kcal=round(caloric_balance, 2),
            caloric_sufficiency_pct=round(sufficiency_pct, 1),
            alert_level=overall_alert,
            crop_balances=sorted(crop_balances, key=lambda x: x.surplus_deficit_pct),
            inter_zone_recommendations=inter_zone_recs,
        )

    def compute_all_zones(
        self,
        production_map: dict[int, dict[str, float]],   # {zone_id: {crop: mt}}
    ) -> list[ZoneSummary]:
        summaries = []
        for zone_id, crop_productions in production_map.items():
            summary = self.compute_zone_balance(zone_id, crop_productions)
            summaries.append(summary)
        return sorted(summaries, key=lambda x: x.caloric_sufficiency_pct)

    def get_alerts(self, summaries: list[ZoneSummary]) -> list[dict]:
        """Return only zones that need action, ranked by urgency."""
        alerts = []
        for s in summaries:
            if s.alert_level in (AlertLevel.CRITICAL, AlertLevel.WARNING):
                deficient_crops = [
                    c for c in s.crop_balances
                    if c.alert_level in (AlertLevel.CRITICAL, AlertLevel.WARNING)
                ]
                alerts.append({
                    "zone_id": s.zone_id,
                    "zone_name": s.zone_name,
                    "states": s.states,
                    "alert_level": s.alert_level.value,
                    "caloric_sufficiency_pct": s.caloric_sufficiency_pct,
                    "deficient_crops": [
                        {"crop": c.crop, "deficit_mt": abs(c.surplus_deficit_mt),
                         "deficit_pct": abs(c.surplus_deficit_pct)}
                        for c in deficient_crops
                    ],
                    "recommendations": s.inter_zone_recommendations,
                })
        return alerts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _crop_alert(self, surplus_pct: float) -> AlertLevel:
        if surplus_pct <= self.CRITICAL_THRESHOLD:
            return AlertLevel.CRITICAL
        elif surplus_pct <= self.WARNING_THRESHOLD:
            return AlertLevel.WARNING
        elif surplus_pct >= self.SURPLUS_THRESHOLD:
            return AlertLevel.SURPLUS
        return AlertLevel.STABLE

    def _overall_alert(self, sufficiency_pct: float) -> AlertLevel:
        if sufficiency_pct < 80:
            return AlertLevel.CRITICAL
        elif sufficiency_pct < 95:
            return AlertLevel.WARNING
        elif sufficiency_pct > 115:
            return AlertLevel.SURPLUS
        return AlertLevel.STABLE

    def _procurement_recommendation(
        self, crop: str, zone: Zone, surplus_mt: float, surplus_pct: float
    ) -> str:
        if surplus_pct <= self.CRITICAL_THRESHOLD:
            return (
                f"URGENT: {zone.name} faces a {abs(surplus_pct):.0f}% deficit in {crop}. "
                f"Import {abs(surplus_mt):,.0f} MT immediately from adjacent surplus zones."
            )
        elif surplus_pct <= self.WARNING_THRESHOLD:
            return (
                f"Procure {abs(surplus_mt):,.0f} MT of {crop} from external zones within 4 weeks "
                f"to buffer {zone.name}'s shortfall."
            )
        elif surplus_pct >= self.SURPLUS_THRESHOLD:
            return (
                f"{zone.name} has a {surplus_pct:.0f}% surplus in {crop} "
                f"({surplus_mt:,.0f} MT). Prioritise vendor connections and export routes."
            )
        return f"{crop.title()} supply in {zone.name} is stable. No immediate action needed."

    def _inter_zone_recommendations(
        self, zone: Zone, crop_balances: list[ZoneCropBalance], sufficiency_pct: float
    ) -> list[str]:
        recs = []
        if sufficiency_pct < 95:
            recs.append(
                f"Zone {zone.zone_id} ({zone.name}) is at {sufficiency_pct:.1f}% caloric sufficiency. "
                "Activate vendor procurement alerts for deficit crops."
            )
        critical_crops = [c for c in crop_balances if c.alert_level == AlertLevel.CRITICAL]
        warning_crops = [c for c in crop_balances if c.alert_level == AlertLevel.WARNING]
        surplus_zones_hint = self._find_surplus_donors(zone.zone_id)
        if critical_crops:
            crops_str = ", ".join(c.crop for c in critical_crops)
            recs.append(
                f"Critical deficit in: {crops_str}. "
                f"Recommended donor zones: {surplus_zones_hint}."
            )
        if warning_crops:
            crops_str = ", ".join(c.crop for c in warning_crops)
            recs.append(f"Early warning for: {crops_str}. Monitor over next 2 weeks.")
        return recs

    @staticmethod
    def _find_surplus_donors(zone_id: int) -> str:
        """Heuristic: map known surplus zones to deficient ones."""
        donor_map = {
            3:  "Zone 6 (Trans-Gangetic, wheat/rice surplus)",
            4:  "Zone 6 (Trans-Gangetic) or Zone 8 (Central Plateau)",
            7:  "Zone 11 (East Coast, rice surplus)",
            9:  "Zone 8 (Central Plateau) or Zone 13 (Gujarat)",
            10: "Zone 11 (East Coast, rice) or Zone 6 (wheat)",
            12: "Zone 10 or Zone 13",
            14: "Zone 6 (wheat) or Zone 13 (groundnut/cotton)",
        }
        return donor_map.get(zone_id, "Zones 5, 6 (Trans-Gangetic surplus belt)")


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Simulated output from Model 2 for two zones
    production_map = {
        6: {   # Trans-Gangetic Plain (Punjab/Haryana) — large wheat surplus expected
            "wheat":        18400,   # MT (predicted by Model 2)
            "basmati rice": 4800,
        },
        3: {   # Lower Gangetic Plain (WB/Bihar) — rice near-deficit scenario
            "rice":  14200,   # below normal due to drought scenario
            "potato": 7800,
        },
        9: {   # Western Plateau (Maharashtra) — mixed
            "onion":     4200,
            "tomato":    1800,
            "sugarcane": 98000,
        },
    }

    model = SurplusDeficitModel()
    summaries = model.compute_all_zones(production_map)

    print("=== Zone Surplus / Deficit Report ===\n")
    for s in summaries:
        print(f"Zone {s.zone_id}: {s.zone_name}")
        print(f"  Population: {s.population_m:.0f}M")
        print(f"  Caloric sufficiency: {s.caloric_sufficiency_pct:.1f}%")
        print(f"  Alert level: {s.alert_level.value}")
        for c in s.crop_balances:
            sign = "+" if c.surplus_deficit_mt >= 0 else ""
            print(f"    {c.crop:20s}: {sign}{c.surplus_deficit_mt:,.0f} MT ({sign}{c.surplus_deficit_pct:.0f}%) [{c.alert_level.value}]")
        for r in s.inter_zone_recommendations:
            print(f"  ▶ {r}")
        print()

    print("=== Active Alerts ===")
    alerts = model.get_alerts(summaries)
    print(json.dumps(alerts, indent=2))
