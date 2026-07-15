import os
import time
import subprocess
import urllib.parse
from typing import Optional, List, Set


def build_launch_uri(ticket: str, place_id: Optional[int] = None, job_id: Optional[str] = None) -> str:
    now_ms = int(time.time() * 1000)

    if place_id is not None:
        params = f"request=RequestGame&placeId={place_id}"
        if job_id:
            params += f"&gameId={job_id}"
        place_launcher = f"https://assetgame.roblox.com/game/PlaceLauncher.ashx?{params}"
        encoded_launcher = urllib.parse.quote(place_launcher, safe="")
        uri = f"roblox-player:1+launchmode:play+gameinfo:{ticket}+launchtime:{now_ms}+placelauncherurl:{encoded_launcher}"
    else:
        # app launch mode without immediate place join
        uri = f"roblox-player:1+launchmode:app+gameinfo:{ticket}+launchtime:{now_ms}"

    return uri


def get_running_roblox_pids() -> Set[int]:
    pids = set()
    if os.name != "nt":
        return pids

    try:
        # tasklist is faster and has less overhead than spinning up wmi
        cmd = ["tasklist", "/fi", "imagename eq RobloxPlayerBeta.exe", "/fo", "csv", "/nh"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        for line in output.strip().splitlines():
            parts = line.split(",")
            if len(parts) >= 2:
                raw_pid = parts[1].strip('"')
                if raw_pid.isdigit():
                    pids.add(int(raw_pid))
    except Exception:
        pass
    return pids


def launch_roblox(ticket: str, place_id: Optional[int] = None, job_id: Optional[str] = None, timeout: int = 15) -> Optional[int]:
    """Launches Roblox via protocol URI and waits for the spawned client process ID."""
    initial_pids = get_running_roblox_pids()
    uri = build_launch_uri(ticket=ticket, place_id=place_id, job_id=job_id)

    # print(f"debug launch uri: {uri}")

    if os.name == "nt":
        os.startfile(uri)
    else:
        subprocess.Popen(["xdg-open", uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.name != "nt":
        return None

    # FIXME: on win11 roblox sometimes opens under background tasks for ~3s before window appears
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(0.7)
        current_pids = get_running_roblox_pids()
        new_pids = current_pids - initial_pids
        if new_pids:
            return list(new_pids)[0]

    return None
