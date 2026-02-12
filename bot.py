import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

# ✅ Safe: read token from environment variable instead of hardcoding
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

CALIFORNIA_TZ = ZoneInfo("America/Los_Angeles")
last_announced_date = None


def get_california_time():
    return datetime.now(CALIFORNIA_TZ)


def get_california_day():
    return get_california_time().strftime("%A")


def time_until_midnight():
    now = get_california_time()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return tomorrow - now


@bot.event
async def on_ready():
    await bot.tree.sync()
    check_midnight.start()
    print(f"Bot is online as {bot.user}")
    print("Today in California is:", get_california_day())


# 🔥 CHANGE ICON COMMAND
@bot.tree.command(name="seticon", description="Change the server icon (day role only)")
async def seticon(interaction: discord.Interaction, image: discord.Attachment):

    current_day = get_california_day()
    role = discord.utils.get(interaction.guild.roles, name=current_day)

    if role is None:
        await interaction.response.send_message(
            f"No role named '{current_day}' found.", ephemeral=True
        )
        return

    if role not in interaction.user.roles:
        await interaction.response.send_message(
            f"You must have the '{current_day}' role to use this command.",
            ephemeral=True
        )
        return

    if not image.content_type.startswith("image"):
        await interaction.response.send_message(
            "File must be an image.", ephemeral=True
        )
        return

    image_bytes = await image.read()

    try:
        await interaction.guild.edit(icon=image_bytes)
        await interaction.response.send_message("Server icon updated successfully.")
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)


# 📅 CURRENT DAY COMMAND
@bot.tree.command(name="currentday", description="Shows current California day")
async def currentday(interaction: discord.Interaction):
    current_day = get_california_day()
    current_time = get_california_time().strftime("%I:%M %p")
    await interaction.response.send_message(
        f"📅 Today in California is **{current_day}**\n🕒 Current time: **{current_time} PST/PDT**"
    )


# ⏳ COUNTDOWN COMMAND
@bot.tree.command(name="countdown", description="Time until next day unlock")
async def countdown(interaction: discord.Interaction):
    remaining = time_until_midnight()

    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    await interaction.response.send_message(
        f"⏳ Time until next unlock:\n"
        f"**{hours}h {minutes}m {seconds}s**"
    )


# 🌅 MIDNIGHT ANNOUNCER
@tasks.loop(minutes=1)
async def check_midnight():
    global last_announced_date

    now = get_california_time()

    if now.hour == 0 and now.minute == 0:
        if last_announced_date != now.date():
            last_announced_date = now.date()
            current_day = get_california_day()

            for guild in bot.guilds:

                channel = guild.system_channel

                if channel is None:
                    for ch in guild.text_channels:
                        if ch.permissions_for(guild.me).send_messages:
                            channel = ch
                            break

                if channel:
                    await channel.send(
                        f"🌅 It is now **{current_day}**.\n"
                        f"The **{current_day}** role may now change the server icon."
                    )


bot.run(TOKEN)
