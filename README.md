# Math Tool

A calculator suite: arithmetic/symbolic calculator, equation solver, graph plotter, area-under-curve, and matrix operations. `engine/` holds all the math (parser, calculator, solver, matrix, graph, integration) and is UI-agnostic — it's used by both frontends below.

## Features

- **Calculator** — evaluate arithmetic and symbolic expressions (`2+2*3`, `sqrt(4)`, `sin(pi/2)`, `2x^2 + 3x - 5`), with history (plus reload chips) and memory (`MC`/`MR`/`M+`/`M-`/`MS`). The Streamlit UI's keypad has three tabs (Algebra / Trigonometry / Calculus) and a SHIFT modifier that arms a key's secondary function for exactly one press (e.g. SHIFT+sin → `asin(`), then auto-resets — see "Parser whitelist" below for what's wired for real vs. a grayed-out placeholder.
- **Equation Solver** — solve algebraic equations
- **Graph Plotter** — plot multiple single-variable functions at once (add/remove/toggle-visible rows, each its own color), with Plotly pan/zoom (`dragmode="pan"`, `scrollZoom`) — Streamlit UI only, see note below
- **Area Under Curve** — numerical/symbolic integration
- **Matrix** — determinant, inverse, and other matrix operations, including solving `Ax = b`

### Parser whitelist (`engine/parser.py`)

Allowed functions: `sin cos tan asin acos atan sqrt log ln exp abs factorial`. Allowed constants: `pi e E oo`. Everything else (`csc/sec/cot` and their inverses, `nCr`/`nPr`, `Σ`, `∫`, `∮`, `lim`, `d/dx`, `C(n,k)`/`P(n,k)`, `Π`) is intentionally **not** in the whitelist yet — the calculator's Trigonometry/Calculus tabs show these as disabled keys reserved for a future phase, rather than wiring them to something that would raise "Unknown function."

> **Frontend parity note:** the SHIFT/tabs calculator and multi-function graph pan/zoom described above were built into the **Streamlit UI** (`ui/calculator.py`, `ui/graph.py`) only. The static HTML/JS frontend (`web/`) still has the earlier flat-keypad calculator and single-function graph — it hasn't been ported to match. `engine/` (including the whitelist extension) is shared by both, so the FastAPI backend's `/api/calculate` etc. already support `asin`/`acos`/`atan`/`factorial`/`oo`; only the `web/` UI itself is behind.

## HTML + FastAPI

A static HTML/CSS/JS frontend (`web/`) calling a FastAPI JSON backend (`api/`).

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Open http://127.0.0.1:8000 — the API serves the frontend directly, no separate dev server needed. API docs (OpenAPI/Swagger) are at `/docs`.

## Streamlit

The original Streamlit UI (`app.py`, `ui/`) is kept alongside the FastAPI backend and currently has the more complete feature set (see the parity note above).

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pip install -r requirements.txt pytest
pytest
```

`tests/test_parser.py` and `tests/test_engine.py` cover `engine/` (golden-value, invariant, and error-path cases). `tests/test_ui_calculator.py` and `tests/test_ui_graph.py` smoke-test the Streamlit UI via `streamlit.testing.v1.AppTest` — SHIFT arm/consume/reset behavior, cosmetic keys staying inert, history chips, and multi-function add/remove/toggle for the graph page.

## Deploying

- **FastAPI**: any ASGI host (Render, Fly.io, Railway, a VM behind `uvicorn`/`gunicorn`). Entry point: `api.main:app`.
- **Streamlit**: [Streamlit Community Cloud](https://streamlit.io/cloud), entry point `app.py`.
