"""Demo script for the PawPal+ system.

Run with:  python main.py
"""

import sys

# The formatted output uses emojis and box-drawing characters. Windows consoles
# default to cp1252, which can't encode them, so switch stdout to UTF-8 up front
# (errors="replace" so an odd character degrades gracefully instead of crashing).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):  # non-reconfigurable stream: carry on
    pass

from cli_format import color, tasks_table
from pawpal_system import Owner, Pet, Task, Scheduler


def header(title: str) -> None:
    """Print a bold, cyan-ish section header so the output is easy to scan."""
    print("\n" + color(f"── {title} ──", "grey", bold=True))


def main() -> None:
    # 1. Create the owner (60 minutes available for pet care today).
    owner = Owner(name="Sam", time_available=60)

    # 2. Create two pets.
    buddy = Pet(name="Buddy", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)

    # 3. Add tasks OUT OF ORDER (times are not chronological) so we can prove
    #    sort_by_time() actually reorders them.
    buddy.add_task(Task("Evening walk", duration=30, frequency="daily", priority="High", time="18:30"))
    buddy.add_task(Task("Morning walk", duration=30, frequency="daily", priority="High", time="07:00"))
    buddy.add_task(Task("Long weekend hike", duration=90, frequency="weekly", priority="Low", time="09:00"))

    luna.add_task(Task("Groom", duration=20, frequency="weekly", priority="Low", time="21:00"))
    luna.add_task(Task("Feed", duration=10, frequency="daily", priority="Medium", time="06:30"))

    # Deliberately create a conflict: Luna's "Play" is scheduled at 18:30, the
    # same time as Buddy's "Evening walk" above (a cross-pet clash).
    luna.add_task(Task("Play", duration=15, frequency="daily", priority="Medium", time="18:30"))

    # 4. Add the pets to the owner.
    owner.add_pet(buddy)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)

    # Recurrence demo: completing Luna's daily "Feed" should auto-queue a fresh,
    # incomplete "Feed" for the next occurrence.
    feed = luna.get_tasks()[1]  # Luna's "Feed" (daily)
    header("Recurrence: completing Luna's daily Feed")
    print(f"Luna's task count before completing Feed: {len(luna.get_tasks())}")
    scheduler.mark_task_complete(feed)
    print(f"Luna's task count after completing Feed:  {len(luna.get_tasks())}")
    luna_feeds = [t for t in scheduler.filter_tasks(pet_name="Luna") if t.description == "Feed"]
    print(tasks_table(luna_feeds))

    # 5. Sorting demo: all tasks ordered by time of day.
    header("All tasks sorted by time")
    print(tasks_table(scheduler.sort_by_time()))

    # 5b. Priority-based scheduling: priority first (High->Medium->Low), then
    #     time of day within each priority level.
    header("All tasks sorted by priority, then time")
    print(tasks_table(scheduler.sort_by_priority()))

    # 6. Filtering demo: by pet name, then by completion status.
    header("Buddy's tasks (filtered by pet, sorted by time)")
    print(tasks_table(scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Buddy"))))

    header("Outstanding tasks (filtered by status)")
    print(tasks_table(scheduler.sort_by_time(scheduler.filter_tasks(completed=False))))

    # 6b. Conflict detection: warn about tasks whose times overlap.
    header("Schedule conflicts")
    conflicts = scheduler.detect_conflicts()
    if not conflicts:
        print(color("✅ None — no overlapping tasks.", "green"))
    else:
        for warning in conflicts:
            print(color(f"⚠️  {warning}", "yellow"))

    # 7. Original scheduling demo still works on top of the same data.
    schedule = scheduler.generate_schedule()
    header("Today's Schedule (fits in available time, priority order)")
    if not schedule:
        print(color("  No tasks fit in the available time today.", "yellow"))
    else:
        print(tasks_table(schedule))

    header("Reasoning")
    for line in scheduler.reasoning:
        # Color the marker so picks (green) and skips (grey) are scannable.
        marker = color("✔", "green") if "scheduled" in line else color("✘", "grey")
        print(f"  {marker}  {line}")


if __name__ == "__main__":
    main()
