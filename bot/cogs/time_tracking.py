"""Time tracking cog for Discord bot."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from models import TimeEntry
from services import TaskService, UserService

logger = logging.getLogger(__name__)


class TimeTrackingCog(commands.Cog):
    """Commands for time tracking."""

    def __init__(self, bot):
        self.bot = bot
        # Dictionary to store active timers: {user_id: {task_id: start_time}}
        self.active_timers = {}

    @app_commands.command(
        name="start-timer", description="Start tracking time for a task"
    )
    @app_commands.describe(task_id="ID of the task to track time for")
    async def start_timer(self, interaction: discord.Interaction, task_id: int):
        """Start a timer for a task."""
        # Check if task exists
        task = await TaskService.get_task_by_id(task_id)
        if not task:
            await interaction.response.send_message(
                "❌ Task not found.", ephemeral=True
            )
            return

        user_id = interaction.user.id

        # Check if user already has a timer running for this task
        if user_id in self.active_timers and task_id in self.active_timers[user_id]:
            await interaction.response.send_message(
                f"⏱️ You already have a timer running for task **{task.title}**.",
                ephemeral=True,
            )
            return

        # Start timer
        if user_id not in self.active_timers:
            self.active_timers[user_id] = {}

        self.active_timers[user_id][task_id] = datetime.now(timezone.utc)

        embed = discord.Embed(
            title="⏱️ Timer Started",
            description=f"Started tracking time for task **{task.title}**",
            color=0x2ECC71,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Task ID", value=str(task_id), inline=True)
        embed.add_field(
            name="Started at",
            value=f"<t:{int(datetime.now(timezone.utc).timestamp())}:t>",
            inline=True,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="stop-timer", description="Stop tracking time for a task"
    )
    @app_commands.describe(
        task_id="ID of the task to stop tracking",
        description="Description of the work done",
    )
    async def stop_timer(
        self,
        interaction: discord.Interaction,
        task_id: int,
        description: Optional[str] = None,
    ):
        """Stop a timer for a task."""
        user_id = interaction.user.id

        # Check if user has a timer running for this task
        if (
            user_id not in self.active_timers
            or task_id not in self.active_timers[user_id]
        ):
            await interaction.response.send_message(
                "❌ No active timer found for this task.", ephemeral=True
            )
            return

        # Calculate duration
        start_time = self.active_timers[user_id][task_id]
        end_time = datetime.now(timezone.utc)
        duration = end_time - start_time
        duration_hours = duration.total_seconds() / 3600

        # Remove from active timers
        del self.active_timers[user_id][task_id]
        if not self.active_timers[user_id]:
            del self.active_timers[user_id]

        # Get task info
        task = await TaskService.get_task_by_id(task_id)
        if not task:
            await interaction.response.send_message(
                "❌ Task not found.", ephemeral=True
            )
            return

        # TODO: Save time entry to database
        # For now, just show the summary

        embed = discord.Embed(
            title="⏹️ Timer Stopped",
            description=f"Stopped tracking time for task **{task.title}**",
            color=0xE74C3C,
            timestamp=datetime.now(timezone.utc),
        )

        # Format duration
        hours = int(duration_hours)
        minutes = int((duration_hours - hours) * 60)
        duration_text = f"{hours}h {minutes}m"

        embed.add_field(name="Duration", value=duration_text, inline=True)
        embed.add_field(
            name="Started at", value=f"<t:{int(start_time.timestamp())}:t>", inline=True
        )
        embed.add_field(
            name="Ended at", value=f"<t:{int(end_time.timestamp())}:t>", inline=True
        )

        if description:
            embed.add_field(name="Work Description", value=description, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="active-timers", description="View your active timers")
    async def active_timers(self, interaction: discord.Interaction):
        """View user's active timers."""
        user_id = interaction.user.id

        if user_id not in self.active_timers or not self.active_timers[user_id]:
            await interaction.response.send_message(
                "⏱️ You have no active timers.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⏱️ Your Active Timers",
            color=0x3498DB,
            timestamp=datetime.now(timezone.utc),
        )

        for task_id, start_time in self.active_timers[user_id].items():
            # Get task info
            task = await TaskService.get_task_by_id(task_id)
            if task:
                # Calculate current duration
                current_duration = datetime.now(timezone.utc) - start_time
                hours = int(current_duration.total_seconds() // 3600)
                minutes = int((current_duration.total_seconds() % 3600) // 60)
                duration_text = f"{hours}h {minutes}m"

                embed.add_field(
                    name=f"📋 {task.title}",
                    value=f"Task ID: {task_id}\nRunning for: {duration_text}\nStarted: <t:{int(start_time.timestamp())}:R>",
                    inline=False,
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="time-report", description="View time tracking report")
    @app_commands.describe(
        task_id="Specific task ID (optional)",
        days="Number of days to look back (default: 7)",
    )
    async def time_report(
        self,
        interaction: discord.Interaction,
        task_id: Optional[int] = None,
        days: Optional[int] = 7,
    ):
        """View time tracking report."""
        # TODO: Implement time report from database
        # For now, show placeholder

        embed = discord.Embed(
            title="📊 Time Tracking Report",
            description="Time tracking reports will be available once the database time entries are implemented.",
            color=0x9B59B6,
            timestamp=datetime.now(timezone.utc),
        )

        embed.add_field(
            name="Coming Soon",
            value="• Time entries per task\n• Daily/weekly summaries\n• Team time reports\n• Productivity insights",
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(TimeTrackingCog(bot))
