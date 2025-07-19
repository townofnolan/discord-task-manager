"""Main entry point for Discord Task Manager."""

import asyncio
import logging
from bot.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application stopped by user")
    except Exception as e:
        logging.critical(f"Critical error: {e}", exc_info=True)