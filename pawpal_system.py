"""PawPal+ logic layer.

Backend classes for the PawPal+ pet-care planning assistant.

Design overview:
    Owner has many Pets, each Pet has many Tasks, and the Scheduler reads an
    Owner to build a daily plan that fits the owner's available time.

Priority is a readable label: "High", "Medium", or "Low".
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

# Ranks priority labels so the scheduler can sort by importance.
# Higher rank = more important. Unknown labels rank lowest (0).
PRIORITY_RANK = {"High": 3, "Medium": 2, "Low": 1}


@dataclass
class Task:
    """A single pet-care task (a walk, a feeding, medication, etc.)."""

    description: str        # what the task is, e.g. "Morning walk"
    duration: int           # how long it takes, in minutes
    frequency: str          # how often, e.g. "daily" or "weekly"
    priority: str           # "High", "Medium", or "Low"
    time: str = "00:00"     # time of day to do it, 24h "HH:MM"
    completed: bool = False  # whether it has been done today
    # Back-reference to the owning Pet, set by Pet.add_task(). Excluded from
    # equality/repr so it doesn't affect how tasks compare or print, and so it
    # never creates an infinite Pet<->Task repr loop.
    pet: "Pet | None" = field(default=None, repr=False, compare=False)

    # Frequencies that should regenerate themselves after completion.
    RECURRING = ("daily", "weekly")

    def mark_complete(self) -> None:
        """Mark this task as done.

        If the task recurs ("daily"/"weekly") and belongs to a pet, completing
        it automatically queues a fresh, incomplete copy for the next
        occurrence (tomorrow for daily, next week for weekly). Marking an
        already-complete task does nothing, so it never spawns duplicates.
        """
        if self.completed:
            return
        self.completed = True
        if self.frequency in self.RECURRING and self.pet is not None:
            # add_task() will wire the new copy's pet back-reference.
            self.pet.add_task(self._next_occurrence())

    def _next_occurrence(self) -> "Task":
        """Build the next incomplete copy of this task for its recurrence.

        The copy carries over description, duration, frequency, priority, and
        time, and is created incomplete. Because there is no calendar date in
        the model, "next occurrence" is represented purely as a fresh task
        (conceptually tomorrow for daily, next week for weekly). The copy's
        ``pet`` back-reference is wired up when it is attached via
        ``Pet.add_task``, not here.

        Returns:
            A new, incomplete ``Task`` with the same details as this one.
        """
        return Task(
            description=self.description,
            duration=self.duration,
            frequency=self.frequency,
            priority=self.priority,
            time=self.time,
        )

    def edit_task(
        self,
        description: str | None = None,
        duration: int | None = None,
        frequency: str | None = None,
        priority: str | None = None,
        time: str | None = None,
    ) -> None:
        """Update any task fields that are provided; leave the rest unchanged."""
        if description is not None:
            self.description = description
        if duration is not None:
            self.duration = duration
        if frequency is not None:
            self.frequency = frequency
        if priority is not None:
            self.priority = priority
        if time is not None:
            self.time = time

    def to_dict(self) -> dict:
        """Serialize this task to a plain dict for JSON.

        The ``pet`` back-reference is deliberately omitted — it would create a
        Pet<->Task cycle and is re-wired by ``Pet.add_task`` on load.
        """
        return {
            "description": self.description,
            "duration": self.duration,
            "frequency": self.frequency,
            "priority": self.priority,
            "time": self.time,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuild a Task from a dict produced by :meth:`to_dict`.

        Unknown keys are ignored and missing keys fall back to the field
        defaults, so older/partial ``data.json`` files still load.
        """
        return cls(
            description=data["description"],
            duration=data["duration"],
            frequency=data["frequency"],
            priority=data["priority"],
            time=data.get("time", "00:00"),
            completed=data.get("completed", False),
        )


@dataclass
class Pet:
    """A pet belonging to an owner, along with its care tasks."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def update_info(self, name: str, species: str, age: int) -> None:
        """Update this pet's basic information."""
        self.name = name
        self.species = species
        self.age = age

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        task.pet = self  # so the task can regenerate itself when completed
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet (does nothing if it isn't present)."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        """Return all of this pet's tasks."""
        return self.tasks

    def to_dict(self) -> dict:
        """Serialize this pet (and its tasks) to a plain dict for JSON."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Rebuild a Pet and its tasks from a dict produced by :meth:`to_dict`.

        Tasks are attached via ``add_task`` so each task's ``pet`` back-reference
        is wired up correctly on load.
        """
        pet = cls(name=data["name"], species=data["species"], age=data["age"])
        for task_data in data.get("tasks", []):
            pet.add_task(Task.from_dict(task_data))
        return pet


@dataclass
class Owner:
    """The pet owner using PawPal+."""

    name: str
    time_available: int     # minutes available for pet care today
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def update_preferences(self, preferences: dict) -> None:
        """Replace the owner's scheduling preferences."""
        self.preferences = preferences

    def get_all_tasks(self) -> list[Task]:
        """Collect every task from every pet into one list."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def to_dict(self) -> dict:
        """Serialize the whole owner (pets and tasks) to a plain dict for JSON."""
        return {
            "name": self.name,
            "time_available": self.time_available,
            "preferences": self.preferences,
            "pets": [pet.to_dict() for pet in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Rebuild a full Owner (with pets and tasks) from a serialized dict."""
        owner = cls(
            name=data["name"],
            time_available=data["time_available"],
            preferences=data.get("preferences", {}),
        )
        for pet_data in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pet_data))
        return owner

    def save_to_json(self, path: str = "data.json") -> None:
        """Write this owner and all pets/tasks to ``path`` as JSON.

        Persists the entire object graph so a later ``load_from_json`` restores
        the same pets, tasks, completion state, times, and preferences. Overwrites
        the file if it already exists.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> "Owner":
        """Load an owner previously saved with :meth:`save_to_json`.

        Args:
            path: Path to the JSON file (defaults to ``data.json``).

        Returns:
            The reconstructed ``Owner`` with every pet and task restored and each
            task's ``pet`` back-reference re-wired.

        Raises:
            FileNotFoundError: if ``path`` does not exist — callers that want a
                blank start on first run should catch this and create a new Owner.
        """
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


class Scheduler:
    """Builds a daily plan for an owner that fits within their available time."""

    def __init__(self, owner: Owner) -> None:
        """Set up the scheduler to plan for one owner's pets."""
        self.owner = owner
        self.available_time = owner.time_available
        # Filled in by generate_schedule():
        self.schedule: list[Task] = []   # the tasks chosen for today
        self.reasoning: list[str] = []    # one explanation line per task

    def mark_task_complete(self, task: Task) -> None:
        """Mark a task complete, auto-queuing its next occurrence if recurring.

        Thin wrapper over Task.mark_complete() so callers working through the
        Scheduler have a single entry point for completing tasks.
        """
        task.mark_complete()

    @staticmethod
    def _time_key(time_str: str) -> tuple[int, int]:
        """Sortable key for a task's time-of-day, robust to bad values.

        Returns ``(0, minutes-since-midnight)`` for a valid "HH:MM" string and
        ``(1, 0)`` for anything unparseable, so ordering is numeric (an unpadded
        "9:00" still precedes "10:00") and invalid times sort *last* instead of
        raising. This keeps sorting consistent with ``detect_conflicts`` and
        ``find_next_available_slot``, which also degrade gracefully on bad times.
        """
        minutes = Scheduler._to_minutes(time_str)
        if minutes is None:
            return (1, 0)   # unparseable: sort after all valid times
        return (0, minutes)

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks ordered by their time of day, earliest first.

        Times are "HH:MM" strings, ordered numerically so an unpadded "9:00"
        sorts before "10:00" (a plain string sort would put "10:00" first
        because the character "1" < "9"). Tasks whose time can't be parsed are
        placed last rather than raising. The input list is not modified; a new
        sorted list is returned.

        Args:
            tasks: Tasks to sort. Defaults to every task the owner has
                (``owner.get_all_tasks()``) when omitted, so it composes with
                ``filter_tasks`` — e.g. ``sort_by_time(filter_tasks(...))``.

        Returns:
            A new list of the same tasks in ascending time-of-day order.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(tasks, key=lambda task: self._time_key(task.time))

    def sort_by_priority(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks ordered by priority first, then by time of day.

        This is the priority-based scheduling order: tasks are grouped High →
        Medium → Low (unknown labels rank lowest), and *within* the same priority
        they fall back to chronological order so the day still reads top-to-bottom
        in time. The sort key is ``(-priority_rank, time_key)``:

        * ``-PRIORITY_RANK`` makes higher priority sort first (ascending sort,
          negated rank), with unknown labels defaulting to rank 0 (last).
        * ``_time_key`` breaks ties numerically (so an unpadded ``"9:00"`` still
          precedes ``"10:00"``) and places unparseable times last rather than
          raising.

        The input list is not modified; a new sorted list is returned.

        Args:
            tasks: Tasks to sort. Defaults to every task the owner has, so it
                composes with ``filter_tasks`` just like ``sort_by_time``.

        Returns:
            A new list ordered by priority (highest first), then time (earliest
            first) within each priority level.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(
            tasks,
            key=lambda task: (
                -PRIORITY_RANK.get(task.priority, 0),
                self._time_key(task.time),
            ),
        )

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return tasks filtered by completion status and/or pet name.

        Both filters are optional and combine with AND: passing both keeps only
        the named pet's tasks that also match the completion status. Any filter
        left as ``None`` is ignored, so calling with no arguments returns every
        task across every pet.

        Args:
            completed: Keep only tasks whose ``completed`` flag equals this
                value (``True`` for done, ``False`` for outstanding). ``None``
                (default) means don't filter on status.
            pet_name: Keep only tasks belonging to the pet with this exact name.
                ``None`` (default) means don't filter on pet.

        Returns:
            A new list of the matching tasks, in owner→pet→task insertion order.
        """
        results: list[Task] = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name != pet_name:
                continue
            for task in pet.get_tasks():
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results

    @staticmethod
    def _to_minutes(time_str: str) -> int | None:
        """Convert an 'HH:MM' string to minutes since midnight.

        Returns None (rather than raising) if the string isn't valid, so
        conflict detection degrades gracefully instead of crashing.
        """
        try:
            hours, minutes = time_str.split(":")
            return int(hours) * 60 + int(minutes)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _to_time_str(minutes: int) -> str:
        """Convert minutes since midnight back to an 'HH:MM' string."""
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return a warning message for each pair of tasks whose times overlap.

        A conflict is any two tasks whose [start, start + duration) minute
        windows overlap — whether they belong to the same pet or to different
        pets. Tasks are sorted by start time so each is only compared against
        later-starting ones, and the inner scan stops as soon as a task starts
        after the current one ends (so the work is closer to O(n log n) than the
        O(n²) a naive all-pairs check would cost).

        This is a lightweight, non-destructive check: it only *reports*
        conflicts (it never reschedules), it never raises, and it skips any task
        whose time string can't be parsed instead of crashing.

        Args:
            tasks: Tasks to check. Defaults to the owner's *incomplete* tasks
                when omitted, so an already-done task and its regenerated next
                occurrence don't get flagged against each other.

        Returns:
            A list of human-readable warning strings (one per overlapping pair),
            or an empty list when no tasks conflict.
        """
        if tasks is None:
            tasks = [t for t in self.owner.get_all_tasks() if not t.completed]

        # Build (start, end, task) windows in minutes, dropping bad times.
        windows = []
        for task in tasks:
            start = self._to_minutes(task.time)
            if start is None:
                continue  # unparseable time: skip rather than crash
            windows.append((start, start + task.duration, task))

        # Sort by start so we only compare a task against later-starting ones.
        windows.sort(key=lambda window: window[0])

        warnings: list[str] = []
        for i, (a_start, a_end, a) in enumerate(windows):
            for b_start, b_end, b in windows[i + 1:]:
                if b_start >= a_end:
                    break  # sorted by start: nothing further can overlap `a`
                a_pet = a.pet.name if a.pet else "Unassigned"
                b_pet = b.pet.name if b.pet else "Unassigned"
                if a_start == b_start:
                    warnings.append(
                        f"Conflict: '{a.description}' ({a_pet}) and "
                        f"'{b.description}' ({b_pet}) are both scheduled at "
                        f"{a.time}."
                    )
                else:
                    warnings.append(
                        f"Conflict: '{a.description}' ({a_pet}, "
                        f"{a.time}-{self._to_time_str(a_end)}) overlaps "
                        f"'{b.description}' ({b_pet}, "
                        f"{b.time}-{self._to_time_str(b_end)})."
                    )
        return warnings

    def find_next_available_slot(
        self,
        duration: int,
        earliest: str = "00:00",
        latest: str = "23:59",
        tasks: list[Task] | None = None,
    ) -> str | None:
        """Return the earliest start time that fits a task of ``duration`` minutes.

        Scans the day for the first open gap — between ``earliest`` and
        ``latest`` — large enough to hold a ``duration``-minute task without
        overlapping any existing task's ``[start, start + duration)`` window.
        This is the natural companion to :meth:`detect_conflicts`: rather than
        only *reporting* a clash, it *proposes* a clash-free time to use instead.

        The scan is greedy and left-to-right: it starts a cursor at ``earliest``
        and, whenever a busy window would overlap the cursor, jumps the cursor to
        the end of that window; the first point where ``duration`` minutes are
        free before the next window (or before ``latest``) is the answer. Busy
        windows are sorted once, so the work is O(n log n).

        Args:
            duration: Length of the task to place, in minutes.
            earliest: Earliest acceptable start time, "HH:MM" (default midnight).
            latest: Latest acceptable *end* time, "HH:MM" (default 23:59). The
                returned slot plus ``duration`` will not run past this.
            tasks: Existing tasks to schedule around. Defaults to the owner's
                *incomplete* tasks (so a completed task doesn't block its slot).

        Returns:
            The earliest fitting start time as an "HH:MM" string, or ``None`` if
            no gap of ``duration`` minutes exists within the window. Returns
            ``None`` for a non-positive duration or an invalid/backwards range.
        """
        if duration <= 0:
            return None

        cursor = self._to_minutes(earliest)
        limit = self._to_minutes(latest)
        if cursor is None or limit is None or cursor + duration > limit:
            return None

        if tasks is None:
            tasks = [t for t in self.owner.get_all_tasks() if not t.completed]

        # Busy windows in minutes, sorted by start; skip unparseable times.
        windows = []
        for task in tasks:
            start = self._to_minutes(task.time)
            if start is None:
                continue
            windows.append((start, start + task.duration))
        windows.sort(key=lambda window: window[0])

        for start, end in windows:
            # If the free gap before this window is big enough, we're done.
            if start >= cursor + duration:
                return self._to_time_str(cursor)
            # Otherwise this window blocks the cursor; jump past it.
            if end > cursor:
                cursor = end
                if cursor + duration > limit:
                    return None

        # No remaining windows: the slot fits if it still ends by `latest`.
        return self._to_time_str(cursor) if cursor + duration <= limit else None

    def prioritize_tasks(self) -> list[Task]:
        """Return the owner's unfinished tasks, most important first."""
        tasks = self.owner.get_all_tasks()
        unfinished = [task for task in tasks if not task.completed]
        # Sort by priority rank, highest importance first.
        return sorted(
            unfinished,
            key=lambda task: PRIORITY_RANK.get(task.priority, 0),
            reverse=True,
        )

    def generate_schedule(self) -> list[Task]:
        """Pick tasks in priority order until the available time runs out."""
        # Results are stored in self.schedule and self.reasoning (see __init__).
        self.schedule = []
        self.reasoning = []
        time_left = self.available_time

        for task in self.prioritize_tasks():
            if task.duration <= time_left:
                self.schedule.append(task)
                time_left -= task.duration
                if len(self.schedule) == 1:
                    self.reasoning.append(
                        f"{task.description} scheduled first because it has "
                        f"the highest priority."
                    )
                else:
                    self.reasoning.append(
                        f"{task.description} scheduled next because it fits "
                        f"within the available time."
                    )
            else:
                self.reasoning.append(
                    f"{task.description} skipped because it needs "
                    f"{task.duration} min but only {time_left} min remain."
                )

        return self.schedule

    def explain_plan(self) -> str:
        """Return a readable explanation of why tasks were picked or skipped."""
        if not self.reasoning:
            return "No schedule generated yet. Call generate_schedule() first."
        return "\n".join(self.reasoning)
