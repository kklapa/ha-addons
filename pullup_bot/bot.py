import os
import discord
from discord.ext import commands, tasks
import sqlite3
from datetime import datetime
import cv2
import mediapipe as mp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GUILD_ID = int(os.environ.get("GUILD_ID", 0))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))



if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== DATABASE ==========
conn = sqlite3.connect("pullup_bot.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    last_submission DATE,
    missed_days INTEGER DEFAULT 0,
    pullups_count INTEGER DEFAULT 0
)
""")
conn.commit()

# ========== MEDIA PIPE ==========
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def count_pullups(video_path):
    cap = cv2.VideoCapture(video_path)
    pullup_count = 0
    stage = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            l_sh = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            r_sh = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            l_el = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
            r_el = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]

            if (l_el.y < l_sh.y) and (r_el.y < r_sh.y):
                if stage == "down" or stage is None:
                    stage = "up"
                    pullup_count += 1
            elif (l_el.y > l_sh.y) and (r_el.y > r_sh.y):
                stage = "down"
    cap.release()
    return pullup_count

# ========== SUBMIT ==========
@bot.command()
async def submit(ctx):
    if not ctx.message.attachments:
        await ctx.send("Прикріпи відео до повідомлення!")
        return
    attachment = ctx.message.attachments[0]
    video_path = f"{VIDEO_FOLDER}/{ctx.author.id}_{datetime.utcnow().date()}.mp4"
    await attachment.save(video_path)

    pullups_detected = count_pullups(video_path)
    today = datetime.utcnow().date()
    c.execute("SELECT last_submission, pullups_count FROM users WHERE user_id=?", (ctx.author.id,))
    result = c.fetchone()

    if result and result[0] == str(today):
        await ctx.send(f"{ctx.author.mention}, ти вже відправляв відео сьогодні!")
        return

    if result:
        c.execute(
            "UPDATE users SET last_submission=?, pullups_count=pullups_count+? WHERE user_id=?",
            (str(today), pullups_detected, ctx.author.id)
        )
    else:
        c.execute(
            "INSERT INTO users (user_id, username, last_submission, pullups_count) VALUES (?, ?, ?, ?)",
            (ctx.author.id, ctx.author.name, str(today), pullups_detected)
        )
    conn.commit()

    if pullups_detected > 0:
        await ctx.send(f"{ctx.author.mention}, зараховано {pullups_detected} підтягувань ✅")
    else:
        await ctx.send(f"{ctx.author.mention}, підтягувань не знайдено ❌")

# ========== REMINDER ==========
@tasks.loop(hours=24)
async def reminder():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(CHANNEL_ID)
    today = datetime.utcnow().date()
    c.execute("SELECT user_id, last_submission, username, missed_days FROM users")
    for user_id, last_submission, username, missed_days in c.fetchall():
        if last_submission != str(today):
            missed_days += 1
            c.execute("UPDATE users SET missed_days=? WHERE user_id=?", (missed_days, user_id))
            member = guild.get_member(user_id)
            if member:
                try:
                    await member.send(f"Привіт {username}! Ти ще не надіслав відео сьогодні!")
                    # Можна змінити нік, якщо пропущено
                    new_nick = f"{member.display_name}_пропуск{missed_days}"
                    await member.edit(nick=new_nick)
                except:
                    pass
    conn.commit()

# ========== LEADERBOARD ==========
@bot.command()
async def leaderboard(ctx):
    c.execute("SELECT username, pullups_count FROM users ORDER BY pullups_count DESC LIMIT 10")
    top = c.fetchall()
    msg = "🏆 **Лідерборд підтягувань** 🏆\n"
    for i, (username, count) in enumerate(top, 1):
        msg += f"{i}. {username} — {count} підтягувань\n"
    await ctx.send(msg)

# ========== START ==========
@bot.event
async def on_ready():
    print(f"Бот запущено як {bot.user}")
    if not reminder.is_running():
        reminder.start()

async def main():
    await bot.start(TOKEN)

import asyncio
asyncio.run(main())

