## Route Optimization Model (Road + Rail + Claude explanations)

This project is a working MVP of your “route optimizer”:

- Graph routing (Dijkstra) across a demo Indian road + rail network
- Optimization criteria: fastest (`time`), cheapest (`toll/fare`), or shortest (`km`)
- Routing modes: road only, rail only, or road+rail
- Rule-based “live alerts” + cargo intelligence panel
- Interactive SVG map in the browser
- Google Maps (real India map + real route rendering) when you add a Google Maps API key
- Claude-backed natural-language route briefing (optional; uses `ANTHROPIC_API_KEY`)

### Run locally

1. Create a virtualenv and install dependencies:
   - `python -m venv .venv`
   - `./.venv/Scripts/Activate.ps1` (Windows)
   - `pip install -r requirements.txt`
2. Configure environment variables (optional):
   - Copy `.env.example` to `.env`
   - Set `ANTHROPIC_API_KEY` if you want Claude explanations
3. Start the server:
   - `python -m uvicorn backend.main:app --reload --port 8000`
4. Open:
   - `http://localhost:8000`

### Enable Google Maps (real India map + real routes)

1. Get a Google Maps API key and enable:
   - Maps JavaScript API
   - Directions API
2. Put your key into `frontend/config.js`:
   - `window.GMAPS_API_KEY = "YOUR_KEY_HERE";`

### Notes

- The network data in `backend/graph_data.py` is a demo dataset. Replace it with your real 21-city road/rail edges when ready.
- The ML component is “weight adjuster ready” but defaults to synthetic training (so the app works out of the box). See `backend/ml_weight_adjuster.py`.

