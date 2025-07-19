"""Main Discord Task Manager Bot."""

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from config import settings
from utils import init_database, close_database

logger = logging.getLogger(__name__)


class TaskManagerBot(commands.Bot):
    """Main Discord Task Manager Bot class."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=settings.bot_prefix,
            intents=intents,
            description="Discord Task Manager - Airtable-like task management for small teams"
        )
    
    async def setup_hook(self):
        """Setup hook called when bot is starting."""
        logger.info("Setting up Discord Task Manager Bot...")
        
        # Initialize database
        await init_database()
        
        # Load cogs/extensions
        await self.load_extensions()
        
        logger.info("Bot setup complete")
    
    async def load_extensions(self):
        """Load bot extensions/cogs."""
        extensions = [
            "bot.cogs.tasks",
            "bot.cogs.projects", 
            "bot.cogs.time_tracking",
            "bot.cogs.calendar_integration",
            "bot.cogs.admin"
        ]
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for task management commands"
        )
        await self.change_presence(activity=activity)
    
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
            await ctx.send("❌ I don't have the required permissions to execute this command.")
        else:
            logger.error(f"Unhandled command error: {error}", exc_info=True)
            await ctx.send("❌ An unexpected error occurred. Please try again later.")
    
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