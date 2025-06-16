#!/usr/bin/env python3
import asyncio
import logging
from bot import main

if __name__ == "__main__":
	logging.basicConfig(
		level=logging.INFO,
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
		handlers=[
			logging.FileHandler('logs/bot.log'),
			logging.StreamHandler()
		]
	)
	asyncio.run(main())
