
# Zoroverse Direct Link Uploader Bot
# Powerful Telegram bot to upload files from direct links to Telegram chats

import os
import asyncio
import logging
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
LOG_CHANNEL = os.getenv("LOG_CHANNEL")
FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 2_000_000_000))  # 2GB default

if not BOT_TOKEN or not API_ID or not API_HASH:
    raise ValueError("Missing required environment variables: BOT_TOKEN, API_ID, or API_HASH")

# Pyrogram Client
bot = Client("ZoroverseUploaderBot",
             bot_token=BOT_TOKEN,
             api_id=API_ID,
             api_hash=API_HASH)


@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        f"👋 Hello {message.from_user.first_name}!\n\n"
        f"I'm ZoroverseX Link Uploader Bot.\n"
        f"Send me any direct download link and I'll upload it to Telegram!",
        quote=True
    )


@bot.on_message(filters.text & filters.private & (~filters.command([])))
async def handle_links(client: Client, message: Message):
 async def handle_direct_link(client: Client, message: Message):
    url = message.text.strip()

    if not url.startswith("http"):
        return await message.reply_text("❌ Invalid URL. Please send a direct download link.")

    msg = await message.reply("🔄 Downloading the file...")
    filename = url.split("/")[-1].split("?")[0] or "file.bin"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=120) as resp:
                file_size = int(resp.headers.get("Content-Length", 0))

                if file_size == 0:
                    return await msg.edit("❌ Could not determine file size or empty file.")

                if file_size > MAX_FILE_SIZE:
                    return await msg.edit("⚠️ File is too large to upload to Telegram.")

                with open(filename, "wb") as f:
                    while True:
                        chunk = await resp.content.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

        await client.send_document(
            chat_id=message.chat.id,
            document=filename,
            caption=f"✅ Uploaded by @ZoroverseBot",
        )
        await msg.delete()

        os.remove(filename)

        if LOG_CHANNEL:
            await client.send_message(LOG_CHANNEL, f"📤 File uploaded: {filename} by {message.from_user.mention}")

    except asyncio.TimeoutError:
        await msg.edit("⏱️ Download timed out. Please try again with a faster link.")
    except aiohttp.ClientError as e:
        logger.error(f"Client error: {e}")
        await msg.edit("❌ Failed to fetch file. Link may be invalid or server refused connection.")
    except Exception as e:
        logger.exception("Unexpected error")
        await msg.edit("❌ An unexpected error occurred. Please try again later.")


if __name__ == "__main__":
    bot.run()
