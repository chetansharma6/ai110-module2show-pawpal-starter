from datetime import time
from pathlib import Path

import streamlit as st

# (1) Import the existing OO logic. These classes are NOT redefined here —
# app.py only creates instances and calls their methods.
from pawpal_system import Owner, Pet, Task, Scheduler

# Persist to data.json next to this file, so pets/tasks survive between runs.
DATA_FILE = str(Path(__file__).parent / "data.json")


def save_owner() -> None:
    """Persist the current owner to disk, surfacing any error in the UI."""
    try:
        st.session_state.owner.save_to_json(DATA_FILE)
    except OSError as exc:  # e.g. permission/disk error — don't crash the app
        st.session_state.save_error = str(exc)
    else:
        st.session_state.save_error = None


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

Enter your owner info, add pets and their tasks, then generate a daily schedule.
"""
)

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

# (2) Create ONE Owner and keep it in st.session_state so it survives reruns.
# Streamlit re-runs this whole script on every interaction; the `if` guard means
# the Owner is loaded/constructed only the first time, then reused afterward.
# On first load we try data.json so pets/tasks persist across app restarts.
if "owner" not in st.session_state:
    st.session_state.load_warning = None
    try:
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
        st.session_state.loaded_existing = True
    except FileNotFoundError:
        # No saved data yet -> start blank (normal on first run).
        st.session_state.owner = Owner(name="Jordan", time_available=60)
        st.session_state.loaded_existing = False
    except (ValueError, KeyError, TypeError) as exc:
        # Corrupt or incompatible data.json -> don't brick the app; start blank
        # and warn, keeping the bad file so the user can inspect it.
        st.session_state.owner = Owner(name="Jordan", time_available=60)
        st.session_state.loaded_existing = False
        st.session_state.load_warning = f"Could not read saved data ({exc}); started fresh."
    st.session_state.save_error = None

owner = st.session_state.owner  # the persistent Owner instance

# --- Sidebar: persistence controls -------------------------------------------
with st.sidebar:
    st.header("💾 Data")
    if st.session_state.get("load_warning"):
        st.warning(st.session_state.load_warning)
    elif st.session_state.get("loaded_existing"):
        st.caption(f"Loaded saved data from `{Path(DATA_FILE).name}`.")
    else:
        st.caption("No saved file yet — changes auto-save as you go.")

    if st.button("Save now"):
        save_owner()
        st.success("Saved.")

    if st.button("Clear saved data"):
        # Remove the file and reset to a blank owner, then rerun the page.
        Path(DATA_FILE).unlink(missing_ok=True)
        st.session_state.owner = Owner(name="Jordan", time_available=60)
        st.session_state.loaded_existing = False
        st.rerun()

    if st.session_state.get("save_error"):
        st.error(f"Could not save: {st.session_state.save_error}")

st.divider()

# --- Owner settings ----------------------------------------------------------
# These widgets default to the persisted owner's current values, and we write
# any edits back onto the same object so changes stick across reruns.
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.time_available = st.number_input(
    "Time available today (minutes)", min_value=0, max_value=600,
    value=owner.time_available, step=5,
)

st.divider()

# --- Add Pet -----------------------------------------------------------------
st.subheader("Add a Pet")
# (3) On submit, build a Pet and attach it to the owner via owner.add_pet().
with st.form("add_pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age (years)", min_value=0, max_value=40, value=2)
    add_pet_clicked = st.form_submit_button("Add pet")

if add_pet_clicked:
    if not pet_name.strip():
        st.warning("Please enter a pet name.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
        st.success(f"Added pet: {pet_name}")

st.divider()

# --- Add Task ----------------------------------------------------------------
st.subheader("Add a Task")
# Tasks belong to a pet, so we need at least one pet first.
if not owner.pets:
    st.info("Add a pet above before adding tasks.")
else:
    # (4) On submit, build a Task and attach it to the chosen pet via pet.add_task().
    with st.form("add_task_form"):
        # The selectbox shows pet names; we map the choice back to the Pet object.
        pet_names = [pet.name for pet in owner.pets]
        selected_pet_name = st.selectbox("Which pet?", pet_names)
        description = st.text_input("Task", value="Morning walk")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        # Time of day drives sort_by_time() and detect_conflicts() below.
        task_time = st.time_input("Time of day", value=time(7, 0))
        frequency = st.selectbox("Frequency", ["daily", "weekly"])
        # Capitalized labels to match Task/Scheduler's PRIORITY_RANK.
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        add_task_clicked = st.form_submit_button("Add task")

    if add_task_clicked:
        # Find the Pet object whose name was selected.
        selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)
        selected_pet.add_task(
            Task(
                description=description,
                duration=int(duration),
                frequency=frequency,
                priority=priority,
                time=task_time.strftime("%H:%M"),  # store as the "HH:MM" the logic expects
            )
        )
        st.success(f"Added task '{description}' to {selected_pet_name}")

st.divider()

# --- (5) Current pets and their tasks ---------------------------------------
# Re-reads from the persistent owner on every rerun, so it always reflects the
# latest pets/tasks the user has added. Display goes through the Scheduler's
# filter_tasks() + sort_by_time() so the table is filtered and chronological.
st.subheader("Your Pets & Tasks")
if not owner.pets:
    st.info("No pets yet. Add one above.")
else:
    for pet in owner.pets:
        st.caption(f"{pet.name} — {pet.species}, age {pet.age}")

    # A Scheduler is a cheap read-only view over the owner; build one to reuse
    # its sorting/filtering/conflict logic instead of re-implementing it here.
    view = Scheduler(owner)

    # Filter controls, backed by Scheduler.filter_tasks().
    col1, col2 = st.columns(2)
    with col1:
        pet_choice = st.selectbox(
            "Filter by pet", ["All pets"] + [pet.name for pet in owner.pets]
        )
    with col2:
        status_choice = st.selectbox(
            "Filter by status", ["All", "Outstanding", "Completed"]
        )

    pet_name = None if pet_choice == "All pets" else pet_choice
    completed = {"All": None, "Outstanding": False, "Completed": True}[status_choice]

    # filter_tasks() applies the filters; sort_by_time() orders them by time of day.
    tasks = view.sort_by_time(view.filter_tasks(completed=completed, pet_name=pet_name))

    if not tasks:
        st.info("No tasks match these filters yet.")
    else:
        # st.table renders a clean, professional grid instead of a bullet list.
        st.table(
            [
                {
                    "Time": task.time,
                    "Pet": task.pet.name if task.pet else "—",
                    "Task": task.description,
                    "Duration": f"{task.duration} min",
                    "Frequency": task.frequency,
                    "Priority": task.priority,
                    "Status": "✅ Done" if task.completed else "▫️ Open",
                }
                for task in tasks
            ]
        )

    # Conflict detection — surface overlapping time windows via st.warning /
    # celebrate a clean schedule via st.success.
    st.markdown("#### Schedule conflicts")
    conflicts = view.detect_conflicts()
    if conflicts:
        st.warning(f"Found {len(conflicts)} scheduling conflict(s):")
        for message in conflicts:
            st.warning(message)
    else:
        st.success("No conflicts — every task has a clear time slot. 🎉")

st.divider()

# --- Build Schedule ----------------------------------------------------------
st.subheader("Build Schedule")
# The Scheduler is derived from the owner, so we build it fresh on demand
# rather than persisting it (this avoids holding a stale available_time).
if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule()

    if not schedule:
        st.warning("No tasks fit in the available time today.")
    else:
        total_minutes = sum(task.duration for task in schedule)
        st.success(
            f"Planned {len(schedule)} task(s) using {total_minutes} of "
            f"{owner.time_available} available minutes."
        )

        st.markdown("### Today's Schedule")
        # Present the chosen tasks in chronological order as a clean table.
        chronological = scheduler.sort_by_time(schedule)
        st.table(
            [
                {
                    "Time": task.time,
                    "Pet": task.pet.name if task.pet else "—",
                    "Task": task.description,
                    "Duration": f"{task.duration} min",
                    "Priority": task.priority,
                }
                for task in chronological
            ]
        )

        # Warn if the chosen plan itself has overlapping time slots.
        plan_conflicts = scheduler.detect_conflicts(schedule)
        if plan_conflicts:
            st.warning("Heads up — the planned tasks overlap in time:")
            for message in plan_conflicts:
                st.warning(message)

        st.markdown("### Reasoning")
        for line in scheduler.reasoning:
            st.write(f"- {line}")

# --- Auto-save ---------------------------------------------------------------
# Streamlit reruns this whole script on every interaction, so saving here at the
# end captures the current state — owner edits, added pets, and added tasks —
# without needing a manual save after each action.
save_owner()
