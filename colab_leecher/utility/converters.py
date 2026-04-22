# copyright 2023 © Xron Trix | https://github.com/Xrontrix10


import os
import json
import shutil
import logging
import subprocess
import sys
import asyncio
from asyncio import sleep, create_subprocess_shell, create_subprocess_exec
from asyncio.subprocess import PIPE
from threading import Thread
from datetime import datetime
from os import makedirs, path as ospath
try:
  from moviepy.editor import VideoFileClip as VideoClip # moviepy v1
except ImportError:
  from moviepy import VideoFileClip as VideoClip # moviepy v2
from colab_leecher.utility.variables import BOT, MSG, BotTimes, Paths, Messages
from colab_leecher.utility.helper import (
  getSize,
  fileType,
  keyboard,
  multipartArchive,
  sizeUnit,
  speedETA,
  status_bar,
  sysINFO,
  getTime,
)

# ─── GPU detection (optional) ───────────────────────────────────────
try:
  import GPUtil
  HAS_GPU = len(GPUtil.getAvailable()) > 0
except (ImportError, Exception):
  HAS_GPU = False


def _find_7z():
  """Find 7z executable cross-platform."""
  found = shutil.which("7z")
  if found:
    return found
  # Check common Windows install paths
  if sys.platform == "win32":
    for path in [
      os.path.join(os.environ.get("ProgramFiles", ""), "7-Zip", "7z.exe"),
      os.path.join(os.environ.get("ProgramFiles(x86)", ""), "7-Zip", "7z.exe"),
    ]:
      if os.path.isfile(path):
        return f'"{path}"'
  return "7z" # fallback, hope it's in PATH


def _find_zip():
  """Check if zip/unzip commands are available (Linux/macOS)."""
  return shutil.which("zip") is not None


SEVENZ_PATH = _find_7z()
HAS_ZIP_CMD = _find_zip()


async def videoConverter(file: str):
  global BOT, MSG, BotTimes

  def convert_to_mp4(input_file, out_file):
    clip = VideoClip(input_file)
    clip.write_videofile(
      out_file,
      codec="libx264",
      audio_codec="aac",
      ffmpeg_params=["-strict", "-2"],
    )

  async def msg_updater(c: int, tr, engine: str):
    global Messages
    messg = f"「" + "░" * c + "█" + "░" * (11 - c) + "」"
    messg += f"\n **Status:** __Running 🏃🏼__\n🕹 **Attempt:** __{tr}__"
    messg += f"\n **Engine:** __{engine}__\n💪🏼 **Handler:** __{core}__"
    messg += f"\n🍃 **Time Spent:** __{getTime((datetime.now() - BotTimes.start_time).seconds)}__"
    try:
      await MSG.status_msg.edit_text(
        text=Messages.task_msg + mtext + messg + sysINFO(),
        reply_markup=keyboard(),
      )
    except Exception:
      pass

  name, ext = ospath.splitext(file)

  if ext.lower() in [".mkv", ".mp4"]:
    return file # Return if It's already mp4 / mkv file

  c, out_file, Err = 0, f"{name}.{BOT.Options.video_out}", False

  quality = "-preset slow -qp 0" if BOT.Options.convert_quality else ""

  if HAS_GPU:
    cmd = f"ffmpeg -y -i \"{file}\" {quality} -c:v h264_nvenc -c:a copy \"{out_file}\""
    core = "GPU"
  else:
    cmd = f"ffmpeg -y -i \"{file}\" {quality} -c:v libx264 -c:a copy \"{out_file}\""
    core = "CPU"

  mtext = f"<b>🎥 Converting Video:</b>\n\n{ospath.basename(file)}\n\n"

  proc = await create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)

  while proc.returncode is None:
    await msg_updater(c, "1st", "FFmpeg 🏍")
    c = (c + 1) % 12
    await sleep(3)
    # Check if process has completed
    try:
      await asyncio.wait_for(proc.wait(), timeout=0.1)
    except asyncio.TimeoutError:
      pass

  await proc.wait()

  if ospath.exists(out_file) and getSize(out_file) == 0:
    os.remove(out_file)
    Err = True
  elif not ospath.exists(out_file):
    Err = True

  if Err:
    proc_thread = Thread(target=convert_to_mp4, name="Moviepy", args=(file, out_file))
    proc_thread.start()
    core = "CPU"
    while proc_thread.is_alive(): # Until conversion finishes
      await msg_updater(c, "2nd", "Moviepy 🛵")
      c = (c + 1) % 12
      await sleep(3)

  if ospath.exists(out_file) and getSize(out_file) == 0:
    os.remove(out_file)
    Err = True
  elif not ospath.exists(out_file):
    Err = True
  else:
    Err = False

  if Err:
    logging.error("This Video Can't Be Converted !")
    return file
  else:
    os.remove(file)
    return out_file


async def sizeChecker(file_path, remove: bool):
  global Paths
  max_size = Paths.MAX_UPLOAD_SIZE
  file_size = os.stat(file_path).st_size

  if file_size > max_size:
    if not ospath.exists(Paths.temp_zpath):
      makedirs(Paths.temp_zpath)
    _, filename = ospath.split(file_path)
    filename = filename.lower()
    if (
      filename.endswith(".zip")
      or filename.endswith(".rar")
      or filename.endswith(".7z")
      or filename.endswith(".tar")
      or filename.endswith(".gz")
    ):
      await splitArchive(file_path, max_size)
    else:
      f_type = fileType(file_path)
      if f_type == "video" and BOT.Options.is_split:
        await splitVideo(file_path, max_size // (1024 * 1024), remove)
      else:
        await archive(file_path, True, remove)
      await sleep(2)
    return True
  else:
    return False


async def archive(path, is_split, remove: bool):
  global BOT, Messages
  dir_p, p_name = ospath.split(path)
  
  if is_split:
    split_size = Paths.MAX_UPLOAD_SIZE // (1024 * 1024) # Convert to MB
  else:
    split_size = 0

  if len(BOT.Options.custom_name) != 0:
    name = BOT.Options.custom_name
  elif ospath.isfile(path):
    name = ospath.basename(path)
  else:
    name = Messages.download_name
  Messages.status_head = f"<b>🔐 ZIPPING: </b>\n\n<code>{name}</code>\n"
  Messages.download_name = f"{name}.zip"
  BotTimes.task_start = datetime.now()

  out_path = os.path.join(Paths.temp_zpath, f"{name}.zip")

  if len(BOT.Options.zip_pswd) != 0:
    # Password-protected zip — use 7z
    split_arg = f"-v{split_size}m" if split_size else ""
    cmd = f'{SEVENZ_PATH} a -mx=0 -tzip -p{BOT.Options.zip_pswd} {split_arg} "{out_path}" "{path}"'
  elif HAS_ZIP_CMD and sys.platform != "win32":
    # Linux/macOS: use native zip
    r = "-r" if ospath.isdir(path) else ""
    split_arg = f"-s {split_size}m" if split_size else ""
    cmd = f'cd "{dir_p}" && zip {r} {split_arg} -0 "{out_path}" "{p_name}"'
  else:
    # Windows or no zip cmd: use 7z
    r_flag = "-r" if ospath.isdir(path) else ""
    split_arg = f"-v{split_size}m" if split_size else ""
    cmd = f'{SEVENZ_PATH} a -mx=0 -tzip {split_arg} {r_flag} "{out_path}" "{path}"'

  proc = await create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)
  total_size = getSize(path)
  total_in_unit = sizeUnit(total_size)
  while proc.returncode is None:
    speed_string, eta, percentage = speedETA(
      BotTimes.task_start, getSize(Paths.temp_zpath), total_size
    )
    await status_bar(
      Messages.status_head,
      speed_string,
      percentage,
      getTime(eta),
      sizeUnit(getSize(Paths.temp_zpath)),
      total_in_unit,
      "Xr-Zipp 🔒",
    )
    await sleep(1)
    try:
      await asyncio.wait_for(proc.wait(), timeout=0.1)
    except asyncio.TimeoutError:
      pass

  await proc.wait()

  if remove:
    if ospath.isfile(path):
      os.remove(path)
    else:
      shutil.rmtree(path)


async def extract(zip_filepath, remove: bool):
  global BOT, Paths, Messages
  _, filename = ospath.split(zip_filepath)
  Messages.status_head = f"<b>📂 EXTRACTING:</b>\n\n<code>{filename}</code>\n"
  p = f"-p{BOT.Options.unzip_pswd}" if len(BOT.Options.unzip_pswd) != 0 else ""
  name, ext = ospath.splitext(filename)
  file_pattern, real_name, temp_unzip_path, total_ = (
    "",
    name,
    Paths.temp_unzip_path,
    0,
  )

  if ext == ".rar":
    unrar_path = shutil.which("unrar")
    if unrar_path:
      if "part" in name:
        cmd = f'unrar x -kb -idq {p} "{zip_filepath}" "{temp_unzip_path}"'
        file_pattern = "rar"
      else:
        cmd = f'unrar x {p} "{zip_filepath}" "{temp_unzip_path}"'
    else:
      # Fallback to 7z for rar files
      if "part" in name:
        file_pattern = "rar"
      cmd = f'{SEVENZ_PATH} x {p} "{zip_filepath}" -o"{temp_unzip_path}"'

  elif ext == ".tar":
    if shutil.which("tar"):
      cmd = f'tar -xvf "{zip_filepath}" -C "{temp_unzip_path}"'
    else:
      cmd = f'{SEVENZ_PATH} x "{zip_filepath}" -o"{temp_unzip_path}"'
  elif ext == ".gz":
    if shutil.which("tar"):
      cmd = f'tar -zxvf "{zip_filepath}" -C "{temp_unzip_path}"'
    else:
      cmd = f'{SEVENZ_PATH} x "{zip_filepath}" -o"{temp_unzip_path}"'
  else:
    cmd = f'{SEVENZ_PATH} x {p} "{zip_filepath}" -o"{temp_unzip_path}"'
    if ext == ".001":
      file_pattern = "7z"
    elif ext == ".z01":
      file_pattern = "zip"

  if file_pattern == "":
    total_ = getSize(zip_filepath)
    total = sizeUnit(total_)
  else:
    real_name, total_ = multipartArchive(zip_filepath, file_pattern, False)
    total = sizeUnit(total_)

  BotTimes.task_start = datetime.now()

  proc = await create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)

  while proc.returncode is None:
    speed_string, eta, percentage = speedETA(
      BotTimes.task_start,
      getSize(temp_unzip_path),
      total_,
    )
    await status_bar(
      Messages.status_head,
      speed_string,
      percentage,
      getTime(eta),
      sizeUnit(getSize(temp_unzip_path)),
      total,
      "Xr-Unzip 🔓",
    )
    await sleep(1)
    try:
      await asyncio.wait_for(proc.wait(), timeout=0.1)
    except asyncio.TimeoutError:
      pass

  await proc.wait()

  if remove:
    multipartArchive(zip_filepath, file_pattern, True)

    if ospath.exists(zip_filepath):
      os.remove(zip_filepath)

  Messages.download_name = real_name


async def splitArchive(file_path, max_size):
  global Paths, BOT, MSG, Messages
  _, filename = ospath.split(file_path)
  new_path = os.path.join(Paths.temp_zpath, filename)
  Messages.status_head = f"<b> SPLITTING: </b>\n\n<code>{filename}</code>\n"
  # Get the total size of the file
  total_size = ospath.getsize(file_path)

  BotTimes.task_start = datetime.now()

  # Use buffered reads instead of loading max_size (2GB) into memory
  BUFFER_SIZE = 8 * 1024 * 1024 # 8MB buffer

  with open(file_path, "rb") as f:
    i = 1
    bytes_written = 0
    while True:
      # Generate filename for this chunk
      ext = str(i).zfill(3)
      output_filename = "{}.{}".format(new_path, ext)

      chunk_written = 0
      with open(output_filename, "wb") as out:
        while chunk_written < max_size:
          read_size = min(BUFFER_SIZE, max_size - chunk_written)
          data = f.read(read_size)
          if not data:
            break
          out.write(data)
          chunk_written += len(data)

      if chunk_written == 0:
        # No data was written, remove the empty file
        os.remove(output_filename)
        break

      bytes_written += chunk_written
      speed_string, eta, percentage = speedETA(
        BotTimes.task_start, bytes_written, total_size
      )
      await status_bar(
        Messages.status_head,
        speed_string,
        percentage,
        getTime(eta),
        sizeUnit(bytes_written),
        sizeUnit(total_size),
        "Xr-Split ",
      )

      if not f.read(1): # Check if we've reached EOF
        break
      f.seek(-1, 1) # Seek back the 1 byte we just read

      i += 1 # Increment chunk counter


async def splitVideo(file_path, max_size, remove: bool):
  global Paths, BOT, MSG, Messages
  _, filename = ospath.split(file_path)
  just_name, extension = ospath.splitext(filename)

  if not ospath.exists(Paths.temp_zpath):
    makedirs(Paths.temp_zpath)

  # FFmpeg command to get video information in JSON format
  cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path]

  bitrate = None
  try:
    # Run the command and get output
    output = subprocess.check_output(cmd)
    video_info = json.loads(output)
    # Get bitrate in bits per second
    bitrate = float(video_info["format"]["bit_rate"])
  except subprocess.CalledProcessError:
    logging.error("Error: Could not get video bitrate")
    bitrate = 1000

  # Convert target size from MB to bits
  target_size_bits = max_size * 8 * 1024 * 1024

  # Calculate duration in seconds
  duration = int(target_size_bits / bitrate)

  out_pattern = os.path.join(Paths.temp_zpath, f"{just_name}.part%03d{extension}")
  cmd = f'ffmpeg -i "{file_path}" -c copy -f segment -segment_time {duration} -reset_timestamps 1 "{out_pattern}"'

  Messages.status_head = f"<b> SPLITTING: </b>\n\n<code>{filename}</code>\n"
  BotTimes.task_start = datetime.now()

  proc = await create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)
  total_size = getSize(file_path)
  total_in_unit = sizeUnit(total_size)
  while proc.returncode is None:
    speed_string, eta, percentage = speedETA(
      BotTimes.task_start, getSize(Paths.temp_zpath), total_size
    )
    await status_bar(
      Messages.status_head,
      speed_string,
      percentage,
      getTime(eta),
      sizeUnit(getSize(Paths.temp_zpath)),
      total_in_unit,
      "Xr-Split ",
    )
    await sleep(1)
    try:
      await asyncio.wait_for(proc.wait(), timeout=0.1)
    except asyncio.TimeoutError:
      pass

  await proc.wait()

  if remove:
    os.remove(file_path)
