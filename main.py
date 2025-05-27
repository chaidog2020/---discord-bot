import asyncio
import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, time, timedelta

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

TARGET_DATE = datetime.strptime("2026-01-16", "%Y-%m-%d").date()
CHANNEL_ID = 1365655328351322122 # ← 記得換成你要發送訊息的頻道 ID

today = datetime.now().date()
delta = (TARGET_DATE - today).days

@bot.event
async def on_ready():
    print(f"✅ Bot 上線成功：{bot.user}")
    channel = await bot.fetch_channel(CHANNEL_ID)

    """if channel:
        await channel.send("✅ 測試成功！Bot 可以發訊息了")
        print("✅ 成功發送訊息")
    else:
        print("❌ 找不到頻道，請確認頻道 ID 是否正確，Bot 是否在伺服器內")"""

    wait_until_9am.start()

@bot.command()
async def status(ctx):
    await ctx.send(f"正常運行中！")

@bot.command()
async def date(ctx):
    await ctx.send(f"學測倒數：還有 {delta} 天")

@tasks.loop(hours=24)
async def send_countdown():

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("找不到指定頻道！請確認 CHANNEL_ID 是否正確")
        return

    if delta > 0:
        await channel.send(f"學測倒數：還有 {delta} 天")
    elif delta in [0, -1, -2]:
        await channel.send("今天就是學測 學測就上")
    else:
        await channel.send(f"學測已經過了 {(-delta + 2)} 天")

async def update_channel_name():
    today = datetime.now().date()
    delta = (TARGET_DATE - today).days

    channel = await bot.fetch_channel(CHANNEL_ID)
    if not channel:
        print("找不到指定頻道！")
        return

    if delta > 0:
        new_name = f"學測倒數 {delta} 天"
    elif delta in [0, -1, -2]:
        new_name = "今天學測，大家加油"
    else:
        new_name = f"我是分科戰神🤡"

    try:
        await channel.edit(name=new_name)
        print(f"頻道名稱已更新為：{new_name}")
    except discord.Forbidden:
        print("⚠️ 權限不足，請確認 bot 有管理頻道的權限")
    except discord.HTTPException as e:
        print(f"更新頻道名稱時出錯：{e}")


# 等到晚上00:01開始執行
@tasks.loop(count=1)
async def wait_until_9am():
    now = datetime.now()
    target = datetime.combine(now.date(), time(24, 1))
    if now > target:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())
    send_countdown.start()
    await update_channel_name()

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
