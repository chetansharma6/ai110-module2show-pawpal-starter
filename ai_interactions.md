# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

I used **Claude Code** as an autonomous agent across several phases of PawPal+.
The agent read the existing files, made coordinated multi-file edits, ran the
test suite and demo itself, and reported back — I stayed in the role of lead
architect, reviewing and correcting its work.

### Files modified

| File | Change |
|------|--------|
| [`pawpal_system.py`](pawpal_system.py) | Added `find_next_available_slot()`, `sort_by_priority()`, JSON persistence (`to_dict`/`from_dict`, `save_to_json`/`load_from_json`), and a robust `_time_key()` sort helper; earlier phases added `sort_by_time()`, `filter_tasks()`, `detect_conflicts()`, and recurring-task logic |
| [`tests/test_pawpal.py`](tests/test_pawpal.py) | Grew the suite from 8 → 26 tests: sorting correctness (incl. malformed-time robustness), priority sorting, recurrence, conflict detection, next-available-slot, and persistence round-trips |
| [`app.py`](app.py) | Rewired the Streamlit UI to call `Scheduler` methods (filter + sort into an `st.table`, conflict warnings via `st.warning`/`st.success`), added a time-of-day input, and wired in auto-load/auto-save persistence that recovers from a missing or corrupt file |
| [`cli_format.py`](cli_format.py) | New presentation layer: emojis by task type, ANSI color-coded priority/status badges, and `tabulate` tables |
| [`main.py`](main.py) | Demo now uses the formatted tables and demonstrates priority sorting; reconfigures stdout to UTF-8 for Windows |
| [`README.md`](README.md) | Added Features, Testing (real `pytest` output), Persistence, CLI-formatting, and Demo Walkthrough sections |
| [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) | Re-synced the UML to the final code (new Task/Scheduler methods + the Task→Pet back-reference) |
| [`reflection.md`](reflection.md) | Completed the design, tradeoffs, and AI-strategy reflection prompts |

**What task did you give the agent?**

Over the project I asked it to: verify the scheduler's behavior by running the
code; draft and expand the test suite; wire the `Scheduler` methods into the
Streamlit UI with professional components; update the README and UML to match
the final code; and, most recently, **add a third algorithmic capability beyond
the basic requirements** — which it implemented as `find_next_available_slot()`,
a conflict-free "earliest open gap" finder that complements `detect_conflicts()`.

**What did the agent do?**

- Read the target files before editing so its changes fit the existing style and structure.
- Implemented `find_next_available_slot()` as a greedy O(n log n) interval scan over sorted busy windows, with `earliest`/`latest` bounds, completed-task filtering, and `None` returns for impossible requests.
- Added 6 new tests covering empty day, blocking task, gap-between-tasks, no-fit-before-`latest`, ignoring completed tasks, and non-positive duration — then ran `python -m pytest` and confirmed **18 passed**.
- Kept documentation in sync: added a Features bullet for the new capability and logged this workflow here.
- Ran `python main.py` to capture *real* sample output for the README rather than inventing it.

**What did you have to verify or fix manually?**

- **Verified every change by running it**, not by trusting the description — the full pytest suite after each edit, plus direct execution of `main.py` and the app import.
- **Rejected a UI suggestion** that put schedule-grouping logic (`defaultdict` keyed on `id(pet)`) inside `app.py`; I had it route display through `Scheduler.filter_tasks()`/`sort_by_time()` instead to keep the UI thin, and it then removed the now-unused import.
- **Caught an inconsistency the agent surfaced**: `sort_by_time()` raised on a malformed `"HH:MM"` string while `detect_conflicts()` skipped bad times gracefully. I first left it documented as a known edge case, then in the final "ready to be live" pass had it fixed — both sorts now route through a shared `_time_key()` helper that places unparseable times last, and the app recovers from a corrupt `data.json` instead of crashing on startup.
- **Corrected a Mermaid syntax detail** in the UML — the static-member classifier (`$`) had to move to the end of the line after the return type.

<!-- Prompt Comparison (SF11) stretch feature was not attempted, so its section
     has been removed per this file's instructions. -->
