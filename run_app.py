#!/usr/bin/env python3
import logging
from app import app

if __name__ == "__main__":
	logging.basicConfig(
		level=logging.INFO,
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
		handlers=[
			logging.FileHandler('logs/admin.log'),
			logging.StreamHandler()
		]
	)
	app.run(debug=False, host="0.0.0.0", port=5000)
