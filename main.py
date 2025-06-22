import asyncio
import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, time, timedelta
import re
import random
import json

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

TARGET_DATE = datetime.strptime("2026-01-16", "%Y-%m-%d").date()
CHANNEL_ID = 1384899975434993734

today = datetime.now().date()
delta = (TARGET_DATE - today).days

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANSWER_FILE = os.path.join(BASE_DIR, "answer.json")
TIMES_FILE = os.path.join(BASE_DIR, "times.json")

win = False
def generate_number():
    numbers = []
    while len(numbers) < 6:
        digit = random.randint(0, 9)
        if digit not in numbers:
            numbers.append(digit)
    return ''.join(map(str, numbers)) 

def load_answer():
    # 從 answer.json 讀出 answer 字串
    with open(ANSWER_FILE, "r", encoding="utf-8") as f:
        line = f.read().strip()

    if len(line) == 6 and line.isdigit() and len(set(line)) == 6:
        return line
    
    # 不合法就直接重新生成
    ans = generate_number()
    save_answer(ans)
    return ans

def load_times() -> int:
    # 從 times.json 讀出次數
    with open(TIMES_FILE, "r", encoding="utf-8") as f:
        line = f.read().strip()

    if line == "": #如果為空，其值為0
        save_times(0)
        return 0
        
    try:
        t = int(line) #轉成int儲存
    except ValueError:
        print("Not int!")
        t = 0
        save_times(t)
    return t
    
def save_answer(ans: str):
    # 把 answer 寫入 answer.json
    with open(ANSWER_FILE, "w", encoding="utf-8") as f:
        f.write(ans)

def save_times(times: int):
    # 把 times 寫入 times.json
    with open(TIMES_FILE, "w", encoding="utf-8") as f:
        f.write(str(times))

@bot.event
async def on_ready():
    print(f"✅ Bot 上線成功：{bot.user}")
    global answer,win,times
    answer = load_answer()
    times = load_times()
    win = False
    channel = bot.get_channel(CHANNEL_ID)

    if channel:
        print(f"fetch successfully") #watch out this part

    wait_until_0am.start()

@bot.command()
async def status(ctx):
    await ctx.send(f"正常運行中！")

@bot.command()
async def date(ctx):
    today = datetime.now().date()
    delta = (TARGET_DATE - today).days
    await ctx.send(f"學測倒數：還有 {delta} 天")

"""@bot.command()
async def restart(ctx):
    await ctx.send(f"請輸入半形驚嘆號以及 6 位不重複數字，例如 `!685471`")
    global win
    new_ans = generate_number()
    save_answer(new_ans)
    save_times(0)
    win = False""" #可快速重新開始遊戲

@tasks.loop(hours=24)
async def send_countdown():
    today = datetime.now().date()
    delta = (TARGET_DATE - today).days

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

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("找不到指定頻道！")
        return

    if delta > 0:
        new_name = f"學測倒數{delta}天"
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
async def wait_until_0am():
    now = datetime.now()
    target = datetime.combine(now.date(), time(0, 1))
    if now > target:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())
    send_countdown.start()
    await update_channel_name()

@bot.event
async def on_message(message):
    global answer,win,times
    answer = load_answer()
    times = load_times()

    if message.author.bot:
        return

    if not win and re.fullmatch(r'!(\d{6})', message.content):
        guess = message.content[1:]  # 去掉前面的 "!"
        if len(set(guess)) != 6:
            await message.channel.send("請輸入半形驚嘆號以及 6 位不重複數字，例如 `!685471`")
        else:
            A = sum(guess[i] == answer[i] for i in range(6))
            B = sum((guess[i] in answer) and (guess[i] != answer[i]) for i in range(6))
            times = times + 1
            save_times(times)
            await message.channel.send(f"{message.author.mention}，{A}A{B}B")
            if A == 6:
                win = True
                await message.channel.send(f"🎉 恭喜 {message.author.mention} 猜對了，總共嘗試{times}次！")

                #restart
                new_ans = generate_number()
                save_answer(new_ans)
                save_times(0)
                win = False
        return  # 只在猜數字流程時 return
    
    # 如果訊息不是 !六位數，就讓 commands 去處理其他指令
    await bot.process_commands(message)

@bot.command()
async def showans(ctx):
    await ctx.send(f"{answer}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
