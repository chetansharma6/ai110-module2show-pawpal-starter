"""PawPal+ logic layer.

Backend classes for the PawPal+ pet-care planning assistant.

Design overview:
    Owner has many Pets, each Pet has many Tasks, and the Scheduler reads an
    Owner to build a daily plan that fits the owner's available time.

Priority is a readable label: "High", "Medium", or "Low".
"""

from __future__ import annotations

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
    completed: bool = False  # whether it has been done today

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def edit_task(
        self,
        description: str | None = None,
        duration: int | None = None,
        frequency: str | None = None,
        priority: str | None = None,
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
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet (does nothing if it isn't present)."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        """Return all of this pet's tasks."""
        return self.tasks


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


class Scheduler:
    """Builds a daily plan for an owner that fits within their available time."""

    def __init__(self, owner: Owner) -> None:
        """Set up the scheduler to plan for one owner's pets."""
        self.owner = owner
        self.available_time = owner.time_available
        # Filled in by generate_schedule():
        self.schedule: list[Task] = []   # the tasks chosen for today
        self.reasoning: list[str] = []    # one explanation line per task

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
