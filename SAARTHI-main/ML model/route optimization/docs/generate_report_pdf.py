from pathlib import Path

report_lines = [
    'Route Optimization Model - Implementation Report',
    '',
    'Project Objective',
    '- Build an end-to-end route optimizer using graph algorithms (Dijkstra) on Indian road/rail network.',
    '- Add AI-generated natural language route explanations.',
    '- Provide interactive map visualization and route overlays.',
    '',
    'Backend Delivered (FastAPI)',
    '- API endpoints: GET /api/graph and POST /api/route.',
    '- Graph engine supports optimization by time, cost, and distance.',
    '- Route modes: road only, rail only, and road+rail.',
    '- Segment-wise output with totals (time, INR cost, distance).',
    '- Rule-based alerts for major NH advisory patterns.',
    '- Cargo intelligence advisory module integrated.',
    '',
    'Graph & Routing Core',
    '- Implemented weighted graph traversal with Dijkstra.',
    '- Unified adjacency representation for road and rail edges.',
    '- Dynamic objective switching at runtime:',
    '  * time -> fastest route',
    '  * cost -> cheapest route (toll/fare)',
    '  * km -> shortest route',
    '- Supports mixed-mode pathfinding in road_rail mode.',
    '',
    'Data Layer',
    '- Added demo 21-city India network model with road + rail edges.',
    '- Edge schema includes: id, from_city, to_city, type, label, distance_km, time_hours, cost_inr.',
    '- City coordinate dictionaries prepared for map rendering.',
    '',
    'Cargo System Upgrade (as requested)',
    '- Replaced simple cargo list with 10 categorized cargo groups and sub-types:',
    '  1) Perishable Goods',
    '  2) Non-Perishable Goods',
    '  3) Fragile Goods',
    '  4) Hazardous Materials (Hazmat)',
    '  5) Livestock',
    '  6) Heavy / Bulk Cargo',
    '  7) High-Value Goods',
    '  8) General Cargo',
    '  9) Oversized Cargo',
    ' 10) Liquid Cargo',
    '- Frontend sends cargo as "Category|Item"; backend parses and tailors advisory notes.',
    '',
    'AI Route Briefing',
    '- Added Claude integration via Anthropic Messages API.',
    '- Prompt grounded on computed route facts only (anti-hallucination instruction).',
    '- Added deterministic fallback explanation when API key is absent/unavailable.',
    '',
    'ML Component',
    '- Added optional ML weight adjuster module for time/cost multipliers.',
    '- Synthetic training pipeline included so feature works out-of-the-box.',
    '- Artifact schema checks and retraining guard implemented for feature mismatch recovery.',
    '- Updated ML cargo handling to align with new category format.',
    '',
    'Map Integration Evolution',
    '- Replaced custom SVG network panel with real map container.',
    '- Google Maps route rendering integrated (when key is available).',
    '- Added no-key fallback path:',
    '  * OpenStreetMap tiles via Leaflet',
    '  * OSRM routing for drivable paths',
    '  * polyline fallback when OSRM is unavailable or for rail-only visualization',
    '',
    'Frontend Delivered',
    '- Route builder panel with origin, destination, mode, optimize-by, cargo type, ML toggle, month.',
    '- API response rendering: explanation, totals, alerts, cargo notes, and segment table.',
    '- Automatic map provider behavior:',
    '  * If GMAPS_API_KEY exists -> Google Maps',
    '  * Else -> OpenStreetMap fallback (no API key)',
    '',
    'Reliability & Debugging Work Completed',
    '- Fixed backend reload crash caused by stale import after cargo module refactor.',
    '- Fixed ML artifact feature-length mismatch handling.',
    '- Corrected route behavior for Nashik->Pune timing example in demo data.',
    '- Preserved API compatibility while extending cargo and map functionality.',
    '',
    'Key Files Created/Updated',
    '- backend/main.py, backend/router.py, backend/graph_data.py',
    '- backend/alerts.py, backend/cargo.py, backend/llm.py, backend/ml_weight_adjuster.py',
    '- frontend/index.html, frontend/app.js, frontend/styles.css, frontend/config.js',
    '- README.md, .env.example, requirements.txt',
    '',
    'How to Run',
    '1. Start server: python -m uvicorn backend.main:app --reload --port 8000',
    '2. Open: http://127.0.0.1:8000',
    '3. Optional Google mode: set frontend/config.js -> window.GMAPS_API_KEY="YOUR_KEY"',
    '4. Without key, OpenStreetMap fallback is used automatically.',
    '',
    'Current Status',
    '- End-to-end MVP is implemented and operational.',
    '- Supports routing, cargo advisories, alerts, AI explanation fallback, and map visualization.',
]


def esc_pdf_text(s: str) -> str:
    return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def build_pdf(lines, output_path: Path):
    width, height = 595, 842  # A4 points
    top_margin = 50
    left_margin = 45
    line_h = 14
    usable_lines = int((height - 2 * top_margin) // line_h)

    pages = []
    for i in range(0, len(lines), usable_lines):
        chunk = lines[i:i + usable_lines]
        y = height - top_margin
        content = ['BT', '/F1 11 Tf']
        for line in chunk:
            content.append(f'1 0 0 1 {left_margin} {y} Tm ({esc_pdf_text(line)}) Tj')
            y -= line_h
        content.append('ET')
        pages.append('\n'.join(content).encode('latin-1', errors='replace'))

    objs = []
    # 1: Catalog, 2: Pages
    objs.append(b'<< /Type /Catalog /Pages 2 0 R >>')

    # We'll add page and content objects dynamically.
    page_obj_nums = []
    content_obj_nums = []

    next_obj_num = 3
    for _ in pages:
        page_obj_nums.append(next_obj_num)
        next_obj_num += 1
        content_obj_nums.append(next_obj_num)
        next_obj_num += 1

    # Font object number
    font_obj_num = next_obj_num
    next_obj_num += 1

    kids = ' '.join([f'{n} 0 R' for n in page_obj_nums])
    objs.append(f'<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>'.encode('latin-1'))

    # Add page/content objects
    for idx, content in enumerate(pages):
        pnum = page_obj_nums[idx]
        cnum = content_obj_nums[idx]
        page_obj = (
            f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] '
            f'/Resources << /Font << /F1 {font_obj_num} 0 R >> >> /Contents {cnum} 0 R >>'
        ).encode('latin-1')
        objs.append(page_obj)

        stream = b'<< /Length ' + str(len(content)).encode('latin-1') + b' >>\nstream\n' + content + b'\nendstream'
        objs.append(stream)

    # Font object
    objs.append(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')

    pdf = bytearray()
    pdf.extend(b'%PDF-1.4\n')
    offsets = [0]

    for i, obj in enumerate(objs, start=1):
        offsets.append(len(pdf))
        pdf.extend(f'{i} 0 obj\n'.encode('latin-1'))
        pdf.extend(obj)
        pdf.extend(b'\nendobj\n')

    xref_pos = len(pdf)
    pdf.extend(f'xref\n0 {len(objs)+1}\n'.encode('latin-1'))
    pdf.extend(b'0000000000 65535 f \n')
    for off in offsets[1:]:
        pdf.extend(f'{off:010d} 00000 n \n'.encode('latin-1'))

    pdf.extend(
        (
            f'trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\n'
            f'startxref\n{xref_pos}\n%%EOF\n'
        ).encode('latin-1')
    )

    output_path.write_bytes(pdf)


out = Path('docs') / 'Route_Optimization_Model_Report.pdf'
build_pdf(report_lines, out)
print(str(out.resolve()))
