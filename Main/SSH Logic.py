import discord
from discord.ext import commands
import asyncio
import paramiko
import socket
import os
import re
from dotenv import load_dotenv

load_dotenv()
botToken = os.getenv('botToken')

PASSWORD_PROMPT_PATTERN = re.compile(r'[Pp]assword:?\s*$')

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
ssh_sessions = {}

@client.event
async def on_ready():
    print(f"{client.user.name} is ready!")

async def ssh_start(ctx, hostname, username, password):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname, username=username, password=password, look_for_keys=False, allow_agent=False)
        ssh_sessions[ctx.guild.id] = {
            'client': ssh_client,
            'hostname': hostname,
            'username': username,
            'password': password
        }
        await ctx.send(f"SSH connection established to {hostname}.")
    except paramiko.AuthenticationException:
        await ctx.send("Authentication failed. Please check your credentials.")
    except paramiko.SSHException as e:
        await ctx.send(f"SSH error: {e}")
    except socket.timeout:
        await ctx.send("Connection timed out.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@client.command()
async def ssh(ctx, hostname: str, username: str):
    try:
        await ctx.reply("Sending a direct message to collect the password.")
        await ctx.author.send("Please enter the password of the machine:")

        def check_dm(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

        msg = await client.wait_for('message', check=check_dm, timeout=60)
        password = msg.content.strip()

        await ctx.reply(f"Attempting SSH connection to {hostname}...")
        await ssh_start(ctx, hostname, username, password)
    except asyncio.TimeoutError:
        await ctx.send("Timed out waiting for response.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

async def execute_command(ctx, guild_id, command):
    session = ssh_sessions.get(guild_id)
    if not session:
        await ctx.send("No SSH session established. Please use !ssh command first.")
        return
    
    ssh_client = session['client']
    hostname = session['hostname']
    username = session['username']
    password = session['password']

    try:
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        if output:
            await ctx.send(f"Command output: ```{output}```")
        if error:
            await ctx.send(f"Command error: ```{error}```")

        # Check if sudo or password is requested in output
        if 'sudo' in output.lower() or 'password' in output.lower():
            await ctx.author.send("Please enter the password for sudo command:")

            def check_dm(m):
                return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

            msg = await client.wait_for('message', check=check_dm, timeout=60)
            sudo_password = msg.content.strip()

            stdin.write(sudo_password + '\n')
            stdin.flush()

            # Read output again after sending password
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            if output:
                await ctx.send(f"Command output after sudo: ```{output}```")
            if error:
                await ctx.send(f"Command error after sudo: ```{error}```")

    except asyncio.TimeoutError:
        await ctx.send("Timed out waiting for response.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@client.command()
async def cmd(ctx, *command):
    full_command = ' '.join(command)
    
    try:
        guild_id = ctx.guild.id
        await ctx.reply(f"Attempting SSH command execution on {ssh_sessions[guild_id]['hostname']}...")
        await execute_command(ctx, guild_id, full_command)
    except asyncio.TimeoutError:
        await ctx.send("Timed out waiting for response.")
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
    !ssh <hostname> <username>: Opens an SSH session to the specified hostname with the given username.
    Example: !ssh 192.168.1.100 myuser

    !cmd <command>: Executes a command on the SSH-connected machine. Requires an active SSH session.
    Example: !cmd ls -l

    !CloseSSH: Closes the active SSH session. Requires an active SSH session.
    Example: !CloseSSH

    !StopBot: Stops the bot. Restricted to administrators.
    Example: !StopBot
    ```
    """
    await ctx.send(help_message)
@client.command()
@commands.has_permissions(administrator=True)
async def StopBot(ctx):
    await ctx.send("Shutting down the bot...")
    await client.close()

client.run(botToken)
