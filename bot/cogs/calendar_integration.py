"""Calendar integration cog for Discord bot."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from services import ProjectService, TaskService

logger = logging.getLogger(__name__)


class CalendarIntegrationCog(commands.Cog):
    """Commands for calendar integration."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="calendar-export", description="Export tasks to calendar format"
    )
    @app_commands.describe(
        project_id="Project ID to export (optional)", format_type="Export format (ical)"
    )
    async def calendar_export(
        self,
        interaction: discord.Interaction,
        project_id: Optional[int] = None,
        format_type: Optional[str] = "ical",
    ):
        """Export tasks to calendar format."""
        # TODO: Implement iCal generation

        embed = discord.Embed(
            title="📅 Calendar Export",
            description="Calendar export functionality will be available once iCal generation is implemented.",
            color=0xE67E22,
            timestamp=datetime.now(timezone.utc),
        )

        embed.add_field(
            name="Planned Features",
            value="• iCal feed generation\n• Task due dates as calendar events\n• Project-specific calendars\n• URL-based calendar subscriptions",
            inline=False,
        )

        if project_id:
            project = await ProjectService.get_project_by_id(project_id)
            if project:
                embed.add_field(
                    name="Target Project",
                    value=f"📁 {project.name} (ID: {project_id})",
                    inline=True,
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="upcoming-deadlines", description="View upcoming task deadlines"
    )
    @app_commands.describe(days="Number of days to look ahead (default: 7)")
    async def upcoming_deadlines(
        self, interaction: discord.Interaction, days: Optional[int] = 7
    ):
        """View upcoming task deadlines."""
        # Get tasks assigned to user with due dates in the next N days
        tasks = await TaskService.get_tasks_for_user(interaction.user.id)

        # Filter tasks with due dates in the specified range
        now = datetime.now(timezone.utc)
        future_date = now + timedelta(days=days)

        upcoming_tasks = [
            task
            for task in tasks
            if task.due_date and now <= task.due_date <= future_date
        ]

        if not upcoming_tasks:
            await interaction.response.send_message(
                f"📅 You have no upcoming deadlines in the next {days} days.",
                ephemeral=True,
            )
            return

        # Sort by due date
        upcoming_tasks.sort(key=lambda t: t.due_date)

        embed = discord.Embed(
            title=f"📅 Upcoming Deadlines ({days} days)",
            color=0xF39C12,
            timestamp=datetime.now(timezone.utc),
        )

        for task in upcoming_tasks[:10]:  # Limit to 10 tasks
            # Calculate days until due
            days_until = (task.due_date - now).days
            time_text = (
                "Today"
                if days_until == 0
                else f"{days_until} day{'s' if days_until != 1 else ''}"
            )

            # Priority emoji
            priority_emoji = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🟠",
                "urgent": "🔴",
            }.get(task.priority, "⚪")

            embed.add_field(
                name=f"{priority_emoji} {task.title}",
                value=f"Due: <t:{int(task.due_date.timestamp())}:R> ({time_text})\nTask ID: {task.id}",
                inline=False,
            )

        if len(upcoming_tasks) > 10:
            embed.set_footer(
                text=f"Showing 10 of {len(upcoming_tasks)} upcoming deadlines"
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="overdue-tasks", description="View overdue tasks")
    async def overdue_tasks(self, interaction: discord.Interaction):
        """View overdue tasks."""
        overdue_tasks = await TaskService.get_overdue_tasks()

        # Filter to only tasks assigned to the user
        user_overdue_tasks = [
            task
            for task in overdue_tasks
            if any(
                assignee.discord_id == interaction.user.id
                for assignee in task.assignees
            )
        ]

        if not user_overdue_tasks:
            await interaction.response.send_message(
                "✅ You have no overdue tasks!", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🚨 Overdue Tasks",
            description="These tasks are past their due date and need attention.",
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc),
        )

        for task in user_overdue_tasks[:10]:  # Limit to 10 tasks
            # Calculate days overdue
            now = datetime.now(timezone.utc)
            days_overdue = (now - task.due_date).days
            overdue_text = (
                f"{days_overdue} day{'s' if days_overdue != 1 else ''} overdue"
            )

            # Priority emoji
            priority_emoji = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🟠",
                "urgent": "🔴",
            }.get(task.priority, "⚪")

            embed.add_field(
                name=f"{priority_emoji} {task.title}",
                value=f"Due: <t:{int(task.due_date.timestamp())}:D> ({overdue_text})\nTask ID: {task.id}",
                inline=False,
            )

        if len(user_overdue_tasks) > 10:
            embed.set_footer(
                text=f"Showing 10 of {len(user_overdue_tasks)} overdue tasks"
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(CalendarIntegrationCog(bot))
