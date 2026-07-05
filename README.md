# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

The suite (in [`tests/test_pawpal.py`](tests/test_pawpal.py)) has **12 tests** covering
the core scheduling behaviors:

- **Task & pet basics** — marking a task complete flips its status; adding a task grows the pet's task list.
- **Recurrence logic** — completing a `daily`/`weekly` task auto-queues a fresh, incomplete copy for the next day; completing twice never spawns duplicates; one-off tasks do not regenerate.
- **Sorting correctness** — `sort_by_time()` returns tasks in chronological (time-of-day) order, sorts numerically so `"9:00"` precedes `"10:00"`, and does not mutate the input list.
- **Conflict detection** — flags duplicate/same-time tasks across different pets, catches partial time-window overlaps, and reports no conflicts when times are clear.

Successful run:

```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\mahesh\AppData\Local\Python\pythoncore-3.14-64\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\mahesh\Documents\ai110-module2show-pawpal-starter
plugins: anyio-4.14.0
collecting ... collected 12 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  8%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [ 16%]
tests/test_pawpal.py::test_completing_recurring_task_queues_next_occurrence PASSED [ 25%]
tests/test_pawpal.py::test_completing_twice_does_not_spawn_duplicates PASSED [ 33%]
tests/test_pawpal.py::test_non_recurring_task_does_not_spawn PASSED      [ 41%]
tests/test_pawpal.py::test_detect_conflicts_flags_same_time_across_pets PASSED [ 50%]
tests/test_pawpal.py::test_detect_conflicts_flags_partial_overlap PASSED [ 58%]
tests/test_pawpal.py::test_no_conflicts_when_times_are_clear PASSED      [ 66%]
tests/test_pawpal.py::test_sort_by_time_returns_chronological_order PASSED [ 75%]
tests/test_pawpal.py::test_sort_by_time_is_numeric_not_lexicographic PASSED [ 83%]
tests/test_pawpal.py::test_sort_by_time_does_not_mutate_input PASSED     [ 91%]
tests/test_pawpal.py::test_completing_daily_task_creates_next_day_task PASSED [100%]

============================= 12 passed in 0.48s ==============================
```

### Confidence Level: ⭐⭐⭐⭐☆ (4 / 5)

All 12 tests pass and the **core scheduling logic** — recurrence, sorting, priority
planning, and conflict detection — is well covered and behaves correctly. One star
is withheld because a few edge cases are not yet guarded: `sort_by_time()` raises on a
malformed `"HH:MM"` string (unlike `detect_conflicts()`, which skips it gracefully),
and there is no validation of out-of-range times or negative durations. Hardening
those inputs would take reliability to 5/5.

## 📐 Smarter Scheduling

Beyond the basic "fit tasks into the available time" plan, PawPal+ adds four
smarter-scheduling features. All of them live in the `Scheduler` and `Task`
classes in [`pawpal_system.py`](pawpal_system.py).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time of day | `Scheduler.sort_by_time()` | Orders tasks earliest→latest by their `"HH:MM"` time; numeric key handles unpadded times |
| Filtering | `Scheduler.filter_tasks()` | Filter by pet name and/or completion status; both optional and combine with AND |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns on overlapping time windows (same or different pets); never crashes |
| Recurring tasks | `Task.mark_complete()` → `Task._next_occurrence()` | Completing a daily/weekly task auto-queues its next occurrence |
| Priority planning | `Scheduler.prioritize_tasks()` / `Scheduler.generate_schedule()` | Greedy High→Medium→Low selection within the time budget, with reasoning |

### Sorting behavior — `Scheduler.sort_by_time()`

Sorts tasks by time of day, earliest first. Times are `"HH:MM"` strings, and the
`sorted()` key splits each into a `(hour, minute)` integer tuple so ordering is
numeric — this means an unpadded `"9:00"` correctly sorts *before* `"10:00"`,
whereas a plain string sort would place `"10:00"` first (because `"1" < "9"`).
It defaults to all of the owner's tasks but accepts any task list, so it composes
with filtering: `scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Buddy"))`.

### Filtering behavior — `Scheduler.filter_tasks()`

Returns tasks filtered by **pet name**, **completion status**, or both. Each
filter is optional; passing both narrows with AND (e.g. only *Buddy's*
*unfinished* tasks). Called with no arguments it returns every task across every
pet. Example: `scheduler.filter_tasks(completed=False)` lists everything still
outstanding.

### Conflict detection — `Scheduler.detect_conflicts()`

Flags any two tasks whose `[start, start + duration)` time windows overlap —
covering both exact same-time clashes *and* partial overlaps, and across the same
pet or different pets. It's deliberately **lightweight**: it returns a list of
human-readable warning strings instead of raising, skips tasks with an
unparseable time rather than crashing, and only *reports* conflicts (it leaves
rescheduling to the human). It sorts by start time and short-circuits the inner
scan, keeping it near O(n log n) rather than a naive O(n²) all-pairs check.
Helpers `_to_minutes()` / `_to_time_str()` do the safe `"HH:MM"` conversions.

### Recurring task logic — `Task.mark_complete()` + `Task._next_occurrence()`

When a `"daily"` or `"weekly"` task is marked complete, PawPal+ automatically
queues a fresh, incomplete copy for the next occurrence. `Task.mark_complete()`
sets the task done and, if it recurs and belongs to a pet, appends the copy built
by `Task._next_occurrence()` to that pet's list (`Pet.add_task()` wires the new
copy's `pet` back-reference). Completing an already-complete task is a no-op, so
duplicates are never spawned, and one-off tasks (any non-recurring frequency) do
not regenerate. `Scheduler.mark_task_complete()` is a thin wrapper for callers
that prefer to go through the scheduler.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

**Sample Output**

Today's Schedule

Pet: Buddy
*Walk (30 min, Priority: High)

Pet: Luna
*Feed (10 min, Priority: Medium)
*Groom (20 min, Priority: Low)

Reasoning:
*Walk scheduled first because it has the highest priority.
*Feed scheduled next because it fits within the available time.
*Long weekend hike skipped because it needs 90 min but only 20 min remain.
*Groom scheduled next because it fits within the available time.
