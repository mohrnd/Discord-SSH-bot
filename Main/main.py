
import discord
from discord.ext import commands
import subprocess
import asyncio
import os


from dotenv import load_dotenv
load_dotenv()
botToken = str(os.getenv('botToken'))

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@client.event
async def on_ready():
    print(f"{client.user.name} is ready!")

async def ping_ip(ip):
    param = '-n' if os.name.lower() == 'nt' else '-c'
    try:
        result = subprocess.run(
            ["ping", param, "1", "-w", "500", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            print(f'{ip} online')
            return True
        else:
            print(f'{ip} offline')
            print(result.stderr.decode())
            return False
    except Exception as e:
        print(f"Exception occurred: {e}")
        return False

@client.command()
async def ping(ctx, ip: str):
    try:
        if await ping_ip(ip):
            await ctx.reply(f"The IP {ip} is responsive!")
        else:
            await ctx.reply(f"The IP {ip} is not responsive!")
    except Exception as e:
        await ctx.reply(f"An error occurred: {e}")

client.run(botToken)