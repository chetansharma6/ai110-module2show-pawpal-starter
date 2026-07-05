"""Tests for the PawPal+ logic layer.

Run with:  pytest
"""

import os
import sys

# Make sure pawpal_system.py (in the project root) is importable when the
# tests run from inside the tests/ folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Owner, Pet, Task, Scheduler


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


def test_completing_recurring_task_queues_next_occurrence():
    """Completing a daily/weekly task should auto-add a fresh, incomplete copy."""
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Walk", duration=30, frequency="daily", priority="High", time="07:00"))

    pet.get_tasks()[0].mark_complete()

    tasks = pet.get_tasks()
    assert len(tasks) == 2                       # original + next occurrence
    assert tasks[0].completed is True            # today's is done
    next_task = tasks[1]
    assert next_task.completed is False          # next occurrence is fresh
    assert next_task.description == "Walk"       # same details carried over
    assert next_task.frequency == "daily"
    assert next_task.time == "07:00"
    assert next_task.pet is pet                  # wired back to the pet


def test_completing_twice_does_not_spawn_duplicates():
    """Re-marking an already-complete task should not queue another occurrence."""
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Walk", duration=30, frequency="daily", priority="High"))

    task = pet.get_tasks()[0]
    task.mark_complete()
    task.mark_complete()  # idempotent

    assert len(pet.get_tasks()) == 2  # not 3


def test_non_recurring_task_does_not_spawn():
    """A one-off task (not daily/weekly) should not regenerate on completion."""
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Vet visit", duration=60, frequency="once", priority="High"))

    pet.get_tasks()[0].mark_complete()

    assert len(pet.get_tasks()) == 1


def test_detect_conflicts_flags_same_time_across_pets():
    """Two tasks at the same time on different pets should be reported."""
    owner = Owner(name="Sam", time_available=120)
    buddy = Pet(name="Buddy", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    buddy.add_task(Task("Walk", duration=30, frequency="daily", priority="High", time="18:30"))
    luna.add_task(Task("Play", duration=15, frequency="daily", priority="Medium", time="18:30"))
    owner.add_pet(buddy)
    owner.add_pet(luna)

    conflicts = Scheduler(owner).detect_conflicts()

    assert len(conflicts) == 1
    assert "18:30" in conflicts[0]


def test_detect_conflicts_flags_partial_overlap():
    """Overlapping (not identical) windows should also be flagged."""
    owner = Owner(name="Sam", time_available=120)
    buddy = Pet(name="Buddy", species="dog", age=3)
    buddy.add_task(Task("Hike", duration=90, frequency="weekly", priority="Low", time="09:00"))
    buddy.add_task(Task("Vet", duration=30, frequency="once", priority="High", time="10:00"))
    owner.add_pet(buddy)

    conflicts = Scheduler(owner).detect_conflicts()

    assert len(conflicts) == 1  # 09:00-10:30 overlaps 10:00-10:30


def test_no_conflicts_when_times_are_clear():
    """Non-overlapping tasks should produce no warnings."""
    owner = Owner(name="Sam", time_available=120)
    buddy = Pet(name="Buddy", species="dog", age=3)
    buddy.add_task(Task("Walk", duration=30, frequency="daily", priority="High", time="07:00"))
    buddy.add_task(Task("Feed", duration=10, frequency="daily", priority="Medium", time="18:00"))
    owner.add_pet(buddy)

    assert Scheduler(owner).detect_conflicts() == []


# ---------------------------------------------------------------------------
# Sorting correctness: tasks come back in chronological (time-of-day) order.
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should order tasks earliest-first by time of day."""
    owner = Owner(name="Sam", time_available=120)
    buddy = Pet(name="Buddy", species="dog", age=3)
    # Added out of order on purpose.
    buddy.add_task(Task("Evening walk", duration=30, frequency="daily", priority="High", time="18:00"))
    buddy.add_task(Task("Breakfast", duration=10, frequency="daily", priority="High", time="07:30"))
    buddy.add_task(Task("Lunch", duration=10, frequency="daily", priority="Medium", time="12:00"))
    owner.add_pet(buddy)

    ordered = Scheduler(owner).sort_by_time()

    assert [task.time for task in ordered] == ["07:30", "12:00", "18:00"]
    assert [task.description for task in ordered] == ["Breakfast", "Lunch", "Evening walk"]


def test_sort_by_time_is_numeric_not_lexicographic():
    """An unpadded '9:00' must sort before '10:00' (numeric, not string, order)."""
    owner = Owner(name="Sam", time_available=120)
    luna = Pet(name="Luna", species="cat", age=5)
    luna.add_task(Task("Ten", duration=5, frequency="daily", priority="Low", time="10:00"))
    luna.add_task(Task("Nine", duration=5, frequency="daily", priority="Low", time="9:00"))
    owner.add_pet(luna)

    ordered = Scheduler(owner).sort_by_time()

    # A plain string sort would wrongly put "10:00" first because "1" < "9".
    assert [task.time for task in ordered] == ["9:00", "10:00"]


def test_sort_by_time_does_not_mutate_input():
    """Sorting returns a new list and leaves the original task order untouched."""
    owner = Owner(name="Sam", time_available=120)
    buddy = Pet(name="Buddy", species="dog", age=3)
    buddy.add_task(Task("Later", duration=5, frequency="daily", priority="Low", time="20:00"))
    buddy.add_task(Task("Earlier", duration=5, frequency="daily", priority="Low", time="06:00"))
    owner.add_pet(buddy)

    original = buddy.get_tasks()
    Scheduler(owner).sort_by_time(original)

    # Original list is still in insertion order, not sorted in place.
    assert [task.description for task in original] == ["Later", "Earlier"]


# ---------------------------------------------------------------------------
# Recurrence logic: completing a daily task creates the next day's task.
# ---------------------------------------------------------------------------

def test_completing_daily_task_creates_next_day_task():
    """Marking a daily task complete should add a fresh task for the next day."""
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Morning walk", duration=30, frequency="daily", priority="High", time="07:00"))

    original = pet.get_tasks()[0]
    original.mark_complete()

    tasks = pet.get_tasks()
    assert len(tasks) == 2                      # today's + next day's
    assert tasks[0] is original
    assert tasks[0].completed is True           # today's is done

    next_day = tasks[1]
    assert next_day.completed is False          # next day starts fresh
    assert next_day.description == "Morning walk"
    assert next_day.frequency == "daily"
    assert next_day.time == "07:00"             # same time carried over
    assert next_day.pet is pet                  # linked back to the pet
    assert next_day is not original             # a genuinely new task object
