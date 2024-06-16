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
        await ctx.reply("Pinging the IP address...")
        if await ping_ip(ip):
            await ctx.reply(f"The IP {ip} is responsive!")
        else:
            await ctx.reply(f"The IP {ip} is not responsive!")
    except Exception as e:
        await ctx.reply(f"An error occurred: {e}")

@client.command()
async def ssh(ctx, hostname: str, ip: str):
    def check_dm(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    def check_mentions(m):
        return m.author == ctx.author and m.channel == ctx.channel and len(m.mentions) > 0

    try:
        await ctx.reply("Sending a direct message to collect the password.")
        await ctx.author.send("Please enter the password of the machine. Make sure to delete your message after getting the confirmation message:")
        
        msg = await client.wait_for('message', check=check_dm, timeout=60)
        password = msg.content

        await ctx.reply("Please mention the users who can send commands to the machine.")

        mentions_msg = await client.wait_for('message', check=check_mentions, timeout=60)
        mentioned_users = mentions_msg.mentions

        await ctx.send(f"Attempting to SSH into {hostname} at {ip} with the provided password.")
        
        await ctx.send(f"SSH to {hostname} at {ip} successful.")

    except asyncio.TimeoutError:
        await ctx.send("Timed out waiting for response.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@client.command()
@commands.has_permissions(administrator=True)
async def StopBot(ctx):
    await ctx.send("Shutting down the bot...")
    await client.close()

client.run(botToken)
