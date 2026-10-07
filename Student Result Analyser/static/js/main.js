/**
 * Student Result Analyser — front-end logic
 *
 * IMPORTANT: No grade, percentage, or pass/fail calculations happen here.
 * All computed values are received from the Flask API (Python business layer)
 * and displayed as-is. JavaScript is a pure rendering layer.
 *
 * Flow:
 *   1. On load  → GET /api/subjects → skip Setup if already configured
 *   2. Setup    → POST /api/subjects → render mark inputs in Entry form
 *   3. Entry    → POST /api/students → append row to live table
 *   4. Results  → GET /api/students + GET /api/stats → render cards
 *   5. Reset    → confirm → DELETE /api/students → back to Entry
 */

"use strict";

// ---------------------------------------------------------------------------
// Section navigation
// ---------------------------------------------------------------------------

const SECTIONS = ["setup-section", "entry-section", "results-section"];

function showSection(id) {
  SECTIONS.forEach((sId) => {
    const el = document.getElementById(sId);
    if (el) el.hidden = sId !== id;
  });
}

// ---------------------------------------------------------------------------
// Error helpers
// ---------------------------------------------------------------------------

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = message;
  el.hidden = false;
}

function clearError(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = "";
  el.hidden = true;
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

// ---------------------------------------------------------------------------
// Grade badge HTML — CSS class names match style.css
// ---------------------------------------------------------------------------

function gradeBadge(grade) {
  return `<span class="grade-badge grade-${grade}">${grade}</span>`;
}

function passPill(passFailStr) {
  const isPass = passFailStr === "Pass";
  const cls = isPass ? "pill-pass" : "pill-fail";
  return `<span class="pill ${cls}">${passFailStr}</span>`;
}

// ---------------------------------------------------------------------------
// Render dynamic mark input fields for the Entry form
// ---------------------------------------------------------------------------

function renderMarkInputs(subjects) {
  const container = document.getElementById("marks-inputs");
  container.innerHTML = "";
  subjects.forEach((subject) => {
    const div = document.createElement("div");
    div.className = "form-group";
    div.innerHTML = `
      <label for="mark-${subject.name}">${subject.name}</label>
      <input
        type="number"
        id="mark-${subject.name}"
        name="${subject.name}"
        data-subject="${subject.name}"
        min="0"
        max="100"
        placeholder="0–100"
        required
      />
    `;
    container.appendChild(div);
  });
}

// ---------------------------------------------------------------------------
// Append a row to the live student table in the Entry section
// ---------------------------------------------------------------------------

function appendStudentRow(student) {
  const tbody = document.getElementById("student-table-body");
  const rowNum = tbody.rows.length + 1;
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${rowNum}</td>
    <td>${escHtml(student.name)}</td>
    <td>${escHtml(student.roll_number)}</td>
    <td>${student.total} / ${student.max_total}</td>
    <td>${student.percentage}%</td>
    <td>${gradeBadge(student.grade)}</td>
    <td>${passPill(student.pass_fail)}</td>
  `;
  tbody.appendChild(tr);

  // Show table wrapper and update count
  document.getElementById("student-table-wrapper").hidden = false;
  document.getElementById("student-count").textContent = rowNum;
}

// ---------------------------------------------------------------------------
// Rebuild the live table from the full student list (used after page load)
// ---------------------------------------------------------------------------

function rebuildStudentTable(students) {
  const tbody = document.getElementById("student-table-body");
  tbody.innerHTML = "";
  students.forEach((s) => appendStudentRow(s));
}

// ---------------------------------------------------------------------------
// Render result cards in the Results section
// ---------------------------------------------------------------------------

function renderResultCards(students) {
  const container = document.getElementById("result-cards");
  container.innerHTML = "";

  students.forEach((s) => {
    const card = document.createElement("div");
    card.className = "result-card";

    const subjectRows = s.subject_performance
      .map(
        (p) => `
        <tr class="${p.passed ? "" : "subject-failed"}">
          <td>${escHtml(p.subject)}</td>
          <td>${p.marks}</td>
          <td>${p.max_marks}</td>
          <td>${p.passing_marks}</td>
          <td>${p.passed ? "✓ Pass" : "✗ Fail"}</td>
        </tr>`
      )
      .join("");

    card.innerHTML = `
      <div class="result-card-header">
        <div>
          <h4>${escHtml(s.name)} <span class="roll-no">#${escHtml(s.roll_number)}</span></h4>
        </div>
        <div>
          ${gradeBadge(s.grade)}
          ${passPill(s.pass_fail)}
        </div>
      </div>

      <div class="result-summary">
        <span><strong>Total:</strong> ${s.total} / ${s.max_total}</span>
        <span><strong>Percentage:</strong> ${s.percentage}%</span>
      </div>

      <table class="subject-table">
        <thead>
          <tr>
            <th>Subject</th>
            <th>Marks</th>
            <th>Max</th>
            <th>Passing</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>${subjectRows}</tbody>
      </table>
    `;
    container.appendChild(card);
  });
}

// ---------------------------------------------------------------------------
// Render class statistics
// ---------------------------------------------------------------------------

function renderStats(stats) {
  const card = document.getElementById("class-stats");
  document.getElementById("stat-total").textContent = stats.total_students;
  document.getElementById("stat-average").textContent = `${stats.average}%`;
  document.getElementById("stat-passed").textContent = stats.passed;
  document.getElementById("stat-failed").textContent = stats.failed;
  document.getElementById("stat-highest").textContent = stats.highest.join(", ");
  document.getElementById("stat-lowest").textContent = stats.lowest.join(", ");
  card.hidden = false;
}

// ---------------------------------------------------------------------------
// Escape HTML to prevent XSS when inserting user-supplied text
// ---------------------------------------------------------------------------

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------------
// SETUP FORM — Step 1
// ---------------------------------------------------------------------------

document.getElementById("setup-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError("setup-error");

  const raw = document.getElementById("subjects-input").value;
  const subjectNames = raw
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  const { ok, data } = await apiFetch("/api/subjects", {
    method: "POST",
    body: JSON.stringify({ subjects: subjectNames }),
  });

  if (!ok) {
    showError("setup-error", data.error || "Failed to set subjects.");
    return;
  }

  renderMarkInputs(data.subjects);
  showSection("entry-section");
});

// ---------------------------------------------------------------------------
// ENTRY FORM — Step 2
// ---------------------------------------------------------------------------

document.getElementById("entry-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError("entry-error");

  const name = document.getElementById("student-name").value.trim();
  const roll = document.getElementById("roll-number").value.trim();

  // Collect marks from dynamically-generated inputs
  const marks = {};
  document
    .querySelectorAll("#marks-inputs input[data-subject]")
    .forEach((input) => {
      const val = input.value.trim();
      marks[input.dataset.subject] = val === "" ? "" : Number(val);
    });

  const { ok, status, data } = await apiFetch("/api/students", {
    method: "POST",
    body: JSON.stringify({ name, roll_number: roll, marks }),
  });

  if (!ok) {
    showError("entry-error", data.error || "Failed to add student.");
    return;
  }

  appendStudentRow(data.student);

  // Clear form fields for next entry
  document.getElementById("student-name").value = "";
  document.getElementById("roll-number").value = "";
  document.querySelectorAll("#marks-inputs input").forEach((i) => (i.value = ""));
  document.getElementById("student-name").focus();
});

// ---------------------------------------------------------------------------
// VIEW RESULTS button
// ---------------------------------------------------------------------------

document.getElementById("view-results-btn").addEventListener("click", async () => {
  clearError("results-error");

  const [studentsResp, statsResp] = await Promise.all([
    apiFetch("/api/students"),
    apiFetch("/api/stats"),
  ]);

  if (!studentsResp.ok) {
    showError("results-error", studentsResp.data.error || "Could not load students.");
    return;
  }

  if (!statsResp.ok) {
    showError("results-error", statsResp.data.error || "No students added yet.");
    showSection("results-section");
    return;
  }

  renderResultCards(studentsResp.data.students);
  renderStats(statsResp.data);
  showSection("results-section");
});

// ---------------------------------------------------------------------------
// BACK button (Results → Entry)
// ---------------------------------------------------------------------------

document.getElementById("back-btn").addEventListener("click", () => {
  showSection("entry-section");
});

// ---------------------------------------------------------------------------
// CHANGE SUBJECTS button (Entry → Setup)
// ---------------------------------------------------------------------------

document.getElementById("change-subjects-btn").addEventListener("click", () => {
  showSection("setup-section");
});

// ---------------------------------------------------------------------------
// RESET button
// ---------------------------------------------------------------------------

document.getElementById("reset-btn").addEventListener("click", async () => {
  if (!confirm("This will delete all student records. Are you sure?")) return;

  const { ok, data } = await apiFetch("/api/students", { method: "DELETE" });

  if (!ok) {
    showError("results-error", data.error || "Reset failed.");
    return;
  }

  // Clear live table and result cards
  document.getElementById("student-table-body").innerHTML = "";
  document.getElementById("student-count").textContent = "0";
  document.getElementById("student-table-wrapper").hidden = true;
  document.getElementById("result-cards").innerHTML = "";
  document.getElementById("class-stats").hidden = true;

  // Clear forms
  document.getElementById("student-name").value = "";
  document.getElementById("roll-number").value = "";
  document.querySelectorAll("#marks-inputs input").forEach((i) => (i.value = ""));

  showSection("entry-section");
});

// ---------------------------------------------------------------------------
// On page load: check if subjects are already configured (e.g. after refresh)
// ---------------------------------------------------------------------------

(async () => {
  const { ok, data } = await apiFetch("/api/subjects");
  if (ok && data.subjects && data.subjects.length > 0) {
    // Subjects already set — re-render mark inputs and go straight to Entry
    renderMarkInputs(data.subjects);

    // Also reload any existing students into the live table
    const studentsResp = await apiFetch("/api/students");
    if (studentsResp.ok && studentsResp.data.students.length > 0) {
      rebuildStudentTable(studentsResp.data.students);
    }

    showSection("entry-section");
  } else {
    showSection("setup-section");
  }
})();
