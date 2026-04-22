# copyright 2023 © Xron Trix | https://github.com/Xrontrix10

import sys
import os
import logging
import json
from pyrogram.client import Client

if sys.platform == "win32":
  sys.stdout.reconfigure(encoding="utf-8")

# ─── Resolve project root dynamically ───────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Read credentials from dynamically resolved path
credentials_path = os.path.join(PROJECT_ROOT, "credentials.json")
if not os.path.exists(credentials_path):
  logging.error(f"credentials.json not found at {credentials_path}")
  logging.error("Please run main.py first, or create credentials.json manually.")
  sys.exit(1)

with open(credentials_path, "r") as file:
  credentials = json.loads(file.read())

API_ID = credentials["API_ID"]
API_HASH = credentials["API_HASH"]
BOT_TOKEN = credentials["BOT_TOKEN"]
OWNER = credentials["USER_ID"]
DUMP_ID = credentials["DUMP_ID"]


from logging.handlers import RotatingFileHandler

log_dir = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "bot.log")

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
  handlers=[
    RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3),
    logging.StreamHandler(sys.stdout)
  ]
)

# uvloop is Linux/macOS only — skip on Windows
if sys.platform != "win32":
  try:
    from uvloop import install
    install()
    logging.info("uvloop installed for event loop optimization.")
  except ImportError:
    logging.warning("uvloop not available — using default event loop.")
else:
  logging.info("Running on Windows — using default asyncio event loop.")

import asyncio
try:
  loop = asyncio.get_event_loop()
except RuntimeError:
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)

colab_bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
