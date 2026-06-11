import os
import sys
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Loguru
logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add("edupulse.log", rotation="10 MB", retention="10 days", level="DEBUG")

def get_env_var(name, default=None):
	value = os.getenv(name, default)
	if value is None:
		logger.warning(f"Environment variable {name} is not set.")
	return value

def log_agent_action(agent_name, action):
	logger.info(f"Agent [{agent_name}] is performing: {action}")
