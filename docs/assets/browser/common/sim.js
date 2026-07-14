/**
 * sim.js — shared UI/helper library for CSE-from-scratch browser simulations.
 * Vanilla JS, no dependencies. Include via <script src="../common/sim.js"></script>
 * All helpers live on the global SimLib object.
 */
(function () {
  'use strict';

  // ── Inject shared styles once ───────────────────────────────────────────────
  if (!document.getElementById('sim-lib-style')) {
    const s = document.createElement('style');
    s.id = 'sim-lib-style';
    s.textContent = `
      .sim-controls { display:flex; gap:0.5rem; justify-content:center; flex-wrap:wrap; margin:0.75rem 0; align-items:center; }
      .sim-label { display:flex; align-items:center; gap:0.4rem; font-size:0.9rem; color:#555; }
      .sim-label input[type=range] { width:120px; }
      .sim-label input[type=number] { width:70px; padding:0.25rem 0.4rem; font-size:0.9rem; }
      .sim-metrics { display:flex; gap:1rem; justify-content:center; flex-wrap:wrap; margin:0.4rem 0; font-size:0.9rem; color:#444; font-family:monospace; }
      .sim-metric-pair { background:#f5f5f5; border:1px solid #ddd; border-radius:4px; padding:0.2rem 0.6rem; }
      .sim-metric-key { color:#888; }
      .sim-metric-val { color:#222; font-weight:600; }
      .sim-side-by-side { display:flex; gap:1rem; justify-content:center; flex-wrap:wrap; margin:0.75rem 0; }
      .sim-panel { display:flex; flex-direction:column; align-items:center; gap:0.3rem; }
      .sim-panel-label { font-size:0.85rem; font-weight:600; color:#555; letter-spacing:0.03em; }
      .sim-panel canvas { border:1px solid #ccc; background:#fafafa; display:block; }
      .sim-strip { border:1px solid #ccc; display:block; margin:0.5rem auto; background:#fff; }
      button { padding:0.4rem 0.8rem; font-size:0.9rem; cursor:pointer; border:1px solid #bbb; border-radius:4px; background:#fff; }
      button:hover { background:#f0f0f0; }
    `;
    document.head.appendChild(s);
  }

  // ── Internal helper ──────────────────────────────────────────────────────────
  function _getControls(container) {
    if (container) return container;
    let el = document.getElementById('controls');
    if (!el) {
      el = document.querySelector('.controls');
    }
    return el || document.body;
  }

  // ── slider ───────────────────────────────────────────────────────────────────
  /**
   * Creates a labeled range slider and appends it to `container` (or #controls).
   * Returns the <input> element.
   */
  function slider(label, min, max, step, initial, onChange, container) {
    const wrap = document.createElement('label');
    wrap.className = 'sim-label';
    const txt = document.createTextNode(label + ': ');
    const inp = document.createElement('input');
    inp.type = 'range';
    inp.min = min; inp.max = max; inp.step = step; inp.value = initial;
    const val = document.createElement('span');
    val.textContent = initial;
    inp.addEventListener('input', function () {
      val.textContent = this.value;
      onChange(Number(this.value));
    });
    wrap.appendChild(txt);
    wrap.appendChild(inp);
    wrap.appendChild(val);
    _getControls(container).appendChild(wrap);
    return inp;
  }

  // ── numberInput ──────────────────────────────────────────────────────────────
  /**
   * Creates a labeled number input. Returns the <input> element.
   */
  function numberInput(label, min, max, initial, onChange, container) {
    const wrap = document.createElement('label');
    wrap.className = 'sim-label';
    const txt = document.createTextNode(label + ': ');
    const inp = document.createElement('input');
    inp.type = 'number';
    inp.min = min; inp.max = max; inp.value = initial;
    inp.addEventListener('change', function () {
      const v = Math.min(max, Math.max(min, Number(this.value)));
      this.value = v;
      onChange(v);
    });
    wrap.appendChild(txt);
    wrap.appendChild(inp);
    _getControls(container).appendChild(wrap);
    return inp;
  }

  // ── makeButton ───────────────────────────────────────────────────────────────
  /**
   * Creates a button and appends it to `container` (or #controls). Returns <button>.
   */
  function makeButton(label, onClick, container) {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.addEventListener('click', onClick);
    _getControls(container).appendChild(btn);
    return btn;
  }

  // ── pauseResumeReset ─────────────────────────────────────────────────────────
  /**
   * Appends Pause/Resume and Reset buttons to `container`.
   * `startFn(timestamp)` is the rAF callback; it should call requestAnimationFrame
   * only when `state.paused === false`.
   *
   * Returns state object: { paused, rafId }
   * Caller drives the loop:
   *   function tick(ts) { if (!state.paused) { draw(); state.rafId = requestAnimationFrame(tick); } }
   *   SimLib.pauseResumeReset(tick, reset, container);
   *   state.rafId = requestAnimationFrame(tick);
   */
  function pauseResumeReset(tickFn, resetFn, container) {
    const state = { paused: false, rafId: null };

    const pauseBtn = makeButton('Pause', function () {
      if (!state.paused) {
        state.paused = true;
        pauseBtn.textContent = 'Resume';
        if (state.rafId) { cancelAnimationFrame(state.rafId); state.rafId = null; }
      } else {
        state.paused = false;
        pauseBtn.textContent = 'Pause';
        state.rafId = requestAnimationFrame(tickFn);
      }
    }, container);

    makeButton('Reset', function () {
      state.paused = false;
      pauseBtn.textContent = 'Pause';
      if (state.rafId) { cancelAnimationFrame(state.rafId); state.rafId = null; }
      resetFn();
      state.rafId = requestAnimationFrame(tickFn);
    }, container);

    return state;
  }

  // ── metrics ──────────────────────────────────────────────────────────────────
  /**
   * Creates or binds a metrics readout below the controls area.
   * `elOrId`: existing element or id string; if omitted, creates a new div after #controls.
   * Returns { update(obj) } — call update({key: value, ...}) each frame.
   */
  function metrics(elOrId) {
    let el;
    if (typeof elOrId === 'string') {
      el = document.getElementById(elOrId);
    } else if (elOrId instanceof Element) {
      el = elOrId;
    }
    if (!el) {
      el = document.createElement('div');
      // insert after controls, before first canvas
      const ctrl = document.querySelector('.controls, #controls');
      const canvas = document.querySelector('canvas');
      if (ctrl && ctrl.nextSibling) {
        ctrl.parentNode.insertBefore(el, ctrl.nextSibling);
      } else if (canvas) {
        canvas.parentNode.insertBefore(el, canvas);
      } else {
        document.body.appendChild(el);
      }
    }
    el.className = 'sim-metrics';

    function update(obj) {
      el.innerHTML = Object.entries(obj).map(function (kv) {
        return '<span class="sim-metric-pair"><span class="sim-metric-key">' +
          kv[0] + ':</span> <span class="sim-metric-val">' + kv[1] + '</span></span>';
      }).join('');
    }

    return { update: update, el: el };
  }

  // ── stripPlot ────────────────────────────────────────────────────────────────
  /**
   * Creates a rolling time-series strip chart on `canvasEl`.
   * `series`: array of {label, color} descriptors.
   * `windowSize`: number of data points to show (default 80).
   *
   * Returns { push(seriesIndex, value) } — call push each frame/step.
   */
  function stripPlot(canvasEl, series, windowSize) {
    windowSize = windowSize || 80;
    const data = series.map(function () { return []; });
    const ctx = canvasEl.getContext('2d');
    canvasEl.className = 'sim-strip';

    function draw() {
      const W = canvasEl.width, H = canvasEl.height;
      const PAD = 28;
      ctx.clearRect(0, 0, W, H);

      // autoscale across all series
      let yMin = Infinity, yMax = -Infinity;
      data.forEach(function (d) {
        d.forEach(function (v) {
          if (v < yMin) yMin = v;
          if (v > yMax) yMax = v;
        });
      });
      if (yMin === yMax) { yMin -= 1; yMax += 1; }
      const range = yMax - yMin;

      // axes
      ctx.strokeStyle = '#ccc';
      ctx.lineWidth = 1;
      ctx.strokeRect(PAD, 4, W - PAD - 4, H - PAD);

      // y-axis labels
      ctx.fillStyle = '#999';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      [0, 0.5, 1].forEach(function (t) {
        const v = yMin + t * range;
        const y = 4 + (H - PAD - 4) * (1 - t);
        ctx.fillText(v.toFixed(v < 10 ? 1 : 0), PAD - 2, y + 3);
      });

      // plot each series
      data.forEach(function (d, si) {
        if (d.length < 2) return;
        const col = (series[si] && series[si].color) || '#2196F3';
        ctx.strokeStyle = col;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        const visLen = Math.min(d.length, windowSize);
        const startIdx = d.length - visLen;
        for (let i = 0; i < visLen; i++) {
          const v = d[startIdx + i];
          const x = PAD + (i / (windowSize - 1)) * (W - PAD - 4);
          const y = 4 + (H - PAD - 4) * (1 - (v - yMin) / range);
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
      });

      // legend
      series.forEach(function (s, i) {
        const lx = PAD + 6 + i * 90;
        const ly = H - 8;
        ctx.strokeStyle = s.color || '#2196F3';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(lx, ly); ctx.lineTo(lx + 18, ly); ctx.stroke();
        ctx.fillStyle = '#555';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(s.label || ('series ' + i), lx + 22, ly + 3);
      });
    }

    function push(seriesIndex, value) {
      if (data[seriesIndex]) data[seriesIndex].push(value);
      draw();
    }

    function reset() {
      data.forEach(function (d) { d.length = 0; });
      ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
    }

    return { push: push, reset: reset, draw: draw };
  }

  // ── sideBySide ───────────────────────────────────────────────────────────────
  /**
   * Creates two labeled canvases side by side inside `parentEl` (or before first canvas).
   * Returns [ctxA, ctxB, canvasA, canvasB].
   */
  function sideBySide(parentEl, labelA, labelB, width, height) {
    width = width || 320;
    height = height || 200;

    if (!parentEl) {
      parentEl = document.createElement('div');
      const firstCanvas = document.querySelector('canvas');
      if (firstCanvas) {
        firstCanvas.parentNode.insertBefore(parentEl, firstCanvas);
        // hide the original canvas if it's just a placeholder
      } else {
        document.body.appendChild(parentEl);
      }
    }
    parentEl.className = 'sim-side-by-side';

    function makePanel(label, w, h) {
      const panel = document.createElement('div');
      panel.className = 'sim-panel';
      const lbl = document.createElement('div');
      lbl.className = 'sim-panel-label';
      lbl.textContent = label;
      const cv = document.createElement('canvas');
      cv.width = w; cv.height = h;
      panel.appendChild(lbl);
      panel.appendChild(cv);
      parentEl.appendChild(panel);
      return cv;
    }

    const cvA = makePanel(labelA, width, height);
    const cvB = makePanel(labelB, width, height);
    return [cvA.getContext('2d'), cvB.getContext('2d'), cvA, cvB];
  }

  // ── Export ───────────────────────────────────────────────────────────────────
  window.SimLib = {
    slider: slider,
    numberInput: numberInput,
    makeButton: makeButton,
    pauseResumeReset: pauseResumeReset,
    metrics: metrics,
    stripPlot: stripPlot,
    sideBySide: sideBySide
  };

}());
