"""Task UI examples using the UI mockup designs."""

import os
from datetime import datetime
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from models import TaskPriority, TaskStatus
from services import ProjectService, TaskService
from utils.ui_helper import (
    COLORS,
    create_add_task_embed,
    create_assign_task_embed,
    create_completed_tasks_embed,
    create_dashboard_embed,
    create_reminders_embed,
    create_task_embed,
    create_task_list_embed,
)


class DashboardView(discord.ui.View):
    """View for the dashboard with buttons for different sections."""

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="My Tasks", style=discord.ButtonStyle.primary, emoji="🐧")
    async def my_tasks(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show my tasks view."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the task list embed
            embed = create_task_list_embed(tasks, title="My Tasks", user_id=user_id)

            # Load mascot image
            penguin_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "assets",
                "ui",
                "penguin.png",
            )

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))

            # Create task list view with buttons
            view = TaskListView(tasks=tasks, user_id=user_id, is_my_tasks=True)

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying tasks: {str(e)}", ephemeral=True
            )

    @discord.ui.button(
        label="Reminders", style=discord.ButtonStyle.secondary, emoji="🔔"
    )
    async def reminders(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show reminders view."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the reminders embed
            embed = create_reminders_embed(tasks, user_id=user_id)

            # Load mascot image
            cat_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "ui", "cat.png"
            )

            files = []
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            # Create task list view with buttons
            view = ReminderView()

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying reminders: {str(e)}", ephemeral=True
            )

    @discord.ui.button(label="Completed", style=discord.ButtonStyle.success, emoji="✅")
    async def completed(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show completed tasks view."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the completed tasks embed
            embed = create_completed_tasks_embed(tasks, user_id=user_id)

            # Load mascot image
            penguin_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "assets",
                "ui",
                "penguin.png",
            )

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))

            await interaction.followup.send(embed=embed, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying completed tasks: {str(e)}", ephemeral=True
            )

    @discord.ui.button(label="Add Task", style=discord.ButtonStyle.success, emoji="➕")
    async def add_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show add task modal."""
        # Create the add task modal
        modal = AddTaskModal()
        await interaction.response.send_modal(modal)


class TaskListView(discord.ui.View):
    """View for task lists with toggle between My Tasks and Their Tasks."""

    def __init__(self, tasks=None, user_id=None, is_my_tasks=True):
        super().__init__(timeout=300)
        self.tasks = tasks or []
        self.user_id = user_id
        self.is_my_tasks = is_my_tasks

    @discord.ui.button(
        label="My Tasks", style=discord.ButtonStyle.primary, emoji="🐧", disabled=True
    )
    async def my_tasks(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Toggle to My Tasks view."""
        if self.is_my_tasks:
            # Already showing my tasks
            await interaction.response.defer()
            return

        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the task list embed
            embed = create_task_list_embed(tasks, title="My Tasks", user_id=user_id)

            # Update button states
            self.is_my_tasks = True
            self.children[0].disabled = True  # My Tasks button
            self.children[1].disabled = False  # Their Tasks button

            # Load mascot image
            penguin_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "assets",
                "ui",
                "penguin.png",
            )

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))

            await interaction.followup.send(embed=embed, view=self, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying tasks: {str(e)}", ephemeral=True
            )

    @discord.ui.button(
        label="Their Tasks", style=discord.ButtonStyle.secondary, emoji="🐱"
    )
    async def their_tasks(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Toggle to Their Tasks view."""
        if not self.is_my_tasks:
            # Already showing their tasks
            await interaction.response.defer()
            return

        await interaction.response.defer(thinking=True)

        try:
            # Get tasks assigned to others (simplified example)
            tasks = await TaskService.get_all_tasks()
            their_tasks = [
                t
                for t in tasks
                if str(interaction.user.id)
                not in [
                    getattr(u, "discord_id", "") for u in getattr(t, "assignees", [])
                ]
            ]

            # Create the task list embed
            embed = create_task_list_embed(their_tasks, title="Their Tasks")

            # Update button states
            self.is_my_tasks = False
            self.children[0].disabled = False  # My Tasks button
            self.children[1].disabled = True  # Their Tasks button

            # Load mascot image
            cat_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "ui", "cat.png"
            )

            files = []
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            await interaction.followup.send(embed=embed, view=self, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying tasks: {str(e)}", ephemeral=True
            )

    @discord.ui.button(label="Add Task", style=discord.ButtonStyle.success, emoji="➕")
    async def add_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show add task modal."""
        # Create the add task modal
        modal = AddTaskModal()
        await interaction.response.send_modal(modal)


class ReminderView(discord.ui.View):
    """View for reminders screen."""

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Dismiss All", style=discord.ButtonStyle.secondary)
    async def dismiss_all(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Dismiss all reminders."""
        await interaction.response.send_message(
            "All reminders dismissed", ephemeral=True
        )


class TaskDetailView(discord.ui.View):
    """View for task details with action buttons."""

    def __init__(self, task_id):
        super().__init__(timeout=300)
        self.task_id = task_id

    @discord.ui.button(label="Complete", style=discord.ButtonStyle.success, emoji="✅")
    async def complete_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Mark task as complete."""
        await interaction.response.defer(thinking=True)

        try:
            # Update task status to Done
            task = await TaskService.update_task(
                self.task_id, status=TaskStatus.DONE.value
            )

            if task:
                # Create updated embed
                embed = create_task_embed(task)

                # Load mascot images
                files = []
                penguin_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "penguin.png",
                )
                cat_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "cat.png",
                )

                if os.path.exists(penguin_path):
                    files.append(discord.File(penguin_path, filename="penguin.png"))
                if os.path.exists(cat_path):
                    files.append(discord.File(cat_path, filename="cat.png"))

                # Disable the complete button
                self.children[0].disabled = True

                await interaction.followup.send(embed=embed, view=self, files=files)
            else:
                await interaction.followup.send("Failed to update task", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"Error completing task: {str(e)}", ephemeral=True
            )

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Edit task details."""
        # Get current task data
        task = await TaskService.get_task_by_id(self.task_id)

        if not task:
            await interaction.response.send_message("Task not found", ephemeral=True)
            return

        # Create and send edit modal
        modal = EditTaskModal(self.task_id, task)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Assign", style=discord.ButtonStyle.secondary, emoji="👤")
    async def assign_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Assign task to someone."""
        await interaction.response.defer(thinking=True)

        try:
            task = await TaskService.get_task_by_id(self.task_id)

            if task:
                # Create assignment embed
                embed = create_assign_task_embed(task)

                # Load mascot images
                files = []
                penguin_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "penguin.png",
                )
                cat_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "cat.png",
                )

                if os.path.exists(penguin_path):
                    files.append(discord.File(penguin_path, filename="penguin.png"))
                if os.path.exists(cat_path):
                    files.append(discord.File(cat_path, filename="cat.png"))

                # Create assignment view
                view = TaskAssignView(self.task_id)

                await interaction.followup.send(embed=embed, view=view, files=files)
            else:
                await interaction.followup.send("Task not found", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"Error assigning task: {str(e)}", ephemeral=True
            )


class TaskAssignView(discord.ui.View):
    """View for assigning tasks to users."""

    def __init__(self, task_id):
        super().__init__(timeout=300)
        self.task_id = task_id

    @discord.ui.button(
        label="Assign to Me", style=discord.ButtonStyle.primary, emoji="🐧"
    )
    async def assign_to_me(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Assign the task to the current user."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)

            # Update task with the new assignee
            task = await TaskService.assign_task(self.task_id, user_id)

            if task:
                # Create updated task embed
                embed = create_task_embed(task)

                # Load mascot images
                files = []
                penguin_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "penguin.png",
                )
                cat_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "cat.png",
                )

                if os.path.exists(penguin_path):
                    files.append(discord.File(penguin_path, filename="penguin.png"))
                if os.path.exists(cat_path):
                    files.append(discord.File(cat_path, filename="cat.png"))

                # Create task detail view
                view = TaskDetailView(self.task_id)

                await interaction.followup.send(
                    f"Task assigned to you!", embed=embed, view=view, files=files
                )
            else:
                await interaction.followup.send("Failed to assign task", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"Error assigning task: {str(e)}", ephemeral=True
            )

    @discord.ui.button(
        label="Assign to Them", style=discord.ButtonStyle.secondary, emoji="🐱"
    )
    async def assign_to_them(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show modal to select another user to assign to."""
        # Create user selection modal
        modal = AssignUserModal(self.task_id)
        await interaction.response.send_modal(modal)


class AddTaskModal(discord.ui.Modal, title="Add New Task"):
    """Modal for adding a new task."""

    task_title = discord.ui.TextInput(
        label="Title",
        placeholder="Enter a clear, concise task title",
        required=True,
        max_length=100,
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Provide details about the task",
        required=False,
        max_length=1000,
        style=discord.TextStyle.paragraph,
    )

    due_date = discord.ui.TextInput(
        label="Due Date",
        placeholder="YYYY-MM-DD (optional)",
        required=False,
        max_length=10,
    )

    priority = discord.ui.TextInput(
        label="Priority",
        placeholder="low, medium, high, urgent (default: medium)",
        required=False,
        max_length=10,
    )

    assignees = discord.ui.TextInput(
        label="Assignees",
        placeholder="@mentions or user IDs (optional)",
        required=False,
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Process the form submission."""
        await interaction.response.defer(thinking=True)

        try:
            # Parse inputs
            title = self.task_title.value
            description = self.description.value

            # Parse due date
            due_date = None
            if self.due_date.value:
                try:
                    due_date = datetime.strptime(self.due_date.value, "%Y-%m-%d").date()
                except ValueError:
                    await interaction.followup.send(
                        "Invalid date format. Please use YYYY-MM-DD", ephemeral=True
                    )
                    return

            # Parse priority
            priority = self.priority.value.lower() if self.priority.value else "medium"
            if priority not in [p.value for p in TaskPriority]:
                priority = TaskPriority.MEDIUM.value

            # Create the task
            task = await TaskService.create_task(
                title=title,
                description=description,
                creator_id=str(interaction.user.id),
                due_date=due_date,
                priority=priority,
                status=TaskStatus.TODO.value,
            )

            if task:
                # If assignees were provided, assign the task
                if self.assignees.value:
                    # Parse assignee mentions or IDs
                    # This is a simplification - you'd need to extract user IDs from mentions
                    assignee_id = str(interaction.user.id)  # Default to self
                    await TaskService.assign_task(task.id, assignee_id)

                # Get the updated task
                task = await TaskService.get_task_by_id(task.id)

                # Create task embed
                embed = create_task_embed(task)

                # Load mascot images
                files = []
                penguin_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "penguin.png",
                )
                cat_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "cat.png",
                )

                if os.path.exists(penguin_path):
                    files.append(discord.File(penguin_path, filename="penguin.png"))
                if os.path.exists(cat_path):
                    files.append(discord.File(cat_path, filename="cat.png"))

                # Create task detail view
                view = TaskDetailView(task.id)

                await interaction.followup.send(
                    "Task created!", embed=embed, view=view, files=files
                )
            else:
                await interaction.followup.send("Failed to create task", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"Error creating task: {str(e)}", ephemeral=True
            )


class EditTaskModal(discord.ui.Modal, title="Edit Task"):
    """Modal for editing an existing task."""

    def __init__(self, task_id, task=None):
        super().__init__()
        self.task_id = task_id

        # Add text inputs with pre-filled values if task is provided
        self.task_title = discord.ui.TextInput(
            label="Title",
            placeholder="Enter a clear, concise task title",
            required=True,
            max_length=100,
            default=task.title if task and hasattr(task, "title") else "",
        )
        self.add_item(self.task_title)

        self.description = discord.ui.TextInput(
            label="Description",
            placeholder="Provide details about the task",
            required=False,
            max_length=1000,
            style=discord.TextStyle.paragraph,
            default=task.description if task and hasattr(task, "description") else "",
        )
        self.add_item(self.description)

        due_date_default = ""
        if task and hasattr(task, "due_date") and task.due_date:
            due_date_default = task.due_date.strftime("%Y-%m-%d")

        self.due_date = discord.ui.TextInput(
            label="Due Date",
            placeholder="YYYY-MM-DD (optional)",
            required=False,
            max_length=10,
            default=due_date_default,
        )
        self.add_item(self.due_date)

        priority_default = ""
        if task and hasattr(task, "priority") and task.priority:
            priority_default = task.priority

        self.priority = discord.ui.TextInput(
            label="Priority",
            placeholder="low, medium, high, urgent (default: medium)",
            required=False,
            max_length=10,
            default=priority_default,
        )
        self.add_item(self.priority)

    async def on_submit(self, interaction: discord.Interaction):
        """Process the form submission."""
        await interaction.response.defer(thinking=True)

        try:
            # Parse inputs
            title = self.task_title.value
            description = self.description.value

            # Parse due date
            due_date = None
            if self.due_date.value:
                try:
                    due_date = datetime.strptime(self.due_date.value, "%Y-%m-%d").date()
                except ValueError:
                    await interaction.followup.send(
                        "Invalid date format. Please use YYYY-MM-DD", ephemeral=True
                    )
                    return

            # Parse priority
            priority = self.priority.value.lower() if self.priority.value else "medium"
            if priority not in [p.value for p in TaskPriority]:
                priority = TaskPriority.MEDIUM.value

            # Update the task
            task = await TaskService.update_task(
                self.task_id,
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
            )

            if task:
                # Create task embed
                embed = create_task_embed(task)

                # Load mascot images
                files = []
                penguin_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "penguin.png",
                )
                cat_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "cat.png",
                )

                if os.path.exists(penguin_path):
                    files.append(discord.File(penguin_path, filename="penguin.png"))
                if os.path.exists(cat_path):
                    files.append(discord.File(cat_path, filename="cat.png"))

                # Create task detail view
                view = TaskDetailView(self.task_id)

                await interaction.followup.send(
                    "Task updated!", embed=embed, view=view, files=files
                )
            else:
                await interaction.followup.send("Failed to update task", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"Error updating task: {str(e)}", ephemeral=True
            )


class AssignUserModal(discord.ui.Modal, title="Assign Task"):
    """Modal for assigning a task to another user."""

    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id

        self.user_input = discord.ui.TextInput(
            label="User",
            placeholder="@mention or user ID",
            required=True,
            max_length=100,
        )
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        """Process the form submission."""
        await interaction.response.defer(thinking=True)

        try:
            # Parse user input to extract user ID
            # This is a simplification - you'd need to extract user IDs from mentions
            user_id = self.user_input.value

            # Update task with the new assignee
            task = await TaskService.assign_task(self.task_id, user_id)

            if task:
                # Create updated task embed
                embed = create_task_embed(task)

                # Load mascot images
                files = []
                penguin_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "penguin.png",
                )
                cat_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "cat.png",
                )

                if os.path.exists(penguin_path):
                    files.append(discord.File(penguin_path, filename="penguin.png"))
                if os.path.exists(cat_path):
                    files.append(discord.File(cat_path, filename="cat.png"))

                # Create task detail view
                view = TaskDetailView(self.task_id)

                await interaction.followup.send(
                    f"Task assigned!", embed=embed, view=view, files=files
                )
            else:
                await interaction.followup.send("Failed to assign task", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"Error assigning task: {str(e)}", ephemeral=True
            )


class TaskUIExamples(commands.Cog):
    """Examples of task UI implementations using the mockup designs."""

    def __init__(self, bot):
        self.bot = bot

        # Create file path for UI assets
        self.asset_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "ui"
        )

        # Check if UI assets directory exists
        if not os.path.exists(self.asset_path):
            os.makedirs(self.asset_path, exist_ok=True)

    @app_commands.command(name="dashboard", description="Show your task dashboard")
    async def dashboard(self, interaction: discord.Interaction):
        """Display the dashboard overview from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)
            projects = await ProjectService.get_projects_for_user(user_id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the dashboard embed
            embed = create_dashboard_embed(projects, tasks, user_id)

            # Load mascot images
            penguin_path = os.path.join(self.asset_path, "penguin.png")
            cat_path = os.path.join(self.asset_path, "cat.png")

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            # Create dashboard view with buttons
            view = DashboardView()

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying dashboard: {str(e)}", ephemeral=True
            )

    @app_commands.command(name="my_tasks", description="Show your assigned tasks")
    async def my_tasks(self, interaction: discord.Interaction):
        """Display the My Tasks view from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the task list embed
            embed = create_task_list_embed(tasks, title="My Tasks", user_id=user_id)

            # Load mascot image
            penguin_path = os.path.join(self.asset_path, "penguin.png")

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))

            # Create task list view with buttons
            view = TaskListView(tasks=tasks, user_id=user_id, is_my_tasks=True)

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying tasks: {str(e)}", ephemeral=True
            )

    @app_commands.command(
        name="their_tasks", description="Show tasks assigned to someone else"
    )
    @app_commands.describe(user="The user whose tasks to view")
    async def their_tasks(
        self, interaction: discord.Interaction, user: Optional[discord.User] = None
    ):
        """Display the Other Person's Tasks view from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            target_user = user or interaction.user
            target_user_id = str(target_user.id)

            # Get tasks for the specified user
            if user:
                tasks = await TaskService.get_tasks_for_user(target_user_id)
                title = f"{target_user.display_name}'s Tasks"
            else:
                # Get tasks not assigned to the current user
                all_tasks = await TaskService.get_all_tasks()
                tasks = [
                    t
                    for t in all_tasks
                    if str(interaction.user.id)
                    not in [
                        getattr(u, "discord_id", "")
                        for u in getattr(t, "assignees", [])
                    ]
                ]
                title = "Their Tasks"

            # Create the task list embed
            embed = create_task_list_embed(tasks, title=title)

            # Load mascot image
            cat_path = os.path.join(self.asset_path, "cat.png")

            files = []
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            # Create task list view
            view = TaskListView(tasks=tasks, is_my_tasks=False)

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying tasks: {str(e)}", ephemeral=True
            )

    @app_commands.command(name="task", description="Show details for a specific task")
    @app_commands.describe(task_id="The ID of the task to view")
    async def show_task(self, interaction: discord.Interaction, task_id: int):
        """Display the task detail view from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            # Get the task
            task = await TaskService.get_task_by_id(task_id)

            if not task:
                await interaction.followup.send("Task not found", ephemeral=True)
                return

            # Create task embed
            embed = create_task_embed(task)

            # Load mascot images
            penguin_path = os.path.join(self.asset_path, "penguin.png")
            cat_path = os.path.join(self.asset_path, "cat.png")

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            # Create task detail view
            view = TaskDetailView(task_id)

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying task: {str(e)}", ephemeral=True
            )

    @app_commands.command(name="add_task", description="Create a new task")
    async def create_task(self, interaction: discord.Interaction):
        """Display the add task modal from the mockup."""
        # Create and send the modal
        modal = AddTaskModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="reminders", description="Show upcoming task deadlines")
    async def reminders(self, interaction: discord.Interaction):
        """Display the reminders view from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the reminders embed
            embed = create_reminders_embed(tasks, user_id=user_id)

            # Load mascot image
            cat_path = os.path.join(self.asset_path, "cat.png")

            files = []
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            # Create reminder view
            view = ReminderView()

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying reminders: {str(e)}", ephemeral=True
            )

    @app_commands.command(name="completed_tasks", description="Show completed tasks")
    async def completed_tasks(self, interaction: discord.Interaction):
        """Display the completed tasks view from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the completed tasks embed
            embed = create_completed_tasks_embed(tasks, user_id=user_id)

            # Load mascot image
            penguin_path = os.path.join(self.asset_path, "penguin.png")

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))

            await interaction.followup.send(embed=embed, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying completed tasks: {str(e)}", ephemeral=True
            )

    @app_commands.command(name="assign_task", description="Assign a task to someone")
    @app_commands.describe(task_id="The ID of the task to assign")
    async def assign_task(self, interaction: discord.Interaction, task_id: int):
        """Display the assign task view from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            # Get the task
            task = await TaskService.get_task_by_id(task_id)

            if not task:
                await interaction.followup.send("Task not found", ephemeral=True)
                return

            # Create assign task embed
            embed = create_assign_task_embed(task)

            # Load mascot images
            penguin_path = os.path.join(self.asset_path, "penguin.png")
            cat_path = os.path.join(self.asset_path, "cat.png")

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            # Create task assign view
            view = TaskAssignView(task_id)

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying assign task view: {str(e)}", ephemeral=True
            )


async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(TaskUIExamples(bot))


import os
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from models import TaskStatus
from services import ProjectService, TaskService
from utils.ui_helper import (
    COLORS,
    create_dashboard_embed,
    create_task_embed,
    create_task_list_embed,
)


class TaskUIExamples(commands.Cog):
    """Examples of task UI implementations using the mockup designs."""

    def __init__(self, bot):
        self.bot = bot

        # Create file path for UI assets
        self.asset_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "ui"
        )

        # Check if UI assets directory exists
        if not os.path.exists(self.asset_path):
            os.makedirs(self.asset_path, exist_ok=True)

    @app_commands.command(name="dashboard", description="Show your task dashboard")
    async def dashboard(self, interaction: discord.Interaction):
        """Display the dashboard overview from the mockup."""
        await interaction.response.defer(thinking=True)

        # Get user's projects and tasks
        try:
            user_id = str(interaction.user.id)
            projects = await ProjectService.get_projects_for_user(user_id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the dashboard embed
            embed = create_dashboard_embed(projects, tasks, user_id)

            # Load mascot images
            penguin_path = os.path.join(self.asset_path, "penguin.png")
            cat_path = os.path.join(self.asset_path, "cat.png")

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            # Create dashboard view with buttons
            view = DashboardView()

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying dashboard: {str(e)}", ephemeral=True
            )

    @app_commands.command(name="my_tasks", description="Show your assigned tasks")
    async def my_tasks(self, interaction: discord.Interaction):
        """Display the My Tasks view from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(interaction.user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the task list embed
            embed = create_task_list_embed(tasks, title="My Tasks", user_id=user_id)

            # Load mascot image
            penguin_path = os.path.join(self.asset_path, "penguin.png")

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))

            # Create task list view with buttons
            view = TaskListView(tasks=tasks, user_id=user_id, is_my_tasks=True)

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying tasks: {str(e)}", ephemeral=True
            )

    @app_commands.command(
        name="their_tasks", description="Show tasks assigned to someone else"
    )
    @app_commands.describe(user="The user whose tasks to view")
    async def their_tasks(self, interaction: discord.Interaction, user: discord.User):
        """Display the Other Person's Tasks view from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            user_id = str(user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the task list embed
            embed = create_task_list_embed(
                tasks, title=f"{user.display_name}'s Tasks", user_id=user_id
            )

            # Load mascot image
            cat_path = os.path.join(self.asset_path, "cat.png")

            files = []
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            # Create task list view with buttons
            view = TaskListView(tasks=tasks, user_id=user_id, is_my_tasks=False)

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying tasks: {str(e)}", ephemeral=True
            )

    @app_commands.command(name="task", description="Show details for a task")
    @app_commands.describe(task_id="The ID of the task to view")
    async def show_task(self, interaction: discord.Interaction, task_id: int):
        """Display the Task Detail view from the mockup."""
        await interaction.response.defer(thinking=True)

        try:
            task = await TaskService.get_task_by_id(task_id)
            if not task:
                await interaction.followup.send("Task not found.", ephemeral=True)
                return

            # Create the task detail embed
            embed = create_task_embed(task)

            # Load mascot images
            penguin_path = os.path.join(self.asset_path, "penguin.png")
            cat_path = os.path.join(self.asset_path, "cat.png")

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            # Create task view with buttons
            view = EnhancedTaskView(task_id=task_id)

            await interaction.followup.send(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.followup.send(
                f"Error displaying task: {str(e)}", ephemeral=True
            )


class DashboardView(discord.ui.View):
    """Dashboard view with buttons matching the UI mockup."""

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="My Tasks", style=discord.ButtonStyle.primary, emoji="📋")
    async def my_tasks_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show my tasks."""
        # Simulate the /my_tasks command
        user_id = str(interaction.user.id)
        tasks = await TaskService.get_tasks_for_user(user_id)
        embed = create_task_list_embed(tasks, title="My Tasks", user_id=user_id)

        # Load mascot image
        penguin_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "ui", "penguin.png"
        )

        files = []
        if os.path.exists(penguin_path):
            files.append(discord.File(penguin_path, filename="penguin.png"))

        view = TaskListView(tasks=tasks, user_id=user_id, is_my_tasks=True)
        await interaction.response.send_message(
            embed=embed, view=view, files=files, ephemeral=True
        )

    @discord.ui.button(label="Add Task", style=discord.ButtonStyle.success, emoji="➕")
    async def add_task_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Open add task modal."""
        modal = AddTaskModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Projects", style=discord.ButtonStyle.secondary, emoji="📁"
    )
    async def projects_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Show projects."""
        user_id = str(interaction.user.id)
        projects = await ProjectService.get_projects_for_user(user_id)

        if not projects:
            await interaction.response.send_message(
                "No projects found.", ephemeral=True
            )
            return

        # Create a simple embed for projects
        embed = discord.Embed(
            title="📁 Projects",
            description=f"You have {len(projects)} projects",
            color=COLORS["blue"],
        )

        for project in projects:
            task_count = len(project.tasks) if hasattr(project, "tasks") else 0
            embed.add_field(
                name=project.name,
                value=f"{task_count} tasks"
                + (f"\n*{project.description}*" if project.description else ""),
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class TaskListView(discord.ui.View):
    """Task list view with buttons matching the UI mockup."""

    def __init__(self, tasks, user_id, is_my_tasks=True):
        super().__init__(timeout=300)
        self.tasks = tasks
        self.user_id = user_id
        self.is_my_tasks = is_my_tasks

    @discord.ui.button(label="Add Task", style=discord.ButtonStyle.success, emoji="➕")
    async def add_task_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Open add task modal."""
        modal = AddTaskModal(default_assignee=self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Filter", style=discord.ButtonStyle.secondary, emoji="🔍")
    async def filter_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Open filter modal."""
        # Placeholder for filter functionality
        await interaction.response.send_message(
            "Filter functionality coming soon!", ephemeral=True
        )

    @discord.ui.button(
        label="Toggle View", style=discord.ButtonStyle.primary, emoji="🔄"
    )
    async def toggle_view_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Toggle between My Tasks and Their Tasks."""
        if self.is_my_tasks:
            # Show a modal to select which user's tasks to view
            modal = SelectUserModal()
            await interaction.response.send_modal(modal)
        else:
            # Switch back to my tasks
            user_id = str(interaction.user.id)
            tasks = await TaskService.get_tasks_for_user(user_id)
            embed = create_task_list_embed(tasks, title="My Tasks", user_id=user_id)

            # Load mascot image
            penguin_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "assets",
                "ui",
                "penguin.png",
            )

            files = []
            if os.path.exists(penguin_path):
                files.append(discord.File(penguin_path, filename="penguin.png"))

            view = TaskListView(tasks=tasks, user_id=user_id, is_my_tasks=True)
            await interaction.response.edit_message(
                embed=embed, view=view, attachments=files
            )


class EnhancedTaskView(discord.ui.View):
    """Enhanced task view with buttons matching the UI mockup."""

    def __init__(self, task_id: int):
        super().__init__(timeout=300)
        self.task_id = task_id

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Edit task button."""
        # Fetch the current task data
        task = await TaskService.get_task_by_id(self.task_id)
        if not task:
            await interaction.response.send_message(
                "❌ Task not found.", ephemeral=True
            )
            return

        # Create the modal
        modal = EditTaskModal(self.task_id)

        # Pre-fill the modal fields with existing task data
        if hasattr(task, "title") and task.title is not None:
            modal.task_title.default = str(task.title)

        if hasattr(task, "description") and task.description is not None:
            # Handle None or empty string case
            description = task.description or ""
            modal.description.default = str(description)

        if hasattr(task, "priority") and task.priority is not None:
            modal.priority.default = str(task.priority)

        if hasattr(task, "due_date") and task.due_date is not None:
            try:
                modal.due_date.default = task.due_date.strftime("%Y-%m-%d")
            except (AttributeError, TypeError):
                modal.due_date.default = ""

        # Send the modal
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Complete", style=discord.ButtonStyle.success, emoji="✅")
    async def complete_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Mark task as complete with confetti animation."""
        task = await TaskService.update_task(self.task_id, status=TaskStatus.DONE.value)
        if task:
            # Create celebration embed
            embed = discord.Embed(
                title="🎉 Task Completed! 🎊",
                description=f"**{task.title}** has been marked as complete!",
                color=COLORS["green"],
            )

            # Show the celebration embed briefly
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Then update the task view
            task_embed = create_task_embed(task)
            await interaction.message.edit(embed=task_embed)
        else:
            await interaction.response.send_message(
                "❌ Failed to update task.", ephemeral=True
            )

    @discord.ui.button(
        label="Change Status", style=discord.ButtonStyle.secondary, emoji="🔄"
    )
    async def change_status(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Change task status button."""
        # Create and send the status selection modal
        modal = ChangeStatusModal(self.task_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Delete task button with confirmation."""
        # Create confirmation view
        view = ConfirmationView(self.task_id)
        await interaction.response.send_message(
            "⚠️ Are you sure you want to delete this task? This action cannot be undone.",
            view=view,
            ephemeral=True,
        )


class AddTaskModal(discord.ui.Modal, title="Add New Task"):
    """Add task modal matching the UI mockup."""

    task_title = discord.ui.TextInput(
        label="Task Title",
        placeholder="Enter task title...",
        max_length=100,
        required=True,
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter task description...",
        style=discord.TextStyle.paragraph,
        required=False,
    )

    priority = discord.ui.TextInput(
        label="Priority",
        placeholder="low, medium, high, or urgent",
        required=False,
    )

    due_date = discord.ui.TextInput(
        label="Due Date",
        placeholder="YYYY-MM-DD",
        required=False,
    )

    assignees = discord.ui.TextInput(
        label="Assignees",
        placeholder="@user1 @user2 (or leave blank for self-assignment)",
        required=False,
    )

    def __init__(self, default_assignee=None):
        super().__init__()
        if default_assignee:
            self.assignees.default = f"<@{default_assignee}>"

    async def on_submit(self, interaction: discord.Interaction):
        # Process form submission
        try:
            # Get values from form
            title = self.task_title.value
            description = self.description.value
            priority = self.priority.value.lower() if self.priority.value else "medium"
            due_date_str = self.due_date.value

            # Create the task
            task = await TaskService.create_task(
                title=title,
                description=description,
                priority=priority,
                due_date_str=due_date_str,
                creator_id=str(interaction.user.id),
                assignee_mentions=self.assignees.value,
            )

            if task:
                # Create and show the task
                embed = create_task_embed(task)

                # Load mascot images
                penguin_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "penguin.png",
                )
                cat_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "cat.png",
                )

                files = []
                if os.path.exists(penguin_path):
                    files.append(discord.File(penguin_path, filename="penguin.png"))
                if os.path.exists(cat_path):
                    files.append(discord.File(cat_path, filename="cat.png"))

                view = EnhancedTaskView(task_id=task.id)

                await interaction.response.send_message(
                    "✅ Task created successfully!", embed=embed, view=view, files=files
                )
            else:
                await interaction.response.send_message(
                    "❌ Failed to create task.", ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error creating task: {str(e)}", ephemeral=True
            )


class EditTaskModal(discord.ui.Modal, title="Edit Task"):
    """Edit task modal matching the UI mockup."""

    task_title = discord.ui.TextInput(
        label="Task Title",
        placeholder="Enter task title...",
        max_length=100,
        required=True,
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter task description...",
        style=discord.TextStyle.paragraph,
        required=False,
    )

    priority = discord.ui.TextInput(
        label="Priority",
        placeholder="low, medium, high, or urgent",
        required=False,
    )

    due_date = discord.ui.TextInput(
        label="Due Date",
        placeholder="YYYY-MM-DD",
        required=False,
    )

    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id

    async def on_submit(self, interaction: discord.Interaction):
        # Process form submission
        try:
            # Get values from form
            title = self.task_title.value
            description = self.description.value
            priority = self.priority.value.lower() if self.priority.value else None
            due_date_str = self.due_date.value

            # Update the task
            task = await TaskService.update_task(
                task_id=self.task_id,
                title=title,
                description=description,
                priority=priority,
                due_date_str=due_date_str,
            )

            if task:
                # Create and show the updated task
                embed = create_task_embed(task)
                view = EnhancedTaskView(task_id=self.task_id)

                # Load mascot images
                penguin_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "penguin.png",
                )
                cat_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "cat.png",
                )

                files = []
                if os.path.exists(penguin_path):
                    files.append(discord.File(penguin_path, filename="penguin.png"))
                if os.path.exists(cat_path):
                    files.append(discord.File(cat_path, filename="cat.png"))

                await interaction.response.send_message(
                    "✅ Task updated successfully!", embed=embed, view=view, files=files
                )
            else:
                await interaction.response.send_message(
                    "❌ Failed to update task.", ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error updating task: {str(e)}", ephemeral=True
            )


class ChangeStatusModal(discord.ui.Modal, title="Change Task Status"):
    """Change task status modal."""

    status = discord.ui.TextInput(
        label="Status",
        placeholder="todo, in_progress, done, or blocked",
        required=True,
    )

    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id

    async def on_submit(self, interaction: discord.Interaction):
        # Process form submission
        try:
            # Get status from form
            status = self.status.value.lower()

            # Map input to valid status
            status_map = {
                "todo": TaskStatus.TODO.value,
                "in_progress": TaskStatus.IN_PROGRESS.value,
                "done": TaskStatus.DONE.value,
                "blocked": TaskStatus.BLOCKED.value,
            }

            if status not in status_map:
                await interaction.response.send_message(
                    "❌ Invalid status. Please use todo, in_progress, done, or blocked.",
                    ephemeral=True,
                )
                return

            # Update the task
            task = await TaskService.update_task(
                task_id=self.task_id, status=status_map[status]
            )

            if task:
                # Create and show the updated task
                embed = create_task_embed(task)

                # Load mascot images
                penguin_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "penguin.png",
                )
                cat_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "assets",
                    "ui",
                    "cat.png",
                )

                files = []
                if os.path.exists(penguin_path):
                    files.append(discord.File(penguin_path, filename="penguin.png"))
                if os.path.exists(cat_path):
                    files.append(discord.File(cat_path, filename="cat.png"))

                view = EnhancedTaskView(task_id=self.task_id)

                await interaction.response.send_message(
                    f"✅ Task status updated to {status}!",
                    embed=embed,
                    view=view,
                    files=files,
                )
            else:
                await interaction.response.send_message(
                    "❌ Failed to update task.", ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error updating task: {str(e)}", ephemeral=True
            )


class ConfirmationView(discord.ui.View):
    """Confirmation view for delete operations."""

    def __init__(self, task_id):
        super().__init__(timeout=60)
        self.task_id = task_id

    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        success = await TaskService.delete_task(self.task_id)
        if success:
            await interaction.response.edit_message(
                content="✅ Task deleted successfully.", view=None
            )
            # Also update the original message
            try:
                await interaction.message.edit(
                    content="✅ Task deleted.", embed=None, view=None
                )
            except:
                pass  # Original message might not be accessible
        else:
            await interaction.response.edit_message(
                content="❌ Failed to delete task.", view=None
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="Task deletion cancelled.", view=None
        )


class SelectUserModal(discord.ui.Modal, title="Select User"):
    """Modal to select a user to view their tasks."""

    user_id = discord.ui.TextInput(
        label="User ID or Mention",
        placeholder="Enter user ID or @mention",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Extract user ID from input
        user_input = self.user_id.value

        # Handle mention format
        if user_input.startswith("<@") and user_input.endswith(">"):
            user_id = user_input[2:-1]
            if user_id.startswith("!"):  # Handle nickname mentions
                user_id = user_id[1:]
        else:
            user_id = user_input

        try:
            # Try to fetch the user
            user = await interaction.client.fetch_user(user_id)

            # Get their tasks
            tasks = await TaskService.get_tasks_for_user(user_id)

            # Create the task list embed
            embed = create_task_list_embed(
                tasks, title=f"{user.display_name}'s Tasks", user_id=user_id
            )

            # Load mascot image
            cat_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "assets", "ui", "cat.png"
            )

            files = []
            if os.path.exists(cat_path):
                files.append(discord.File(cat_path, filename="cat.png"))

            view = TaskListView(tasks=tasks, user_id=user_id, is_my_tasks=False)

            await interaction.response.send_message(embed=embed, view=view, files=files)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error finding user or their tasks: {str(e)}", ephemeral=True
            )


def setup(bot):
    bot.add_cog(TaskUIExamples(bot))
