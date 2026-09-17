import streamlit as st
import plotly.graph_objects as go

from engine.parser import parse_expression
from engine.graph import generate_numeric_data
from engine.errors import MathToolError
from engine.history import log_entry
from ui import theme

# Cycled per function row, same order every time so a given row keeps its
# color as others are added/removed.
_PALETTE = ["#5DCBFF", "#FF7A7A", "#6BCB77", "#FFC46B", "#C792EA", "#F78FB3"]


def _new_function() -> dict:
    st.session_state.graph_next_id += 1
    color = _PALETTE[(st.session_state.graph_next_id - 1) % len(_PALETTE)]
    return {"id": st.session_state.graph_next_id, "color": color, "visible": True}


def _add_function() -> None:
    st.session_state.graph_functions.append(_new_function())


def _remove_function(fn_id: int) -> None:
    st.session_state.graph_functions = [
        f for f in st.session_state.graph_functions if f["id"] != fn_id
    ]
    st.session_state.pop(f"graph_expr_{fn_id}", None)


def _toggle_visible(fn_id: int) -> None:
    for f in st.session_state.graph_functions:
        if f["id"] == fn_id:
            f["visible"] = not f["visible"]


def _init_state() -> None:
    st.session_state.setdefault("graph_next_id", 0)
    if "graph_functions" not in st.session_state:
        st.session_state.graph_functions = [_new_function()]


def _render_algebra_panel() -> None:
    st.html('<p class="card-label">Functions</p>')
    for i, fn in enumerate(st.session_state.graph_functions):
        fn_id = fn["id"]
        row = st.columns([0.14, 0.62, 0.12, 0.12], vertical_alignment="center")
        with row[0]:
            st.html(
                f'<div style="width:14px;height:14px;border-radius:50%;'
                f'background:{fn["color"]};margin:auto;'
                f'opacity:{"1" if fn["visible"] else "0.3"}"></div>'
            )
        with row[1]:
            st.text_input(
                f"f{i + 1}(x) =", key=f"graph_expr_{fn_id}",
                placeholder="sin(x) + x^2" if i == 0 else f"e.g. x^{i + 2}",
                label_visibility="collapsed",
            )
        with row[2]:
            st.button(
                "\U0001f441" if fn["visible"] else "\U0001f6ab",
                key=f"graph_toggle_{fn_id}", on_click=_toggle_visible, args=(fn_id,),
                help="Toggle visibility", width="stretch",
            )
        with row[3]:
            st.button(
                "✕", key=f"graph_remove_{fn_id}", on_click=_remove_function,
                args=(fn_id,), help="Remove", width="stretch",
                disabled=len(st.session_state.graph_functions) <= 1,
            )
    st.button("+ Add function", key="graph_add", on_click=_add_function, width="stretch")


def render() -> None:
    theme.page_header(
        "Graph plotter",
        "Graph Plotter",
        "Plot multiple single-variable functions at once. Drag to pan, scroll to zoom.",
    )

    _init_state()

    with theme.card("graph-card"):
        col_panel, col_canvas = st.columns([1, 2.2], gap="medium")

        with col_panel:
            _render_algebra_panel()

            st.html('<div style="height:10px"></div>')
            bound_cols = st.columns(2)
            x_min = bound_cols[0].number_input("x min", value=-10.0, key="graph_xmin")
            x_max = bound_cols[1].number_input("x max", value=10.0, key="graph_xmax")

        with col_canvas:
            if x_max <= x_min:
                theme.note("<strong>Error</strong> — x max must be greater than x min.", err=True)
                return

            fig = go.Figure()
            any_plotted = False
            for i, fn in enumerate(st.session_state.graph_functions):
                if not fn["visible"]:
                    continue
                text = st.session_state.get(f"graph_expr_{fn['id']}", "")
                if not text.strip():
                    continue
                try:
                    expr = parse_expression(text)
                    x_vals, y_vals = generate_numeric_data(expr, x_min, x_max)
                except MathToolError as e:
                    theme.note(
                        f"<strong>f{i + 1}(x) error</strong> — {theme.esc(e)}", err=True
                    )
                    continue
                fig.add_trace(go.Scatter(
                    x=x_vals, y=y_vals, mode="lines", name=f"f{i + 1}(x) = {text}",
                    line=dict(color=fn["color"], width=2),
                ))
                any_plotted = True
                try:
                    log_entry("Graph Plotter", f"f{i + 1}(x)={text}", f"plotted over [{x_min}, {x_max}]")
                except Exception:  # noqa: BLE001 — history is best-effort
                    pass

            fig.update_layout(
                xaxis_title="x",
                yaxis_title="f(x)",
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="#1B1B1B",
                plot_bgcolor="#1B1B1B",
                font=dict(color="#A3A3A3", family="IBM Plex Mono, monospace"),
                xaxis=dict(gridcolor="#2A2A2A", zerolinecolor="#333333"),
                yaxis=dict(gridcolor="#2A2A2A", zerolinecolor="#333333"),
                dragmode="pan",
                legend=dict(orientation="h", y=-0.15),
            )
            st.plotly_chart(
                fig, width="stretch",
                config={"scrollZoom": True, "displaylogo": False},
            )
            if not any_plotted:
                theme.empty_note("Enter a function above to plot it — e.g. sin(x) + x^2, 1/x")
