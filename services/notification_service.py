"""Notification service for managing scheduled notifications."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import discord

from models import Task, TaskStatus
from services.task_service import TaskService

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing scheduled notifications."""

    def __init__(self, bot):
        self.bot = bot
        self.scheduled_tasks = {}
        self.running = False

    def start(self):
        """Start the notification service."""
        if self.running:
            return

        self.running = True
        asyncio.create_task(self._notification_loop())
        logger.info("Notification service started")

    def stop(self):
        """Stop the notification service."""
        self.running = False
        logger.info("Notification service stopping...")

    async def _notification_loop(self):
        """Main notification loop that runs periodically."""
        while self.running:
            try:
                now = datetime.now(timezone.utc)

                # Check if it's morning time (8:00 AM)
                if now.hour == 8 and now.minute == 0:
                    await self.send_morning_summary()

                # Check if it's evening time (8:00 PM)
                if now.hour == 20 and now.minute == 0:
                    await self.send_evening_summary()

                # Check for overdue tasks every hour
                if now.minute == 0:
                    await self.send_overdue_task_alerts()

                # Process recurring tasks every hour
                if now.minute == 0:
                    await TaskService.process_recurring_tasks()

                # Sleep for 1 minute before checking again
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in notification loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Sleep on error to avoid spam

    async def send_morning_summary(self):
        """Send morning summary of today's tasks to all active channels."""
        logger.info("Sending morning summary...")

        try:
            # Get today's date range
            now = datetime.now(timezone.utc)
            start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)

            # Get tasks due today
            today_tasks = await TaskService.get_tasks_by_date_range(
                start_date=start_of_day, end_date=end_of_day
            )

            if not today_tasks:
                return  # No tasks to report

            # Group tasks by channel
            tasks_by_channel = {}
            for task in today_tasks:
                if not task.discord_channel_id:
                    continue

                channel_id = task.discord_channel_id
                if channel_id not in tasks_by_channel:
                    tasks_by_channel[channel_id] = []

                tasks_by_channel[channel_id].append(task)

            # Send summary to each channel
            for channel_id, tasks in tasks_by_channel.items():
                try:
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        continue

                    # Create embed
                    embed = discord.Embed(
                        title="☀️ Morning Task Summary",
                        description=f"Here are your tasks for today ({start_of_day.strftime('%A, %B %d')})",
                        color=0x3498DB,
                        timestamp=now,
                    )

                    # Group tasks by assignee
                    tasks_by_assignee = {}
                    for task in tasks:
                        for assignee in task.assignees:
                            if assignee.discord_id not in tasks_by_assignee:
                                tasks_by_assignee[assignee.discord_id] = []
                            tasks_by_assignee[assignee.discord_id].append(task)

                    # Add a field for each assignee
                    for discord_id, user_tasks in tasks_by_assignee.items():
                        # Try to get the user
                        user = None
                        try:
                            guild = channel.guild
                            user = await guild.fetch_member(discord_id)
                        except:
                            pass

                        user_name = user.display_name if user else "Unknown User"

                        # Format tasks
                        task_list = []
                        for task in user_tasks:
                            priority_emoji = {
                                "low": "🟢",
                                "medium": "🟡",
                                "high": "🟠",
                                "urgent": "🔴",
                            }.get(task.priority, "⚪")

                            time_str = ""
                            if task.due_date:
                                time_str = (
                                    f" (due {task.due_date.strftime('%I:%M %p')})"
                                )

                            task_list.append(
                                f"{priority_emoji} **{task.title}**{time_str}"
                            )

                        task_text = "\n".join(task_list)
                        embed.add_field(
                            name=f"{user_name}'s Tasks", value=task_text, inline=False
                        )

                    # Send the embed
                    await channel.send(embed=embed)

                except Exception as e:
                    logger.error(
                        f"Error sending morning summary to channel {channel_id}: {e}",
                        exc_info=True,
                    )

        except Exception as e:
            logger.error(f"Error in morning summary: {e}", exc_info=True)

    async def send_evening_summary(self):
        """Send evening summary of completed tasks and tomorrow's tasks."""
        logger.info("Sending evening summary...")

        try:
            # Get today's completed tasks
            now = datetime.now(timezone.utc)
            start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)

            # Get tomorrow's date range
            start_of_tomorrow = end_of_day
            end_of_tomorrow = start_of_tomorrow + timedelta(days=1)

            # Get tasks completed today
            # We'd need to add a new method to TaskService for this

            # Get tasks due tomorrow
            tomorrow_tasks = await TaskService.get_tasks_by_date_range(
                start_date=start_of_tomorrow, end_date=end_of_tomorrow
            )

            if not tomorrow_tasks:
                return  # No tasks to report

            # Group tasks by channel
            tasks_by_channel = {}
            for task in tomorrow_tasks:
                if not task.discord_channel_id:
                    continue

                channel_id = task.discord_channel_id
                if channel_id not in tasks_by_channel:
                    tasks_by_channel[channel_id] = []

                tasks_by_channel[channel_id].append(task)

            # Send summary to each channel
            for channel_id, tasks in tasks_by_channel.items():
                try:
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        continue

                    # Create embed
                    embed = discord.Embed(
                        title="🌙 Evening Task Preview",
                        description=f"Here are your tasks for tomorrow ({start_of_tomorrow.strftime('%A, %B %d')})",
                        color=0x9B59B6,
                        timestamp=now,
                    )

                    # Group tasks by assignee
                    tasks_by_assignee = {}
                    for task in tasks:
                        for assignee in task.assignees:
                            if assignee.discord_id not in tasks_by_assignee:
                                tasks_by_assignee[assignee.discord_id] = []
                            tasks_by_assignee[assignee.discord_id].append(task)

                    # Add a field for each assignee
                    for discord_id, user_tasks in tasks_by_assignee.items():
                        # Try to get the user
                        user = None
                        try:
                            guild = channel.guild
                            user = await guild.fetch_member(discord_id)
                        except:
                            pass

                        user_name = user.display_name if user else "Unknown User"

                        # Format tasks
                        task_list = []
                        for task in user_tasks:
                            priority_emoji = {
                                "low": "🟢",
                                "medium": "🟡",
                                "high": "🟠",
                                "urgent": "🔴",
                            }.get(task.priority, "⚪")

                            time_str = ""
                            if task.due_date:
                                time_str = (
                                    f" (due {task.due_date.strftime('%I:%M %p')})"
                                )

                            task_list.append(
                                f"{priority_emoji} **{task.title}**{time_str}"
                            )

                        task_text = "\n".join(task_list)
                        embed.add_field(
                            name=f"{user_name}'s Tasks for Tomorrow",
                            value=task_text,
                            inline=False,
                        )

                    # Send the embed
                    await channel.send(embed=embed)

                except Exception as e:
                    logger.error(
                        f"Error sending evening summary to channel {channel_id}: {e}",
                        exc_info=True,
                    )

        except Exception as e:
            logger.error(f"Error in evening summary: {e}", exc_info=True)

    async def send_overdue_task_alerts(self):
        """Send alerts for overdue tasks."""
        logger.info("Checking for overdue tasks...")

        try:
            # Get overdue tasks
            overdue_tasks = await TaskService.get_overdue_tasks()

            if not overdue_tasks:
                return  # No overdue tasks

            # Group tasks by channel
            tasks_by_channel = {}
            for task in overdue_tasks:
                if not task.discord_channel_id:
                    continue

                channel_id = task.discord_channel_id
                if channel_id not in tasks_by_channel:
                    tasks_by_channel[channel_id] = []

                tasks_by_channel[channel_id].append(task)

            # Send alerts to each channel
            for channel_id, tasks in tasks_by_channel.items():
                try:
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        continue

                    now = datetime.now(timezone.utc)

                    # Only alert for tasks that are newly overdue (less than 2 hours)
                    # or have been overdue for more than 24 hours
                    filtered_tasks = []
                    for task in tasks:
                        if task.due_date:
                            hours_overdue = (now - task.due_date).total_seconds() / 3600
                            if hours_overdue < 2 or (
                                hours_overdue > 24 and hours_overdue % 24 < 2
                            ):
                                filtered_tasks.append(task)

                    if not filtered_tasks:
                        continue

                    # Create embed
                    embed = discord.Embed(
                        title="🚨 Overdue Task Alert",
                        description="The following tasks need immediate attention:",
                        color=0xE74C3C,
                        timestamp=now,
                    )

                    # Add each overdue task
                    for task in filtered_tasks:
                        # Calculate how overdue
                        hours_overdue = (now - task.due_date).total_seconds() / 3600
                        days_overdue = int(hours_overdue / 24)

                        if days_overdue > 0:
                            overdue_text = f"{days_overdue} day{'s' if days_overdue != 1 else ''} overdue"
                        else:
                            overdue_text = f"{int(hours_overdue)} hour{'s' if int(hours_overdue) != 1 else ''} overdue"

                        # Format assignees
                        assignee_mentions = []
                        for assignee in task.assignees:
                            assignee_mentions.append(f"<@{assignee.discord_id}>")

                        assignee_text = (
                            ", ".join(assignee_mentions)
                            if assignee_mentions
                            else "Unassigned"
                        )

                        embed.add_field(
                            name=f"🔴 {task.title}",
                            value=f"**Status:** {task.status.capitalize()}\n"
                            f"**Due:** <t:{int(task.due_date.timestamp())}:R> ({overdue_text})\n"
                            f"**Assigned to:** {assignee_text}",
                            inline=False,
                        )

                    # Send the embed
                    await channel.send(embed=embed)

                except Exception as e:
                    logger.error(
                        f"Error sending overdue alerts to channel {channel_id}: {e}",
                        exc_info=True,
                    )

        except Exception as e:
            logger.error(f"Error in overdue alerts: {e}", exc_info=True)
