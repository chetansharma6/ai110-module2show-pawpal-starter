"""Demo script for the PawPal+ system.

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


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
    print(f"Luna's task count before completing Feed: {len(luna.get_tasks())}")
    scheduler.mark_task_complete(feed)
    print(f"Luna's task count after completing Feed:  {len(luna.get_tasks())}")
    print("Luna's Feed tasks now:")
    for task in scheduler.filter_tasks(pet_name="Luna"):
        if task.description == "Feed":
            status = "done" if task.completed else "todo"
            print(f"  {task.time}  Feed ({status})")
    print()

    # 5. Sorting demo: all tasks ordered by time of day.
    print("All tasks sorted by time:")
    for task in scheduler.sort_by_time():
        status = "done" if task.completed else "todo"
        print(f"  {task.time}  {task.description} ({task.duration} min, {status})")

    # 6. Filtering demo: by pet name, then by completion status.
    print("\nBuddy's tasks (sorted by time):")
    buddy_tasks = scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Buddy"))
    for task in buddy_tasks:
        print(f"  {task.time}  {task.description}")

    print("\nUnfinished tasks (sorted by time):")
    todo_tasks = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    for task in todo_tasks:
        print(f"  {task.time}  {task.description}")

    print("\nCompleted tasks:")
    done_tasks = scheduler.filter_tasks(completed=True)
    for task in done_tasks:
        print(f"  {task.time}  {task.description}")

    # 6b. Conflict detection: warn about tasks whose times overlap.
    print("\nSchedule conflicts:")
    conflicts = scheduler.detect_conflicts()
    if not conflicts:
        print("  None — no overlapping tasks.")
    else:
        for warning in conflicts:
            print(f"  [!] {warning}")

    # 7. Original scheduling demo still works on top of the same data.
    schedule = scheduler.generate_schedule()
    print("\nToday's Schedule (fits in available time, priority order):")
    if not schedule:
        print("  No tasks fit in the available time today.")
    else:
        for task in schedule:
            print(f"  {task.description} ({task.duration} min, Priority: {task.priority})")

    print("\nReasoning:")
    for line in scheduler.reasoning:
        print(f"  *{line}")


if __name__ == "__main__":
    main()
