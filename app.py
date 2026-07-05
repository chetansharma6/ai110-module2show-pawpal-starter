from collections import defaultdict

import streamlit as st

# (1) Import the existing OO logic. These classes are NOT redefined here —
# app.py only creates instances and calls their methods.
from pawpal_system import Owner, Pet, Task, Scheduler

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
# the Owner is constructed only the first time, then reused every rerun afterward.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", time_available=60)

owner = st.session_state.owner  # the persistent Owner instance

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
            )
        )
        st.success(f"Added task '{description}' to {selected_pet_name}")

st.divider()

# --- (5) Current pets and their tasks ---------------------------------------
# Re-reads from the persistent owner on every rerun, so it always reflects the
# latest pets/tasks the user has added.
st.subheader("Your Pets & Tasks")
if not owner.pets:
    st.info("No pets yet. Add one above.")
else:
    for pet in owner.pets:
        st.markdown(f"**{pet.name}** — {pet.species}, age {pet.age}")
        if not pet.get_tasks():
            st.caption("No tasks yet.")
        else:
            for task in pet.get_tasks():
                done = "✅" if task.completed else "▫️"
                st.write(
                    f"{done} {task.description} "
                    f"({task.duration} min, {task.frequency}, Priority: {task.priority})"
                )

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
        st.markdown("### Today's Schedule")
        # Group the schedule by pet in a single pass. We key on id(pet) because
        # Pet is an unhashable dataclass; id() is both hashable and identity-
        # based, so it's O(schedule) and avoids the value-equality mixups that
        # `t in pet.get_tasks()` could cause between look-alike tasks.
        by_pet = defaultdict(list)
        for t in schedule:
            by_pet[id(t.pet)].append(t)

        for pet in owner.pets:
            # Iterate owner.pets so pets print in order; each bucket is already
            # in the scheduler's chosen task order.
            pet_tasks = by_pet.get(id(pet), [])
            if not pet_tasks:
                continue
            st.markdown(f"**{pet.name}**")
            for task in pet_tasks:
                st.write(f"- {task.description} ({task.duration} min, Priority: {task.priority})")

        st.markdown("### Reasoning")
        for line in scheduler.reasoning:
            st.write(f"- {line}")
