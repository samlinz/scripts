#!/usr/bin/python3
# 26.02.2018 Samuel Lindqvist
# Lists pulseaudio sinks and allows the user to change default sink and move sources on the fly

import subprocess, re, os

dir_path = os.path.dirname(os.path.realpath(__file__))

commands = {
    "get_sinks": ["pacmd", "list-sinks"],
    "change_sink": ["{}/changesink.sh".format(dir_path)]
}

regex = {
    "get_sink_count": r'(\d{1,}) sink\(s\) available',
    "get_sink_names": r'index:\s(\d{1,})(?:.|\n|\r|\t)+?alsa\.card_name = \"(.+?)\"'
}

def get_output(command):
    sinks = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data, err = sinks.communicate()
    if err is None or len(err) > 0:
        raise Exception("Command failed with {}".format(str(err)))
    return data

# List sinks
sinks = get_output(commands["get_sinks"])
output = sinks.decode("ascii")

sink_count = re.match(regex["get_sink_count"], output, re.I)
sink_count = int(sink_count.group(1))

if (sink_count <= 1):
    exit("Nothing to choose from")

sink_names = re.findall(regex["get_sink_names"], output, re.I)
if sink_names is None:
    exit("Failed to parse sink names")

indexes = dict()
# Iterate sink ids and names
for i in range(len(sink_names)):
    index = int(sink_names[i][0])
    name = sink_names[i][1]
    indexes[index] = name
    print("Index {}, name {}".format(index, name))

while True:
    try:
        selected = input("Select the sink: ")
        selected = int(selected)
    except KeyboardInterrupt:
        exit(0)
    except Exception:
        print("Invalid input")
        continue
    if selected not in indexes:
        print("Invalid choice")
        continue
    break

print("Changing the sink to {}".format(indexes[selected]))

input = commands["change_sink"]
input.append(str(selected))

output = get_output(input)
output = output.decode("ascii")
if "Done\n" in output:
    exit("Success")
else:
    exit("Failed")