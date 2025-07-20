"""Task management cog for Discord bot."""

import logging
from typing import Optional, List
from datetime import datetime, timezone

import discord
from discord.ext import commands
from discord import app_commands

from models import TaskStatus, TaskPriority
from services import TaskService, UserService, ProjectService

logger = logging.getLogger(__name__)


class TaskView(discord.ui.View):
    """Interactive view for task management."""
    
    def __init__(self, task_id: int):
        super().__init__(timeout=300)
        self.task_id = task_id
    
    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit task button."""
        # Fetch the current task data
        task = await TaskService.get_task_by_id(self.task_id)
        if not task:
            await interaction.response.send_message(
                "❌ Task not found.",
                ephemeral=True
            )
            return
            
        # Create the modal
        modal = EditTaskModal(self.task_id)
        
        # Pre-fill the modal fields with existing task data
        modal.task_title.default = task.title
        
        if task.description:
            modal.description.default = task.description
            
        if task.priority:
            modal.priority.default = task.priority
            
        if task.due_date:
            modal.due_date.default = task.due_date.strftime("%Y-%m-%d")
            
        if task.assignees:
            # Format the assignees as mentions
            mentions = []
            for user in task.assignees:
                mentions.append(f"<@{user.discord_id}>")
            assignee_mentions = " ".join(mentions)
            if len(assignee_mentions) <= 500:  # Max length for TextInput
                modal.assignees.default = assignee_mentions
        
        # Send the modal
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Complete", style=discord.ButtonStyle.success, emoji="✅")
    async def complete_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mark task as complete."""
        task = await TaskService.update_task(self.task_id, status=TaskStatus.DONE.value)
        if task:
            embed = create_task_embed(task)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Failed to update task.", ephemeral=True)
    
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete task button."""
        success = await TaskService.delete_task(self.task_id)
        if success:
            await interaction.response.edit_message(content="✅ Task deleted.", embed=None, view=None)
        else:
            await interaction.response.send_message("❌ Failed to delete task.", ephemeral=True)


class CreateTaskModal(discord.ui.Modal, title="Create New Task"):
    """Modal for creating new tasks."""
    
    task_title = discord.ui.TextInput(
        label="Task Title",
        placeholder="Enter task title...",
        required=True,
        max_length=300
    )
    
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter task description...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000
    )
    
    priority = discord.ui.TextInput(
        label="Priority",
        placeholder="low, medium, high, urgent",
        required=False,
        default="medium",
        max_length=10
    )
    
    due_date = discord.ui.TextInput(
        label="Due Date",
        placeholder="YYYY-MM-DD or leave empty",
        required=False,
        max_length=20
    )
    
    assignees = discord.ui.TextInput(
        label="Assignees",
        placeholder="@user1 @user2 or leave empty",
        required=False,
        max_length=500
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
                        "❌ Invalid due date format. Use YYYY-MM-DD.",
                        ephemeral=True
                    )
                    return
            
            # Parse assignees
            assignee_discord_ids = []
            if self.assignees.value:
                # Extract user mentions
                import re
                mentions = re.findall(r'<@!?(\d+)>', self.assignees.value)
                assignee_discord_ids = [int(mention) for mention in mentions]
            
            # Create task
            task = await TaskService.create_task(
                title=self.task_title.value,
                creator_discord_id=interaction.user.id,
                description=self.description.value if self.description.value else None,
                project_id=self.project_id,
                priority=priority,
                assignee_discord_ids=assignee_discord_ids if assignee_discord_ids else None,
                due_date=due_date,
                discord_channel_id=interaction.channel_id
            )
            
            # Create embed and view
            embed = create_task_embed(task)
            view = TaskView(task.id)
            
            await interaction.response.send_message(embed=embed, view=view)
            
            # Update task with message ID
            message = await interaction.original_response()
            await TaskService.update_task(task.id, discord_message_id=message.id)
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            await interaction.response.send_message(
                "❌ Failed to create task. Please try again.",
                ephemeral=True
            )


class EditTaskModal(discord.ui.Modal, title="Edit Task"):
    """Modal for editing existing tasks."""
    
    task_title = discord.ui.TextInput(
        label="Task Title",
        placeholder="Enter task title...",
        required=True,
        max_length=300
    )
    
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter task description...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000
    )
    
    priority = discord.ui.TextInput(
        label="Priority",
        placeholder="low, medium, high, urgent",
        required=False,
        max_length=10
    )
    
    due_date = discord.ui.TextInput(
        label="Due Date",
        placeholder="YYYY-MM-DD or leave empty",
        required=False,
        max_length=20
    )
    
    assignees = discord.ui.TextInput(
        label="Assignees",
        placeholder="@user1 @user2 or leave empty",
        required=False,
        max_length=500
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
                        "❌ Invalid due date format. Use YYYY-MM-DD.",
                        ephemeral=True
                    )
                    return
            
            # Parse assignees
            if self.assignees.value:
                import re
                mentions = re.findall(r'<@!?(\d+)>', self.assignees.value)
                if mentions:
                    assignee_discord_ids = [int(uid) for uid in mentions]
                    # Update task assignees
                    await TaskService.assign_users_to_task(
                        task_id=self.task_id,
                        user_discord_ids=assignee_discord_ids
                    )
            
            # Update task
            task = await TaskService.update_task(
                task_id=self.task_id,
                title=self.task_title.value,
                description=self.description.value,
                priority=priority,
                due_date=due_date
            )
            
            if task:
                embed = create_task_embed(task)
                view = TaskView(task.id)
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
        TaskStatus.TODO.value: 0x95a5a6,        # Gray
        TaskStatus.IN_PROGRESS.value: 0x3498db,  # Blue
        TaskStatus.REVIEW.value: 0xf39c12,       # Orange
        TaskStatus.DONE.value: 0x27ae60,         # Green
        TaskStatus.CANCELLED.value: 0xe74c3c     # Red
    }
    
    # Priority emojis
    priority_emojis = {
        TaskPriority.LOW.value: "🟢",
        TaskPriority.MEDIUM.value: "🟡",
        TaskPriority.HIGH.value: "🟠",
        TaskPriority.URGENT.value: "🔴"
    }
    
    color = status_colors.get(task.status, 0x95a5a6)
    embed = discord.Embed(
        title=f"📋 {task.title}",
        description=task.description or "No description provided",
        color=color,
        timestamp=task.created_at
    )
    
    # Status field
    embed.add_field(
        name="Status",
        value=task.status.replace("_", " ").title(),
        inline=True
    )
    
    # Priority field
    priority_emoji = priority_emojis.get(task.priority, "⚪")
    embed.add_field(
        name="Priority",
        value=f"{priority_emoji} {task.priority.title()}",
        inline=True
    )
    
    # Project field
    if task.project:
        embed.add_field(
            name="Project",
            value=task.project.name,
            inline=True
        )
    
    # Assignees field
    if task.assignees:
        assignee_mentions = [f"<@{user.discord_id}>" for user in task.assignees]
        embed.add_field(
            name="Assignees",
            value=", ".join(assignee_mentions),
            inline=False
        )
    
    # Due date field
    if task.due_date:
        embed.add_field(
            name="Due Date",
            value=f"<t:{int(task.due_date.timestamp())}:F>",
            inline=True
        )
    
    # Creator field
    embed.add_field(
        name="Created by",
        value=f"<@{task.creator.discord_id}>",
        inline=True
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
        due_date="Due date (YYYY-MM-DD format)"
    )
    async def create_task(
        self,
        interaction: discord.Interaction,
        title: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[discord.Member] = None,
        due_date: Optional[str] = None
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
                    "❌ Invalid due date format. Use YYYY-MM-DD.",
                    ephemeral=True
                )
                return
        
        try:
            # Get project for current channel
            project = await ProjectService.get_project_by_channel(interaction.channel_id)
            
            # Create task
            task = await TaskService.create_task(
                title=title,
                creator_discord_id=interaction.user.id,
                description=description,
                project_id=project.id if project else None,
                priority=priority,
                assignee_discord_ids=[assignee.id] if assignee else None,
                due_date=parsed_due_date,
                discord_channel_id=interaction.channel_id
            )
            
            # Create embed and view
            embed = create_task_embed(task)
            view = TaskView(task.id)
            
            await interaction.response.send_message(embed=embed, view=view)
            
            # Update task with message ID
            message = await interaction.original_response()
            await TaskService.update_task(task.id, discord_message_id=message.id)
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            await interaction.response.send_message(
                "❌ Failed to create task. Please try again.",
                ephemeral=True
            )
    
    @app_commands.command(name="task", description="View or manage a task")
    @app_commands.describe(task_id="ID of the task to view")
    async def view_task(self, interaction: discord.Interaction, task_id: int):
        """View a specific task."""
        task = await TaskService.get_task_by_id(task_id)
        
        if not task:
            await interaction.response.send_message(
                "❌ Task not found.",
                ephemeral=True
            )
            return
        
        embed = create_task_embed(task)
        view = TaskView(task.id)
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="my-tasks", description="View your assigned tasks")
    @app_commands.describe(status="Filter by task status")
    async def my_tasks(
        self,
        interaction: discord.Interaction,
        status: Optional[str] = None
    ):
        """View user's assigned tasks."""
        tasks = await TaskService.get_tasks_for_user(
            user_discord_id=interaction.user.id,
            status=status
        )
        
        if not tasks:
            status_text = f" with status '{status}'" if status else ""
            await interaction.response.send_message(
                f"📝 You have no assigned tasks{status_text}.",
                ephemeral=True
            )
            return
        
        # Create embed with task list
        embed = discord.Embed(
            title="📋 Your Tasks",
            color=0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        
        for task in tasks[:10]:  # Limit to 10 tasks
            status_emoji = "✅" if task.status == TaskStatus.DONE.value else "⏳"
            due_text = ""
            if task.due_date:
                due_text = f" (Due: <t:{int(task.due_date.timestamp())}:d>)"
            
            embed.add_field(
                name=f"{status_emoji} {task.title}",
                value=f"ID: {task.id} | Status: {task.status.replace('_', ' ').title()}{due_text}",
                inline=False
            )
        
        if len(tasks) > 10:
            embed.set_footer(text=f"Showing 10 of {len(tasks)} tasks")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @commands.command(name="task-modal")
    async def create_task_modal(self, ctx):
        """Open task creation modal (prefix command)."""
        # Get project for current channel
        project = await ProjectService.get_project_by_channel(ctx.channel.id)
        
        modal = CreateTaskModal(project.id if project else None)
        
        # For prefix commands, we need to create a view with a button to open the modal
        class ModalView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="Create Task", style=discord.ButtonStyle.primary, emoji="📋")
            async def create_task_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(modal)
        
        view = ModalView()
        await ctx.send("Click the button to create a new task:", view=view)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(TasksCog(bot))