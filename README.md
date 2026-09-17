# Math Tool

A calculator suite: arithmetic/symbolic calculator, equation solver, graph plotter, area-under-curve, and matrix operations. `engine/` holds all the math (parser, calculator, solver, matrix, graph, integration) and is UI-agnostic — it's used by both frontends below.

## Features

- **Calculator** — evaluate arithmetic and symbolic expressions (`2+2*3`, `sqrt(4)`, `sin(pi/2)`, `2x^2 + 3x - 5`), with history and memory (`MC`/`MR`/`M+`/`M-`/`MS`)
- **Equation Solver** — solve algebraic equations
- **Graph Plotter** — plot single-variable functions
- **Area Under Curve** — numerical/symbolic integration
- **Matrix** — determinant, inverse, and other matrix operations, including solving `Ax = b`

## HTML + FastAPI (current)

A static HTML/CSS/JS frontend (`web/`) calling a FastAPI JSON backend (`api/`).

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Open http://127.0.0.1:8000 — the API serves the frontend directly, no separate dev server needed. API docs (OpenAPI/Swagger) are at `/docs`.

## Streamlit (legacy)

The original Streamlit UI (`app.py`, `ui/`) still works and is kept alongside the FastAPI backend.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pip install -r requirements.txt pytest
pytest
```

Tests cover `engine/` only — both frontends are thin layers on top of it.

## Deploying

- **FastAPI**: any ASGI host (Render, Fly.io, Railway, a VM behind `uvicorn`/`gunicorn`). Entry point: `api.main:app`.
- **Streamlit**: [Streamlit Community Cloud](https://streamlit.io/cloud), entry point `app.py`.
