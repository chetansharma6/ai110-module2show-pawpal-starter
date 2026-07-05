# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design:

- My initial UML design focused on organizing the pet care application into four main classes. The design separates user information, pet information, pet care tasks, and scheduling logic so that each class has a clear responsibility.

- What classes did you include, and what responsibilities did you assign to each?

- I included four classes: Owner, Pet, Task, and Scheduler. The Owner class stores the owner's information, available time, and preferences. The Pet class stores details about each pet, such as its name, species, and age. The Task class represents pet care activities, including their duration, priority, and completion status. The Scheduler class is responsible for organizing tasks into a daily plan based on priorities and the owner's available time, and for explaining why the schedule was created.

###Core User Actions:

- A user can add a pet.
- A user can schedule vet visits for their pet.
- A user can view the schedule for the whole day and appropriately make changes as per his/her needs.

**b. Design changes**

- Did your design change during implementation? 

- Yes.

- If yes, describe at least one change and why you made it.

- UML declares Pet "1" --> "0..*" Task : has, but the Pet dataclass had no way to hold tasks — the relationship existed in the diagram but not the code.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

- My scheduler considers three main constraints. The first is the owner's **available time** for the day (`Owner.time_available`), which acts as a hard budget the plan cannot exceed. The second is each task's **priority** label (High / Medium / Low), which decides the order tasks are considered in. The third is each task's **time of day and duration**, which I use for sorting the day chronologically and for detecting scheduling **conflicts** when two tasks overlap. I also carry an owner `preferences` dictionary for future rules, though the current plan is driven mainly by time and priority.

- How did you decide which constraints mattered most?

- I decided time and priority mattered most because they map directly to how a real pet owner makes decisions: "I only have so many minutes today, so do the most important things first." Everything else — chronological sorting, conflict warnings, recurrence — supports that core decision rather than competing with it. I treated conflicts as *advisory* rather than *blocking* because a human, not the app, should decide how to resolve an overlap.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

- The scheduler uses a **greedy, priority-first** selection strategy: `prioritize_tasks()` sorts every unfinished task by priority (High → Medium → Low), and `generate_schedule()` walks that list once, adding each task if it still fits in the remaining time and skipping it otherwise. It never revisits an earlier decision. The tradeoff is that this does **not** guarantee the *best* use of the available time. For example, with 60 minutes free, one High-priority 60-minute task will be chosen over three High-priority 20-minute tasks even though the latter would complete more care activities. Finding the truly optimal set is a 0/1 knapsack problem; we deliberately chose the simpler greedy approach instead.

- Why is that tradeoff reasonable for this scenario?

- It is reasonable because the greedy approach matches how a pet owner actually thinks: "do the most important things first." It is fast (O(n log n), dominated by the sort) and, just as importantly, it is **explainable** — `generate_schedule()` records a plain-language reason for every task it schedules or skips (e.g. "Groom skipped because it needs 20 min but only 0 min remain"), which a knapsack optimizer could not produce as clearly. For a single owner's daily task list — a handful of tasks, not thousands — the difference between greedy and optimal is small, while the gain in simplicity and transparency is large. A related tradeoff lives in conflict handling: `detect_conflicts()` only *warns* about overlapping task windows rather than automatically rescheduling them, leaving the human in control of the final decision.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

- I worked with Claude (through Claude Code) as a pair-programming partner across every phase of the project. In the design phase I used it to pressure-test my UML — asking whether my four classes and their relationships made sense before I wrote any code. During implementation I used it to turn the UML into class skeletons, then to fill in the scheduling logic incrementally. I leaned on it heavily for the "smarter" features (sorting, filtering, conflict detection, and recurring tasks), for writing and running the pytest suite, and for refactoring the Streamlit UI so it called my `Scheduler` methods instead of duplicating logic. I also used it to keep my documentation — the README and this reflection — in sync with the code as it changed.

- What kinds of prompts or questions were most helpful?

- The most helpful prompts were **specific and verifiable**: "verify these behaviors by actually running the code," "what edge cases matter for a scheduler with sorting and recurring tasks," and "does the UML still match the final code?" Prompts that asked the AI to *check its own claims against the running program* (rather than just describe what the code should do) gave me the most trustworthy answers. Asking for tradeoffs and edge cases up front — before writing code — was more valuable than asking for finished code, because it shaped better decisions.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

- When wiring conflict detection and the task table into the Streamlit UI, an early suggestion grouped the schedule inside `app.py` using a `defaultdict` keyed on `id(pet)` — logic that lived entirely in the view layer. I modified this to keep the design clean: instead of re-implementing grouping and ordering in the UI, I routed the display through the `Scheduler`'s own `filter_tasks()` and `sort_by_time()` methods and rendered the result in an `st.table`. This kept the UI "thin," left the logic layer as the single source of truth, and removed a now-unused import. I made the same call about `detect_conflicts()` — I kept it as a method on `Scheduler` that the UI simply *calls*, rather than embedding conflict math in the page.

- How did you evaluate or verify what the AI suggested?

- I did not take correctness on faith. I ran the full `pytest` suite after each change, and for behaviors I cared about I had the AI exercise the actual objects and print results rather than just reason about them. That process caught real issues — for example, that `sort_by_time()` *raised* on a malformed `"HH:MM"` string even though `detect_conflicts()` handled bad times gracefully. In the final hardening pass I fixed that inconsistency (both sorts now route through a shared `_time_key()` helper that places unparseable times last instead of crashing), and I confirmed the numeric sort so `"9:00"` correctly precedes `"10:00"`. Verifying against the running program, not the description of the program, was the key discipline.

**c. AI strategy — working across separate sessions**

- I deliberately used **separate chat sessions for different phases** (design/UML, class skeletons, core logic, the smarter-scheduling features, testing, and documentation). This kept me organized in a few concrete ways. Each session had one clear goal, so the context stayed focused and the AI's suggestions stayed on-topic instead of drifting across unrelated concerns. It mapped naturally onto my git history — each phase became its own set of commits — so I could reason about one layer at a time. And when something needed revisiting (like re-syncing the UML to the final code), I could open a fresh, clean session with a narrow prompt rather than wading back through a long, tangled conversation. The tradeoff was that I, not the AI, had to carry the "memory" of decisions between sessions — but that was a feature, because it forced me to stay the one who understood the whole system.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

- I tested the core scheduling behaviors with a 12-test pytest suite: marking a task complete, adding tasks to a pet, **recurrence** (completing a daily task queues a fresh copy for the next day, completing twice does not spawn duplicates, and one-off tasks do not regenerate), **sorting correctness** (chronological order, numeric ordering so `"9:00"` precedes `"10:00"`, and that sorting does not mutate the input), and **conflict detection** (same-time clashes across pets, partial overlaps, and no false alarms when times are clear).

- Why were these tests important?

- These are the behaviors a user would actually notice if they broke. A scheduler that silently mis-orders the day, loses a recurring task, or fails to warn about a double-booking would be worse than no scheduler at all. Testing sorting numerically was important because the naive string sort is a subtle, easy-to-miss bug. Testing recurrence idempotency mattered because an off-by-one there would quietly flood the list with duplicates.

**b. Confidence**

- How confident are you that your scheduler works correctly?

- I am confident (about 5 out of 5) in the **core logic** — recurrence, sorting, priority-based scheduling, conflict detection, next-available-slot, and persistence all pass their 26 tests and behave correctly when I exercise them directly. The one inconsistency I had flagged earlier — `sort_by_time()` crashing on a malformed time while `detect_conflicts()` handled it gracefully — has since been fixed, so all the sorts now degrade gracefully.

- What edge cases would you test next if you had more time?

- The malformed-time case is now handled (unparseable times sort last instead of raising), so next I would push validation to the *input boundary*: rejecting or clamping negative/zero durations, times outside `00:00–23:59`, and midnight rollover in the time math (a 23:45 task plus 30 minutes currently formats as `24:15`). I would also test unbounded growth from repeatedly completing recurring tasks, and empty cases: an owner with no pets, or a pet with no tasks.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

- I am most satisfied with how cleanly the layers separated. The logic lives entirely in `pawpal_system.py`, the tests exercise it independently, and both `main.py` and the Streamlit `app.py` are thin consumers that only *call* the `Scheduler` — they never re-implement scheduling rules. Because of that, adding the smarter features (sorting, filtering, conflict detection, recurrence) felt like extending a solid core rather than patching a UI.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

- I already made malformed times degrade gracefully in sorting and made the app recover from a corrupt save file; the next step is to push validation all the way to the input boundary (rejecting negative durations and out-of-range times before they ever reach the scheduler). I would also introduce a real date/time model so "next occurrence" means an actual tomorrow instead of a fresh copy, and consider a smarter-than-greedy planner (or at least a mode that maximizes the *number* of important tasks completed) for cases where greedy leaves time on the table.

**c. Key takeaway — being the "lead architect" with powerful AI tools**

- The biggest thing I learned is that working with a powerful AI assistant does not make me less responsible for the design — it makes me *more* responsible for it. The AI could generate correct-looking code faster than I could read it, so my real job was to stay the **lead architect**: own the class boundaries and relationships, decide the tradeoffs (greedy vs. optimal, warn vs. auto-resolve), and insist that suggestions fit the architecture rather than reshaping the architecture to fit a suggestion. I learned to treat AI output as a proposal to be *verified*, not an answer to be *accepted* — running the tests, exercising the real objects, and rejecting cleanups that would have leaked logic into the UI. Splitting the work into focused, phase-specific sessions reinforced this, because it kept me holding the mental model of the whole system while the AI handled one well-scoped layer at a time. In short: the AI was an excellent, fast collaborator, but the coherence of the design came from the human decisions about *what* to build and *what to say no to*.
