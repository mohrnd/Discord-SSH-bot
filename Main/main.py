import discord
from discord.ext import commands, tasks
import asyncio
import paramiko
import socket
import os
import re
from dotenv import load_dotenv
import subprocess
from datetime import datetime, timedelta
import logging

load_dotenv()
botToken = os.getenv('botToken')

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
ssh_sessions = {}

logging.basicConfig(level=logging.INFO)

@client.event
async def on_ready():
    print(f"{client.user.name} is ready!")
    session_cleanup.start()

async def ping_ip(ip):
    param = '-n' if os.name.lower() == 'nt' else '-c'
    try:
        result = subprocess.run(
            ["ping", param, "1", "-w", "500", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
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

async def ssh_start(ctx, hostname, username, password, allowed_users):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname, username=username, password=password, look_for_keys=False, allow_agent=False)
        transport = ssh_client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel.invoke_shell()

        ssh_sessions[ctx.guild.id] = {
            'client': ssh_client,
            'channel': channel,
            'hostname': hostname,
            'username': username,
            'password': password,
            'allowed_users': allowed_users,
            'last_activity': datetime.now()
        }
        await ctx.send(f"SSH connection established to {hostname}.")
        client.loop.create_task(read_ssh_output(ctx.guild.id, ctx.channel, ctx.author))
    except paramiko.AuthenticationException:
        await ctx.send("Authentication failed. Please check your credentials.")
    except paramiko.SSHException as e:
        await ctx.send(f"SSH error: {e}")
    except socket.timeout:
        await ctx.send("Connection timed out.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

async def read_ssh_output(guild_id, channel, command_author):
    session = ssh_sessions.get(guild_id)
    if not session:
        return
    ssh_channel = session['channel']
    
    while True:
        if ssh_channel.recv_ready():
            output = ssh_channel.recv(4096).decode('utf-8')
            output = filter_special_chars(output)
            await send_long_message(channel, output)
            session['last_activity'] = datetime.now()
            if "[sudo] password" in output or "password" in output:
                try:
                    await command_author.send("SSH session requires a password. Please enter it here:")
                    await channel.send(f"Sending a direct message to collect the password.")
                    def check_dm(m):
                        return m.author == command_author and isinstance(m.channel, discord.DMChannel)
                    
                    password_msg = await client.wait_for('message', check=check_dm, timeout=60)
                    password = password_msg.content.strip()
                    ssh_channel.send(password + '\n')
                except asyncio.TimeoutError:
                    await command_author.send("Timed out waiting for the password.")
                except Exception as e:
                    await command_author.send(f"An error occurred while handling the password prompt: {e}")

        await asyncio.sleep(1)

async def send_long_message(channel, message):
    while message:
        part = message[:1500]
        await channel.send(f"```{part}```")
        message = message[1500:]

@client.command()
async def ssh(ctx, hostname: str, username: str):
    try:
        await ctx.reply("Sending a direct message to collect the password.")
        await ctx.author.send("Please enter the password of the machine:")

        def check_dm(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)
        def check_mentions(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.mentions) > 0
        
        msg = await client.wait_for('message', check=check_dm, timeout=60)
        password = msg.content.strip()
        
        await ctx.reply("Please mention the users who can send commands to the machine.")
        mentions_msg = await client.wait_for('message', check=check_mentions, timeout=60)
        mentioned_users = mentions_msg.mentions
        
        allowed_users = [user.id for user in mentioned_users]
        
        await ctx.reply(f"Attempting SSH connection to {hostname}...")
        await ssh_start(ctx, hostname, username, password, allowed_users)
    except asyncio.TimeoutError:
        await ctx.send("Timed out waiting for response.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@client.command()
async def cmd(ctx, *command):
    full_command = ' '.join(command)
    try:
        guild_id = ctx.guild.id
        
        if guild_id not in ssh_sessions:
            await ctx.send("No SSH session established. Please use !ssh command first.")
            return
        
        session = ssh_sessions[guild_id]
        allowed_users = session['allowed_users']
        
        if ctx.author.id not in allowed_users:
            await ctx.send("Sorry, you are not allowed to use this command.")
            return
        
        channel = session['channel']
        channel.send(full_command + '\n')
        await ctx.send(f"Command `{full_command}` sent to {session['hostname']}.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@client.command()
async def CloseSSH(ctx):
    try:
        guild_id = ctx.guild.id
        if guild_id in ssh_sessions:
            ssh_sessions[guild_id]['client'].close()
            del ssh_sessions[guild_id]
            await ctx.send("SSH session closed.")
        else:
            await ctx.send("No SSH session to close.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@client.command()
async def SSHelp(ctx):
    help_message = """
    ```
Available Commands:

1. !ping <hostname>
   - Description: Pings the specified hostname to check whether the IP is up or not.
   - Example: `!ping 192.168.1.100`

2. !ssh <hostname> <username>
   - Description: Opens an SSH session to the specified hostname using the given username.
   - Example: `!ssh 192.168.1.100 myuser`

3. !cmd <command>
   - Description: Executes a command on the SSH-connected machine. Requires an active SSH session.
   - Example: `!cmd ls -l`

4. !CloseSSH
   - Description: Closes the active SSH session. Requires an active SSH session.
   - Example: `!CloseSSH`

5. !StopBot
   - Description: Stops the bot. Restricted to administrators.
   - Example: `!StopBot`
    ```
    """
    await ctx.send(help_message)
    
@client.command()
@commands.has_permissions(administrator=True)
async def StopBot(ctx):
    await ctx.send("Shutting down the bot...")
    await client.close()

@tasks.loop(minutes=1)
async def session_cleanup():
    now = datetime.now()
    inactive_sessions = [guild_id for guild_id, session in ssh_sessions.items() if now - session['last_activity'] > timedelta(minutes=2)]

    for guild_id in inactive_sessions:
        ssh_sessions[guild_id]['client'].close()
        del ssh_sessions[guild_id]
        channel = client.get_guild(guild_id).system_channel
        if channel:
            await channel.send("SSH session closed due to inactivity.")

def filter_special_chars(text):
    filtered_text = re.sub(r'\x1b\[[^a-zA-Z]*[a-zA-Z]', '', text)
    return filtered_text

client.run(botToken)
