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

// Function-key definitions per tab. Every key NOT marked cosmetic:true
// inserts a token the engine parser can actually evaluate (see
// engine/parser.py's whitelist) — mirrors ui/calculator.py's _ALGEBRA_ROWS
// / _TRIG_ROWS / _CALCULUS_ROWS exactly, so both frontends offer the same
// functions.
const CALC_TABS = {
  algebra: [
    [
      { key: "alg-x2", label: "x²", tok: "^2", shift: ["√", "sqrt("] },
      { key: "alg-xy", label: "x^y", tok: "^", shift: ["ʸ√x", "^(1/"] },
      { key: "alg-log", label: "log", tok: "log(", shift: ["ln", "ln("] },
      { key: "alg-abs", label: "abs", tok: "abs(", shift: ["eˣ", "exp("] },
    ],
    [
      { key: "alg-fact", label: "n!", tok: "factorial(" },
      { key: "alg-inf", label: "∞", tok: "oo" },
      { key: "alg-ncr", label: "nCr", cosmetic: true },
      { key: "alg-npr", label: "nPr", cosmetic: true },
    ],
    [
      { key: "alg-paren-open", label: "(", tok: "(" },
      { key: "alg-paren-close", label: ")", tok: ")" },
      { key: "alg-pi", label: "π", tok: "pi" },
      { key: "alg-e", label: "e", tok: "e" },
    ],
  ],
  trig: [
    [
      { key: "trig-sin", label: "sin", tok: "sin(", shift: ["sin⁻¹", "asin("] },
      { key: "trig-cos", label: "cos", tok: "cos(", shift: ["cos⁻¹", "acos("] },
      { key: "trig-tan", label: "tan", tok: "tan(", shift: ["tan⁻¹", "atan("] },
      { key: "trig-x2", label: "x²", tok: "^2", shift: ["√", "sqrt("] },
    ],
    [
      { key: "trig-csc", label: "csc", cosmetic: true },
      { key: "trig-sec", label: "sec", cosmetic: true },
      { key: "trig-cot", label: "cot", cosmetic: true },
      { key: "trig-deg", label: "°→rad", tok: "*pi/180" },
    ],
    [
      { key: "trig-paren-open", label: "(", tok: "(" },
      { key: "trig-paren-close", label: ")", tok: ")" },
      { key: "trig-pi", label: "π", tok: "pi" },
      { key: "trig-e", label: "e", tok: "e" },
    ],
  ],
  calculus: [
    [
      { key: "calc-ddx", label: "d/dx", cosmetic: true },
      { key: "calc-int", label: "∫", cosmetic: true },
      { key: "calc-oint", label: "∮", cosmetic: true },
      { key: "calc-sum", label: "Σ", cosmetic: true },
    ],
    [
      { key: "calc-prod", label: "Π", cosmetic: true },
      { key: "calc-lim", label: "lim", cosmetic: true },
      { key: "calc-cnk", label: "C(n,k)", cosmetic: true },
      { key: "calc-pnk", label: "P(n,k)", cosmetic: true },
    ],
    [
      { key: "calc-fact", label: "n!", tok: "factorial(" },
      { key: "calc-inf", label: "∞", tok: "oo" },
      { key: "calc-log", label: "log", tok: "log(", shift: ["ln", "ln("] },
      { key: "calc-paren-open", label: "(", tok: "(" },
    ],
  ],
};

const Calc = (() => {
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
    shiftBtn: document.getElementById("calc-shift-btn"),
    shiftIndicator: document.getElementById("calc-shift-indicator"),
    fnTabs: document.getElementById("calc-fn-tabs"),
    fnGrid: document.getElementById("calc-sci-grid"),
  };

  let expression = "";
  let lastResult = null; // {plain, latex, numeric}
  let shiftActive = false;
  let currentFnTab = "algebra";
  let memory = JSON.parse(localStorage.getItem("mathtool_memory") || "null");

  function persistMemory() {
    localStorage.setItem("mathtool_memory", JSON.stringify(memory));
  }

  function renderDisplay(prevLine) {
    els.hist.textContent = prevLine || "";
    els.display.textContent = expression || "0";
    els.input.value = expression;
  }

  function setShift(on) {
    shiftActive = on;
    els.shiftBtn.classList.toggle("active", on);
    els.shiftIndicator.classList.toggle("shift-on", on);
  }

  async function refreshHistory() {
    let data;
    try {
      data = await apiRequest("GET", "/api/history?mode=Calculator&limit=50");
    } catch {
      return;
    }
    els.historyList.innerHTML = "";
    els.historyEmpty.hidden = data.entries.length > 0;
    els.clearHistoryBtn.hidden = data.entries.length === 0;
    for (const entry of data.entries) {
      const div = document.createElement("div");
      div.className = "hist-entry";
      div.innerHTML =
        `<div class="hist-in">${escapeHtml(entry.input)} =</div>` +
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

  // Any keypress — not just function keys — cancels an armed SHIFT,
  // matching a physical calculator (SHIFT + digit isn't a real
  // combination, so it shouldn't stay armed for the next press).
  function pressDigit(token) {
    append(token);
    setShift(false);
  }

  function pressFunctionKey(keydef) {
    const tok = shiftActive && keydef.shift ? keydef.shift[1] : keydef.tok;
    append(tok);
    setShift(false);
  }

  function clearAll() {
    expression = "";
    lastResult = null;
    els.error.hidden = true;
    els.resultCard.hidden = true;
    setShift(false);
    renderDisplay("");
  }

  function backspace() {
    expression = expression.slice(0, -1);
    setShift(false);
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
    setShift(false);
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

    refreshHistory(); // /api/calculate already logged this server-side
  }

  async function useAns() {
    if (lastResult) append(`(${lastResult.plain})`);
    setShift(false);
  }

  async function memClear() {
    memory = null;
    persistMemory();
    renderMemory();
    setShift(false);
  }

  async function memRecall() {
    if (memory !== null) append(`(${memory})`);
    setShift(false);
  }

  async function memStore() {
    const val = await currentValue();
    if (val !== null) {
      memory = val;
      persistMemory();
      renderMemory();
    }
    setShift(false);
  }

  async function memAdjust(sign) {
    const val = await currentValue();
    if (val !== null) {
      if (memory === null) {
        memory = val;
      } else {
        try {
          const data = await api("/api/calculate", {
            expression: `(${memory})${sign}(${val})`,
          });
          memory = data.plain;
        } catch {
          setShift(false);
          return;
        }
      }
      persistMemory();
      renderMemory();
    }
    setShift(false);
  }

  function renderFnGrid() {
    els.fnGrid.innerHTML = "";
    for (const row of CALC_TABS[currentFnTab]) {
      for (const keydef of row) {
        const btn = document.createElement("button");
        btn.className = "key";
        btn.textContent = keydef.label;
        if (keydef.cosmetic) {
          btn.disabled = true;
          btn.title = "Reserved for a future phase";
        } else {
          if (keydef.shift) btn.title = `SHIFT → ${keydef.shift[0]}`;
          btn.addEventListener("click", () => pressFunctionKey(keydef));
        }
        els.fnGrid.appendChild(btn);
      }
    }
  }

  function bindKeypad() {
    document.querySelectorAll("#page-calculator .key-grid.cols-5 .key[data-tok]").forEach((btn) => {
      btn.addEventListener("click", () => pressDigit(btn.dataset.tok));
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

    els.shiftBtn.addEventListener("click", () => setShift(!shiftActive));

    els.fnTabs.addEventListener("click", (e) => {
      const btn = e.target.closest(".tab-btn");
      if (!btn) return;
      document.querySelectorAll("#calc-fn-tabs .tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentFnTab = btn.dataset.fnTab;
      setShift(false);
      renderFnGrid();
    });

    els.input.addEventListener("input", () => {
      expression = els.input.value;
      els.display.textContent = expression || "0";
    });
    els.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") equals();
    });

    els.clearHistoryBtn.addEventListener("click", async () => {
      await apiRequest("DELETE", "/api/history?mode=Calculator");
      refreshHistory();
    });

    document.getElementById("calc-side-tabs").addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-tab]");
      if (!btn) return;
      document.querySelectorAll("#calc-side-tabs button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const tab = btn.dataset.tab;
      document.getElementById("calc-history-panel").hidden = tab !== "history";
      document.getElementById("calc-memory-panel").hidden = tab !== "memory";
      if (tab === "history") refreshHistory();
    });
  }

  function init() {
    renderFnGrid();
    bindKeypad();
    renderDisplay("");
    refreshHistory();
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
// Graph Plotter (multiple functions, pan/zoom)
// ---------------------------------------------------------------------------

const GRAPH_PALETTE = ["#5DCBFF", "#FF7A7A", "#6BCB77", "#FFC46B", "#C792EA", "#F78FB3"];

const Graph = (() => {
  const els = {
    fnList: document.getElementById("graph-fn-list"),
    addBtn: document.getElementById("graph-add-fn"),
    xmin: document.getElementById("graph-xmin"),
    xmax: document.getElementById("graph-xmax"),
    plot: document.getElementById("graph-plot"),
    error: document.getElementById("graph-error"),
    empty: document.getElementById("graph-empty"),
  };

  const layout = {
    xaxis: { title: "x", gridcolor: "#2A2A2A", zerolinecolor: "#333333" },
    yaxis: { title: "f(x)", gridcolor: "#2A2A2A", zerolinecolor: "#333333" },
    margin: { l: 50, r: 10, t: 10, b: 40 },
    paper_bgcolor: "#1B1B1B",
    plot_bgcolor: "#1B1B1B",
    font: { color: "#A3A3A3", family: "IBM Plex Mono, monospace" },
    dragmode: "pan",
    legend: { orientation: "h", y: -0.15 },
  };

  let nextId = 0;
  let functions = []; // {id, color, visible}
  let debounce;

  function newFunction() {
    nextId += 1;
    return { id: nextId, color: GRAPH_PALETTE[(nextId - 1) % GRAPH_PALETTE.length], visible: true };
  }

  function renderFnList() {
    els.fnList.innerHTML = "";
    functions.forEach((fn, i) => {
      const row = document.createElement("div");
      row.className = "fn-row" + (fn.visible ? "" : " fn-hidden");

      const dot = document.createElement("span");
      dot.className = "color-dot";
      dot.style.background = fn.color;
      dot.style.opacity = fn.visible ? "1" : "0.3";
      dot.title = "Toggle visibility";
      dot.addEventListener("click", () => {
        fn.visible = !fn.visible;
        renderFnList();
        scheduleUpdate(true);
      });

      const input = document.createElement("input");
      input.className = "fn-input";
      input.placeholder = i === 0 ? "sin(x) + x^2" : `e.g. x^${i + 2}`;
      input.value = fn.expr || "";
      input.addEventListener("input", () => {
        fn.expr = input.value;
        scheduleUpdate();
      });

      const removeBtn = document.createElement("button");
      removeBtn.textContent = "✕";
      removeBtn.title = "Remove";
      removeBtn.disabled = functions.length <= 1;
      removeBtn.addEventListener("click", () => {
        functions = functions.filter((f) => f.id !== fn.id);
        renderFnList();
        scheduleUpdate(true);
      });

      row.appendChild(dot);
      row.appendChild(input);
      row.appendChild(removeBtn);
      els.fnList.appendChild(row);
    });
  }

  function scheduleUpdate(immediate) {
    clearTimeout(debounce);
    if (immediate) update();
    else debounce = setTimeout(update, 300);
  }

  async function update() {
    els.error.hidden = true;
    const xMin = parseFloat(els.xmin.value);
    const xMax = parseFloat(els.xmax.value);
    if (!(xMax > xMin)) {
      showError(els.error, "x max must be greater than x min.");
      return;
    }

    const traces = [];
    let anyError = false;
    for (let i = 0; i < functions.length; i++) {
      const fn = functions[i];
      if (!fn.visible || !fn.expr || !fn.expr.trim()) continue;
      let data;
      try {
        data = await api("/api/graph", { expression: fn.expr, x_min: xMin, x_max: xMax });
      } catch (err) {
        showError(els.error, `f${i + 1}(x) error — ${err.message}`);
        anyError = true;
        continue;
      }
      traces.push({
        x: data.x, y: data.y, mode: "lines",
        line: { color: fn.color, width: 2 },
        name: `f${i + 1}(x) = ${fn.expr}`,
      });
    }
    if (!anyError) els.error.hidden = true;

    els.empty.hidden = traces.length > 0;
    if (traces.length === 0) {
      Plotly.purge(els.plot);
      return;
    }
    Plotly.newPlot(els.plot, traces, layout, {
      scrollZoom: true, displaylogo: false, displayModeBar: true, responsive: true,
    });
  }

  function init() {
    functions = [newFunction()];
    renderFnList();
    els.addBtn.addEventListener("click", () => {
      functions.push(newFunction());
      renderFnList();
    });
    els.xmin.addEventListener("input", () => scheduleUpdate());
    els.xmax.addEventListener("input", () => scheduleUpdate());
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
