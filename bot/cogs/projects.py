"""Projects management cog for Discord bot."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from models import TaskStatus
from services import ProjectService, TaskService

logger = logging.getLogger(__name__)

# Predefined color options for projects
COLOR_OPTIONS: Dict[str, str] = {
    "Blue": "#3498db",
    "Red": "#e74c3c",
    "Green": "#2ecc71",
    "Purple": "#9b59b6",
    "Orange": "#e67e22",
}


class ProjectView(discord.ui.View):
    """Interactive view for project management."""

    def __init__(self, project_id: int):
        super().__init__(timeout=300)
        self.project_id = project_id

    @discord.ui.button(
        label="View Tasks", style=discord.ButtonStyle.primary, emoji="📋"
    )
    async def view_tasks(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """View project tasks."""
        project = await ProjectService.get_project_by_id(self.project_id)
        if not project:
            await interaction.response.send_message(
                "❌ Project not found.", ephemeral=True
            )
            return

        tasks = await TaskService.get_tasks_for_project(self.project_id)

        if not tasks:
            await interaction.response.send_message(
                f"📝 No tasks found for project '{project.name}'.", ephemeral=True
            )
            return

        # Create embed with task list
        embed = discord.Embed(
            title=f"📋 Tasks for {project.name}",
            color=(
                int(project.color.replace("#", ""), 16) if project.color else 0x3498DB
            ),
            timestamp=datetime.now(timezone.utc),
        )

        for task in tasks[:10]:  # Limit to 10 tasks
            status_emoji = "✅" if task.status == TaskStatus.DONE.value else "⏳"
            due_text = ""
            if task.due_date:
                due_text = f" (Due: <t:{int(task.due_date.timestamp())}:d>)"

            embed.add_field(
                name=f"{status_emoji} {task.title}",
                value=(
                    f"ID: {task.id} | Status: {task.status.replace('_', ' ').title()}"
                    f"{due_text}"
                ),
                inline=False,
            )

        if len(tasks) > 10:
            embed.set_footer(text=f"Showing 10 of {len(tasks)} tasks")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Members", style=discord.ButtonStyle.success, emoji="👥")
    async def manage_members(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Manage project members button."""
        project = await ProjectService.get_project_by_id(self.project_id)
        if not project:
            await interaction.response.send_message(
                "❌ Project not found.", ephemeral=True
            )
            return

        # Create embed with member list
        embed = discord.Embed(
            title=f"👥 Members of {project.name}",
            color=(
                int(project.color.replace("#", ""), 16) if project.color else 0x3498DB
            ),
            timestamp=datetime.now(timezone.utc),
        )

        if project.members:
            for member in project.members:
                embed.add_field(
                    name=member.username, value=f"<@{member.discord_id}>", inline=True
                )
        else:
            embed.description = "No members in this project."

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Add Member", style=discord.ButtonStyle.secondary, emoji="👤"
    )
    async def add_member(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Add member to project."""
        modal = AddMemberModal(self.project_id)
        await interaction.response.send_modal(modal)


class CreateProjectModal(discord.ui.Modal, title="Create New Project"):
    """Modal for creating new projects."""

    project_name = discord.ui.TextInput(
        label="Project Name",
        placeholder="Enter project name...",
        required=True,
        max_length=200,
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter project description...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=2000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            view = ColorSelectView(
                project_name=self.project_name.value,
                description=self.description.value if self.description.value else None,
                creator_id=interaction.user.id,
            )
            await interaction.response.send_message(
                "Select a color for the project:",
                view=view,
                ephemeral=True,
            )

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            await interaction.response.send_message(
                "❌ Failed to create project. Please try again.", ephemeral=True
            )


def create_project_embed(project) -> discord.Embed:
    """Create Discord embed for a project."""
    try:
        color = int(project.color.replace("#", ""), 16)
    except Exception:  # Use specific exception instead of bare except
        color = 0x3498DB

    embed = discord.Embed(
        title=f"📁 {project.name}",
        description=project.description or "No description provided",
        color=color,
        timestamp=project.created_at,
    )

    # Member count
    member_count = len(project.members) if project.members else 0
    embed.add_field(name="Members", value=str(member_count), inline=True)

    # Task statistics
    if project.tasks:
        total_tasks = len(project.tasks)
        # Split long lines for better readability
        completed_tasks = len(
            [t for t in project.tasks if t.status == TaskStatus.DONE.value]
        )
        in_progress_tasks = len(
            [t for t in project.tasks if t.status == TaskStatus.IN_PROGRESS.value]
        )

        task_stats = f"Total: {total_tasks}\n"
        task_stats += f"Completed: {completed_tasks}\n"
        task_stats += f"In Progress: {in_progress_tasks}"

        embed.add_field(name="Tasks", value=task_stats, inline=True)
    else:
        embed.add_field(name="Tasks", value="No tasks yet", inline=True)

    # Channel info
    if project.discord_channel_id:
        embed.add_field(
            name="Channel", value=f"<#{project.discord_channel_id}>", inline=True
        )

    # Project ID in footer
    embed.set_footer(text=f"Project ID: {project.id}")

    return embed


class AddMemberModal(discord.ui.Modal, title="Add Project Member"):
    """Modal for adding members to projects."""

    member_mention = discord.ui.TextInput(
        label="Member",
        placeholder="@username or user ID",
        required=True,
        max_length=100,
    )

    def __init__(self, project_id: int):
        super().__init__()
        self.project_id = project_id

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            # Parse user mention or ID
            user_id = None
            member_input = self.member_mention.value.strip()

            # Try to extract user ID from mention
            import re

            mention_match = re.search(r"<@!?(\d+)>", member_input)
            if mention_match:
                user_id = int(mention_match.group(1))
            else:
                # Try to parse as direct ID
                try:
                    user_id = int(member_input)
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid user format. Use @username or user ID.",
                        ephemeral=True,
                    )
                    return

            # Add member to project
            success = await ProjectService.add_member_to_project(
                self.project_id, user_id
            )

            if success:
                await interaction.response.send_message(
                    f"✅ Added <@{user_id}> to the project.", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Failed to add member to project.", ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error adding member to project: {e}")
            await interaction.response.send_message(
                "❌ Failed to add member. Please try again.", ephemeral=True
            )


class ColorSelectView(discord.ui.View):
    """View for selecting a project color."""

    def __init__(self, project_name: str, description: Optional[str], creator_id: int):
        super().__init__(timeout=60)
        self.project_name = project_name
        self.description = description
        self.creator_id = creator_id

        options = [
            discord.SelectOption(label=name, value=hex_code)
            for name, hex_code in COLOR_OPTIONS.items()
        ]
        self.add_item(ColorSelect(options))


class ColorSelect(discord.ui.Select):
    def __init__(self, options: List[discord.SelectOption]):
        super().__init__(placeholder="Choose a color...", options=options)

    async def callback(self, interaction: discord.Interaction):
        view: ColorSelectView = self.view  # type: ignore
        selected_color = self.values[0]
        try:
            project = await ProjectService.create_project(
                name=view.project_name,
                description=view.description,
                discord_channel_id=interaction.channel_id,
                color=selected_color,
            )
            await ProjectService.add_member_to_project(project.id, view.creator_id)
            embed = create_project_embed(project)
            await interaction.response.edit_message(
                content=None, embed=embed, view=None
            )
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            await interaction.response.send_message(
                "❌ Failed to create project. Please try again.",
                ephemeral=True,
            )


class ProjectsCog(commands.Cog):
    """Cog for project management commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create-project", description="Create a new project")
    @app_commands.describe(
        name="Project name", description="Project description", color="Project color"
    )
    @app_commands.choices(
        color=[
            app_commands.Choice(name=name, value=hex_code)
            for name, hex_code in COLOR_OPTIONS.items()
        ]
    )
    async def create_project(
        self,
        interaction: discord.Interaction,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[app_commands.Choice[str]] = None,
    ):
        """Create a new project via slash command."""
        # If name is not provided, show the modal
        if name is None:
            modal = CreateProjectModal()
            await interaction.response.send_modal(modal)
            return

        try:
            selected_color = color.value if color else "#3498db"

            # Create project
            project = await ProjectService.create_project(
                name=name,
                description=description,
                discord_channel_id=interaction.channel_id,
                color=selected_color,
            )

            # Add creator as member
            await ProjectService.add_member_to_project(project.id, interaction.user.id)

            # Create embed and view
            embed = create_project_embed(project)
            view = ProjectView(project.id)

            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            await interaction.response.send_message(
                "❌ Failed to create project. Please try again.", ephemeral=True
            )

    @app_commands.command(name="project", description="View or manage a project")
    @app_commands.describe(project_id="ID of the project to view")
    async def view_project(self, interaction: discord.Interaction, project_id: int):
        """View a specific project."""
        project = await ProjectService.get_project_by_id(project_id)

        if not project:
            await interaction.response.send_message(
                "❌ Project not found.", ephemeral=True
            )
            return

        embed = create_project_embed(project)
        view = ProjectView(project.id)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="my-projects", description="View your projects")
    async def my_projects(self, interaction: discord.Interaction):
        """View user's projects."""
        projects = await ProjectService.get_projects_for_user(interaction.user.id)

        if not projects:
            await interaction.response.send_message(
                "📁 You're not a member of any projects yet.", ephemeral=True
            )
            return

        # Create embed with project list
        embed = discord.Embed(
            title="📁 Your Projects",
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc),
        )

        for project in projects[:10]:  # Limit to 10 projects
            task_count = len(project.tasks) if project.tasks else 0
            member_count = len(project.members) if project.members else 0

            embed.add_field(
                name=f"📁 {project.name}",
                value=(
                    f"ID: {project.id} | Tasks: {task_count} | Members: {member_count}"
                ),
                inline=False,
            )

        if len(projects) > 10:
            embed.set_footer(text=f"Showing 10 of {len(projects)} projects")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="projects", description="List all projects")
    async def list_projects(self, interaction: discord.Interaction):
        """List all active projects."""
        projects = await ProjectService.get_all_projects()

        if not projects:
            await interaction.response.send_message(
                "📁 No projects found.", ephemeral=True
            )
            return

        # Create embed with project list
        embed = discord.Embed(
            title="📁 All Projects",
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc),
        )

        for project in projects[:15]:  # Limit to 15 projects
            task_count = len(project.tasks) if project.tasks else 0
            member_count = len(project.members) if project.members else 0

            embed.add_field(
                name=f"📁 {project.name}",
                value=(
                    f"ID: {project.id} | Tasks: {task_count} | Members: {member_count}"
                ),
                inline=True,
            )

        if len(projects) > 15:
            embed.set_footer(text=f"Showing 15 of {len(projects)} projects")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="project-modal")
    async def create_project_modal(self, ctx):
        """Open project creation modal (prefix command)."""
        modal = CreateProjectModal()

        # For prefix commands, we need to create a view with a button to open the modal
        class ModalView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(
                label="Create Project", style=discord.ButtonStyle.primary, emoji="📁"
            )
            async def create_project_button(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                await interaction.response.send_modal(modal)

        view = ModalView()
        await ctx.send("Click the button to create a new project:", view=view)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(ProjectsCog(bot))
