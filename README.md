# Math Tool

A Streamlit-based calculator suite: arithmetic/symbolic calculator, equation solver, graph plotter, area-under-curve, and matrix operations.

## Features

- **Calculator** — evaluate arithmetic and symbolic expressions (`2+2*3`, `sqrt(4)`, `sin(pi/2)`, `2x^2 + 3x - 5`)
- **Equation Solver** — solve algebraic equations
- **Graph Plotter** — plot single-variable functions
- **Area Under Curve** — numerical/symbolic integration
- **Matrix** — determinant, inverse, and other matrix operations, including solving `Ax = b`

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
pip install -r requirements.txt pytest
pytest
```

## Deploying

This app is ready to deploy on [Streamlit Community Cloud](https://streamlit.io/cloud): point it at this repo with `app.py` as the entry point.
