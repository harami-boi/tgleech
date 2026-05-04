# copyright 2023 © Xron Trix | https://github.com/Xrontrix10


import os
import shutil
import logging
import pathlib
from asyncio import sleep
from time import time
from colab_leecher import OWNER, colab_bot
from natsort import natsorted
from datetime import datetime
from os import makedirs, path as ospath
from colab_leecher.uploader.telegram import upload_file
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from colab_leecher.utility.variables import (
  BOT,
  MSG,
  BotTimes,
  Messages,
  Paths,
  Transfer,
)
from colab_leecher.utility.converters import (
  archive,
  extract,
  videoConverter,
  sizeChecker,
)
from colab_leecher.utility.helper import (
  fileType,
  getSize,
  getTime,
  keyboard,
  shortFileName,
  sizeUnit,
  sysINFO,
)


async def Leech(folder_path: str, remove: bool):
  global BOT, BotTimes, Messages, Paths, Transfer
  from colab_leecher import DUMP_ID, colab_bot
  
  last_sent_name = None

  files = [str(p) for p in pathlib.Path(folder_path).glob("**/*") if p.is_file()]
  for f in natsorted(files):
    file_path = f # Already absolute path from glob

    # Send the magnet/torrent name to the dump channel when processing a new top-level item
    try:
      rel_path = ospath.relpath(file_path, folder_path)
      current_name = rel_path.split(os.sep)[0].replace("[METADATA]", "").strip()
      
      if current_name and current_name != last_sent_name:
        last_sent_name = current_name
        await colab_bot.send_message(chat_id=DUMP_ID, text=f"<b>{current_name}</b>")
    except Exception as e:
      logging.error(f"Error sending Torrent Name text: {e}")

    # Converting Video Files
    if BOT.Options.convert_video and fileType(file_path) == "video":
      file_path = await videoConverter(file_path)

  Transfer.total_down_size = getSize(folder_path)

  files = [str(p) for p in pathlib.Path(folder_path).glob("**/*") if p.is_file()]
  for f in natsorted(files):
    file_path = f # Already absolute path from glob

    leech = await sizeChecker(file_path, remove)

    if leech: # File was splitted
      if ospath.exists(file_path) and remove:
        os.remove(file_path) # Delete original Big Zip file

      dir_list = natsorted(os.listdir(Paths.temp_zpath))

      count = 1

      for dir_path in dir_list:
        short_path = ospath.join(Paths.temp_zpath, dir_path)
        file_name = ospath.basename(short_path)
        new_path = shortFileName(short_path)
        os.rename(short_path, new_path)
        BotTimes.current_time = time()
        Messages.status_head = f"<b>📤 UPLOADING SPLIT: {count} OF {len(dir_list)} Files</b>\n\n<code>{file_name}</code>\n"
        try:
          MSG.status_msg = await MSG.status_msg.edit_text(
            text=Messages.task_msg
            + Messages.status_head
            + "\n __Starting.....__"
            + sysINFO(),
            reply_markup=keyboard(),
          )
        except Exception as d:
          logging.info(d)
        await upload_file(new_path, file_name)
        Transfer.up_bytes.append(os.stat(new_path).st_size)

        count += 1

      shutil.rmtree(Paths.temp_zpath)

    else:
      if not ospath.exists(Paths.temp_files_dir): # Create Directory
        makedirs(Paths.temp_files_dir)

      if not remove: # Copy To Temp Dir for Renaming Purposes
        file_path = shutil.copy(file_path, Paths.temp_files_dir)
      file_name = ospath.basename(file_path)
      # Trimming filename upto 50 chars
      new_path = shortFileName(file_path)
      os.rename(file_path, new_path)
      BotTimes.current_time = time()
      Messages.status_head = (
        f"<b>📤 UPLOADING: </b>\n\n<code>{file_name}</code>\n"
      )
      try:
        MSG.status_msg = await MSG.status_msg.edit_text(
          text=Messages.task_msg
          + Messages.status_head
          + "\n __Starting.....__"
          + sysINFO(),
          reply_markup=keyboard(),
        )
      except Exception as d:
        logging.error(f"Error updating status bar: {d}")
      file_size = os.stat(new_path).st_size
      await upload_file(new_path, file_name)
      Transfer.up_bytes.append(file_size)

      if remove:
        if ospath.exists(new_path):
          os.remove(new_path)
      else:
        for file in os.listdir(Paths.temp_files_dir):
          os.remove(ospath.join(Paths.temp_files_dir, file))

  if remove and ospath.exists(folder_path):
    shutil.rmtree(folder_path)
  if ospath.exists(Paths.thumbnail_ytdl):
    shutil.rmtree(Paths.thumbnail_ytdl)
  if ospath.exists(Paths.temp_files_dir):
    shutil.rmtree(Paths.temp_files_dir)


async def Zip_Handler(down_path: str, is_split: bool, remove: bool):
  global BOT, Messages, MSG, Transfer

  Messages.status_head = (
    f"<b>🔐 ZIPPING: </b>\n\n<code>{Messages.download_name}</code>\n"
  )

  try:
    MSG.status_msg = await MSG.status_msg.edit_text(
      text=Messages.task_msg + Messages.status_head + sysINFO(),
      reply_markup=keyboard(),
    )
  except Exception as e2:
    logging.error(f"Problem in ZipLeech !{e2}")

  logging.info("\nNow ZIPPING the folder...")
  BotTimes.current_time = time()
  if not ospath.exists(Paths.temp_zpath):
    makedirs(Paths.temp_zpath)
  await archive(down_path, is_split, remove)

  await sleep(2) # Time for renmaing newly created archives

  Transfer.total_down_size = getSize(Paths.temp_zpath)

  if remove and ospath.exists(down_path):
    shutil.rmtree(down_path)


async def Unzip_Handler(down_path: str, remove: bool):
  global MSG, Messages

  Messages.status_head = (
    f"\n<b>📂 EXTRACTING: </b>\n\n<code>{Messages.download_name}</code>\n"
  )

  MSG.status_msg = await MSG.status_msg.edit_text(
    text=Messages.task_msg
    + Messages.status_head
    + "\n __Starting.....__"
    + sysINFO(),
    reply_markup=keyboard(),
  )
  filenames = [str(p) for p in pathlib.Path(down_path).glob("**/*") if p.is_file()]
  for f in natsorted(filenames):
    short_path = ospath.join(down_path, f)
    if not ospath.exists(Paths.temp_unzip_path):
      makedirs(Paths.temp_unzip_path)
    filename = ospath.basename(f).lower()
    _, ext = ospath.splitext(filename)
    try:
      if ospath.exists(short_path):
        if ext in [".7z", ".gz", ".zip", ".rar", ".001", ".tar", ".z01"]:
          await extract(short_path, remove)
        else:
          shutil.copy(short_path, Paths.temp_unzip_path)
    except Exception as e5:
      logging.error(f"UZLeech Launcher Exception: {e5}")

  if remove:
    shutil.rmtree(down_path)


async def cancelTask(Reason: str):
  text = f"Task Stopped\nMode: {BOT.Mode.mode.capitalize()}\nReason: {Reason}\nElapsed: {getTime((datetime.now() - BotTimes.start_time).seconds)}"
  if BOT.State.task_going:
    try:
      BOT.TASK.cancel() # type: ignore
      shutil.rmtree(Paths.WORK_PATH)
    except Exception as e:
      logging.error(f"Error Deleting Task Folder: {e}")
    else:
      logging.info(f"On-Going Task Cancelled !")
    finally:
      BOT.State.task_going = False
      await MSG.status_msg.delete()
      await colab_bot.send_message(
        chat_id=OWNER,
        text=text
      )
      from colab_leecher.utility.task_manager import check_queue
      await check_queue()


async def SendLogs(is_leech: bool):
  global Transfer, Messages

  if is_leech:
    file_count = f"Files: {len(Transfer.sent_file)}\n"
  else:
    file_count = ""

  size = (
    sizeUnit(sum(Transfer.up_bytes))
    if is_leech
    else sizeUnit(Transfer.total_down_size)
  )

  last_text = (
    f"\n\n{(BOT.Mode.mode).upper()} COMPLETE\n"
    + f"Name: {Messages.download_name}\n"
    + f"Size: {size}\n"
    + file_count
    + f"Elapsed: {getTime((datetime.now() - BotTimes.start_time).seconds)}"
  )

  if BOT.State.task_going:
    try:
      await MSG.status_msg.edit_text(text=Messages.task_msg + last_text)
      
      if is_leech:
        final_text = "Files uploaded to dump channel:\n"
        final_texts = []
        for i in range(len(Transfer.sent_file)):
          file_link = (
            f"https://t.me/c/{Messages.link_p}/{Transfer.sent_file[i].id}"
          )
          fileName = Transfer.sent_file_names[i]
          fileText = (
            f"\n({str(i+1).zfill(2)}) <a href={file_link}>{fileName}</a>"
          )
          if len(final_text + fileText) >= 4096:
            final_texts.append(final_text)
            final_text = fileText
          else:
            final_text += fileText
        final_texts.append(final_text)

        for fn_txt in final_texts:
          await colab_bot.send_message(chat_id=OWNER, text=fn_txt, disable_web_page_preview=True)
          
    except Exception as e:
      logging.error(f"Error Sending logs: {e}")

  BOT.State.started = False
  BOT.State.task_going = False
  
  from colab_leecher.utility.task_manager import check_queue
  await check_queue()
