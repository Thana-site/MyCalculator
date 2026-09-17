# Math Tool

A calculator suite: arithmetic/symbolic calculator, equation solver, graph plotter, area-under-curve, matrix operations, and a persistent calculation history. `engine/` holds all the math (parser, calculator, solver, matrix, graph, integration, history) and is UI-agnostic — it's used by both frontends below, and they **share the same `data/history.db`** if you run them from the same folder.

## Features

- **Calculator** — evaluate arithmetic and symbolic expressions (`2+2*3`, `sqrt(4)`, `sin(pi/2)`, `2x^2 + 3x - 5`), with history (plus reload chips) and memory (`MC`/`MR`/`M+`/`M-`/`MS`). Both frontends' keypads have three tabs (Algebra / Trigonometry / Calculus) and a SHIFT modifier that arms a key's secondary function for exactly one press (e.g. SHIFT+sin → `asin(`), then auto-resets — see "Parser whitelist" below for what's wired for real vs. a grayed-out placeholder.
- **Equation Solver** — solve algebraic equations
- **Graph Plotter** — plot multiple single-variable functions at once (add/remove/toggle-visible rows, each its own color), with Plotly pan/zoom (`dragmode="pan"`, `scrollZoom`) — in both frontends
- **Area Under Curve** — numerical/symbolic integration
- **Matrix** — determinant, inverse, and other matrix operations, including solving `Ax = b`. The Streamlit UI uses a grid/table editor (`st.data_editor`) you can paste directly from Excel/Sheets into, instead of typing bracket syntax — see the parity note below
- **History** — every successful calculation, across every mode, is logged to a local SQLite database (`data/history.db`) and browsable/filterable/clearable from a dedicated History page in both frontends

### Parser whitelist (`engine/parser.py`)

Allowed functions: `sin cos tan asin acos atan sqrt log ln exp abs factorial`. Allowed constants: `pi e E oo`. Everything else (`csc/sec/cot` and their inverses, `nCr`/`nPr`, `Σ`, `∫`, `∮`, `lim`, `d/dx`, `C(n,k)`/`P(n,k)`, `Π`) is intentionally **not** in the whitelist yet — the calculator's Trigonometry/Calculus tabs show these as disabled keys reserved for a future phase, rather than wiring them to something that would raise "Unknown function." (Same key set, same shift-mappings, same disabled list in both frontends.)

`parse_matrix()` (bracket-text: `[[1,2],[3,4]]`) and `matrix_from_grid()` (a 2D list of cell strings, e.g. from a UI grid editor) both funnel through a shared private helper (`_matrix_from_str_rows()`), so the two input paths can never silently diverge in validation/parsing behavior.

> **Frontend parity note:** the SHIFT/tabs calculator, multi-function graph (pan/zoom, add/remove/toggle), and History are now at parity between both frontends — same key layout, same behavior, same shared `data/history.db`. The **one remaining gap** is the matrix grid editor (`st.data_editor`, paste-from-Excel): that's Streamlit-only (`ui/matrix.py`). The HTML frontend's Matrix page still uses bracket-text input (`[[1,2],[3,4]]`) — functionally equivalent (same `engine/parser.py` underneath), just a different UI.

## HTML + FastAPI

A static HTML/CSS/JS frontend (`web/`) calling a FastAPI JSON backend (`api/`).

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Open http://127.0.0.1:8000 — the API serves the frontend directly, no separate dev server needed. API docs (OpenAPI/Swagger) are at `/docs`.

## Streamlit

The original Streamlit UI (`app.py`, `ui/`) is kept alongside the FastAPI backend. Its only remaining edge over the HTML frontend is the matrix grid editor (see the parity note above).

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pip install -r requirements.txt pytest
pytest
```

- `tests/test_parser.py`, `tests/test_engine.py` — `engine/` golden-value, invariant, and error-path cases (including `matrix_from_grid()` parity with `parse_matrix()`)
- `tests/test_history.py` — `engine/history.py` round-trip, filtering, and clearing, isolated from the real `data/history.db` via `monkeypatch`
- `tests/test_ui_calculator.py`, `tests/test_ui_graph.py` — smoke-test the Streamlit UI via `streamlit.testing.v1.AppTest` (SHIFT arm/consume/reset, cosmetic keys staying inert, history chips reading real `engine.history`, multi-function add/remove/toggle), also DB-isolated

## Deploying

- **FastAPI**: any ASGI host (Render, Fly.io, Railway, a VM behind `uvicorn`/`gunicorn`). Entry point: `api.main:app`.
- **Streamlit**: [Streamlit Community Cloud](https://streamlit.io/cloud), entry point `app.py`.
- Either way, `data/` (the SQLite history file) needs a writable, persistent volume if you want history to survive restarts/redeploys.
