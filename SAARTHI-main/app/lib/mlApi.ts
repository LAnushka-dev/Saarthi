const ML_API_BASE =
  process.env.NEXT_PUBLIC_ML_API_URL ??
  process.env.ML_API_URL ??
  "http://localhost:8000";

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

async function mlFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${ML_API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`ML API error ${response.status}: ${text}`);
  }

  return response.json() as Promise<T>;
}

export function cropQuery(params: {
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

export function forecastProduction(params: {
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

export function getZoneBalance(
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
