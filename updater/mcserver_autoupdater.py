# Automatically compare installed version of Minecrafter server to latest version
import requests
import subprocess
import os
import sys
import datetime
import requests
import platform
import re
import shutil
import glob
import zipfile
import time
import threading

def print_log(msg):
    global logfile
    with open(logfile, "a") as file:
        timenow = "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "]: "
        
        msg = timenow + msg

        print(msg)
        file.write(msg + "\n")

def start_server(exe_path):
    # Start the Minecraft server
    try:
        server = subprocess.Popen([exe_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1000)
        print_log("Server started successfully.")
        return server
    except Exception as e:
        print_log("Error starting server: " + str(e))
        return None

def try_stop_server(subprocess):
    # Stop the Minecraft server safely if it's running
    if subprocess is None:
        print_log("No server process to stop.")
        return

    try:
        # Later
        print("stop\n", file=subprocess.stdin)
        subprocess.stdin.flush()
        subprocess.wait(timeout=10)

    except Exception as e:
        print_log("Error stopping server: " + str(e))

def send_server_message(message):
    # Send a message to the Minecraft server console
    if running_server is not None:
        # split message into multiple lines split by \n
        message_lines = message.rstrip().split("\n")

        for line in message_lines:
            print("say " + line, file=running_server.stdin)

        running_server.stdin.flush()
        print_log("Sent message to server: " + message)
    else:
        print_log("No running server to send message to.")

def migrate_server(minecraft_directory):
    # Migrate current server to newest version (preserves server settings & world data)
    minecraft_directory = os.path.abspath(minecraft_directory)

    # Paths
    backup_dir = os.path.join(minecraft_directory, "backup")
    running_dir = os.path.join(minecraft_directory, "running")
    updater_dir = os.path.join(minecraft_directory, "updater")

    print_log("Erasing old backup...")
    # Remove backup folder
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    print_log("Backup erased")

    print_log("Creating new backup...")
    # Move running to backup
    if os.path.exists(running_dir):
        shutil.move(running_dir, backup_dir)
    print_log("Created new backup")

    # Create new running directory
    os.makedirs(running_dir, exist_ok=True)

    print_log("Unzipping new server...")
    # Unzip new server (bedrock-server*.zip)
    for zip_file in glob.glob(os.path.join(updater_dir, "bedrock-server*")):
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(running_dir)
        os.remove(zip_file)
    print_log("New server unzipped")

    print_log("Copying Worlds...")
    # Copy worlds
    src_worlds = os.path.join(backup_dir, "worlds")
    dst_worlds = os.path.join(running_dir, "worlds")
    if os.path.exists(src_worlds):
        shutil.copytree(src_worlds, dst_worlds, dirs_exist_ok=True)
    print_log("World migrated")

    # Copy server settings
    files_to_copy = [
        "allowlist.json",
        "permissions.json",
        "profanity_filter.wlist",
        "server.properties"
    ]

    print_log("Copying server settings...")
    for f in files_to_copy:
        src = os.path.join(backup_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, running_dir)
    print_log("Server setting migrated")

running_server = None
minecraft_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logfile = os.path.join(minecraft_directory , "updater", "update.log")

server_update_check_time = 43200  # check every 12 hours (43200 seconds) if the server is up to date
server_update_buffer_time = 60 * 5  # 5 minutes buffer time to update server

server_update_message = "Server will shut down in " + str(server_update_buffer_time // 60) + " minutes for update.\n" + \
    "Please save your progress and exit the game.\n" + \
    "The server will be restarted automatically after the update.\n" + \
    "Thank you for your patience!\n"
server_one_min_warning_message = "Server will shut down in 1 minute for update.\n" + \
    "Please save your progress and exit the game.\n" + \
    "The server will be restarted automatically after the update.\n" + \
    "Thank you for your patience!\n"

HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"
    }

def get_download_link():
    global HEADERS

    system_name = platform.system()
    if system_name == "Windows":
        download_type = "serverBedrockWindows"
    elif system_name == "Linux":
        download_type = "serverBedrockLinux"

    if download_type is None:
        print_log("Unsupported operating system: " + system_name)
        sys.exit(1)

    DOWNLOAD_LINKS_URL = r"https://net-secondary.web.minecraft-services.net/api/v1.0/download/links"

    try:
        response = requests.get(DOWNLOAD_LINKS_URL, headers=HEADERS, timeout=5)
        response_json = response.json()

        all_links = response_json["result"]["links"]
        download_link = None

        # Find the serverBedrockWindows download link
        for link in all_links:
            if link["downloadType"] == download_type:
                download_link = link["downloadUrl"]
                break

        if download_link is None:
            raise Exception(download_type + " download link not found")

    except requests.exceptions.Timeout:
        print_log("Error fetching download link: timeout raised, try again")
        sys.exit(1)
    except Exception as e:
        print_log("Error fetching download link: " + str(e))
        sys.exit(1)

    print_log("Download link: " + download_link)
    return download_link

def get_file_version(filename : str):
    """
    Get the version number from the filename.
    The filename should contain a version number in the format #.#.#.
    """
    version_search = re.search(r"(?:\d+\.)+", filename)
    if version_search:
        return version_search.group(0).strip(".")
    else:
        print_log("Version number not found in the filename.")
        return None

def server_out_of_date():
    """
    Check if the server is out of date by comparing the current version with the latest version.
    Returns True if the server is out of date, False otherwise.
    """
    version_file = os.path.join(minecraft_directory, "updater", "version.txt")

    if not os.path.isfile(version_file):
        return True  # If version file doesn't exist, consider it out of date
    with open(version_file, "r") as file:
        current_version = file.read().strip()
    latest_version = get_file_version(get_download_link())
    return current_version != latest_version

def update_or_run_server():
    global running_server
    global HEADERS

    version_file = os.path.join(minecraft_directory, "updater", "version.txt")
    process_name = "bedrock_server.exe"  # Name of the process (example: "notepad.exe")
    exe_path = os.path.join(minecraft_directory, "running", process_name)  # Full path to the .exe

    if not os.path.isfile(version_file):
        with open(version_file, "w") as file:
            file.write("unknown")

    with open(version_file, "r") as file:
        prev_version = file.read()

    download_link = get_download_link()

    # find last slash in download_link
    server_download_filename = download_link[download_link.rfind("/") + 1 :]

    server_download_version = get_file_version(server_download_filename)

    if server_download_version != prev_version:
        # Download server binary
        with requests.get(download_link, headers=HEADERS, stream=True) as r:
            r.raise_for_status()
            with open(server_download_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        # Stop MC server safely
        print_log("Stopping Server...")
        try_stop_server(running_server)
        running_server = None
        #subprocess.run([minecraft_directory + "/updater/stopserver.bat"])

        print_log("Migrating Server Files...")
        # Migrate current server to newest version (preserves server settings & world data)
        migrate_server(minecraft_directory)

        # Save the download link to a text file
        with open(version_file, "w") as file:
            file.write(server_download_version)

        print_log("Starting Server...")
        # run MC server
        running_server = start_server(exe_path)

        if running_server is None:
            print_log("Failed to start the server.")
            sys.exit(1)
        # subprocess.run([minecraft_directory+"/updater/startserver.bat", minecraft_directory])

        print_log("Minecraft server is updated " + "(" + prev_version + " -> " + server_download_version + ")")
    else:
        print_log("Minecraft server is already newest version (" + server_download_version + ")... nothing to update.")

        print_log("Starting Server...")
        # run MC server
        running_server = start_server(exe_path)

        if running_server is None:
            print_log("Failed to start the server.")
            sys.exit(1)
        # subprocess.run([minecraft_directory+"/updater/startserver.bat", minecraft_directory])

def console_input_loop():
    """
        Read lines the *user* types into THIS Python console and forward to server.
        Non-blocking to main thread because runs in daemon thread.
        """

    global running_server

    console_input = ""

    print_log("Console input thread started. Type commands to send to the server.")

    while True:
        user_input = sys.stdin.read(1)

        if user_input.find("\n") != -1:
            print("Sending user input to server: " + console_input)
            if running_server is not None:
                print(console_input, file=running_server.stdin)
                running_server.stdin.flush()
            console_input = ""
        else:
            console_input += user_input

        #sleep
        time.sleep(0.0001)

def console_output_loop():
    """
        Read lines from server output and print them to the console.
        Non-blocking to main thread because runs in daemon thread.
        """

    global running_server

    print_log("Console output thread started. Printing server output to console.")

    while True:
        if running_server is not None:
            output = running_server.stdout.readline()
            if output:
                print(output.strip())

        #sleep
        time.sleep(0.0001)

update_or_run_server()

stdin_thread = threading.Thread(target=console_input_loop, name="BedrockConsoleInput", daemon=True)
stdin_thread.start()

stdout_thread = threading.Thread(target=console_output_loop, name="BedrockConsoleOutput", daemon=True)
stdout_thread.start()

last_check_time = time.time()
is_out_of_date = False;
did_send_one_minute_warning = False
server_update_time = 0;

while running_server is not None:
    try:
        if not is_out_of_date and time.time() - last_check_time > server_update_check_time:
            print_log("Checking for updates...")
            last_check_time = time.time()
            if server_out_of_date():
                print_log("Server is out of date, updating...")
                is_out_of_date = True
                server_update_time = time.time() + server_update_buffer_time
                send_server_message(server_update_message)

                if time.time() > server_update_time - 60:
                    did_send_one_minute_warning = True
            else:
                print_log("Server is up to date.")

        if is_out_of_date:
            #check to send the 1 minute warning message
            if not did_send_one_minute_warning and time.time() > server_update_time - 60:
                print_log("Sending 1 minute warning message...")
                send_server_message(server_one_min_warning_message)
                did_send_one_minute_warning = True

            if time.time() > server_update_time:
                print_log("Server update time reached, updating server...")
                update_or_run_server()
                last_check_time = time.time()
                is_out_of_date = False
                did_send_one_minute_warning = False

        if running_server is None or running_server.poll() is not None:
            print_log("Server process has terminated.")
            break

        # Wait for a while before checking again
        time.sleep(1)

    except KeyboardInterrupt:
        break
