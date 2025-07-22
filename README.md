# Minecraft-Bedrock-Server-Runner-Updater
Automatically detect new version of minecraft bedrock server and update your server without losing server data

## How this works
1. Detects newest version in Minecraft Bedrock Server download page
2. Download .zip file
3. Stop the server and backup server data
4. Extract .zip file
5. Restore your backup server's worlds data and setting data
6. Run updated version of server (in python subprocess.Popen)
7. checks for updates on a 12 hour schedule

## Prerequisite
Python 3.

Works Crossplatform (Windows/Linux) as all things using Python _should_.

Linux:

```sh
./install_packages_linux.sh
```

Windows:

https://www.python.org/downloads/

## How to run
### 1. Run updater
### 1-1) If you want to start new server
Just run updater/mcserver_autoupdater.py script
It automatically downloads server and run subprocess

Linux:
```
python3 ./updater/mcserver_autoupdater.py
```

Windows:
```
py  ./updater/mcserver_autoupdater.py
```

### 1-2) If you want to use your previous server
1. Stop your server
2. Put your previous server files (worlds, server.properties, etc...) to /running directory
3. Run updater
Linux:
```
python3 ./updater/mcserver_autoupdater.py
```

Windows:
```
py  ./updater/mcserver_autoupdater.py
```
### 1-3) If your server already runs in /running directory
Just like in step 2-1) run updater/mcserver_autoupdater.py script
It automatically downloads server, backup your data, install new server and load your previous worlds & server settings
Linux:
```
python3 ./updater/mcserver_autoupdater.py
```

Windows:
```
py  ./updater/mcserver_autoupdater.py
```

### 2. Join your server and play!

### Cron

No need to run Cron, just auto startup, since this runs as a subprocess within the python script.

Linux:

You can register mcserver_autoupdater.py to run at startup
```sh
# In your terminal
crontab -e
```
```sh
# In crontab, add below line
@reboot /usr/bin/python3 /home/ubuntu/Minecraft-Bedrock-Server-Runner-Updater/updater/mcserver_autoupdater.py > /home/ubuntu/Minecraft-Bedrock-Server-Updater/updater/cron.log
```

Windows:

- Set up a Windows Schedule job on startup to run mcserver_autoupdater.py

or

- Just launch:

```cmd
py ./updater/mcserver_autoupdater.py
```

### 3. Console Input

Console Input is relayed to the Minecraft Bedrock server subprocess.

This is the exact same functionality as if you ran the bedrock server executable manually.

#### Helpful Commands

- ##### Stopping the server
Stops the server gracefully

      stop
- ##### help
Displays all available commands, pages starting at 1.

      help [page number]
- ##### say
Sends a message from the server to players in game

      say [message]
      
The rest is available to discover through the help function