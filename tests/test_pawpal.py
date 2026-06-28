"""Tests for the PawPal+ logic layer.

Run with:  pytest
"""

import os
import sys

# Make sure pawpal_system.py (in the project root) is importable when the
# tests run from inside the tests/ folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    """Calling mark_complete() should flip the task's status to completed."""
    task = Task("Walk", duration=30, frequency="daily", priority="High")

    assert task.completed is False  # starts incomplete
    task.mark_complete()
    assert task.completed is True   # now complete


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet should increase that pet's task count by one."""
    pet = Pet(name="Buddy", species="dog", age=3)

    assert len(pet.get_tasks()) == 0
    pet.add_task(Task("Feed", duration=10, frequency="daily", priority="Medium"))
    assert len(pet.get_tasks()) == 1
