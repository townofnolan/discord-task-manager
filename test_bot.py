"""Test script to check Discord bot token."""

import asyncio
import logging
import os

import discord
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SimpleTestBot(discord.Client):
    async def on_ready(self):
        logger.info(f"Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        await self.close()


async def main():
    """Test the Discord bot token."""
    # Load environment variables
    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN")

    # Log the token length for verification (don't log the full token)
    if token:
        logger.info(f"Loaded token (length: {len(token)})")
    else:
        logger.error("Failed to load Discord token from .env file")
        return

    # Create intents
    intents = discord.Intents.default()
    intents.message_content = True

    # Create and start the bot
    logger.info("Starting bot...")
    client = SimpleTestBot(intents=intents)

    try:
        logger.info("Attempting to connect to Discord...")
        await client.start(token)
    except discord.errors.LoginFailure as e:
        logger.error(f"Login failed: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.info("Bot test complete")


if __name__ == "__main__":
    asyncio.run(main())
