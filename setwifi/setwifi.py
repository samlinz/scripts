#!/usr/bin/python3
# 26.02.18
# Find and connect to an AP from terminal

import subprocess, re, os

regex_ifs = r"(^[a-z0-9]{2,10})\s{3,}.+$"
regex_ssid = r"SSID:\s([a-z0-9A-Z_-]*)"
regex_inet = r"WIF\s+(?:.|\n|\t|\r)+(?:\s{10}){1}inet addr:(\d{3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"

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

if __name__ == "__main__":
    # Get all network interfaces
    output_ifs = run("ifconfig", "-a")
    ifs = re.findall(regex_ifs, output_ifs, re.I | re.M)
    wifi_interfaces = [f for f in ifs if f.startswith("w")]
    if len(wifi_interfaces) == 0:
        exit("No wifi interfaces were found on the system")
    elif len(wifi_interfaces) > 1:
        exit("Multiple wifi interfaces were found")
        # TODO: make user choose?
    wif = wifi_interfaces[0]

    print("Setting the network interface up")

    # Set the interface up
    run("sudo", "ifconfig", wif, "up")

    print("Scanning...")

    # Scan for APs
    aps = run("sudo", "iw", "dev", wif, "scan")
    
    ssids = re.findall(regex_ssid, aps, re.M)
    
    print("Found the following wireless access points")
    for ind, ssid in enumerate(ssids):
        print("{}: {}".format(ind, ssid))
    

    while True:
        try:
            selection = input("Choose the AP: ")
            selection = int(selection)
            if selection < 0 or selection > len(ssids):
                print("Invalid selection")
                continue            
        except KeyboardInterrupt:
            exit(0)
        except Exception:
            print("Invalid selection")
            continue
        break
    ssid = ssids[selection]

    print("Connecting to ESSID {}".format(ssid))

    pwd = input("If the AP needs a password, input it now or press return: ")

    if len(pwd) > 0:
        output_conn = run("sudo", "iwconfig", wif, "essid", ssid, "key", pwd)
    else:
        output_conn = run("sudo", "iwconfig", wif, "essid", ssid)
    
    output_dhcp = run("sudo", "dhclient", wif)

    # Confirm that we have an ip address
    output_ifconfig = run("ifconfig")
    inet = re.findall(regex_inet.replace("WIF", wif), output_ifconfig, re.M)

    if inet is None or len(inet) == 0:
        exit("Failed to connect and/or fetch IP address")
        #TODO: IPv6 doesn't work
    
    print("Your ip address is {}".format(inet[0]))
    print("Done")
