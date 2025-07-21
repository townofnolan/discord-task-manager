"""Helper functions for creating UI elements in Discord."""

from datetime import datetime

import discord

from models import TaskPriority, TaskStatus

# Pastel colors from UI kit
COLORS = {
    "blue": 0xAEE0F9,  # Light blue for task views
    "purple": 0xD8BFD8,  # Lavender for reminders
    "green": 0xB0E0B0,  # Light green for success/completion
    "yellow": 0xFFF8DC,  # Light yellow for warnings/pending
    "red": 0xFFB6C1,  # Light red for errors/important
}

PRIORITY_EMOJI = {
    TaskPriority.LOW.value: "🟢",  # Green circle for low priority
    TaskPriority.MEDIUM.value: "🟡",  # Yellow circle for medium priority
    TaskPriority.HIGH.value: "🟠",  # Orange circle for high priority
    TaskPriority.URGENT.value: "🔴",  # Red circle for urgent priority
}

STATUS_EMOJI = {
    TaskStatus.TODO.value: "📋",  # Clipboard for to-do
    TaskStatus.IN_PROGRESS.value: "⏳",  # Hourglass for in progress
    TaskStatus.DONE.value: "✅",  # Check mark for done
    TaskStatus.BLOCKED.value: "🚫",  # No entry for blocked
}


def create_task_embed(task):
    """Create a rich embed for a task, matching the UI mockup style."""

    # Determine color based on status
    color = COLORS["blue"]
    if task.status == TaskStatus.DONE.value:
        color = COLORS["green"]
    elif task.status == TaskStatus.BLOCKED.value:
        color = COLORS["red"]

    # Create embed with pastel colors and rounded appearance
    embed = discord.Embed(
        title=f"{STATUS_EMOJI.get(task.status, '📋')} {task.title}",
        description=task.description or "*No description provided*",
        color=color,
    )

    # Add priority field with emoji
    priority_emoji = PRIORITY_EMOJI.get(task.priority, "⚪")
    embed.add_field(
        name="Priority",
        value=f"{priority_emoji} {task.priority.capitalize() if task.priority else 'None'}",
        inline=True,
    )

    # Add due date with formatting
    if task.due_date:
        # Format date nicely
        due_date_str = task.due_date.strftime("%b %d, %Y")

        # Check if due date is within 3 days
        days_until_due = (task.due_date - datetime.now().date()).days

        if days_until_due < 0:
            due_str = f"⚠️ Overdue: {due_date_str}"
        elif days_until_due == 0:
            due_str = f"⏰ Due today: {due_date_str}"
        elif days_until_due <= 3:
            due_str = f"🔜 Due soon: {due_date_str}"
        else:
            due_str = f"📅 {due_date_str}"

        embed.add_field(name="Due Date", value=due_str, inline=True)

    # Add assignees field
    if task.assignees:
        assignee_list = []
        for user in task.assignees:
            if hasattr(user, "discord_id") and user.discord_id:
                assignee_list.append(f"<@{user.discord_id}>")
            else:
                assignee_list.append(str(user))

        embed.add_field(
            name="Assigned to",
            value=" ".join(assignee_list) or "*No assignees*",
            inline=False,
        )

    # Add project field if available
    if hasattr(task, "project") and task.project:
        embed.add_field(
            name="Project",
            value=(
                f"📁 {task.project.name}"
                if hasattr(task.project, "name")
                else "*No project*"
            ),
            inline=True,
        )

    # Add created date at the bottom
    if hasattr(task, "created_at") and task.created_at:
        embed.set_footer(text=f"Created: {task.created_at.strftime('%b %d, %Y')}")

    # Set thumbnail based on assignee (penguin for user, cat for partner)
    # Assuming we can identify specific users, otherwise use a default image
    if task.assignees and hasattr(task.assignees[0], "discord_id"):
        # Example: If the first assignee is user ID 123456789, show penguin
        if task.assignees[0].discord_id == "123456789":
            embed.set_thumbnail(url="attachment://penguin.png")
        # If it's user ID 987654321, show cat
        elif task.assignees[0].discord_id == "987654321":
            embed.set_thumbnail(url="attachment://cat.png")

    return embed


def create_task_list_embed(tasks, title="Tasks", user_id=None):
    """Create an embed for a list of tasks, matching the UI mockup."""
    embed = discord.Embed(
        title=f"📋 {title}",
        description=f"{len(tasks)} tasks found",
        color=COLORS["blue"],
    )

    # Group tasks by status
    todo_tasks = [t for t in tasks if t.status == TaskStatus.TODO.value]
    in_progress_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS.value]
    done_tasks = [t for t in tasks if t.status == TaskStatus.DONE.value]
    blocked_tasks = [t for t in tasks if t.status == TaskStatus.BLOCKED.value]

    # Add To-Do tasks
    if todo_tasks:
        task_list = "\n".join(
            [f"• {t.title} {PRIORITY_EMOJI.get(t.priority, '')}" for t in todo_tasks]
        )
        embed.add_field(
            name=f"{STATUS_EMOJI[TaskStatus.TODO.value]} To Do",
            value=task_list,
            inline=False,
        )

    # Add In Progress tasks
    if in_progress_tasks:
        task_list = "\n".join(
            [
                f"• {t.title} {PRIORITY_EMOJI.get(t.priority, '')}"
                for t in in_progress_tasks
            ]
        )
        embed.add_field(
            name=f"{STATUS_EMOJI[TaskStatus.IN_PROGRESS.value]} In Progress",
            value=task_list,
            inline=False,
        )

    # Add Done tasks (limited to 5 most recent)
    if done_tasks:
        # Sort by completion date if available
        done_tasks = sorted(
            done_tasks,
            key=lambda t: getattr(t, "updated_at", datetime.now()),
            reverse=True,
        )
        # Limit to 5 tasks
        limited_done = done_tasks[:5]
        task_list = "\n".join([f"• {t.title}" for t in limited_done])

        if len(done_tasks) > 5:
            task_list += f"\n*...and {len(done_tasks) - 5} more*"

        embed.add_field(
            name=f"{STATUS_EMOJI[TaskStatus.DONE.value]} Recently Completed",
            value=task_list,
            inline=False,
        )

    # Add Blocked tasks
    if blocked_tasks:
        task_list = "\n".join([f"• {t.title}" for t in blocked_tasks])
        embed.add_field(
            name=f"{STATUS_EMOJI[TaskStatus.BLOCKED.value]} Blocked",
            value=task_list,
            inline=False,
        )

    # Set thumbnail based on whose tasks are being viewed
    if title.lower().startswith("my"):
        embed.set_thumbnail(url="attachment://penguin.png")
    elif title.lower().startswith("her") or title.lower().startswith("their"):
        embed.set_thumbnail(url="attachment://cat.png")

    # Add footer
    embed.set_footer(text=f"Updated: {datetime.now().strftime('%b %d, %Y at %H:%M')}")

    return embed


def create_dashboard_embed(projects, tasks, user_id=None):
    """Create a dashboard overview embed, matching the UI mockup."""
    embed = discord.Embed(
        title="✨ Task Dashboard",
        description="Your project and task summary",
        color=COLORS["purple"],
    )

    # Add project summary
    if projects:
        project_list = "\n".join(
            [
                f"• {p.name} ({len(p.tasks) if hasattr(p, 'tasks') else '0'} tasks)"
                for p in projects[:5]
            ]
        )
        if len(projects) > 5:
            project_list += f"\n*...and {len(projects) - 5} more*"
        embed.add_field(name="📁 Projects", value=project_list, inline=False)

    # Add task statistics
    if tasks:
        # Count tasks by status
        todo_count = sum(1 for t in tasks if t.status == TaskStatus.TODO.value)
        in_progress_count = sum(
            1 for t in tasks if t.status == TaskStatus.IN_PROGRESS.value
        )
        done_count = sum(1 for t in tasks if t.status == TaskStatus.DONE.value)

        stats = f"📋 To Do: {todo_count}\n⏳ In Progress: {in_progress_count}\n✅ Done: {done_count}"
        embed.add_field(name="Task Stats", value=stats, inline=True)

        # Add upcoming deadlines
        upcoming = [
            t for t in tasks if t.status != TaskStatus.DONE.value and t.due_date
        ]
        upcoming = sorted(upcoming, key=lambda t: t.due_date)[
            :3
        ]  # Get 3 nearest deadlines

        if upcoming:
            deadline_list = "\n".join(
                [f"• {t.title}: {t.due_date.strftime('%b %d')}" for t in upcoming]
            )
            embed.add_field(
                name="⏰ Upcoming Deadlines", value=deadline_list, inline=True
            )

    # Set cute cat thumbnail (from UI mockup)
    embed.set_thumbnail(url="attachment://cat.png")

    return embed


def create_completed_tasks_embed(tasks, user_id=None):
    """Create an embed for completed tasks with celebratory styling."""
    embed = discord.Embed(
        title="✨ Completed Tasks ✨",
        description="Great job on completing these tasks!",
        color=COLORS["green"],
    )

    # Filter for completed tasks
    completed_tasks = [t for t in tasks if t.status == TaskStatus.DONE.value]

    # Sort by completion date
    completed_tasks = sorted(
        completed_tasks,
        key=lambda t: getattr(t, "updated_at", datetime.now()),
        reverse=True,
    )

    # Group by date
    by_date = {}
    for task in completed_tasks:
        completed_date = getattr(task, "updated_at", datetime.now()).strftime(
            "%b %d, %Y"
        )
        if completed_date not in by_date:
            by_date[completed_date] = []
        by_date[completed_date].append(task)

    # Add fields for each date
    for date, date_tasks in by_date.items():
        task_list = "\n".join([f"• {t.title}" for t in date_tasks])
        embed.add_field(name=f"📅 {date}", value=task_list, inline=False)

    # Set penguin thumbnail (from UI mockup)
    embed.set_thumbnail(url="attachment://penguin.png")

    # Add celebratory footer
    embed.set_footer(text=f"🎉 {len(completed_tasks)} tasks completed! 🎉")

    return embed


def create_reminders_embed(tasks, user_id=None):
    """Create an embed for task reminders and deadlines."""
    embed = discord.Embed(
        title="🔔 Upcoming Deadlines",
        description="Here are your upcoming tasks and reminders",
        color=COLORS["yellow"],
    )

    # Filter for tasks with due dates that aren't completed
    upcoming_tasks = [
        t for t in tasks if t.status != TaskStatus.DONE.value and t.due_date
    ]

    # Sort by due date
    upcoming_tasks = sorted(upcoming_tasks, key=lambda t: t.due_date)

    # Group by urgency
    overdue = [
        t for t in upcoming_tasks if (t.due_date - datetime.now().date()).days < 0
    ]
    today = [
        t for t in upcoming_tasks if (t.due_date - datetime.now().date()).days == 0
    ]
    this_week = [
        t for t in upcoming_tasks if 0 < (t.due_date - datetime.now().date()).days <= 7
    ]
    later = [t for t in upcoming_tasks if (t.due_date - datetime.now().date()).days > 7]

    # Add overdue tasks
    if overdue:
        task_list = "\n".join(
            [f"• {t.title} ({t.due_date.strftime('%b %d')})" for t in overdue]
        )
        embed.add_field(name="⚠️ Overdue", value=task_list, inline=False)

    # Add today's tasks
    if today:
        task_list = "\n".join([f"• {t.title}" for t in today])
        embed.add_field(name="⏰ Due Today", value=task_list, inline=False)

    # Add this week's tasks
    if this_week:
        task_list = "\n".join(
            [f"• {t.title} ({t.due_date.strftime('%b %d')})" for t in this_week]
        )
        embed.add_field(name="📅 This Week", value=task_list, inline=False)

    # Add later tasks
    if later:
        task_list = "\n".join(
            [f"• {t.title} ({t.due_date.strftime('%b %d')})" for t in later]
        )
        embed.add_field(name="🗓️ Later", value=task_list, inline=False)

    # Set cat thumbnail (from UI mockup)
    embed.set_thumbnail(url="attachment://cat.png")

    # Add footer with next reminder
    next_due = upcoming_tasks[0].due_date if upcoming_tasks else None
    if next_due:
        days_until = (next_due - datetime.now().date()).days
        if days_until < 0:
            next_str = "Tasks are overdue!"
        elif days_until == 0:
            next_str = "Next deadline is today!"
        else:
            next_str = (
                f"Next deadline in {days_until} day{'s' if days_until != 1 else ''}"
            )
        embed.set_footer(text=next_str)

    return embed


def create_add_task_embed():
    """Create an embed showing the add task form example."""
    embed = discord.Embed(
        title="➕ Add New Task",
        description="Fill in the details for your new task",
        color=COLORS["green"],
    )

    # Add example form fields
    embed.add_field(
        name="Title", value="Enter a clear, concise task title", inline=False
    )
    embed.add_field(
        name="Description", value="Provide details about the task", inline=False
    )
    embed.add_field(
        name="Due Date", value="When does this task need to be completed?", inline=True
    )
    embed.add_field(name="Priority", value="Set the importance level", inline=True)
    embed.add_field(
        name="Assignee", value="Who is responsible for this task?", inline=False
    )

    # Set penguin thumbnail
    embed.set_thumbnail(url="attachment://penguin.png")

    return embed


def create_assign_task_embed(task):
    """Create an embed for the assign task interface."""
    embed = discord.Embed(
        title="👥 Assign Task",
        description=f"**{task.title}**\n{task.description or '*No description provided*'}",
        color=COLORS["purple"],
    )

    # Add current assignees if any
    if task.assignees:
        assignee_list = []
        for user in task.assignees:
            if hasattr(user, "discord_id") and user.discord_id:
                assignee_list.append(f"<@{user.discord_id}>")
            else:
                assignee_list.append(str(user))

        embed.add_field(
            name="Currently Assigned To",
            value=" ".join(assignee_list) or "*No one*",
            inline=False,
        )

    embed.add_field(
        name="Choose Who To Assign", value="Select an option below:", inline=False
    )

    # We'll use both mascots in the footer
    embed.set_footer(text="Use the buttons below to assign the task")

    return embed

    # Add footer
    embed.set_footer(text=f"Updated: {datetime.now().strftime('%b %d, %Y at %H:%M')}")

    # Set thumbnail alternating between penguin and cat, or based on user
    embed.set_thumbnail(url="attachment://penguin.png")  # Default to penguin

    return embed
