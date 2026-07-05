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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

- The scheduler uses a **greedy, priority-first** selection strategy: `prioritize_tasks()` sorts every unfinished task by priority (High → Medium → Low), and `generate_schedule()` walks that list once, adding each task if it still fits in the remaining time and skipping it otherwise. It never revisits an earlier decision. The tradeoff is that this does **not** guarantee the *best* use of the available time. For example, with 60 minutes free, one High-priority 60-minute task will be chosen over three High-priority 20-minute tasks even though the latter would complete more care activities. Finding the truly optimal set is a 0/1 knapsack problem; we deliberately chose the simpler greedy approach instead.

- Why is that tradeoff reasonable for this scenario?

- It is reasonable because the greedy approach matches how a pet owner actually thinks: "do the most important things first." It is fast (O(n log n), dominated by the sort) and, just as importantly, it is **explainable** — `generate_schedule()` records a plain-language reason for every task it schedules or skips (e.g. "Groom skipped because it needs 20 min but only 0 min remain"), which a knapsack optimizer could not produce as clearly. For a single owner's daily task list — a handful of tasks, not thousands — the difference between greedy and optimal is small, while the gain in simplicity and transparency is large. A related tradeoff lives in conflict handling: `detect_conflicts()` only *warns* about overlapping task windows rather than automatically rescheduling them, leaving the human in control of the final decision.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
