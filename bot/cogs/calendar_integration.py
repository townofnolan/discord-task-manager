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

    @app_commands.command(
        name="daily-schedule", description="View today's schedule for both partners"
    )
    async def daily_schedule(self, interaction: discord.Interaction):
        """View today's schedule for both partners."""
        # Get today's date range
        now = datetime.now(timezone.utc)
        start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        end_of_day = start_of_day + timedelta(days=1)

        # Get all users in the guild
        guild_members = interaction.guild.members if interaction.guild else []

        # Get tasks due today for all users in the guild
        async with interaction.channel.typing():
            # Fetch tasks for today
            all_today_tasks = await TaskService.get_tasks_by_date_range(
                start_date=start_of_day, end_date=end_of_day
            )

            if not all_today_tasks:
                await interaction.response.send_message(
                    "📅 There are no tasks scheduled for today.", ephemeral=False
                )
                return

            # Create schedule display
            embed = discord.Embed(
                title="📅 Today's Schedule",
                description=f"Tasks for {start_of_day.strftime('%A, %B %d, %Y')}",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc),
            )

            # Group tasks by assignee
            tasks_by_assignee = {}
            for task in all_today_tasks:
                for assignee in task.assignees:
                    if assignee.discord_id not in tasks_by_assignee:
                        tasks_by_assignee[assignee.discord_id] = []
                    tasks_by_assignee[assignee.discord_id].append(task)

            # Add a field for each user
            for discord_id, tasks in tasks_by_assignee.items():
                # Try to get the user from the guild
                user = None
                for member in guild_members:
                    if member.id == discord_id:
                        user = member
                        break

                # Skip if user not found in guild (should not happen typically)
                if not user:
                    continue

                # Sort tasks by due time
                tasks.sort(
                    key=lambda t: (
                        t.due_date
                        if t.due_date
                        else datetime.max.replace(tzinfo=timezone.utc)
                    )
                )

                # Format tasks for this user
                task_list = []
                for task in tasks:
                    priority_emoji = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🟠",
                        "urgent": "🔴",
                    }.get(task.priority, "⚪")

                    status_emoji = {
                        "todo": "📝",
                        "in_progress": "🏃",
                        "review": "👀",
                        "done": "✅",
                        "cancelled": "❌",
                    }.get(task.status, "📝")

                    time_str = ""
                    if task.due_date:
                        time_str = f" at {task.due_date.strftime('%I:%M %p')}"

                    task_list.append(
                        f"{priority_emoji} {status_emoji} **{task.title}**{time_str}"
                    )

                task_text = (
                    "\n".join(task_list) if task_list else "*No tasks for today*"
                )

                embed.add_field(
                    name=f"{user.display_name}'s Tasks", value=task_text, inline=False
                )

            # Add button to create a new task
            class ScheduleView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=300)

                @discord.ui.button(
                    label="Create Task", style=discord.ButtonStyle.primary, emoji="➕"
                )
                async def create_task(
                    self, interaction: discord.Interaction, button: discord.ui.Button
                ):
                    # Create a modal for task creation
                    modal = CreateTaskModal()
                    await interaction.response.send_modal(modal)

            # Send the embed with the view
            view = ScheduleView()
            await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(
        name="weekly-schedule", description="View this week's schedule"
    )
    async def weekly_schedule(self, interaction: discord.Interaction):
        """View weekly schedule."""
        # Get today and determine the start of the week (Monday)
        now = datetime.now(timezone.utc)
        start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

        # Calculate days to subtract to get to Monday (Monday=0, Sunday=6)
        days_to_monday = start_of_day.weekday()
        start_of_week = start_of_day - timedelta(days=days_to_monday)
        end_of_week = start_of_week + timedelta(days=7)

        # Get all tasks for the week
        async with interaction.channel.typing():
            weekly_tasks = await TaskService.get_tasks_by_date_range(
                start_date=start_of_week, end_date=end_of_week
            )

            if not weekly_tasks:
                await interaction.response.send_message(
                    "📅 There are no tasks scheduled for this week.", ephemeral=False
                )
                return

            # Create weekly view
            embed = discord.Embed(
                title="📅 Weekly Schedule",
                description=f"Week of {start_of_week.strftime('%B %d')} - {(end_of_week - timedelta(days=1)).strftime('%B %d, %Y')}",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc),
            )

            # Group tasks by day of week
            tasks_by_day = {i: [] for i in range(7)}
            for task in weekly_tasks:
                if task.due_date:
                    day_index = task.due_date.weekday()
                    tasks_by_day[day_index].append(task)

            # Days of the week
            days = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]

            # Add a field for each day
            for day_index, day_name in enumerate(days):
                tasks = tasks_by_day[day_index]

                # If it's the current day, highlight it
                day_prefix = "📍 " if day_index == days_to_monday else ""

                # Sort tasks by due time
                tasks.sort(
                    key=lambda t: (
                        t.due_date
                        if t.due_date
                        else datetime.max.replace(tzinfo=timezone.utc)
                    )
                )

                # Format tasks for this day
                task_list = []
                for task in tasks:
                    priority_emoji = {
                        "low": "🟢",
                        "medium": "🟡",
                        "high": "🟠",
                        "urgent": "🔴",
                    }.get(task.priority, "⚪")

                    # Get assignee names
                    assignee_names = []
                    for assignee in task.assignees:
                        for member in interaction.guild.members:
                            if member.id == assignee.discord_id:
                                assignee_names.append(member.display_name)
                                break

                    assignee_text = (
                        f" ({', '.join(assignee_names)})" if assignee_names else ""
                    )

                    time_str = ""
                    if task.due_date:
                        time_str = f" {task.due_date.strftime('%I:%M %p')}"

                    task_list.append(
                        f"{priority_emoji} **{task.title}**{time_str}{assignee_text}"
                    )

                task_text = (
                    "\n".join(task_list) if task_list else "*No tasks scheduled*"
                )

                embed.add_field(
                    name=f"{day_prefix}{day_name}", value=task_text, inline=False
                )

            # Send the embed
            await interaction.response.send_message(embed=embed)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(CalendarIntegrationCog(bot))
