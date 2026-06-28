"""PawPal+ logic layer.

Backend classes for the PawPal+ pet-care planning assistant.
Skeleton generated from diagrams/uml.mmd — method bodies are stubs to be
implemented next.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Pet:
    """A pet belonging to an owner."""

    name: str
    species: str
    age: int

    def update_info(self, name: str, species: str, age: int) -> None:
        """Update this pet's basic information."""
        raise NotImplementedError


@dataclass
class Task:
    """A single pet-care task (walk, feeding, meds, etc.)."""

    task_name: str
    duration: int
    priority: int
    task_type: str
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        raise NotImplementedError

    def edit_task(self, duration: int, priority: int) -> None:
        """Edit this task's duration and/or priority."""
        raise NotImplementedError


@dataclass
class Owner:
    """The pet owner using PawPal+."""

    name: str
    time_available: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def update_preferences(self, preferences: dict) -> None:
        """Update the owner's scheduling preferences."""
        raise NotImplementedError


class Scheduler:
    """Builds a daily plan from a set of tasks and available time."""

    def __init__(self, list_of_tasks: list[Task], available_time: int) -> None:
        self.list_of_tasks = list_of_tasks
        self.available_time = available_time

    def generate_schedule(self) -> list[Task]:
        """Produce a daily schedule honoring constraints and priorities."""
        raise NotImplementedError

    def prioritize_tasks(self) -> list[Task]:
        """Return tasks ordered by priority."""
        raise NotImplementedError

    def explain_plan(self) -> str:
        """Explain why the generated plan was chosen."""
        raise NotImplementedError
