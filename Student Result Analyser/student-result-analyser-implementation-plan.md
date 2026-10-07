# Student Result Analyser — Implementation Plan

## Overview

Build a Flask web application that allows a teacher to enter student marks across
multiple subjects and automatically compute totals, percentages, grades, pass/fail
status, subject-wise performance, class average, and highest/lowest scores.

**Technology stack:** Python · Flask · HTML · CSS · JavaScript · pytest

**Scope:**
- In-memory data store only (no database, no authentication)
- Single class/session per application run
- REST JSON API served by Flask; thin HTML/CSS/JS front end
- All business logic isolated in a service layer, fully unit-tested

**Non-goals:** user login, persistent storage, multi-class support, CSV export.

**Follows the same layered architecture and conventions as the existing
`Student tracker/student-expense-tracker/` reference project.**

---

## Business Rules (locked)

| Rule | Value |
|---|---|
| Max marks per subject | 100 (uniform across all subjects) |
| Passing marks per subject | 33 |
| Overall pass condition | Must pass **every** subject |
| Grade A | percentage >= 90 |
| Grade B | percentage >= 75 |
| Grade C | percentage >= 60 |
| Grade D | percentage >= 40 |
| Grade F | percentage < 40 |
| Marks type | Integer only (0–100 inclusive) |
| Absent students | Treated as 0 marks (no special flag in v1) |
| Tie handling | All tied students listed for highest/lowest |

---

## Architecture

```
Browser (HTML + CSS + JS)
        |  fetch() JSON API calls
        v
Flask app (routes.py)   ←  entry point: app.py
        |
        v
ResultService  (orchestrates all business logic)
        |
   +----+-----+
   |          |
Validator   StudentRepository  (in-memory list, no file I/O)
   |          |
   v          v
Student model   Subject model
```

**Layer rules:**
- Routes call only `ResultService`; they never touch models directly
- `ResultService` coordinates `Validator` + `StudentRepository`
- `Validator` raises custom exceptions; never returns booleans
- Models are plain dataclasses with `to_dict()` for JSON serialisation

---

## Project Structure

```
Student Result Analyser/
├── app.py                        # Flask app factory + entry point
├── routes.py                     # All Flask route/API handlers
├── models/
│   ├── __init__.py
│   ├── student.py                # Student dataclass + computed methods
│   └── subject.py                # Subject dataclass + grade/pass logic
├── services/
│   ├── __init__.py
│   └── result_service.py         # Business logic orchestrator
├── repository/
│   ├── __init__.py
│   └── student_repository.py     # In-memory store for students
├── utils/
│   ├── __init__.py
│   ├── exceptions.py             # Custom exception classes
│   └── validator.py              # Input validation (static methods)
├── static/
│   ├── css/
│   │   └── style.css             # All custom styles
│   └── js/
│       └── main.js               # All front-end logic (fetch calls)
├── templates/
│   └── index.html                # Single-page shell; JS renders content
├── tests/
│   ├── __init__.py
│   ├── test_models.py            # Student / Subject model unit tests
│   ├── test_validator.py         # Validator unit tests
│   ├── test_result_service.py    # ResultService integration unit tests
│   └── test_routes.py            # Flask route tests via test client
└── requirements.txt
```

---

## Class Responsibilities

| Class / Module | Responsibility |
|---|---|
| `Subject` (dataclass) | Holds `name`, `max_marks=100`, `passing_marks=33`; has `to_dict()` |
| `Student` (dataclass) | Holds `id`, `name`, `roll_number`, `marks` dict; owns all computed methods |
| `StudentRepository` | In-memory list; add, get_all, find_by_roll, clear |
| `ResultService` | Orchestrates validation → model creation → storage → stats |
| `Validator` | Static methods raise exceptions on bad input; never returns bool |
| `exceptions.py` | Domain-specific exception hierarchy |
| `routes.py` | Thin HTTP handlers; delegate to `ResultService`; return JSON |
| `app.py` | `create_app()` factory; registers routes; owns the service singleton |
| `main.js` | Client-side section navigation, form submission, result rendering |
| `index.html` | Semantic HTML5 shell; three hidden sections shown by JS |
| `style.css` | Layout, table styles, grade badge colours, pass/fail pill badges |

---

## Flask Routes & API Endpoints

| Method | Path | Purpose | Request Body | Success Response |
|---|---|---|---|---|
| GET | `/` | Serve the HTML shell | — | 200 HTML |
| GET | `/api/subjects` | Return configured subject list | — | `{ "subjects": [...] }` |
| POST | `/api/subjects` | Set subjects for the session | `{ "subjects": ["Math","Science"] }` | `{ "subjects": [...] }` |
| GET | `/api/students` | Return all students with computed fields | — | `{ "students": [...] }` |
| POST | `/api/students` | Add a student | `{ "name", "roll_number", "marks": {subject: value} }` | `{ "student": {...} }` |
| DELETE | `/api/students` | Clear all students (reset session) | — | `{ "message": "cleared" }` |
| GET | `/api/stats` | Return class statistics | — | `{ "average", "highest", "lowest", "total_students", "passed", "failed" }` |

**Error responses:** All non-2xx responses return `{ "error": "human-readable message" }`.

---

## UI Screens

### Screen 1 — Setup
- Text input: subject names (comma-separated), e.g. `Math, Science, English`
- Submit button: calls `POST /api/subjects`
- On success: transitions to Entry screen with dynamic per-subject mark fields

### Screen 2 — Enter Marks
- Student name field (text)
- Roll number field (text)
- One numeric input per subject (dynamically generated from subject list)
- Add Student button: calls `POST /api/students`
- Live table below form: shows all added students (name, roll, total, percentage, grade, pass/fail)
- View Results button: transitions to Results screen
- Inline error display for API 400 responses

### Screen 3 — Results
- Per-student result card: name, roll, total, percentage, grade badge, pass/fail pill, subject breakdown table
- Class summary section: average percentage, highest scorer(s), lowest scorer(s), total/passed/failed counts
- Reset button: confirm dialog → `DELETE /api/students` → return to Entry screen

---

## Data Flow

```
Teacher fills Setup form
        ↓
POST /api/subjects → ResultService.set_subjects() → stored in service state
        ↓
Teacher fills Entry form (name + roll + marks per subject)
        ↓
POST /api/students
  → routes.py extracts body
  → ResultService.add_student(name, roll, marks_dict)
      → Validator.validate_student_input() → raises on bad data
      → StudentRepository.find_by_roll() → raises DuplicateRollError if exists
      → Build Student dataclass → call compute_total/percentage/grade/pass
      → StudentRepository.add(student)
      → return student.to_dict()
  → 201 JSON response → JS appends row to live table
        ↓
Teacher clicks "View Results"
        ↓
GET /api/students → all students with computed fields
GET /api/stats    → average, highest, lowest, counts
        ↓
JS renders result cards + class summary
        ↓
Teacher clicks "Reset"
        ↓
DELETE /api/students → StudentRepository.clear() → 200 → JS resets to Entry screen
```

---

## Validation Rules

| Input | Rule | Exception Raised |
|---|---|---|
| Student name | Non-empty, letters and spaces only, max 50 chars | `ValidationError` |
| Roll number | Non-empty, alphanumeric, max 20 chars | `ValidationError` |
| Roll uniqueness | No two students share the same roll number | `DuplicateRollError` |
| Marks per subject | Integer, 0–100 inclusive | `ValidationError` |
| All subjects covered | Marks dict must have a key for every configured subject | `ValidationError` |
| Subjects list | At least 1 subject; each name non-empty string | `NoSubjectsError` |
| Stats request | At least 1 student must exist | `NoStudentsError` |

---

## Error Handling

| Exception | HTTP Status | When |
|---|---|---|
| `ValidationError` | 400 | Any invalid input field |
| `DuplicateRollError` | 400 | Roll number already exists |
| `StudentNotFoundError` | 404 | Roll number not found (future use) |
| `NoStudentsError` | 400 | Stats requested with empty student list |
| `NoSubjectsError` | 400 | Student added before subjects are configured |
| Unhandled exception | 500 | Unexpected server error |

All exceptions are caught in route handlers and returned as `{ "error": "..." }` JSON.
The `Validator` and service layer raise exceptions; routes never raise directly.

---

## Testing Strategy

### Test Files

| File | Coverage |
|---|---|
| `tests/test_models.py` | `Subject.to_dict()`, `Student.compute_total()`, `compute_percentage()`, `assign_grade()` at all grade boundaries, `is_pass()` when all pass and when one subject fails, `to_dict()` shape, `subject_performance()` output |
| `tests/test_validator.py` | Valid input passes silently; empty name raises; invalid roll raises; marks < 0 raises; marks > 100 raises; non-integer marks raises; duplicate roll raises; empty subjects list raises |
| `tests/test_result_service.py` | Add student succeeds; duplicate roll raises; `get_class_stats()` average calculation; single student average equals their percentage; all same score → all in highest AND lowest; no students → raises `NoStudentsError` |
| `tests/test_routes.py` | Happy path for all 7 endpoints; error path (400) for invalid inputs; `GET /api/stats` on empty list returns 400 |

### Testing Conventions (from reference project)
- pytest fixtures provide a fresh service instance per test (isolated state)
- `pytest.raises(ExceptionClass)` for all error-path tests
- No mocking of the repository — use real in-memory instances
- Test class names: `TestValidateName`, `TestAddStudent`, `TestGetClassStats`

---

## Implementation Sequence

Sub-tasks are designed to be completed in order. Each sub-task is independently testable before moving to the next.

---

### Sub-Task 1 — Project Scaffold & Models

**Intent:** Create the project skeleton with all directories, placeholder `__init__.py`
files, `requirements.txt`, and the two core dataclass models (`Subject`, `Student`).
This is the foundation every other sub-task builds on.

**Expected Outcomes:**
- All directories and `__init__.py` files exist
- `Subject` dataclass: `name`, `max_marks=100`, `passing_marks=33`; has `to_dict()`
- `Student` dataclass: `id`, `name`, `roll_number`, `marks` (dict keyed by subject name);
  has `to_dict()`, `compute_total()`, `compute_percentage(total_max)`,
  `assign_grade()`, `is_pass(subjects)`, `subject_performance(subjects)`
- Grade logic and pass/fail logic live inside the `Student` model
- `requirements.txt` lists `flask` and `pytest`
- `tests/test_models.py` passes for all model methods

**Todo list:**
1. Create directory tree and all `__init__.py` files
2. Write `Subject` dataclass in `models/subject.py`
3. Write `Student` dataclass in `models/student.py` with all computed methods
4. Write `requirements.txt`
5. Write `tests/test_models.py` covering: total, percentage, grade boundaries,
   pass (all subjects pass), fail (one subject below threshold), `to_dict()` shape,
   `subject_performance()` output

**Relevant context:**
- `Student tracker/student-expense-tracker/models/expense.py` — dataclass pattern
  with `to_dict()` / `from_dict()`
- Business rules table above (grade bands, passing threshold = 33)

**Status:** [ ] pending

---

### Sub-Task 2 — Custom Exceptions & Validator

**Intent:** Define the full set of custom exceptions and the `Validator` class that
enforces all input rules. Centralising validation here keeps both the service layer
and the routes clean.

**Expected Outcomes:**
- `utils/exceptions.py` defines: `ValidationError`, `DuplicateRollError`,
  `StudentNotFoundError`, `NoStudentsError`, `NoSubjectsError`
- `Validator` class with static methods: `validate_name`, `validate_roll_number`,
  `validate_marks`, `validate_subjects_list`, `validate_student_input`
  (composite — calls all field validators)
- `tests/test_validator.py` passes for: valid input, empty name, invalid roll,
  marks below 0, marks above 100, non-integer marks, duplicate roll detection,
  empty subjects list

**Todo list:**
1. Write all exception classes in `utils/exceptions.py`
2. Write `Validator` class in `utils/validator.py` with static field validators
3. Add composite `validate_student_input` that calls all field validators
4. Write `tests/test_validator.py` covering all valid and invalid cases

**Relevant context:**
- `Student tracker/student-expense-tracker/utils/exceptions.py` — exception pattern
- `Student tracker/student-expense-tracker/utils/validator.py` — static validator pattern
- Validation rules: name non-empty letters/spaces max 50; roll alphanumeric max 20; marks integer 0–100; at least 1 subject

**Status:** [ ] pending

---

### Sub-Task 3 — Repository & Service Layer

**Intent:** Build the in-memory `StudentRepository` and the `ResultService` that
orchestrates all operations. The repository is the single source of truth for student
data; the service exposes every operation the API layer will need.

**Expected Outcomes:**
- `StudentRepository`: `add(student)`, `get_all()`, `find_by_roll(roll)`, `clear()`
  — backed by a plain Python list
- `ResultService`: `set_subjects(subjects)`, `get_subjects()`, `add_student(name, roll, marks_dict)`,
  `get_all_students()`, `get_class_stats()` returning
  `{ average, highest (list), lowest (list), total_students, passed, failed }`
- `tests/test_result_service.py` passes for: add student, duplicate roll raises,
  class average, single student, all same score (tied), empty class stats raises

**Todo list:**
1. Write `StudentRepository` in `repository/student_repository.py`
2. Write `ResultService` in `services/result_service.py`; inject repository and accept
   subjects list via `set_subjects()` method
3. Implement `add_student`, `get_all_students`, `get_class_stats` on service
4. Write `tests/test_result_service.py` using pytest fixtures for isolated service instances

**Relevant context:**
- `Student tracker/student-expense-tracker/repository/expense_repository.py` —
  repository pattern (swap file I/O for in-memory list)
- `Student tracker/student-expense-tracker/services/expense_service.py` —
  service pattern with injected repository

**Status:** [ ] pending

---

### Sub-Task 4 — Flask App & API Routes

**Intent:** Wire up the Flask application with an app factory, serve the HTML shell,
and expose the REST JSON API endpoints the front end will consume.

**Expected Outcomes:**
- `app.py` creates and returns a Flask app via `create_app()` factory
- `routes.py` registers all route handlers on the app
- All API endpoints return JSON; non-2xx responses include `{ "error": "..." }`
- HTML shell served at `GET /` from `templates/index.html`
- `tests/test_routes.py` passes using Flask test client for all 7 endpoints

**Todo list:**
1. Write `app.py` with `create_app()` factory; register routes blueprint
2. Write all 7 route handlers in `routes.py`; use `ResultService` singleton per app instance
3. Apply consistent error handling: catch `ValidationError`, `DuplicateRollError`,
   `NoStudentsError`, `NoSubjectsError` → return 400 JSON; unhandled → 500
4. Register `index.html` template for `GET /`
5. Write `tests/test_routes.py`: happy-path + error-path for each endpoint

**Relevant context:**
- Sub-Tasks 1–3 must be complete before this sub-task
- All exceptions defined in `utils/exceptions.py`
- Service lives at the app level (not per-request) since data is in-memory
- API contracts table in the Flask Routes section above

**Status:** [ ] pending

---

### Sub-Task 5 — HTML Template & CSS

**Intent:** Create the single-page HTML shell and stylesheet. The page has three
sections rendered by JavaScript — Setup, Enter Marks, and Results — with no page reloads.

**Expected Outcomes:**
- `templates/index.html`: semantic HTML5, links `style.css` and `main.js`,
  contains three `<section>` elements (`#setup-section`, `#entry-section`, `#results-section`)
  hidden/shown by JS
- `static/css/style.css`: clean table styles, colour-coded grade badges, pass/fail pill
  badges (green/red), responsive layout with no framework dependency
- Page is presentable without JavaScript (graceful degradation)

**Todo list:**
1. Write `templates/index.html` with all three `<section>` elements and all form fields
2. Write `static/css/style.css` with layout, table styles, grade badge colour map
   (A=green, B=blue, C=yellow, D=orange, F=red), pass=green pill / fail=red pill
3. Verify HTML renders correctly when opened statically (before JS wires it up)

**Relevant context:**
- No CSS framework — keep styles minimal and classroom-appropriate
- CSS class names for grade badges and pass/fail pills must match what JS will apply
- UI Screens section above defines all required form fields and display elements

**Status:** [ ] pending

---

### Sub-Task 6 — JavaScript Front End

**Intent:** Write all client-side logic in `static/js/main.js`. It calls the Flask API,
renders the dynamic UI sections, and handles all user interactions without any page reload.

**Expected Outcomes:**
- On load: calls `GET /api/subjects`; if subjects are set, skips Setup and shows Entry screen
- Setup form: `POST /api/subjects` → on success, render dynamic per-subject mark input
  fields in the Entry form
- Entry form: `POST /api/students` → on success, append student row to live table;
  show inline error on validation failure
- Results view: `GET /api/students` + `GET /api/stats` → render result cards and class summary
- Reset button: confirm dialog → `DELETE /api/students` → clear and return to Entry screen
- No external JS libraries (vanilla JS only, `fetch()` API)

**Todo list:**
1. Write `main.js`: section navigation helpers, Setup form handler, Entry form handler
   with dynamic subject inputs, live student table update
2. Implement Results view: render per-student cards (with subject breakdown) and class stats
3. Add inline error display for API 400 responses (message below the form)
4. Add Reset flow: confirm dialog → DELETE → re-render to Entry screen
5. Manual browser test: add subjects → add 3+ students → view results → reset

**Relevant context:**
- All API contracts defined in Sub-Task 4
- Grade badge and pass/fail CSS class names defined in Sub-Task 5
- Vanilla `fetch()` with `Content-Type: application/json` headers

**Status:** [ ] pending

---

### Sub-Task 7 — Final Integration & Test Run

**Intent:** Run the full pytest suite, fix any failures, smoke-test the app end-to-end
in a browser, and verify all 8 requirements are met.

**Expected Outcomes:**
- `pytest` exits with 0 failures across all four test files
- Browser smoke test: setup subjects → add students → view result cards with correct
  totals, percentages, grades, pass/fail → class stats show correct average, highest, lowest
- `requirements.txt` is complete and accurate
- No `print` debug statements left in source files
- Usage instructions added to `app.py` module docstring

**Todo list:**
1. Run `pytest` from `Student Result Analyser/`; fix any failures
2. Run Flask app (`python app.py`) and perform full browser smoke test
3. Verify edge cases: single student; all same score (tied highest/lowest); student fails exactly one subject
4. Remove any debug prints; ensure all public methods have docstrings
5. Confirm `requirements.txt` matches all imports used in the project

**Relevant context:**
- All prior sub-tasks must be complete and green before this sub-task
- Edge cases: single student → avg = their percentage; tie → all names in highest/lowest;
  one failed subject → overall FAIL regardless of total

**Status:** [ ] pending
