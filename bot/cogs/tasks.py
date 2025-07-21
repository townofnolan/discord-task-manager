"""Task management cog for Discord bot."""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from models import TaskPriority, TaskStatus
from services import ProjectService, TaskService

logger = logging.getLogger(__name__)


class TaskView(discord.ui.View):
    """Interactive view for task management."""

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
                logger.error(f"Invalid due_date format: {task.due_date}")
                modal.due_date.default = ""

        if hasattr(task, "assignees") and task.assignees:
            try:
                # Format the assignees as mentions
                mentions = []
                for user in task.assignees:
                    if hasattr(user, "discord_id") and user.discord_id:
                        mentions.append(f"<@{user.discord_id}>")
                assignee_mentions = " ".join(mentions)
                if len(assignee_mentions) <= 500:  # Max length for TextInput
                    modal.assignees.default = assignee_mentions
            except Exception as e:
                logger.error(f"Error formatting assignees: {e}")

        # Send the modal
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Complete", style=discord.ButtonStyle.success, emoji="✅")
    async def complete_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Mark task as complete."""
        task = await TaskService.update_task(self.task_id, status=TaskStatus.DONE.value)
        if task:
            embed = create_task_embed(task)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(
                "❌ Failed to update task.", ephemeral=True
            )

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_task(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Delete task button."""
        success = await TaskService.delete_task(self.task_id)
        if success:
            await interaction.response.edit_message(
                content="✅ Task deleted.", embed=None, view=None
            )
        else:
            await interaction.response.send_message(
                "❌ Failed to delete task.", ephemeral=True
            )


class CreateTaskModal(discord.ui.Modal, title="Create New Task"):
    """Modal for creating new tasks."""

    task_title = discord.ui.TextInput(
        label="Task Title",
        placeholder="Enter task title...",
        required=True,
        max_length=300,
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter task description...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000,
    )

    priority = discord.ui.TextInput(
        label="Priority",
        placeholder="low, medium, high, urgent",
        required=False,
        default="medium",
        max_length=10,
    )

    due_date = discord.ui.TextInput(
        label="Due Date",
        placeholder="YYYY-MM-DD or leave empty",
        required=False,
        max_length=20,
    )

    assignees = discord.ui.TextInput(
        label="Assignees",
        placeholder="@user1 @user2 or leave empty",
        required=False,
        max_length=500,
    )

    def __init__(self, project_id: Optional[int] = None):
        super().__init__()
        self.project_id = project_id

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            # Parse priority
            priority = self.priority.value.lower() if self.priority.value else "medium"
            if priority not in [p.value for p in TaskPriority]:
                priority = TaskPriority.MEDIUM.value

            # Parse due date
            due_date = None
            if self.due_date.value:
                try:
                    due_date = datetime.strptime(self.due_date.value, "%Y-%m-%d")
                    due_date = due_date.replace(tzinfo=timezone.utc)
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid due date format. Use YYYY-MM-DD.", ephemeral=True
                    )
                    return

            # Parse assignees
            assignee_discord_ids = []
            if self.assignees.value:
                # Extract user mentions
                mentions = re.findall(r"<@!?(\d+)>", self.assignees.value)
                assignee_discord_ids = [int(mention) for mention in mentions]

            # Log task creation attempt with parameters
            logger.info(
                f"Attempting to create task with title: {self.task_title.value}"
            )
            logger.info(f"Creator ID: {interaction.user.id}")
            logger.info(f"Project ID: {self.project_id}")
            logger.info(f"Priority: {priority}")
            logger.info(f"Assignee IDs: {assignee_discord_ids}")
            logger.info(f"Due Date: {due_date}")
            logger.info(f"Channel ID: {interaction.channel_id}")

            # Create task
            task = await TaskService.create_task(
                title=self.task_title.value,
                creator_discord_id=interaction.user.id,
                description=self.description.value if self.description.value else None,
                project_id=self.project_id,
                priority=priority,
                assignee_discord_ids=(
                    assignee_discord_ids if assignee_discord_ids else None
                ),
                due_date=due_date,
                discord_channel_id=interaction.channel_id,
            )

            # Create embed and view
            embed = create_task_embed(task)
            # Convert SQLAlchemy Column to Python int
            task_id = getattr(task, "id")
            view = TaskView(task_id)

            await interaction.response.send_message(embed=embed, view=view)

            # Update task with message ID
            message = await interaction.original_response()
            # Convert SQLAlchemy Column to Python int
            await TaskService.update_task(task_id, discord_message_id=message.id)
            logger.info(f"Task updated with message ID: {message.id}")

        except Exception as e:
            logger.error(f"Error creating task: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ Failed to create task: {str(e)}", ephemeral=True
            )


class EditTaskModal(discord.ui.Modal, title="Edit Task"):
    """Modal for editing existing tasks."""

    task_title = discord.ui.TextInput(
        label="Task Title",
        placeholder="Enter task title...",
        required=True,
        max_length=300,
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter task description...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000,
    )

    priority = discord.ui.TextInput(
        label="Priority",
        placeholder="low, medium, high, urgent",
        required=False,
        max_length=10,
    )

    due_date = discord.ui.TextInput(
        label="Due Date",
        placeholder="YYYY-MM-DD or leave empty",
        required=False,
        max_length=20,
    )

    assignees = discord.ui.TextInput(
        label="Assignees",
        placeholder="@user1 @user2 or leave empty",
        required=False,
        max_length=500,
    )

    def __init__(self, task_id: int):
        super().__init__()
        self.task_id = task_id
        # Populate fields will be handled in callback before the modal is shown

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            # Parse priority
            priority = None
            if self.priority.value:
                priority = self.priority.value.lower()
                if priority not in [p.value for p in TaskPriority]:
                    priority = None

            # Parse due date
            due_date = None
            if self.due_date.value:
                try:
                    date_str = self.due_date.value
                    due_date = datetime.strptime(date_str, "%Y-%m-%d")
                    due_date = due_date.replace(tzinfo=timezone.utc)
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid due date format. Use YYYY-MM-DD.", ephemeral=True
                    )
                    return

            # Parse assignees
            if self.assignees.value:
                mentions = re.findall(r"<@!?(\d+)>", self.assignees.value)
                if mentions:
                    assignee_discord_ids = [int(uid) for uid in mentions]
                    # Update task assignees
                    await TaskService.assign_users_to_task(
                        task_id=self.task_id, user_discord_ids=assignee_discord_ids
                    )

            # Update task
            task = await TaskService.update_task(
                task_id=self.task_id,
                title=self.task_title.value,
                description=self.description.value,
                priority=priority,
                due_date=due_date,
            )

            if task:
                embed = create_task_embed(task)
                # Convert SQLAlchemy Column to Python int
                task_id = getattr(task, "id")
                view = TaskView(task_id)
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                msg = "❌ Failed to update task."
                await interaction.response.send_message(msg, ephemeral=True)

        except Exception as e:
            logger.error(f"Error updating task: {e}", exc_info=True)
            error_msg = f"❌ Error updating task: {str(e)}"
            await interaction.response.send_message(error_msg, ephemeral=True)


def create_task_embed(task) -> discord.Embed:
    """Create Discord embed for a task."""
    # Status color mapping
    status_colors = {
        TaskStatus.TODO.value: 0x95A5A6,  # Gray
        TaskStatus.IN_PROGRESS.value: 0x3498DB,  # Blue
        TaskStatus.REVIEW.value: 0xF39C12,  # Orange
        TaskStatus.DONE.value: 0x27AE60,  # Green
        TaskStatus.CANCELLED.value: 0xE74C3C,  # Red
    }

    # Priority emojis
    priority_emojis = {
        TaskPriority.LOW.value: "🟢",
        TaskPriority.MEDIUM.value: "🟡",
        TaskPriority.HIGH.value: "🟠",
        TaskPriority.URGENT.value: "🔴",
    }

    color = status_colors.get(task.status, 0x95A5A6)
    embed = discord.Embed(
        title=f"📋 {task.title}",
        description=task.description or "No description provided",
        color=color,
        timestamp=task.created_at,
    )

    # Status field
    embed.add_field(
        name="Status", value=task.status.replace("_", " ").title(), inline=True
    )

    # Priority field
    priority_emoji = priority_emojis.get(task.priority, "⚪")
    embed.add_field(
        name="Priority", value=f"{priority_emoji} {task.priority.title()}", inline=True
    )

    # Project field
    if task.project:
        embed.add_field(name="Project", value=task.project.name, inline=True)

    # Assignees field
    if task.assignees:
        assignee_mentions = [f"<@{user.discord_id}>" for user in task.assignees]
        embed.add_field(
            name="Assignees", value=", ".join(assignee_mentions), inline=False
        )

    # Due date field
    if task.due_date:
        embed.add_field(
            name="Due Date",
            value=f"<t:{int(task.due_date.timestamp())}:F>",
            inline=True,
        )

    # Creator field
    embed.add_field(
        name="Created by", value=f"<@{task.creator.discord_id}>", inline=True
    )

    # Task ID in footer
    embed.set_footer(text=f"Task ID: {task.id}")

    return embed


class TasksCog(commands.Cog):
    """Commands for task management."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create-task", description="Create a new task")
    @app_commands.describe(
        title="Task title",
        description="Task description",
        priority="Task priority (low, medium, high, urgent)",
        assignee="User to assign the task to",
        due_date="Due date (YYYY-MM-DD format)",
    )
    async def create_task(
        self,
        interaction: discord.Interaction,
        title: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[discord.Member] = None,
        due_date: Optional[str] = None,
    ):
        """Create a new task via slash command."""
        # Parse and validate inputs
        priority = priority.lower() if priority else "medium"
        if priority not in [p.value for p in TaskPriority]:
            priority = TaskPriority.MEDIUM.value

        # Parse due date
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d")
                parsed_due_date = parsed_due_date.replace(tzinfo=timezone.utc)
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid due date format. Use YYYY-MM-DD.", ephemeral=True
                )
                return

        try:
            # Get project for current channel
            project = None
            channel_id = interaction.channel_id
            if channel_id is not None:
                project = await ProjectService.get_project_by_channel(channel_id)

            # Set project ID
            project_id = None
            if project:
                project_id = getattr(project, "id")

            # Create task
            task = await TaskService.create_task(
                title=title,
                creator_discord_id=interaction.user.id,
                description=description,
                project_id=project_id,
                priority=priority,
                assignee_discord_ids=[assignee.id] if assignee else None,
                due_date=parsed_due_date,
                discord_channel_id=interaction.channel_id,
            )

            # Create embed and view
            embed = create_task_embed(task)
            # Convert SQLAlchemy Column to Python int
            task_id = getattr(task, "id")
            view = TaskView(task_id)

            await interaction.response.send_message(embed=embed, view=view)

            # Update task with message ID
            message = await interaction.original_response()
            await TaskService.update_task(task_id, discord_message_id=message.id)

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            await interaction.response.send_message(
                "❌ Failed to create task. Please try again.", ephemeral=True
            )

    @app_commands.command(name="task", description="View or manage a task")
    @app_commands.describe(task_id="ID of the task to view")
    async def view_task(self, interaction: discord.Interaction, task_id: int):
        """View a specific task."""
        task = await TaskService.get_task_by_id(task_id)

        if not task:
            await interaction.response.send_message(
                "❌ Task not found.", ephemeral=True
            )
            return

        embed = create_task_embed(task)
        # Convert SQLAlchemy Column to Python int
        task_id = getattr(task, "id")
        view = TaskView(task_id)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="my-tasks", description="View your assigned tasks")
    @app_commands.describe(status="Filter by task status")
    async def my_tasks(
        self, interaction: discord.Interaction, status: Optional[str] = None
    ):
        """View user's assigned tasks."""
        tasks = await TaskService.get_tasks_for_user(
            user_discord_id=interaction.user.id, status=status
        )

        if not tasks:
            status_text = f" with status '{status}'" if status else ""
            await interaction.response.send_message(
                f"📝 You have no assigned tasks{status_text}.", ephemeral=True
            )
            return

        # Create embed with task list
        embed = discord.Embed(
            title="📋 Your Tasks", color=0x3498DB, timestamp=datetime.now(timezone.utc)
        )

        for task in tasks[:10]:  # Limit to 10 tasks
            status_emoji = "✅" if str(task.status) == TaskStatus.DONE.value else "⏳"
            due_text = ""
            try:
                if hasattr(task, "due_date") and task.due_date is not None:
                    due_text = f" (Due: <t:{int(task.due_date.timestamp())}:d>)"
            except (AttributeError, TypeError) as e:
                logger.warning(f"Error handling task due date: {e}")

            task_id = getattr(task, "id")
            task_status = str(task.status)
            task_title = str(task.title)

            status_formatted = task_status.replace("_", " ").title()
            field_value = f"ID: {task_id} | Status: {status_formatted}{due_text}"

            embed.add_field(
                name=f"{status_emoji} {task_title}", value=field_value, inline=False
            )

        if len(tasks) > 10:
            embed.set_footer(text=f"Showing 10 of {len(tasks)} tasks")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="task-modal")
    async def create_task_modal(self, ctx):
        """Open task creation modal (prefix command)."""
        # Get project for current channel
        project = await ProjectService.get_project_by_channel(ctx.channel.id)

        project_id = None
        if project:
            project_id = getattr(project, "id")

        modal = CreateTaskModal(project_id)

        # For prefix commands, we need to create a view with a button to open the modal
        class ModalView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(
                label="Create Task", style=discord.ButtonStyle.primary, emoji="📋"
            )
            async def create_task_button(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                await interaction.response.send_modal(modal)

        view = ModalView()
        await ctx.send("Click the button to create a new task:", view=view)

    @app_commands.command(name="recurring-task", description="Create a recurring task")
    @app_commands.describe(
        title="Title of the task",
        pattern="Recurrence pattern (daily, weekly, monthly)",
        frequency="How often the task should recur (e.g., 1 for every day, 2 for every other day)",
        description="Description of the task",
        assignee="User to assign the task to",
        due_date="Due date (YYYY-MM-DD)",
        priority="Task priority",
        end_date="End date for recurring task (YYYY-MM-DD)",
    )
    @app_commands.choices(
        pattern=[
            app_commands.Choice(name="Daily", value="daily"),
            app_commands.Choice(name="Weekly", value="weekly"),
            app_commands.Choice(name="Monthly", value="monthly"),
        ],
        priority=[
            app_commands.Choice(name="Low", value="low"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="High", value="high"),
            app_commands.Choice(name="Urgent", value="urgent"),
        ],
    )
    async def create_recurring_task(
        self,
        interaction: discord.Interaction,
        title: str,
        pattern: str,
        frequency: int = 1,
        description: Optional[str] = None,
        assignee: Optional[discord.Member] = None,
        due_date: Optional[str] = None,
        priority: Optional[str] = "medium",
        end_date: Optional[str] = None,
    ):
        """Create a recurring task."""
        # Parse due date if provided
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid due date format. Please use YYYY-MM-DD.", ephemeral=True
                )
                return

        # Parse end date if provided
        end_date_obj = None
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                await interaction.response.send_message(
                    "❌ Invalid end date format. Please use YYYY-MM-DD.", ephemeral=True
                )
                return

        # Get assignee discord ID if provided
        assignee_discord_ids = []
        if assignee:
            assignee_discord_ids.append(assignee.id)

        # Create the task
        try:
            task = await TaskService.create_recurring_task(
                title=title,
                creator_discord_id=interaction.user.id,
                description=description,
                priority=priority,
                assignee_discord_ids=assignee_discord_ids,
                due_date=due_date_obj,
                discord_channel_id=interaction.channel_id,
                recurrence_pattern=pattern,
                recurrence_frequency=frequency,
                recurrence_end_date=end_date_obj,
            )

            embed = create_task_embed(task)
            view = TaskView(task.id)

            await interaction.response.send_message(
                "✅ Recurring task created successfully!", embed=embed, view=view
            )
        except Exception as e:
            logger.error(f"Error creating recurring task: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ Failed to create recurring task: {str(e)}", ephemeral=True
            )

    @app_commands.command(
        name="quick-task", description="Create a task quickly with simple syntax"
    )
    @app_commands.describe(
        task_text="Task description with optional parameters (e.g., Buy groceries @user #high by tomorrow)"
    )
    async def quick_task(self, interaction: discord.Interaction, task_text: str):
        """Create a task quickly with a natural language command."""
        # Parse the task text
        title = task_text
        description = None
        assignee_discord_ids = []
        due_date = None
        priority = TaskPriority.MEDIUM.value

        # Extract mentions
        mention_pattern = r"<@!?(\d+)>"
        mentions = re.findall(mention_pattern, task_text)
        if mentions:
            assignee_discord_ids = [int(mention) for mention in mentions]
            # Remove mentions from title
            title = re.sub(mention_pattern, "", title).strip()

        # Extract priority
        priority_pattern = r"#(urgent|high|medium|low)"
        priority_match = re.search(priority_pattern, title, re.IGNORECASE)
        if priority_match:
            priority = priority_match.group(1).lower()
            # Remove priority from title
            title = re.sub(priority_pattern, "", title, flags=re.IGNORECASE).strip()

        # Extract due date
        due_date_patterns = [
            (r"by\s+today", 0),
            (r"by\s+tomorrow", 1),
            (r"by\s+next\s+week", 7),
            (r"by\s+(\d{4}-\d{2}-\d{2})", None),  # YYYY-MM-DD format
        ]

        for pattern, days in due_date_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                if days is not None:
                    due_date = datetime.now(timezone.utc) + timedelta(days=days)
                else:
                    # Parse specific date
                    date_str = match.group(1)
                    try:
                        due_date = datetime.strptime(date_str, "%Y-%m-%d").replace(
                            tzinfo=timezone.utc
                        )
                    except ValueError:
                        await interaction.response.send_message(
                            f"❌ Invalid date format: {date_str}. Please use YYYY-MM-DD.",
                            ephemeral=True,
                        )
                        return

                # Remove due date from title
                title = re.sub(pattern, "", title, flags=re.IGNORECASE).strip()
                break

        # Create the task
        try:
            task = await TaskService.create_task(
                title=title,
                creator_discord_id=interaction.user.id,
                description=description,
                priority=priority,
                assignee_discord_ids=assignee_discord_ids,
                due_date=due_date,
                discord_channel_id=interaction.channel_id,
            )

            embed = create_task_embed(task)
            view = TaskView(task.id)

            await interaction.response.send_message(
                "✅ Task created successfully!", embed=embed, view=view
            )
        except Exception as e:
            logger.error(f"Error creating quick task: {e}", exc_info=True)
            await interaction.response.send_message(
                f"❌ Failed to create task: {str(e)}", ephemeral=True
            )


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(TasksCog(bot))
