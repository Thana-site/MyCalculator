"use strict";

// ---------------------------------------------------------------------------
// Small shared helpers
// ---------------------------------------------------------------------------

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value);
  return div.innerHTML;
}

function typeset(el) {
  if (window.MathJax && window.MathJax.typesetPromise) {
    window.MathJax.typesetPromise([el]).catch(() => {});
  }
}

function setLatex(el, latex) {
  el.innerHTML = `\\(${latex}\\)`;
  typeset(el);
}

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Request failed.");
  }
  return data;
}

async function apiRequest(method, path) {
  const res = await fetch(path, { method });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Request failed.");
  }
  return data;
}

function showError(el, message) {
  el.textContent = "";
  const strong = document.createElement("strong");
  strong.textContent = "Error";
  el.appendChild(strong);
  el.appendChild(document.createTextNode(" — " + message));
  el.hidden = false;
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

document.getElementById("nav").addEventListener("click", (e) => {
  const btn = e.target.closest(".nav-item");
  if (!btn) return;
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  const page = btn.dataset.page;
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.getElementById("page-" + page).classList.add("active");
  if (page === "history") History.load();
});

// ---------------------------------------------------------------------------
// Calculator
// ---------------------------------------------------------------------------

const Calc = (() => {
  const HISTORY_LIMIT = 50;

  const els = {
    display: document.getElementById("calc-display"),
    hist: document.getElementById("calc-hist"),
    input: document.getElementById("calc-input"),
    resultCard: document.getElementById("calc-result-card"),
    exact: document.getElementById("calc-exact"),
    numeric: document.getElementById("calc-numeric"),
    error: document.getElementById("calc-error"),
    historyList: document.getElementById("calc-history-list"),
    historyEmpty: document.getElementById("calc-history-empty"),
    clearHistoryBtn: document.getElementById("calc-clear-history"),
    memoryValue: document.getElementById("calc-memory-value"),
    memoryEmpty: document.getElementById("calc-memory-empty"),
  };

  let expression = "";
  let lastResult = null; // {plain, latex, numeric}
  let history = JSON.parse(localStorage.getItem("mathtool_history") || "[]");
  let memory = JSON.parse(localStorage.getItem("mathtool_memory") || "null");

  function persist() {
    localStorage.setItem("mathtool_history", JSON.stringify(history));
    localStorage.setItem("mathtool_memory", JSON.stringify(memory));
  }

  function renderDisplay(prevLine) {
    els.hist.textContent = prevLine || "";
    els.display.textContent = expression || "0";
    els.input.value = expression;
  }

  function renderHistory() {
    els.historyList.innerHTML = "";
    els.historyEmpty.hidden = history.length > 0;
    els.clearHistoryBtn.hidden = history.length === 0;
    for (const entry of history) {
      const div = document.createElement("div");
      div.className = "hist-entry";
      div.innerHTML =
        `<div class="hist-in">${escapeHtml(entry.expr)} =</div>` +
        `<div class="hist-out">${escapeHtml(entry.result)}</div>`;
      els.historyList.appendChild(div);
    }
  }

  function renderMemory() {
    els.memoryEmpty.hidden = memory !== null;
    els.memoryValue.textContent = memory === null ? "" : memory;
  }

  function append(token) {
    expression += token;
    renderDisplay("");
  }

  function clearAll() {
    expression = "";
    lastResult = null;
    els.error.hidden = true;
    els.resultCard.hidden = true;
    renderDisplay("");
  }

  function backspace() {
    expression = expression.slice(0, -1);
    renderDisplay("");
  }

  async function currentValue() {
    if (lastResult) return lastResult.plain;
    if (!expression.trim()) return null;
    try {
      const data = await api("/api/calculate", { expression });
      return data.plain;
    } catch {
      return null;
    }
  }

  async function equals() {
    if (!expression.trim()) return;
    const text = expression;
    let data;
    try {
      data = await api("/api/calculate", { expression: text });
    } catch (err) {
      showError(els.error, err.message);
      return;
    }
    els.error.hidden = true;
    lastResult = data;
    expression = data.plain;
    renderDisplay(text + " =");

    els.resultCard.hidden = false;
    setLatex(els.exact, data.latex);
    els.numeric.textContent = data.numeric;

    history.unshift({ expr: text, result: data.plain });
    history.length = Math.min(history.length, HISTORY_LIMIT);
    persist();
    renderHistory();
  }

  async function useAns() {
    if (lastResult) append(`(${lastResult.plain})`);
  }

  async function memClear() {
    memory = null;
    persist();
    renderMemory();
  }

  async function memRecall() {
    if (memory !== null) append(`(${memory})`);
  }

  async function memStore() {
    const val = await currentValue();
    if (val !== null) {
      memory = val;
      persist();
      renderMemory();
    }
  }

  async function memAdjust(sign) {
    const val = await currentValue();
    if (val === null) return;
    if (memory === null) {
      memory = val;
    } else {
      try {
        const data = await api("/api/calculate", {
          expression: `(${memory})${sign}(${val})`,
        });
        memory = data.plain;
      } catch {
        return;
      }
    }
    persist();
    renderMemory();
  }

  function bindKeypad() {
    document.querySelectorAll("#page-calculator .key[data-tok]").forEach((btn) => {
      btn.addEventListener("click", () => append(btn.dataset.tok));
    });
    document.querySelectorAll("#page-calculator .key[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        if (action === "del") backspace();
        else if (action === "ac") clearAll();
        else if (action === "ans") useAns();
        else if (action === "eq") equals();
      });
    });
    document.querySelectorAll("#calc-mem-row .key[data-mem]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.mem;
        if (action === "mc") memClear();
        else if (action === "mr") memRecall();
        else if (action === "ms") memStore();
        else if (action === "m+") memAdjust("+");
        else if (action === "m-") memAdjust("-");
      });
    });

    els.input.addEventListener("input", () => {
      expression = els.input.value;
      els.display.textContent = expression || "0";
    });
    els.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") equals();
    });

    els.clearHistoryBtn.addEventListener("click", () => {
      history = [];
      persist();
      renderHistory();
    });

    document.getElementById("calc-side-tabs").addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-tab]");
      if (!btn) return;
      document.querySelectorAll("#calc-side-tabs button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const tab = btn.dataset.tab;
      document.getElementById("calc-history-panel").hidden = tab !== "history";
      document.getElementById("calc-memory-panel").hidden = tab !== "memory";
    });
  }

  function init() {
    bindKeypad();
    renderDisplay("");
    renderHistory();
    renderMemory();
  }

  return { init };
})();

// ---------------------------------------------------------------------------
// Equation Solver
// ---------------------------------------------------------------------------

const Solver = (() => {
  const els = {
    input: document.getElementById("solver-input"),
    variableRow: document.getElementById("solver-variable-row"),
    variableSelect: document.getElementById("solver-variable"),
    result: document.getElementById("solver-result"),
    solvingFor: document.getElementById("solver-solving-for"),
    exact: document.getElementById("solver-exact"),
    numeric: document.getElementById("solver-numeric"),
    error: document.getElementById("solver-error"),
  };

  async function solve(variable) {
    els.error.hidden = true;
    const text = els.input.value;
    if (!text.trim()) {
      els.result.hidden = true;
      els.variableRow.hidden = true;
      return;
    }
    let data;
    try {
      data = await api("/api/solve", { equation: text, variable: variable || null });
    } catch (err) {
      showError(els.error, err.message);
      els.result.hidden = true;
      return;
    }

    if (data.needs_variable) {
      els.variableRow.hidden = false;
      els.variableSelect.innerHTML = data.symbols
        .map((s) => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`)
        .join("");
      els.result.hidden = true;
      return;
    }

    els.variableRow.hidden = data.symbols.length <= 1;
    els.solvingFor.textContent = `Solving for ${data.variable}`;
    els.exact.innerHTML = data.exact.length
      ? data.exact.map((s) => `<div>\\(${s.latex}\\)</div>`).join("")
      : "No solution found.";
    typeset(els.exact);
    els.numeric.innerHTML = data.numeric
      .map((n, i) => `<div>x_${i + 1} = ${n === null ? "(not numeric)" : escapeHtml(n)}</div>`)
      .join("");
    els.result.hidden = false;
  }

  function init() {
    let debounce;
    els.input.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => solve(null), 300);
    });
    els.variableSelect.addEventListener("change", () => solve(els.variableSelect.value));
  }

  return { init };
})();

// ---------------------------------------------------------------------------
// Graph Plotter
// ---------------------------------------------------------------------------

const Graph = (() => {
  const els = {
    input: document.getElementById("graph-input"),
    xmin: document.getElementById("graph-xmin"),
    xmax: document.getElementById("graph-xmax"),
    plot: document.getElementById("graph-plot"),
    error: document.getElementById("graph-error"),
  };

  const layout = {
    xaxis: { title: "x", gridcolor: "#2A2A2A", zerolinecolor: "#333333" },
    yaxis: { title: "f(x)", gridcolor: "#2A2A2A", zerolinecolor: "#333333" },
    margin: { l: 50, r: 10, t: 10, b: 40 },
    paper_bgcolor: "#1B1B1B",
    plot_bgcolor: "#1B1B1B",
    font: { color: "#A3A3A3", family: "IBM Plex Mono, monospace" },
  };

  async function update() {
    els.error.hidden = true;
    const text = els.input.value;
    const xMin = parseFloat(els.xmin.value);
    const xMax = parseFloat(els.xmax.value);
    if (!text.trim()) {
      Plotly.purge(els.plot);
      return;
    }
    if (!(xMax > xMin)) {
      showError(els.error, "x max must be greater than x min.");
      return;
    }
    let data;
    try {
      data = await api("/api/graph", { expression: text, x_min: xMin, x_max: xMax });
    } catch (err) {
      showError(els.error, err.message);
      return;
    }
    Plotly.newPlot(
      els.plot,
      [{ x: data.x, y: data.y, mode: "lines", line: { color: "#5DCBFF", width: 2 }, name: text }],
      layout,
      { displayModeBar: true, responsive: true }
    );
  }

  function init() {
    let debounce;
    const onChange = () => {
      clearTimeout(debounce);
      debounce = setTimeout(update, 300);
    };
    els.input.addEventListener("input", onChange);
    els.xmin.addEventListener("input", onChange);
    els.xmax.addEventListener("input", onChange);
  }

  return { init };
})();

// ---------------------------------------------------------------------------
// Area Under Curve
// ---------------------------------------------------------------------------

const Area = (() => {
  const els = {
    input: document.getElementById("area-input"),
    a: document.getElementById("area-a"),
    b: document.getElementById("area-b"),
    plot: document.getElementById("area-plot"),
    error: document.getElementById("area-error"),
    resultCard: document.getElementById("area-result-card"),
    result: document.getElementById("area-result"),
    modeRow: document.getElementById("area-mode"),
  };

  let mode = "signed";

  const layout = {
    xaxis: { title: "x", gridcolor: "#2A2A2A", zerolinecolor: "#333333" },
    yaxis: { title: "f(x)", gridcolor: "#2A2A2A", zerolinecolor: "#333333" },
    margin: { l: 50, r: 10, t: 10, b: 40 },
    paper_bgcolor: "#1B1B1B",
    plot_bgcolor: "#1B1B1B",
    font: { color: "#A3A3A3", family: "IBM Plex Mono, monospace" },
    showlegend: false,
  };

  async function update() {
    els.error.hidden = true;
    const text = els.input.value;
    const a = parseFloat(els.a.value);
    const b = parseFloat(els.b.value);
    if (!text.trim()) {
      Plotly.purge(els.plot);
      els.resultCard.hidden = true;
      return;
    }
    if (!(b > a)) {
      showError(els.error, "b must be greater than a.");
      return;
    }
    let data;
    try {
      data = await api("/api/area", { expression: text, a, b, mode });
    } catch (err) {
      showError(els.error, err.message);
      els.resultCard.hidden = true;
      return;
    }
    Plotly.newPlot(
      els.plot,
      [
        { x: data.x, y: data.y, mode: "lines", line: { color: "#5DCBFF", width: 2 } },
        { x: data.x, y: data.y, fill: "tozeroy", mode: "none", fillcolor: "rgba(93, 203, 255, 0.18)" },
      ],
      layout,
      { displayModeBar: true, responsive: true }
    );
    els.resultCard.hidden = false;
    setLatex(els.result, data.latex);
  }

  function init() {
    let debounce;
    const onChange = () => {
      clearTimeout(debounce);
      debounce = setTimeout(update, 300);
    };
    els.input.addEventListener("input", onChange);
    els.a.addEventListener("input", onChange);
    els.b.addEventListener("input", onChange);
    els.modeRow.addEventListener("click", (e) => {
      const btn = e.target.closest(".pill");
      if (!btn) return;
      document.querySelectorAll("#area-mode .pill").forEach((p) => p.classList.remove("selected"));
      btn.classList.add("selected");
      mode = btn.dataset.mode;
      update();
    });
  }

  return { init };
})();

// ---------------------------------------------------------------------------
// Matrix
// ---------------------------------------------------------------------------

const Matrix = (() => {
  function renderEigen(el, eigenvalues) {
    el.innerHTML = eigenvalues
      .map((e) => `<div>\\(${e.latex}\\) &nbsp; (&times;${e.multiplicity})</div>`)
      .join("");
    typeset(el);
  }

  function initSingle() {
    const matrixInput = document.getElementById("matrix-a-single");
    const opSelect = document.getElementById("matrix-op-single");
    const result = document.getElementById("matrix-single-result");
    const error = document.getElementById("matrix-single-error");

    async function update() {
      error.hidden = true;
      const text = matrixInput.value;
      if (!text.trim()) {
        result.innerHTML = "";
        return;
      }
      try {
        const data = await api("/api/matrix/single", { matrix: text, operation: opSelect.value });
        if (data.eigenvalues) renderEigen(result, data.eigenvalues);
        else if (data.latex) setLatex(result, data.latex);
        else result.textContent = data.plain;
      } catch (err) {
        result.innerHTML = "";
        showError(error, err.message);
      }
    }

    let debounce;
    matrixInput.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(update, 300);
    });
    opSelect.addEventListener("change", update);
  }

  function initTwo() {
    const aInput = document.getElementById("matrix-a-two");
    const bInput = document.getElementById("matrix-b-two");
    const opSelect = document.getElementById("matrix-op-two");
    const result = document.getElementById("matrix-two-result");
    const error = document.getElementById("matrix-two-error");

    async function update() {
      error.hidden = true;
      if (!aInput.value.trim() || !bInput.value.trim()) {
        result.innerHTML = "";
        return;
      }
      try {
        const data = await api("/api/matrix/two", {
          matrix_a: aInput.value, matrix_b: bInput.value, operation: opSelect.value,
        });
        setLatex(result, data.latex);
      } catch (err) {
        result.innerHTML = "";
        showError(error, err.message);
      }
    }

    let debounce;
    [aInput, bInput].forEach((el) =>
      el.addEventListener("input", () => {
        clearTimeout(debounce);
        debounce = setTimeout(update, 300);
      })
    );
    opSelect.addEventListener("change", update);
  }

  function initSolve() {
    const aInput = document.getElementById("matrix-a-solve");
    const bInput = document.getElementById("matrix-b-solve");
    const result = document.getElementById("matrix-solve-result");
    const error = document.getElementById("matrix-solve-error");

    async function update() {
      error.hidden = true;
      if (!aInput.value.trim() || !bInput.value.trim()) {
        result.innerHTML = "";
        return;
      }
      try {
        const data = await api("/api/matrix/solve", { matrix_a: aInput.value, vector_b: bInput.value });
        setLatex(result, data.latex);
      } catch (err) {
        result.innerHTML = "";
        showError(error, err.message);
      }
    }

    let debounce;
    [aInput, bInput].forEach((el) =>
      el.addEventListener("input", () => {
        clearTimeout(debounce);
        debounce = setTimeout(update, 300);
      })
    );
  }

  function initTabs() {
    document.getElementById("matrix-tabs").addEventListener("click", (e) => {
      const btn = e.target.closest(".tab-btn");
      if (!btn) return;
      document.querySelectorAll("#matrix-tabs .tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.querySelectorAll(".matrix-tab").forEach((panel) => (panel.hidden = true));
      document.getElementById(`matrix-tab-${btn.dataset.tab}`).hidden = false;
    });
  }

  function init() {
    initTabs();
    initSingle();
    initTwo();
    initSolve();
  }

  return { init };
})();

// ---------------------------------------------------------------------------
// History
// ---------------------------------------------------------------------------

const History = (() => {
  const els = {
    filter: document.getElementById("history-filter"),
    clearBtn: document.getElementById("history-clear-btn"),
    list: document.getElementById("history-list"),
    empty: document.getElementById("history-empty"),
  };

  async function load() {
    const mode = els.filter.value;
    const qs = mode ? `?mode=${encodeURIComponent(mode)}` : "";
    let data;
    try {
      data = await apiRequest("GET", `/api/history${qs}`);
    } catch {
      return;
    }
    els.list.innerHTML = "";
    els.empty.hidden = data.entries.length > 0;
    for (const entry of data.entries) {
      const div = document.createElement("div");
      div.className = "hist-entry";
      div.innerHTML =
        `<div class="hist-in">${escapeHtml(entry.mode)} &middot; ${escapeHtml(entry.created_at.replace("T", " "))}<br>` +
        `${escapeHtml(entry.input)}</div>` +
        `<div class="hist-out">${escapeHtml(entry.result)}</div>`;
      els.list.appendChild(div);
    }
  }

  function init() {
    els.filter.addEventListener("change", load);
    els.clearBtn.addEventListener("click", async () => {
      const mode = els.filter.value;
      const qs = mode ? `?mode=${encodeURIComponent(mode)}` : "";
      await apiRequest("DELETE", `/api/history${qs}`);
      load();
    });
  }

  return { init, load };
})();

// ---------------------------------------------------------------------------

Calc.init();
Solver.init();
Graph.init();
Area.init();
Matrix.init();
History.init();
