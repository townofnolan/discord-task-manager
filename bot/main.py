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
        )

        # Set up event for when the bot is ready
        self.initial_sync_done = False

        # Set up command tree events
        self._setup_listeners()

    async def setup_hook(self):
        """Setup hook called when bot is starting."""
        logger.info("Setting up Discord Task Manager Bot...")

        # Initialize database
        await init_database()

        # Load cogs/extensions
        await self.load_extensions()

        # Sync slash commands with Discord
        logger.info("Syncing application commands with Discord...")
        await self.tree.sync()

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

            # Register a test slash command directly
            if not self.initial_sync_done:
                # Add a test command to the tree
                @self.tree.command(
                    name="ping", description="Check if the bot is responsive"
                )
                async def ping(interaction: discord.Interaction):
                    await interaction.response.send_message("Pong! 🏓")

                # Sync the commands with Discord
                await self.tree.sync()
                self.initial_sync_done = True
                logger.info("Slash commands synchronized with Discord")

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

        # If message is just prefix + space, show help
        if content.startswith(f"{prefix} ") and len(content.strip()) <= len(prefix) + 1:
            ctx = await self.get_context(message)
            await ctx.send_help()
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

    async def close(self):
        """Clean shutdown."""
        logger.info("Shutting down bot...")
        await close_database()
        await super().close()


# Global bot instance
bot = TaskManagerBot()


async def main():
    """Main function to run the bot."""
    try:
        await bot.start(settings.discord_bot_token)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        await bot.close()


if __name__ == "__main__":
    # Import logging setup
    from config.logging import setup_logging

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown complete")
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
