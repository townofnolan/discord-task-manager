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

        # Process application ID properly
        app_id = None
        if settings.discord_application_id:
            try:
                app_id = int(settings.discord_application_id)
                logger.info(f"Using application ID: {app_id}")
            except ValueError:
                logger.error(
                    f"Invalid application ID format: {settings.discord_application_id}"
                )

        # Only use slash commands - no prefix needed
        super().__init__(
            command_prefix=commands.when_mentioned,  # Only respond when mentioned
            intents=intents,
            description="Discord Task Manager",
            case_insensitive=True,
            application_id=app_id,  # This must be an int or None
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

    async def copy_global_to_guild(self, guild_id):
        """Copy all commands to a specific guild to ensure they appear."""
        try:
            guild = self.get_guild(guild_id)
            if not guild:
                logger.error(f"Could not find guild with ID {guild_id}")
                return False

            # First clear any existing commands in the guild
            self.tree.clear_commands(guild=guild)
            logger.info(f"Cleared existing commands for guild {guild.name}")

            # Sync the cleared state to ensure we start fresh
            await self.tree.sync(guild=guild)

            # Now sync globally to get all commands
            global_commands = await self.tree.sync()
            logger.info(f"Synced {len(global_commands)} commands globally")

            # Force a sync specifically for this guild which should copy global commands
            guild_commands = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(guild_commands)} commands for guild {guild.name}")

            # Let's try one more thing - register via app_commands
            try:
                # Register all commands in app_commands namespace directly to guild
                from discord import app_commands

                logger.info(f"Using app_commands.CommandTree for {guild.name}")

                # Create a fresh command tree for this guild only
                guild_tree = app_commands.CommandTree(self)

                # Copy all our commands to the new tree
                for command in self.tree.get_commands():
                    guild_tree.add_command(command)
                    logger.info(f"Added {command.name} to guild tree")

                # Sync this tree specifically to the guild
                await guild_tree.sync(guild=guild)
                logger.info(f"Synced guild tree to {guild.name}")

            except Exception as e:
                logger.error(f"Error during app_commands direct sync: {e}")

            return True
        except Exception as e:
            logger.error(f"Error copying commands to guild {guild_id}: {e}")
            return False

    def register_core_commands(self):
        """Register core bot commands directly in the command tree."""

        @self.tree.command(name="help", description="Show help information for the bot")
        async def help_command(interaction: discord.Interaction):
            # Create a help embed
            embed = discord.Embed(
                title="Discord Task Manager Help",
                description="Use these slash commands to manage tasks and projects.",
                color=0x3498DB,
            )

            # Get all commands from the bot's command tree
            commands = await self.tree.fetch_commands()

            # Create command categories
            categories = {
                "Tasks": [],
                "Projects": [],
                "Time Tracking": [],
                "Calendar": [],
                "Admin": [],
                "General": [],
            }

            # Categorize commands
            for cmd in commands:
                # Check for task related commands
                if (
                    cmd.name.startswith("task")
                    or cmd.name.endswith("task")
                    or "task" in cmd.name
                ):
                    categories["Tasks"].append(cmd)
                # Check for project related commands
                elif (
                    cmd.name.startswith("project")
                    or cmd.name.endswith("project")
                    or "project" in cmd.name
                ):
                    categories["Projects"].append(cmd)
                # Check for time tracking commands
                elif "time" in cmd.name:
                    categories["Time Tracking"].append(cmd)
                # Check for calendar commands
                elif "calendar" in cmd.name or "event" in cmd.name:
                    categories["Calendar"].append(cmd)
                # Check for admin commands
                elif cmd.name in ["admin", "settings", "config"]:
                    categories["Admin"].append(cmd)
                # Default category
                else:
                    categories["General"].append(cmd)

            # Add each category to the embed
            for category, cmds in categories.items():
                if cmds:
                    # Format command list with descriptions
                    commands_text = "\n".join(
                        [f"• `/{cmd.name}` - {cmd.description}" for cmd in cmds]
                    )
                    # Add to embed
                    embed.add_field(
                        name=f"{category} Commands", value=commands_text, inline=False
                    )

            # Add footer with additional info
            embed.set_footer(text="All commands are available as slash commands (/)")

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

            # Sync all commands with Discord
            if not self.initial_sync_done:
                # Log application info for debugging
                logger.info(f"Bot Application ID: {self.application_id}")

                # Get Discord guild ID from settings
                from config import settings

                guild_id = settings.discord_guild_id

                try:
                    logger.info("===== STARTING COMMAND SYNC PROCESS =====")

                    # First, sync globally
                    global_commands = await self.tree.sync()
                    logger.info(f"1. Synced {len(global_commands)} commands globally")

                    # Get the list of currently available commands to debug
                    logger.info("2. Available commands in tree:")
                    for cmd in self.tree.get_commands():
                        logger.info(f"   - Command: {cmd.name}")

                    # Process the main guild if configured
                    if guild_id:
                        try:
                            # Convert to int if needed
                            guild_id_int = int(guild_id)
                            main_guild = self.get_guild(guild_id_int)

                            if main_guild:
                                logger.info(
                                    f"3. Syncing to main guild: {main_guild.name} ({guild_id_int})"
                                )

                                # Use our special function
                                await self.copy_global_to_guild(guild_id_int)

                                # Double-check the guild commands after sync
                                guild_commands = await self.tree.sync(guild=main_guild)
                                logger.info(
                                    f"4. Main guild now has {len(guild_commands)} commands"
                                )
                            else:
                                logger.warning(
                                    f"3. Main guild with ID {guild_id_int} not found"
                                )
                        except ValueError:
                            logger.error(f"Invalid guild ID format: {guild_id}")
                    else:
                        logger.warning("3. No main guild ID configured in settings")

                    # For each other guild, also sync directly
                    logger.info("5. Syncing to all connected guilds:")
                    for guild in self.guilds:
                        # Skip if this is the main guild we already processed
                        if guild_id and int(guild_id) == guild.id:
                            logger.info(
                                f"   - Skipping main guild {guild.name} (already processed)"
                            )
                            continue

                        try:
                            logger.info(
                                f"   - Syncing to guild: {guild.name} ({guild.id})"
                            )
                            guild_commands = await self.tree.sync(guild=guild)
                            logger.info(f"     Synced {len(guild_commands)} commands")
                        except Exception as e:
                            logger.error(
                                f"     Failed to sync to guild {guild.name}: {e}"
                            )

                    self.initial_sync_done = True
                    logger.info("===== COMMAND SYNC PROCESS COMPLETE =====")

                    # Final report - check global commands one more time
                    final_commands = await self.tree.fetch_commands()
                    logger.info(
                        f"Final check: {len(final_commands)} global commands available"
                    )

                    # Verify the commands were registered
                    all_commands = await self.tree.fetch_commands()
                    command_names = ", ".join([cmd.name for cmd in all_commands])
                    logger.info(
                        f"Verified {len(all_commands)} global commands: {command_names}"
                    )

                    # Add debug info about guild registrations
                    logger.info("=== DEBUG: Guild Command Registration ===")
                    for guild in self.guilds:
                        try:
                            guild_cmds = await self.tree.fetch_commands(guild=guild)
                            cmd_list = ", ".join([c.name for c in guild_cmds])
                            logger.info(
                                f"Guild {guild.name}: {len(guild_cmds)} commands"
                            )
                            if guild_cmds:
                                logger.info(f"Commands: {cmd_list}")
                        except Exception as e:
                            logger.error(f"Error fetching guild commands: {e}")

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
        """Handle message events."""
        # Ignore messages from bots
        if message.author.bot:
            return

        # Only process mentions since we're now using slash commands
        if self.user:
            mentions = [f"<@{self.user.id}>", f"<@!{self.user.id}>"]
            if message.content in mentions:
                # Reply with help when the bot is mentioned
                await message.channel.send(
                    f"👋 Hi {message.author.mention}! I'm a task management bot. "
                    f"Use `/help` to see available commands."
                )
            return

        # Process the message normally
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
