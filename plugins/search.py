import asyncio
from info import *
from utils import *
from time import time
from client import User
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Set a limit on the number of messages to forward at once
FORWARD_LIMIT = 10

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    f_sub = await force_sub(bot, message)
    if f_sub == False:
        return
    
    channels = (await get_group(message.chat.id))["channels"]
    if not channels:
        return

    if message.text.startswith("/"):
        return

    query = message.text.strip().lower()  # Convert the query to lowercase for case-insensitive comparison
    forward_count = 0  # Counter to limit the number of forwards

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                # Check for exact match
                message_text = (msg.text or msg.caption).strip().lower()  # Ensure text is lowercase and stripped
                if query == message_text:
                    if forward_count < FORWARD_LIMIT:  # Check the limit before forwarding
                        await msg.forward(message.chat.id)
                        forward_count += 1
                    else:
                        break

        if forward_count == 0:
            await message.reply_text("No exact match found for your query.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    await update.message.edit("Searching..💥")
    id = update.data.split("_")[-1]
    query = await search_imdb(id)
    channels = (await get_group(update.message.chat.id))["channels"]
    forward_count = 0

    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                # Check for exact match
                message_text = (msg.text or msg.caption).strip().lower()
                if query == message_text:
                    if forward_count < FORWARD_LIMIT:  # Check the limit before forwarding
                        await msg.forward(update.message.chat.id)
                        forward_count += 1
                    else:
                        break

        if forward_count == 0:
            await update.message.edit("Still no exact match found!")
    except Exception as e:
        await update.message.edit(f"❌ Error: {e}")

@Client.on_callback_query(filters.regex(r"^request"))
async def request(bot, update):
    clicked = update.from_user.id
    try:
        typed = update.message.reply_to_message.from_user.id
    except:
        return await update.message.delete()

    if clicked != typed:
        return await update.answer("That's not for you! 👀", show_alert=True)

    admin = (await get_group(update.message.chat.id))["user_id"]
    id = update.data.split("_")[1]
    name = await search_imdb(id)
    url = "https://www.imdb.com/title/tt" + id
    text = f"#RequestFromYourGroup\n\nName: {name}\nIMDb: {url}"
    await bot.send_message(chat_id=admin, text=text, disable_web_page_preview=True)
    await update.answer("✅ Request Sent To Admin", show_alert=True)
    await update.message.delete(60)
