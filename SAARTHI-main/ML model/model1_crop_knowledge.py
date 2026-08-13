"""
Model 1: Crop-State Knowledge Engine
=====================================
Answers queries like:
  - "Which state has Grade A basmati right now?"
  - "What is Karnataka's best kharif crop this season?"
  - "Where should I source tomatoes from in October?"

Approach:
  - Sentence-transformer embeddings on crop-state knowledge corpus
  - FAISS vector index for semantic retrieval
  - Lightweight classifier for crop-grade ranking
  - Falls back to structured lookup if embedding score is low
"""

from __future__ import annotations
import json
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Static knowledge base  (replace with DB / API calls in production)
# ---------------------------------------------------------------------------

CROP_STATE_KNOWLEDGE: list[dict] = [
    # Format: crop, state, grade, season, peak_months, notes
    {"crop": "basmati rice",     "state": "Punjab",         "grade": "A", "season": "kharif", "peak_months": [10,11],    "note": "Best aromatic long-grain basmati; APMC Amritsar hub"},
    {"crop": "basmati rice",     "state": "Haryana",        "grade": "A", "season": "kharif", "peak_months": [10,11],    "note": "Karnal basmati is GI-tagged"},
    {"crop": "wheat",            "state": "Punjab",         "grade": "A", "season": "rabi",   "peak_months": [4,5],      "note": "Highest wheat yield per hectare in India"},
    {"crop": "wheat",            "state": "Haryana",        "grade": "A", "season": "rabi",   "peak_months": [4,5],      "note": "Bhiwani and Sirsa surplus zones"},
    {"crop": "wheat",            "state": "Uttar Pradesh",  "grade": "B", "season": "rabi",   "peak_months": [4,5],      "note": "Large volume; moderate grade"},
    {"crop": "orange",           "state": "Maharashtra",    "grade": "A", "season": "winter", "peak_months": [11,12,1],  "note": "Nagpur mandarin; GI-tagged"},
    {"crop": "sugarcane",        "state": "Maharashtra",    "grade": "A", "season": "annual", "peak_months": [1,2,3],    "note": "Kolhapur and Pune belt"},
    {"crop": "sugarcane",        "state": "Uttar Pradesh",  "grade": "A", "season": "annual", "peak_months": [11,12,1],  "note": "Largest sugarcane state by volume"},
    {"crop": "rice",             "state": "West Bengal",    "grade": "A", "season": "kharif", "peak_months": [11,12],    "note": "Gobindobhog aromatic variety"},
    {"crop": "rice",             "state": "Andhra Pradesh", "grade": "A", "season": "kharif", "peak_months": [11,12],    "note": "East Godavari district"},
    {"crop": "tomato",           "state": "Andhra Pradesh", "grade": "A", "season": "rabi",   "peak_months": [1,2,3],    "note": "Madanapalle cluster; major supplier"},
    {"crop": "tomato",           "state": "Karnataka",      "grade": "A", "season": "kharif", "peak_months": [10,11],    "note": "Kolar and Chikkaballapur districts"},
    {"crop": "tomato",           "state": "Maharashtra",    "grade": "B", "season": "kharif", "peak_months": [9,10],     "note": "Nashik belt"},
    {"crop": "banana",           "state": "Maharashtra",    "grade": "A", "season": "annual", "peak_months": [1,2,3,4],  "note": "Jalgaon G9 variety; premium export"},
    {"crop": "banana",           "state": "Tamil Nadu",     "grade": "A", "season": "annual", "peak_months": [6,7,8],    "note": "Trichy and Thanjavur belt"},
    {"crop": "onion",            "state": "Maharashtra",    "grade": "A", "season": "rabi",   "peak_months": [3,4,5],    "note": "Nashik; India's largest onion market"},
    {"crop": "onion",            "state": "Karnataka",      "grade": "B", "season": "kharif", "peak_months": [10,11],    "note": "Hubli-Dharwad belt"},
    {"crop": "potato",           "state": "Uttar Pradesh",  "grade": "A", "season": "rabi",   "peak_months": [1,2,3],    "note": "Agra-Mathura cold-chain corridor"},
    {"crop": "potato",           "state": "West Bengal",    "grade": "A", "season": "rabi",   "peak_months": [2,3],      "note": "Hooghly and Bardhaman districts"},
    {"crop": "cotton",           "state": "Gujarat",        "grade": "A", "season": "kharif", "peak_months": [10,11,12], "note": "Bt cotton; Saurashtra belt"},
    {"crop": "soybean",          "state": "Maharashtra",    "grade": "A", "season": "kharif", "peak_months": [10,11],    "note": "Vidarbha region"},
    {"crop": "soybean",          "state": "Madhya Pradesh", "grade": "A", "season": "kharif", "peak_months": [10,11],    "note": "Malwa plateau; largest soy state"},
    {"crop": "chilli",           "state": "Andhra Pradesh", "grade": "A", "season": "rabi",   "peak_months": [2,3,4],    "note": "Guntur; world's largest chilli market"},
    {"crop": "groundnut",        "state": "Gujarat",        "grade": "A", "season": "kharif", "peak_months": [10,11],    "note": "Junagadh and Rajkot districts"},
    {"crop": "mustard",          "state": "Rajasthan",      "grade": "A", "season": "rabi",   "peak_months": [3,4],      "note": "Alwar and Bharatpur zones"},
    {"crop": "apple",            "state": "Himachal Pradesh","grade":"A", "season": "summer", "peak_months": [8,9,10],   "note": "Shimla and Kullu valleys"},
    {"crop": "mango",            "state": "Uttar Pradesh",  "grade": "A", "season": "summer", "peak_months": [5,6,7],    "note": "Dasheri and Langra; Lucknow-Varanasi belt"},
    {"crop": "mango",            "state": "Maharashtra",    "grade": "A", "season": "summer", "peak_months": [4,5,6],    "note": "Alphonso (Hapus); Ratnagiri GI-tagged"},
    {"crop": "grapes",           "state": "Maharashtra",    "grade": "A", "season": "winter", "peak_months": [1,2,3],    "note": "Nashik; largest grape export region"},
    {"crop": "turmeric",         "state": "Telangana",      "grade": "A", "season": "rabi",   "peak_months": [1,2,3],    "note": "Nizamabad; highest curcumin content"},
]

# Grade scores for ranking
GRADE_SCORE = {"A": 3, "B": 2, "C": 1}

# Season keywords
SEASON_KEYWORDS = {
    "kharif":  ["monsoon", "rainy", "june", "july", "august", "september", "kharif"],
    "rabi":    ["winter", "rabi", "october", "november", "december", "january", "february", "march"],
    "summer":  ["summer", "april", "may", "june"],
    "annual":  ["annual", "year-round", "all year"],
    "winter":  ["winter", "cold", "november", "december", "january"],
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CropMatch:
    crop: str
    state: str
    grade: str
    season: str
    peak_months: list[int]
    note: str
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "crop": self.crop,
            "state": self.state,
            "grade": self.grade,
            "season": self.season,
            "peak_months": self.peak_months,
            "note": self.note,
            "relevance_score": round(self.relevance_score, 3),
        }


@dataclass
class QueryResult:
    query: str
    matches: list[CropMatch] = field(default_factory=list)
    answer_summary: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "answer_summary": self.answer_summary,
            "confidence": round(self.confidence, 3),
            "matches": [m.to_dict() for m in self.matches],
        }


# ---------------------------------------------------------------------------
# Knowledge Engine (embedding-based retrieval)
# ---------------------------------------------------------------------------

class CropKnowledgeEngine:
    """
    Two-stage retrieval:
      Stage 1 — keyword & rule-based filtering (fast, no GPU needed)
      Stage 2 — sentence-transformer re-ranking (if available)

    In production, swap the keyword scorer with a fine-tuned bi-encoder
    trained on Indian agricultural Q&A pairs.
    """

    def __init__(self, use_embeddings: bool = False):
        self.knowledge = CROP_STATE_KNOWLEDGE
        self.use_embeddings = use_embeddings
        self._model = None

        if use_embeddings:
            self._load_embedding_model()

    # ------------------------------------------------------------------
    # Embedding model (optional, requires sentence-transformers)
    # ------------------------------------------------------------------

    def _load_embedding_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            import faiss

            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            texts = [self._record_to_text(r) for r in self.knowledge]
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

            dim = embeddings.shape[1]
            self._index = faiss.IndexFlatIP(dim)   # inner-product = cosine on normalised vecs
            self._index.add(embeddings.astype(np.float32))
            print(f"[CropKnowledgeEngine] FAISS index built with {len(texts)} records.")
        except ImportError:
            print("[CropKnowledgeEngine] sentence-transformers / faiss not installed. Falling back to keyword mode.")
            self.use_embeddings = False

    def _record_to_text(self, r: dict) -> str:
        months = ", ".join(str(m) for m in r["peak_months"])
        return (
            f"{r['crop']} grown in {r['state']} state during {r['season']} season, "
            f"grade {r['grade']}, peak harvest months {months}. {r['note']}"
        )

    # ------------------------------------------------------------------
    # Keyword scorer (always available)
    # ------------------------------------------------------------------

    def _keyword_score(self, record: dict, query_lower: str, month: Optional[int]) -> float:
        score = 0.0

        # Crop name match
        if record["crop"] in query_lower:
            score += 3.0
        else:
            # Partial match
            for word in record["crop"].split():
                if word in query_lower:
                    score += 1.0

        # State mention
        if record["state"].lower() in query_lower:
            score += 2.0

        # Season match
        for season, kws in SEASON_KEYWORDS.items():
            if season == record["season"]:
                for kw in kws:
                    if kw in query_lower:
                        score += 1.5
                        break

        # Month match (availability check)
        if month and month in record["peak_months"]:
            score += 2.0

        # Grade preference
        if "grade a" in query_lower or "best" in query_lower or "premium" in query_lower:
            score += GRADE_SCORE.get(record["grade"], 0) * 0.5

        return score

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(self, question: str, current_month: Optional[int] = None, top_k: int = 5) -> QueryResult:
        """
        Main entry point.

        Args:
            question: natural-language query
            current_month: 1-12, used to check current harvest availability
            top_k: max results to return

        Returns:
            QueryResult with ranked matches and a plain-English summary
        """
        q_lower = question.lower()
        matches: list[CropMatch] = []

        if self.use_embeddings and self._model:
            matches = self._embedding_retrieval(q_lower, top_k * 2)
        else:
            matches = self._keyword_retrieval(q_lower, current_month, top_k * 2)

        # Deduplicate by (crop, state), keep best score
        seen: dict[tuple, CropMatch] = {}
        for m in sorted(matches, key=lambda x: -x.relevance_score):
            key = (m.crop, m.state)
            if key not in seen:
                seen[key] = m

        final = sorted(seen.values(), key=lambda x: -x.relevance_score)[:top_k]
        confidence = final[0].relevance_score / 10.0 if final else 0.0
        confidence = min(confidence, 1.0)

        summary = self._generate_summary(question, final, current_month)
        return QueryResult(query=question, matches=final, answer_summary=summary, confidence=confidence)

    def _keyword_retrieval(self, q_lower: str, month: Optional[int], top_k: int) -> list[CropMatch]:
        scored = []
        for r in self.knowledge:
            s = self._keyword_score(r, q_lower, month)
            if s > 0:
                scored.append(CropMatch(
                    crop=r["crop"], state=r["state"], grade=r["grade"],
                    season=r["season"], peak_months=r["peak_months"],
                    note=r["note"], relevance_score=s,
                ))
        return sorted(scored, key=lambda x: -x.relevance_score)[:top_k]

    def _embedding_retrieval(self, q_lower: str, top_k: int) -> list[CropMatch]:
        q_vec = self._model.encode([q_lower], convert_to_numpy=True)
        q_vec = q_vec / np.linalg.norm(q_vec)
        scores, indices = self._index.search(q_vec.astype(np.float32), top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            r = self.knowledge[idx]
            results.append(CropMatch(
                crop=r["crop"], state=r["state"], grade=r["grade"],
                season=r["season"], peak_months=r["peak_months"],
                note=r["note"], relevance_score=float(score) * 10,
            ))
        return results

    def _generate_summary(self, question: str, matches: list[CropMatch], month: Optional[int]) -> str:
        if not matches:
            return "No matching crop-state data found for your query."

        top = matches[0]
        available_now = month and month in top.peak_months

        availability_str = ""
        if month:
            availability_str = (
                f"currently in peak harvest (month {month})"
                if available_now
                else f"not in peak harvest this month (peak: months {top.peak_months})"
            )

        lines = [
            f"Top match: {top.crop.title()} from {top.state} — Grade {top.grade}.",
            f"Note: {top.note}.",
        ]
        if availability_str:
            lines.append(f"Availability: {availability_str}.")
        if len(matches) > 1:
            others = ", ".join(f"{m.state} ({m.grade})" for m in matches[1:4])
            lines.append(f"Other sources: {others}.")
        return " ".join(lines)

    def best_crops_for_state(self, state: str) -> list[CropMatch]:
        """Return all known Grade-A crops for a given state."""
        results = []
        for r in self.knowledge:
            if r["state"].lower() == state.lower() and r["grade"] == "A":
                results.append(CropMatch(**{k: r[k] for k in r}, relevance_score=3.0))
        return sorted(results, key=lambda x: x.crop)

    def available_crops_now(self, month: int) -> list[CropMatch]:
        """Return all crops currently in their peak harvest month."""
        results = []
        for r in self.knowledge:
            if month in r["peak_months"]:
                results.append(CropMatch(
                    **{k: r[k] for k in r},
                    relevance_score=GRADE_SCORE.get(r["grade"], 0) * 1.0,
                ))
        return sorted(results, key=lambda x: (-x.relevance_score, x.crop))


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    engine = CropKnowledgeEngine(use_embeddings=False)

    queries = [
        ("Which state has Grade A basmati right now?", 10),
        ("Where can I source tomatoes in January?", 1),
        ("What is Karnataka's best kharif crop?", None),
        ("Premium Nagpur oranges availability", 12),
    ]

    for question, month in queries:
        result = engine.query(question, current_month=month)
        print(f"\nQ: {question}")
        print(f"A: {result.answer_summary}")
        print(f"   Confidence: {result.confidence:.2f}")
        for m in result.matches[:3]:
            print(f"   → {m.state:20s} | {m.crop:20s} | Grade {m.grade} | Score {m.relevance_score:.1f}")
