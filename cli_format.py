"""User-friendly CLI formatting helpers for PawPal+.

Pure presentation layer — no scheduling logic lives here. It adds three kinds of
polish to the command-line output:

* **Emojis by task type** — a walk shows 🚶, meds show 💊, and so on, inferred
  from the task description.
* **Color-coded indicators** — priority (High/Medium/Low) and completion status
  are colored with ANSI escape codes. Colors are emitted only when stdout is an
  interactive terminal, so piped/redirected output (and this project's captured
  README samples) stay clean, plain text.
* **Structured tables** — task lists render as boxed tables via the ``tabulate``
  library, with a graceful fallback to aligned columns if it isn't installed.

Import is defensive so the rest of the app never hard-depends on ``tabulate``.
"""

from __future__ import annotations

import sys

try:
    from tabulate import tabulate

    _HAS_TABULATE = True
except ImportError:  # pragma: no cover - exercised only without the dependency
    _HAS_TABULATE = False

# Only colorize when writing to a real terminal; otherwise (pipes, files, the
# README capture) emit plain text so no raw escape codes leak through.
_USE_COLOR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

_RESET = "\033[0m"
_BOLD = "\033[1m"
_COLORS = {
    "red": "\033[31m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "grey": "\033[90m",
}

# Task-type emojis, matched by keyword against the (lowercased) description.
# First match wins, so order the more specific keys before generic ones.
_TASK_EMOJI = {
    "hike": "🥾",
    "walk": "🚶",
    "feed": "🍽️",
    "food": "🍽️",
    "med": "💊",
    "pill": "💊",
    "groom": "✂️",
    "brush": "✂️",
    "play": "🎾",
    "vet": "🏥",
    "bath": "🛁",
    "train": "🎓",
    "clean": "🧹",
    "water": "💧",
}
_DEFAULT_EMOJI = "🐾"

# Priority -> color name for the badge.
_PRIORITY_COLOR = {"High": "red", "Medium": "yellow", "Low": "green"}


def color(text: str, name: str, *, bold: bool = False) -> str:
    """Wrap ``text`` in an ANSI color (and optional bold), or return it plain.

    Returns the text unchanged when colors are disabled (non-terminal output)
    or the color name is unknown, so it is always safe to call.
    """
    code = _COLORS.get(name, "")
    if not _USE_COLOR or not code:
        return text
    prefix = (_BOLD if bold else "") + code
    return f"{prefix}{text}{_RESET}"


def task_emoji(description: str) -> str:
    """Return an emoji for a task based on keywords in its description."""
    lowered = description.lower()
    for keyword, emoji in _TASK_EMOJI.items():
        if keyword in lowered:
            return emoji
    return _DEFAULT_EMOJI


def priority_badge(priority: str) -> str:
    """Return the priority label, color-coded (High red / Medium yellow / Low green)."""
    return color(priority, _PRIORITY_COLOR.get(priority, "grey"), bold=True)


def status_badge(completed: bool) -> str:
    """Return a color-coded completion indicator (✅ done / ▫️ todo)."""
    if completed:
        return color("✅ done", "green")
    return color("▫️ todo", "grey")


def tasks_table(tasks) -> str:
    """Render a list of Task objects as a structured table.

    Columns: Task (with type emoji), Pet, Time, Duration, Priority (colored),
    and Status (colored). Uses ``tabulate`` when available and falls back to a
    simple aligned layout otherwise.
    """
    headers = ["Task", "Pet", "Time", "Duration", "Priority", "Status"]
    rows = [
        [
            f"{task_emoji(task.description)} {task.description}",
            task.pet.name if task.pet else "—",
            task.time,
            f"{task.duration} min",
            priority_badge(task.priority),
            status_badge(task.completed),
        ]
        for task in tasks
    ]

    if not rows:
        return "(no tasks)"

    if _HAS_TABULATE:
        return tabulate(rows, headers=headers, tablefmt="rounded_outline")

    # Fallback: plain aligned columns (widths ignore ANSI codes for simplicity).
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(str(cell))) for w, cell in zip(widths, row)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    out = [line, "  ".join("-" * w for w in widths)]
    for row in rows:
        out.append("  ".join(str(cell).ljust(w) for cell, w in zip(row, widths)))
    return "\n".join(out)
