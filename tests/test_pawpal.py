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


def test_sort_by_priority_orders_high_to_low_then_by_time():
    """sort_by_priority() groups High→Medium→Low, and sorts by time within a level."""
    owner = Owner(name="Sam", time_available=120)
    buddy = Pet(name="Buddy", species="dog", age=3)
    # Deliberately scrambled: a late High, an early Low, and two Mediums.
    buddy.add_task(Task("Late meds", duration=5, frequency="daily", priority="High", time="20:00"))
    buddy.add_task(Task("Early play", duration=5, frequency="daily", priority="Low", time="06:00"))
    buddy.add_task(Task("Noon feed", duration=5, frequency="daily", priority="Medium", time="12:00"))
    buddy.add_task(Task("Dawn feed", duration=5, frequency="daily", priority="Medium", time="07:00"))
    owner.add_pet(buddy)

    ordered = Scheduler(owner).sort_by_priority()

    # High first (regardless of its late time), then Mediums earliest-first,
    # then Low last (regardless of its early time).
    assert [task.description for task in ordered] == [
        "Late meds",   # High, 20:00
        "Dawn feed",   # Medium, 07:00
        "Noon feed",   # Medium, 12:00
        "Early play",  # Low, 06:00
    ]


def test_sort_by_priority_breaks_ties_by_time_numerically():
    """Within one priority, '9:00' must sort before '10:00' (numeric, not string)."""
    owner = Owner(name="Sam", time_available=120)
    luna = Pet(name="Luna", species="cat", age=5)
    luna.add_task(Task("Ten", duration=5, frequency="daily", priority="High", time="10:00"))
    luna.add_task(Task("Nine", duration=5, frequency="daily", priority="High", time="9:00"))
    owner.add_pet(luna)

    ordered = Scheduler(owner).sort_by_priority()

    assert [task.time for task in ordered] == ["9:00", "10:00"]


def test_sort_by_priority_ranks_unknown_priority_last():
    """An unrecognized priority label should sort after all known levels."""
    owner = Owner(name="Sam", time_available=120)
    pet = Pet(name="Rex", species="dog", age=2)
    pet.add_task(Task("Mystery", duration=5, frequency="daily", priority="URGENT", time="06:00"))
    pet.add_task(Task("Real low", duration=5, frequency="daily", priority="Low", time="09:00"))
    owner.add_pet(pet)

    ordered = Scheduler(owner).sort_by_priority()

    assert [task.description for task in ordered] == ["Real low", "Mystery"]


def test_sort_by_time_places_unparseable_time_last_without_raising():
    """A malformed time must not crash the sort — it sorts to the end."""
    owner = Owner(name="Sam", time_available=120)
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Bad", duration=5, frequency="daily", priority="Low", time="oops"))
    pet.add_task(Task("Good", duration=5, frequency="daily", priority="Low", time="08:00"))
    owner.add_pet(pet)

    ordered = Scheduler(owner).sort_by_time()

    assert [task.description for task in ordered] == ["Good", "Bad"]


def test_sort_by_priority_places_unparseable_time_last_within_level():
    """Within a priority level, a malformed time sorts last (no crash)."""
    owner = Owner(name="Sam", time_available=120)
    pet = Pet(name="Buddy", species="dog", age=3)
    pet.add_task(Task("Bad time", duration=5, frequency="daily", priority="High", time="25:99:00"))
    pet.add_task(Task("Good time", duration=5, frequency="daily", priority="High", time="08:00"))
    owner.add_pet(pet)

    ordered = Scheduler(owner).sort_by_priority()

    assert [task.description for task in ordered] == ["Good time", "Bad time"]


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


# ---------------------------------------------------------------------------
# Next available slot: propose the earliest conflict-free time for a new task.
# ---------------------------------------------------------------------------

def _owner_with_tasks(*specs):
    """Helper: build an Owner whose single pet has tasks (description, time, duration)."""
    owner = Owner(name="Sam", time_available=600)
    pet = Pet(name="Buddy", species="dog", age=3)
    for description, time_str, duration in specs:
        pet.add_task(Task(description, duration=duration, frequency="daily",
                          priority="Medium", time=time_str))
    owner.add_pet(pet)
    return owner


def test_next_slot_returns_earliest_when_day_is_empty():
    """With no tasks, the earliest bound itself should be free."""
    owner = _owner_with_tasks()
    assert Scheduler(owner).find_next_available_slot(30, earliest="08:00") == "08:00"


def test_next_slot_skips_past_a_blocking_task():
    """A task occupying the earliest slot should push the answer to its end."""
    owner = _owner_with_tasks(("Walk", "08:00", 30))  # busy 08:00-08:30
    # A 30-min task can't start at 08:00, so the next free start is 08:30.
    assert Scheduler(owner).find_next_available_slot(30, earliest="08:00") == "08:30"


def test_next_slot_finds_gap_between_two_tasks():
    """It should place a task in a gap large enough between two busy windows."""
    owner = _owner_with_tasks(("A", "08:00", 30), ("B", "10:00", 30))  # gap 08:30-10:00
    # 60 min fits in the 90-min gap starting at 08:30.
    assert Scheduler(owner).find_next_available_slot(60, earliest="08:00") == "08:30"


def test_next_slot_returns_none_when_it_cannot_fit_before_latest():
    """If nothing fits before the `latest` bound, it should return None."""
    owner = _owner_with_tasks(("A", "08:00", 60))  # busy 08:00-09:00
    # Only 08:00-09:00 window allowed, and it's fully occupied.
    assert Scheduler(owner).find_next_available_slot(30, earliest="08:00", latest="09:00") is None


def test_next_slot_ignores_completed_tasks():
    """A completed task should not block its own time slot."""
    owner = _owner_with_tasks(("Walk", "08:00", 30))
    owner.pets[0].get_tasks()[0].completed = True
    # The 08:00 task is done, so 08:00 is free again.
    assert Scheduler(owner).find_next_available_slot(30, earliest="08:00") == "08:00"


def test_next_slot_rejects_non_positive_duration():
    """A zero or negative duration has no valid slot."""
    owner = _owner_with_tasks()
    assert Scheduler(owner).find_next_available_slot(0) is None
    assert Scheduler(owner).find_next_available_slot(-15) is None


# ---------------------------------------------------------------------------
# Persistence: save/load the owner (and its pets/tasks) to JSON.
# ---------------------------------------------------------------------------

def test_save_and_load_round_trip_preserves_data(tmp_path):
    """Saving then loading should reproduce the owner, pets, tasks, and state."""
    owner = Owner(name="Sam", time_available=90, preferences={"quiet": "22:00"})
    buddy = Pet(name="Buddy", species="dog", age=3)
    buddy.add_task(Task("Walk", duration=30, frequency="daily", priority="High", time="07:00"))
    luna = Pet(name="Luna", species="cat", age=5)
    done = Task("Feed", duration=10, frequency="daily", priority="Medium", time="06:30")
    luna.add_task(done)
    done.mark_complete()  # completed flag must survive
    owner.add_pet(buddy)
    owner.add_pet(luna)

    path = tmp_path / "data.json"
    owner.save_to_json(str(path))
    loaded = Owner.load_from_json(str(path))

    assert loaded.name == "Sam"
    assert loaded.time_available == 90
    assert loaded.preferences == {"quiet": "22:00"}
    assert [p.name for p in loaded.pets] == ["Buddy", "Luna"]

    loaded_luna = loaded.pets[1]
    # Feed (completed) + its regenerated copy both persisted.
    assert [(t.description, t.completed) for t in loaded_luna.get_tasks()] == [
        ("Feed", True),
        ("Feed", False),
    ]


def test_loaded_tasks_have_pet_back_reference_rewired(tmp_path):
    """After loading, each task's .pet must point back to its owning Pet."""
    owner = Owner(name="Sam", time_available=60)
    buddy = Pet(name="Buddy", species="dog", age=3)
    buddy.add_task(Task("Walk", duration=30, frequency="daily", priority="High", time="07:00"))
    owner.add_pet(buddy)

    path = tmp_path / "data.json"
    owner.save_to_json(str(path))
    loaded = Owner.load_from_json(str(path))

    loaded_pet = loaded.pets[0]
    assert loaded_pet.get_tasks()[0].pet is loaded_pet


def test_load_missing_file_raises(tmp_path):
    """Loading a non-existent file raises FileNotFoundError (caller handles first run)."""
    import pytest

    with pytest.raises(FileNotFoundError):
        Owner.load_from_json(str(tmp_path / "nope.json"))
