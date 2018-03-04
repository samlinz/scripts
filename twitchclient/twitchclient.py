#!/usr/bin/python3

# Command line utility to poll the status of Twitch streamers
# and to open a stream using an external program specified in config.json
# Use of `streamlink` from pip is recommended

from __future__ import print_function
import requests, json, sys, subprocess
from multiprocessing import Pool
from pathlib import Path
from datetime import datetime
from cursesmenu import *
from cursesmenu.items import *


# Print to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


# Run arbitrary UNIX command
def run(command, *arguments):
    comm = list()
    comm.append(str(command))
    comm.extend(arguments)
    try:
        proc = subprocess.Popen(comm, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        exit("Command {} not found".format(command))
    data, err = proc.communicate()
    if err is None or len(err) > 0:
        raise Exception("Command failed with {}".format(err.decode("ascii")))
    return data.decode("ascii")


CONFIG_LOCATIONS = [
    "{}/.config/twitchnotifier/config.json".format(str(Path.home()))
]

_config = None

# Read configuration
for config_location in CONFIG_LOCATIONS:
    try:
        with open(config_location) as f:
            _config = json.load(f)
    except Exception as e:
        continue
    if _config is not None: break

if _config is None:
   eprint("Failed to load config file")
   exit()

CLIENT_ID = _config["ApiKey"]
STREAMS = _config["Channels"]
STREAMS = [s.lower() for s in STREAMS]
#COMMAND_NOTIFY = _config["NotifyCommand"]
COMMAND_STREAM = _config["StreamCommand"]
if (CLIENT_ID is None):
    eprint("Api key is missing")
    exit()
API_BASE_ADDRESS = "https://api.twitch.tv/kraken/streams/{}"
STREAM_BASE_ADDRESS = "https://www.twitch.tv/{}"

if (len(STREAMS) == 0):
    eprint("No streams listed")
    exit()

def _get_headers(client_id):
    return {
        "Client-ID": client_id
    }


def _get_stream_status(name):
    global API_BASE_ADDRESS, CLIENT_ID
    headers = _get_headers(CLIENT_ID)
    response = requests.get(API_BASE_ADDRESS.format(name), headers = headers)
    if response.ok is not True:
        return None
    return json.loads(response.text)


def _get_stream_objects(channel_names):
    pool = Pool()
    responses = pool.map(_get_stream_status, channel_names)
    return responses


def _notify_if_online(stream_statuses):
    global COMMAND_NOTIFY


def _open_stream(url):
    global COMMAND_STREAM
    status = run(COMMAND_STREAM.replace("$url", url))
    exit()


if __name__ == "__main__":
    online_streamers = []
    online_objs = []
    offline_streamers = []

    responses = _get_stream_objects(STREAMS)
    for stream_status in responses:
        info = stream_status["stream"]
        if info is None:
            continue # Not online
        name = info["channel"]["name"]
        title = info["channel"]["status"]
        started = datetime.strptime(info["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        #"2015-10-28T16:13:41Z"
        stream_type = info["stream_type"]
        if stream_type != "live":
            continue
        game = info["game"]
        online_streamers.append(name)
        online_objs.append({
            "name": name,
            "started": started,
            "stream_type": stream_type,
            "game": game,
            "title": title
        })
    offline_streamers = [n for n in STREAMS if n.lower() not in online_streamers]

    # Create Curses menu
    menu = CursesMenu("Open stream", "Select online streamer")
    i = 0
    for online in online_streamers:
        stream_url = STREAM_BASE_ADDRESS.format(online)
        # Open stream with streamlink
        item = CommandItem("{} - {} - {}".format(online, online_objs[i]["game"], online_objs[i]["title"]), COMMAND_STREAM.replace("$url", stream_url))
        menu.append_item(item)
        i += 1

    for offline in offline_streamers:
        item = MenuItem("{} - OFFLINE".format(offline))
        menu.append_item(item)

    menu.show()