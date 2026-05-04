# copyright 2023 © Xron Trix | https://github.com/Xrontrix10


import os
import sys
from time import time
from datetime import datetime
from pyrogram.types import Message


# ─── Dynamic path resolution ────────────────────────────────────────
# variables.py is in colab_leecher/utility/ — go up 2 levels to project root
_THIS_DIR = os.path.dirname(os.path.abspath(__file__)) # colab_leecher/utility
_PACKAGE_DIR = os.path.dirname(_THIS_DIR)        # colab_leecher
PROJECT_ROOT = os.path.dirname(_PACKAGE_DIR)       # project root


class BOT:
  SOURCE = []
  TASK = None
  QUEUE = []
  class Setting:
    stream_upload = "Media"
    convert_video = "Yes"
    convert_quality = "Low"
    caption = "Monospace"
    split_video = "Split Videos"
    prefix = ""
    suffix = ""
    thumbnail = False

  class Options:
    stream_upload = True
    convert_video = True
    convert_quality = False
    is_split = True
    caption = "code"
    video_out = "mp4"
    custom_name = ""
    zip_pswd = ""
    unzip_pswd = ""

  class Mode:
    mode = "leech"
    type = "normal"
    ytdl = False

  class State:
    started = False
    task_going = False
    prefix = False
    suffix = False


class YTDL:
  header = ""
  speed = ""
  percentage = 0.0
  eta = ""
  done = ""
  left = ""


class Transfer:
  down_bytes = [0, 0]
  up_bytes = [0, 0]
  total_down_size = 0
  sent_file = []
  sent_file_names = []

  @classmethod
  def reset(cls):
    cls.down_bytes = [0, 0]
    cls.up_bytes = [0, 0]
    cls.total_down_size = 0
    cls.sent_file = []
    cls.sent_file_names = []


class TaskError:
  state = False
  text = ""


class BotTimes:
  current_time = time()
  start_time = datetime.now()
  task_start = datetime.now()


class Paths:
  WORK_PATH = os.path.join(PROJECT_ROOT, "BOT_WORK")
  THMB_PATH = os.path.join(PROJECT_ROOT, "colab_leecher", "Thumbnail.jpg")
  VIDEO_FRAME = os.path.join(WORK_PATH, "video_frame.jpg")
  HERO_IMAGE = os.path.join(WORK_PATH, "Hero.jpg")
  DEFAULT_HERO = os.path.join(PROJECT_ROOT, "custom_thmb.jpg")
  down_path = os.path.join(WORK_PATH, "Downloads")
  temp_dirleech_path = os.path.join(WORK_PATH, "dir_leech_temp")
  temp_zpath = os.path.join(WORK_PATH, "Leeched_Files")
  temp_unzip_path = os.path.join(WORK_PATH, "Unzipped_Files")
  temp_files_dir = os.path.join(WORK_PATH, "leech_temp")
  thumbnail_ytdl = os.path.join(WORK_PATH, "ytdl_thumbnails")
  access_token = os.path.join(PROJECT_ROOT, "token.pickle")

  # Google Drive mount — only relevant on Linux/Colab
  # On local, user can set GDRIVE_MOUNT_PATH env var
  MOUNTED_DRIVE = os.environ.get("GDRIVE_MOUNT_PATH", os.path.join(PROJECT_ROOT, "drive"))
  mirror_dir = os.path.join(MOUNTED_DRIVE, "MyDrive", "Colab Leecher Uploads")

  # Configurable max upload size (bytes): 2GB default, 4GB for Telegram Premium
  MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", str(2097152000)))


class Messages:
  caution_msg = "\n\n<i>💖 When I'm Doin This, Do Something Else ! <b>Because, Time Is Precious </b></i>"
  download_name = ""
  task_msg = ""
  status_head = f"<b>📥 DOWNLOADING: </b>\n"
  dump_task = ""
  src_link = ""
  link_p = ""


class MSG:
  sent_msg = Message(id=1)
  status_msg = Message(id=2)



class Aria2c:
  link_info = False
  pic_dwn_url = "https://picsum.photos/900/600"


class Gdrive:
  service = None
