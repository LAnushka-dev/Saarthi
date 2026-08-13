/**
 * Saarthi ML API Client
 * =====================
 * Drop this in: app/lib/mlApi.ts
 *
 * Usage in any Server Component or API Route:
 *   import { cropQuery, forecastProduction, getZoneBalance } from '@/lib/mlApi'
 *
 *   const result = await cropQuery({ question: "Best basmati in October?", currentMonth: 10 })
 */

const ML_API_BASE = process.env.ML_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CropMatch {
  crop: string;
  state: string;
  grade: "A" | "B" | "C";
  season: string;
  peak_months: number[];
  note: string;
  relevance_score: number;
}

export interface CropQueryResult {
  query: string;
  answer_summary: string;
  confidence: number;
  matches: CropMatch[];
}

export interface ForecastResult {
  crop: string;
  state: string;
  target_year: number;
  predicted_production_mt: number;
  lower_bound_mt: number;
  upper_bound_mt: number;
  yoy_change_pct: number;
  input_features: Record<string, number | null>;
  model_type: string;
  note: string;
}

export interface ZoneCropBalance {
  zone_id: number;
  zone_name: string;
  crop: string;
  predicted_production_mt: number;
  consumption_need_mt: number;
  surplus_deficit_mt: number;
  surplus_deficit_pct: number;
  caloric_contribution_bn_kcal: number;
  alert_level: "CRITICAL" | "WARNING" | "STABLE" | "SURPLUS";
  procurement_recommendation: string;
}

export interface ZoneSummary {
  zone_id: number;
  zone_name: string;
  states: string[];
  population_m: number;
  overall_caloric_need_bn_kcal: number;
  total_caloric_production_bn_kcal: number;
  caloric_balance_bn_kcal: number;
  caloric_sufficiency_pct: number;
  alert_level: "CRITICAL" | "WARNING" | "STABLE" | "SURPLUS";
  crop_balances: ZoneCropBalance[];
  inter_zone_recommendations: string[];
}

export interface ZoneAlert {
  zone_id: number;
  zone_name: string;
  states: string[];
  alert_level: "CRITICAL" | "WARNING";
  caloric_sufficiency_pct: number;
  deficient_crops: { crop: string; deficit_mt: number; deficit_pct: number }[];
  recommendations: string[];
}

// ---------------------------------------------------------------------------
// Shared fetch helper
// ---------------------------------------------------------------------------

async function mlFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${ML_API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`ML API error ${res.status}: ${error}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Model 1: Crop-State Knowledge Engine
// ---------------------------------------------------------------------------

export async function cropQuery(params: {
  question: string;
  currentMonth?: number;
  topK?: number;
}): Promise<CropQueryResult> {
  return mlFetch<CropQueryResult>("/api/crop-query", {
    method: "POST",
    body: JSON.stringify({
      question: params.question,
      current_month: params.currentMonth ?? new Date().getMonth() + 1,
      top_k: params.topK ?? 5,
    }),
  });
}

export async function getAvailableCrops(month?: number): Promise<{
  month: number;
  crops: CropMatch[];
  count: number;
}> {
  const m = month ?? new Date().getMonth() + 1;
  return mlFetch(`/api/available-crops?month=${m}`);
}

export async function getStateCrops(state: string): Promise<{
  state: string;
  grade_a_crops: CropMatch[];
  count: number;
}> {
  return mlFetch(`/api/state-crops/${encodeURIComponent(state)}`);
}

// ---------------------------------------------------------------------------
// Model 2: Production Forecasting
// ---------------------------------------------------------------------------

export async function forecastProduction(params: {
  crop: string;
  state: string;
  targetYear?: number;
  rainfallMm?: number;
  tempAnomaly?: number;
}): Promise<ForecastResult> {
  return mlFetch<ForecastResult>("/api/forecast", {
    method: "POST",
    body: JSON.stringify({
      crop: params.crop,
      state: params.state,
      target_year: params.targetYear,
      rainfall_mm: params.rainfallMm,
      temp_anomaly: params.tempAnomaly,
    }),
  });
}

// ---------------------------------------------------------------------------
// Model 3: Surplus / Deficit
// ---------------------------------------------------------------------------

export async function getZoneBalance(
  zoneId: number,
  cropProductions: Record<string, number>
): Promise<ZoneSummary> {
  return mlFetch<ZoneSummary>("/api/zone-balance", {
    method: "POST",
    body: JSON.stringify({
      zone_id: zoneId,
      crop_productions: cropProductions,
    }),
  });
}

export async function getAllZoneBalances(
  productionMap: Record<number, Record<string, number>>
): Promise<{ zones: ZoneSummary[]; total_zones: number }> {
  return mlFetch("/api/zone-balance/all", {
    method: "POST",
    body: JSON.stringify({ production_map: productionMap }),
  });
}

export async function getZoneAlerts(): Promise<{
  alerts: ZoneAlert[];
  alert_count: number;
}> {
  return mlFetch("/api/alerts");
}

// ---------------------------------------------------------------------------
// Combined pipeline
// ---------------------------------------------------------------------------

export async function forecastAndBalance(
  zoneId: number,
  crops: string[]
): Promise<{
  zone_id: number;
  forecasts: ForecastResult[];
  balance: ZoneSummary;
}> {
  const params = new URLSearchParams({ zone_id: String(zoneId) });
  crops.forEach((c) => params.append("crops", c));
  return mlFetch(`/api/pipeline/forecast-and-balance?${params}`, { method: "POST" });
}
