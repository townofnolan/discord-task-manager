"""Main Discord Task Manager Bot."""

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from config import settings
from utils import close_database, init_database

logger = logging.getLogger(__name__)


class TaskManagerBot(commands.Bot):
    """Main Discord Task Manager Bot class."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        intents.guilds = True
        intents.members = True

        # Set up both "/" and "pp" as prefixes
        prefixes = [settings.bot_prefix, "/"]
        # Also include case variations
        prefixes += [p.lower() for p in prefixes] + [p.upper() for p in prefixes]

        super().__init__(
            command_prefix=commands.when_mentioned_or(*prefixes),
            intents=intents,
            description="Discord Task Manager",
            case_insensitive=True,
            # Use application ID if provided, else None
            application_id=settings.discord_application_id,
        )

        # Set up event for when the bot is ready
        self.initial_sync_done = False

    async def setup_hook(self):
        """Setup hook called when bot is starting."""
        logger.info("Setting up Discord Task Manager Bot...")

        # Initialize database
        await init_database()

        # Load cogs/extensions
        await self.load_extensions()

        # Register core commands
        self.register_core_commands()

        logger.info("Bot setup complete")

    async def load_extensions(self):
        """Load bot extensions/cogs."""
        extensions = [
            "bot.cogs.tasks",
            "bot.cogs.projects",
            "bot.cogs.time_tracking",
            "bot.cogs.calendar_integration",
            "bot.cogs.admin",
        ]

        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

    def register_core_commands(self):
        """Register core bot commands directly in the command tree."""

        @self.tree.command(name="ping", description="Check if the bot is responsive")
        async def ping_command(interaction: discord.Interaction):
            await interaction.response.send_message("Pong! 🏓")

        @self.tree.command(name="help", description="Show help information for the bot")
        async def help_command(interaction: discord.Interaction):
            # Create a help embed similar to send_formatted_help
            embed = discord.Embed(
                title="Discord Task Manager Help",
                description="Use these commands to manage tasks.",
                color=0x3498DB,
            )
            # Add basic help info
            embed.add_field(
                name="Commands",
                value="• `/create-task` - Create a new task\n"
                "• `/task` - View a task\n"
                "• `/my-tasks` - View your tasks",
                inline=False,
            )
            await interaction.response.send_message(embed=embed)

    async def on_ready(self):
        """Called when bot is ready."""
        if self.user:
            logger.info(f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
            logger.info(f"Connected to {len(self.guilds)} guilds")

            # Set bot status
            activity = discord.Activity(
                type=discord.ActivityType.watching, name="for task management commands"
            )
            await self.change_presence(activity=activity)

            # Register core commands and sync all commands with Discord
            if not self.initial_sync_done:
                # Register core commands
                self.register_core_commands()

                # Log application info for debugging
                logger.info(f"Bot Application ID: {self.application_id}")

                # Sync the commands with Discord for all connected guilds
                try:
                    # First, sync globally
                    logger.info("Attempting to sync commands globally...")
                    global_commands = await self.tree.sync()
                    logger.info(f"Synced {len(global_commands)} commands globally")

                    # Then sync to each guild individually to ensure they appear
                    for guild in self.guilds:
                        try:
                            guild_commands = await self.tree.sync(guild=guild)
                            logger.info(
                                f"Synced {len(guild_commands)} commands for guild: "
                                f"{guild.name} (ID: {guild.id})"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to sync commands for guild {guild.name}: {e}"
                            )

                    self.initial_sync_done = True
                    logger.info("Slash commands synchronization complete")

                    # Verify the commands were registered
                    all_commands = await self.tree.fetch_commands()
                    command_names = ", ".join([cmd.name for cmd in all_commands])
                    logger.info(
                        f"Verified {len(all_commands)} global commands: {command_names}"
                    )

                except Exception as e:
                    logger.error(f"Failed to sync commands: {e}", exc_info=True)

    async def on_error(self, event, *args, **kwargs):
        """Handle bot errors."""
        logger.error(f"Bot error in event {event}", exc_info=True)

    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {error}")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                "❌ I don't have the required permissions to execute this command."
            )
        else:
            logger.error(f"Unhandled command error: {error}", exc_info=True)
            await ctx.send("❌ An unexpected error occurred. Please try again later.")

    async def on_message(self, message):
        """Handle message events, including showing command list for "pp " prefix."""
        # Ignore messages from bots
        if message.author.bot:
            return

        # Check if the message is just the prefix with a space
        content = message.content.lower()
        prefix = settings.bot_prefix.lower()

        # If message is just prefix + space, show formatted help
        if content.startswith(f"{prefix} ") and len(content.strip()) <= len(prefix) + 1:
            ctx = await self.get_context(message)
            await self.send_formatted_help(ctx)
            # Try to delete the command message to keep the channel clean
            try:
                await message.delete()
            except discord.errors.Forbidden:
                # Bot doesn't have permission to delete messages
                pass
            return

        # Check if this is a command message
        ctx = await self.get_context(message)
        if ctx.command is not None:
            # This is a command - process it then delete the original message
            await super().on_message(message)
            # Try to delete the command message to keep the channel clean
            try:
                await message.delete()
            except discord.errors.Forbidden:
                # Bot doesn't have permission to delete messages
                pass
            return

        # Not a command - just process normally
        await super().on_message(message)

    async def send_formatted_help(self, ctx):
        """Send a formatted help message with embeds and buttons."""
        # Create the main help embed
        embed = discord.Embed(
            title="Discord Task Manager Help",
            description="Use these commands to manage tasks in your Discord server.",
            color=0x3498DB,
        )

        # Add general usage section
        embed.add_field(
            name="Getting Started",
            value="Use `/create-task` to create a new task, or\n"
            "`/task <id>` to view an existing task.",
            inline=False,
        )

        # Add command categories
        categories = {
            "Tasks": ["create-task", "task", "my-tasks"],
            "Projects": ["create-project", "project", "my-projects"],
            "Time Tracking": ["start-time", "stop-time", "time-report"],
        }

        for category, commands_list in categories.items():
            commands_text = ", ".join(f"`/{cmd}`" for cmd in commands_list)
            embed.add_field(
                name=f"{category} Commands", value=commands_text, inline=True
            )

        # Add footer with additional help info
        embed.set_footer(
            text="For detailed help on a specific command, use /help <command>"
        )

        # Create a view with buttons for command categories
        view = discord.ui.View(timeout=180)

        # Add buttons for main command categories
        for category in categories.keys():
            button = discord.ui.Button(
                label=category,
                style=discord.ButtonStyle.primary,
                custom_id=f"help_{category.lower().replace(' ', '_')}",
            )
            view.add_item(button)

        await ctx.send(embed=embed, view=view)

    async def close(self):
        """Clean shutdown."""
        logger.info("Shutting down bot...")
        await close_database()
        await super().close()


async def main():
    """Main function to run the bot."""
    # Log the application ID for debugging
    logger.info(f"Using Discord Application ID: {settings.discord_application_id}")

    # Create the bot instance
    bot = TaskManagerBot()
    try:
        await bot.start(settings.discord_bot_token)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        await bot.close()


if __name__ == "__main__":
    # Import and setup logging
    from config.logging import setup_logging

    setup_logging()  # Initialize logging configuration

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown complete")
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
