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

    # 3. Add tasks with different durations and priorities.
    buddy.add_task(Task("Walk", duration=30, frequency="daily", priority="High"))
    buddy.add_task(Task("Long weekend hike", duration=90, frequency="weekly", priority="Low"))

    luna.add_task(Task("Feed", duration=10, frequency="daily", priority="Medium"))
    luna.add_task(Task("Groom", duration=20, frequency="weekly", priority="Low"))

    # 4. Add the pets to the owner.
    owner.add_pet(buddy)
    owner.add_pet(luna)

    # 5. Create a scheduler and generate today's plan.
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule()

    # 6. Print a clean, readable schedule grouped by pet.
    print("Today's Schedule")

    if not schedule:
        print("\nNo tasks fit in the available time today.")
    else:
        for pet in owner.pets:
            # Keep this pet's tasks in the order the scheduler chose them.
            pet_tasks = [task for task in schedule if task in pet.get_tasks()]
            if not pet_tasks:
                continue
            print(f"\nPet: {pet.name}")
            for task in pet_tasks:
                print(f"*{task.description} ({task.duration} min, Priority: {task.priority})")

    # 7. Explain why the plan looks the way it does.
    print("\nReasoning:")
    for line in scheduler.reasoning:
        print(f"*{line}")


if __name__ == "__main__":
    main()
