import os
import json

if __name__ == "__main__":
    pings_in_dir = os.listdir("assets/standard_pings")
    pingMap = {}
    
    start_index = 170  # Champions are indexed 0-169 so start pings at 170
    for i in range(len(pings_in_dir)):
        ping_images = len(os.listdir("assets/standard_pings/{0}".format(pings_in_dir[i])))
        pingMap[start_index + i] = {
            'ping_name': pings_in_dir[i],
            'ping_images': ping_images
        }

    print([ping for ping in pings_in_dir])

    with open("pingMap.json", "w") as f:
        f.write(json.dumps(pingMap))
