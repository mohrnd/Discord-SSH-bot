# Simple Discord SSH Bot

This Discord bot enables users to interact with SSH sessions and perform various commands remotely on specified machines via Discord messages.

## Features
- **Ping Command**: Check the availability of an IP address.
- **SSH Command**: Establish an SSH connection to a specified hostname using a given username and password.
- **Command Execution (`!cmd`)**: Execute commands on the SSH-connected machine.
- **Session Management**: Automatically closes inactive SSH sessions after 2 minutes of inactivity.
- **Error Handling**: Handles authentication failures, SSH errors, timeouts, and other exceptions gracefully.
- **Bot Management**: Includes commands to stop the bot and provide help (`!SSHelp`).

## Setup
1. **Environment Setup**: Ensure Python 3.7+ is installed. Install required dependencies using:
   ```
   pip install -r requirements.txt
   ```
2. **Bot Token**: Create a `.env` file and add your Discord bot token:
   ```
   botToken=your_discord_bot_token_here
   ```
3. **Run the Bot**: Execute the bot script:
   ```
   python bot.py
   ```

## Commands
- `!ping <hostname>`: Pings the specified hostname to check its availability.
  ```
  !ping 192.168.1.100
  ```

- `!ssh <hostname> <username>`: Initiates an SSH session to the specified hostname using the provided username. The bot will prompt for a password and mention users who can send commands.
  ```
  !ssh 192.168.1.100 myuser
  ```

- `!cmd <command>`: Executes a command on the currently active SSH session. Requires an established SSH connection.
  ```
  !cmd ls -l
  ```

- `!CloseSSH`: Closes the active SSH session.
  ```
  !CloseSSH
  ```

- `!SSHelp`: Displays available commands and their descriptions.
  ```
  !SSHelp
  ```

- `!StopBot`: Stops the bot. Only accessible to administrators.
  ```
  !StopBot
  ```

## Notes
- Ensure your Discord bot has the necessary permissions and is invited to the server where you intend to use it.
- For security reasons, ensure sensitive information like passwords and bot tokens are handled securely.
- This bot assumes users have basic knowledge of SSH and Discord commands.

---
