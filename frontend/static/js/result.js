/**
 * Academic dashboard: semester-wise marks + SGPA/CGPA.
 * Backend reads CSV on each request so edits reflect instantly.
 * The dashboard fetches all data from backend APIs (cloud simulation).
 */
const API_BASE = window.API_BASE || "";

const RING_R = 52;
const RING_C = 2 * Math.PI * RING_R;

function setRingProgress(cgpa) {
  const fill = document.querySelector(".ring-progress__fill");
  if (!fill) return;
  const pct = Math.max(0, Math.min(1, Number(cgpa) / 10));
  const dash = RING_C * pct;
  const gap = RING_C - dash;
  fill.style.strokeDasharray = `${dash} ${gap}`;
}

function el(tag, className, text) {
  const n = document.createElement(tag);
  if (className) n.className = className;
  if (text != null) n.textContent = text;
  return n;
}

function renderSemesters(summary) {
  const container = document.getElementById("semesters-container");
  if (!container) return;
  container.innerHTML = "";

  const semesters = (summary.semesters || []).slice().sort((a, b) => a.semester - b.semester);
  semesters.forEach((sem) => {
    const card = el("section", "semester-card");
    const header = el("div", "semester-card__header");
    header.appendChild(el("h3", "semester-card__title", `Semester ${sem.semester}`));
    header.appendChild(el("div", "semester-card__sgpa", `SGPA: ${Number(sem.sgpa).toFixed(2)}`));
    card.appendChild(header);

    const table = el("table", "marks-table");
    table.appendChild(
      (() => {
        const thead = el("thead");
        const tr = el("tr");
        ["Subject", "Credits", "Marks", "Grade Point"].forEach((h) => tr.appendChild(el("th", "", h)));
        thead.appendChild(tr);
        return thead;
      })()
    );
    const tbody = el("tbody");
    (sem.subjects || []).forEach((s) => {
      const tr = el("tr");
      tr.appendChild(el("td", "marks-table__subject", s.subject));
      tr.appendChild(el("td", "", String(s.credits)));
      tr.appendChild(el("td", "", String(s.marks)));
      tr.appendChild(el("td", "", String(s.grade_point)));
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    card.appendChild(table);

    container.appendChild(card);
  });

  const cgpa = Number(summary.cgpa || 0);
  document.getElementById("cgpa-value").textContent = cgpa.toFixed(2);
  setRingProgress(cgpa);

  const latest = semesters[semesters.length - 1];
  if (latest) {
    document.getElementById("latest-sgpa-value").textContent = Number(latest.sgpa).toFixed(2);
    document.getElementById("latest-sgpa-caption").textContent = `Semester ${latest.semester} · ${Number(
      latest.total_credits || 0
    ).toFixed(0)} credits`;
  }

  const comp = (summary.comparison || []).slice(-1)[0];
  if (comp) {
    const delta = Number(comp.sgpa_delta || 0);
    const sign = delta > 0 ? "+" : "";
    document.getElementById("comparison-value").textContent = `${sign}${delta.toFixed(2)}`;
  } else {
    document.getElementById("comparison-value").textContent = "—";
  }

  // ML inference simulation output from backend: predicted next semester SGPA.
  const predicted = Number(summary.predicted_next_sgpa || 0);
  const predictedEl = document.getElementById("predicted-sgpa-value");
  if (predictedEl) {
    predictedEl.textContent = Number.isFinite(predicted) ? predicted.toFixed(2) : "—";
  }

  const foot = document.getElementById("result-footer-hint");
  if (foot) {
    foot.textContent =
      summary.cloud_simulation_note ||
      "Academic summary refreshes automatically with the latest records.";
  }
}

async function fetchResult() {
  const loader = document.getElementById("page-loader");
  const layout = document.getElementById("result-layout");
  const errorEl = document.getElementById("error-msg");
  const dashboard = document.getElementById("dashboard");

  errorEl.hidden = true;
  errorEl.textContent = "";

  if (loader) loader.hidden = false;
  if (layout) layout.hidden = true;

  try {
    console.log("[portal] Fetching /api/academic-summary");
    const res = await fetch(`${API_BASE}/api/academic-summary`, { credentials: "same-origin" });

    const data = await res.json().catch(() => ({}));
    console.log("[portal] Dashboard response:", res.status, data.ok);

    if (res.status === 401) {
      throw new Error("Session expired. Log in again from the home page.");
    }
    if (!res.ok || data.ok === false) {
      throw new Error(data.error || "Could not load results.");
    }

    renderSemesters(data.summary);

    if (dashboard) dashboard.hidden = false;
    if (layout) layout.hidden = false;
  } catch (err) {
    console.error("[portal] Result error:", err);
    errorEl.textContent = err.message || "Failed to load results.";
    errorEl.hidden = false;
    if (layout) {
      layout.hidden = false;
      if (dashboard) dashboard.hidden = true;
    }
    const foot = document.getElementById("result-footer-hint");
    if (foot) foot.textContent = "";
  } finally {
    if (loader) loader.hidden = true;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  console.log("[portal] Result page ready");
  fetchResult();

  const recalc = document.getElementById("recalculate-btn");
  if (recalc) {
    recalc.addEventListener("click", () => {
      console.log("[portal] Recalculate");
      fetchResult();
    });
  }
});
