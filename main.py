# copyright 2023 © Xron Trix | https://github.com/Xrontrix10
# Modified for local execution support


import os
import sys
import json
import shutil
import subprocess
import logging
from logging.handlers import RotatingFileHandler

if sys.platform == "win32":
  sys.stdout.reconfigure(encoding="utf-8")

# Set up logging with rotating files
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
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

# ─── Resolve project root ───────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

banner = r'''

 ____  ____.______ ._______ .______    _____._.______ .___ ____  ____
 \  \_/  /: __  \: .___ \:   \   \__ _:|: __  \: __| \  \_/  /
 \___ ___/ | \____||:  | ||    |    |:|| \____||: | \___ ___/ 
 /  _  \ | : \ |  : ||  |  |    |  || : \ |  | /  _  \ 
 /___/ \___\|  |___\ \_. ___/ |___|  |    |  ||  |___\|  | /___/ \___\
      |___|   :/     |___|    |___||___|  |___|      
           :                           
                                       
 
     _____     _   __         __       
    / ___/__ ____| | __ / /  ___ ___ ____/ / ___ ____  
    / /__/ _ \/ __/| |/ // /  / -_)/ -_)/ __/ _ \/ -_)/ __/ 
    \___/\___/\__/ |___//__/__ \__/ \__/ \__/_//_/\__/ /_/   
             /_____/ [Local Mode]          

'''

print(banner)


def check_external_tools():
  """Auto-detect required external tools and warn about missing ones."""
  tools = {
    "aria2c": {"required": True, "purpose": "Direct link downloads"},
    "ffmpeg": {"required": True, "purpose": "Video conversion & splitting"},
    "ffprobe": {"required": True, "purpose": "Video metadata extraction"},
    "7z": {"required": False, "purpose": "Archive operations (password-protected)"},
  }

  # On Windows, also check common install locations and a local bin folder
  extra_paths = []
  local_bin = os.path.join(PROJECT_ROOT, "bin")
  
  if sys.platform == "win32":
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    extra_paths = [
      local_bin,
      os.path.join(program_files, "aria2"),
      os.path.join(program_files, "7-Zip"),
      os.path.join(program_files_x86, "7-Zip"),
      os.path.join(program_files, "ffmpeg", "bin"),
    ]
    
    # Add local bin to PATH for subprocesses
    if os.path.exists(local_bin):
      os.environ["PATH"] = local_bin + os.pathsep + os.environ.get("PATH", "")

  missing_required = []
  missing_optional = []

  for tool, info in tools.items():
    found = shutil.which(tool)
    if not found:
      # Check extra paths on Windows
      for p in extra_paths:
        exe = tool + (".exe" if sys.platform == "win32" else "")
        candidate = os.path.join(p, exe)
        if os.path.isfile(candidate):
          found = candidate
          break

    if found:
      logging.info(f" [OK] {tool}: {found}")
    elif info["required"]:
      missing_required.append(f" [MISSING] {tool} — {info['purpose']}")
    else:
      missing_optional.append(f" [WARN] {tool} (optional) — {info['purpose']}")

  for msg in missing_optional:
    logging.warning(msg)

  if missing_required:
    logging.error("Missing REQUIRED tools:")
    for msg in missing_required:
      logging.error(msg)
    logging.error(
      "\nPlease install them and ensure they are in your system PATH.\n"
      "Alternatively, create a 'bin' folder in this project directory and drop the .exe files there."
    )
    if sys.platform == "win32":
      logging.error(
        " aria2c: https://github.com/aria2/aria2/releases\n"
        " ffmpeg: https://www.gyan.dev/ffmpeg/builds/\n"
        " 7z:   https://www.7-zip.org/download.html"
      )
    else:
      logging.error(" Try: sudo apt install aria2 ffmpeg p7zip-full")
    sys.exit(1)


def load_credentials():
  """Load credentials from .env file or environment variables."""
  env_path = os.path.join(PROJECT_ROOT, ".env")
  creds_path = os.path.join(PROJECT_ROOT, "credentials.json")

  # Try loading from .env file first
  if os.path.exists(env_path):
    logging.info("Loading credentials from .env file...")
    env_vars = {}
    with open(env_path, "r", encoding="utf-8") as f:
      for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
          key, _, value = line.partition("=")
          env_vars[key.strip()] = value.strip()
    
    api_id = int(env_vars.get("API_ID", "0"))
    api_hash = env_vars.get("API_HASH", "")
    bot_token = env_vars.get("BOT_TOKEN", "")
    user_id = int(env_vars.get("USER_ID", "0"))
    dump_id = int(env_vars.get("DUMP_ID", "0"))

  # Fallback to environment variables
  elif os.environ.get("API_ID"):
    logging.info("Loading credentials from environment variables...")
    api_id = int(os.environ.get("API_ID", "0"))
    api_hash = os.environ.get("API_HASH", "")
    bot_token = os.environ.get("BOT_TOKEN", "")
    user_id = int(os.environ.get("USER_ID", "0"))
    dump_id = int(os.environ.get("DUMP_ID", "0"))

  # Fallback to existing credentials.json
  elif os.path.exists(creds_path):
    logging.info("Loading credentials from credentials.json...")
    with open(creds_path, "r", encoding="utf-8") as f:
      data = json.load(f)
    api_id = data.get("API_ID", 0)
    api_hash = data.get("API_HASH", "")
    bot_token = data.get("BOT_TOKEN", "")
    user_id = data.get("USER_ID", 0)
    dump_id = data.get("DUMP_ID", 0)

  else:
    logging.error(
      "No credentials found!\n"
      " Option 1: Copy .env.example to .env and fill in your values\n"
      " Option 2: Set environment variables (API_ID, API_HASH, BOT_TOKEN, USER_ID, DUMP_ID)\n"
      " Option 3: Create credentials.json in the project root"
    )
    sys.exit(1)

  # Validate
  if not api_id or not api_hash or not bot_token or not user_id:
    logging.error("Incomplete credentials! Please fill in all required fields (API_ID, API_HASH, BOT_TOKEN, USER_ID)")
    sys.exit(1)

  # Fix DUMP_ID format
  if len(str(dump_id)) == 10 and "-100" not in str(dump_id):
    dump_id = int("-100" + str(dump_id))

  credentials = {
    "API_ID": api_id,
    "API_HASH": api_hash,
    "BOT_TOKEN": bot_token,
    "USER_ID": user_id,
    "DUMP_ID": dump_id,
  }

  # Write credentials.json for the bot module to read
  with open(creds_path, "w", encoding="utf-8") as f:
    json.dump(credentials, f)

  logging.info("Credentials loaded successfully.")
  return credentials


def main():
  logging.info("Checking external tools...")
  check_external_tools()

  logging.info("Loading credentials...")
  load_credentials()

  # Remove old bot session to avoid conflicts
  session_path = os.path.join(PROJECT_ROOT, "my_bot.session")
  if os.path.exists(session_path):
    os.remove(session_path)
    logging.info("Removed old bot session.")

  logging.info("Starting Bot....")
  
  # Run the bot module
  result = subprocess.run(
    [sys.executable, "-m", "colab_leecher"],
    cwd=PROJECT_ROOT,
  )
  sys.exit(result.returncode)


if __name__ == "__main__":
  main()
