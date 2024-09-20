#!/usr/bin/python

import json
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Optional


def error(msg: str) -> None:
    print("Error: " + msg)


def run(*args, cwd: Optional[str] = None) -> bool:
    return subprocess.run(args, cwd=cwd).returncode == 0


def get(*args) -> Optional[str]:
    result = subprocess.run(args, capture_output=True)
    if result.returncode == 0:
        return result.stdout.decode().strip()
    return None


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        error("Not enough arguments")
        quit(1)

    ff_addon_dir: str = sys.argv[1]
    if not os.path.isabs(ff_addon_dir):
        error("The given path must be absolute")
        quit(1)
    os.makedirs(ff_addon_dir, exist_ok=True)

    url: str = "https://addons.mozilla.org/api/v5/addons/addon/"

    addon_remote_ids: List[str] = [
        "ublock-origin",
        "darkreader",
        "vimium-ff",
        "redirector",
        "new-tab-suspender",
        "hide-youtube-shorts",
    ]

    for remote_id in addon_remote_ids:
        response_str = get("curl", url + remote_id + "/")
        if not response_str:
            error(
                "Failed to retrieve json data for " + remote_id + " from " + url
            )
            quit(1)

        response = json.loads(response_str)
        try:
            download_link = response["current_version"]["file"]["url"]
        except KeyError:
            error("Invalid json data for " + remote_id + " from " + url)
            quit(1)

        addon_file = ff_addon_dir + "/" + remote_id + ".xpi"
        addon_dir = ff_addon_dir + "/" + remote_id

        if not run(
            "curl",
            "--output",
            addon_file,
            download_link,
        ):
            error("Failed to get " + addon_file + " from " + download_link)
            quit(1)

        if not run("unzip", addon_file, "-d", addon_dir):
            error("Failed to unzip " + addon_file)
            quit(1)

        sig = addon_dir + "/META-INF/mozilla.rsa"
        if not os.path.exists(sig):
            error("Failed to find the addon id")
            quit(1)

        readable_sig = get(
            "openssl",
            "pkcs7",
            "-print",
            "-inform",
            "der",
            "-in",
            sig,
        )
        if readable_sig is None:
            error("Failed to read " + sig)
            quit(1)

        id: Optional[str] = None
        for line in readable_sig.splitlines():
            line = line.strip()
            if (
                line.startswith("subject:")
                and "O=Addons" in line
                and "CN=" in line
            ):
                id = line[(line.find("CN=") + 3) :].split(",")[0].strip()
        if id is None:
            error("Failed to find the addon id")
            quit(1)

        os.rename(addon_file, ff_addon_dir + "/" + id + ".xpi")
        shutil.rmtree(addon_dir)

    # ff_tmp_dir = ff_addon_dir + "/tmp"
    # os.makedirs(ff_addon_dir + "/")

    # if not run(
    #     "rsync",
    #     "--archive",
    #     "--ignore-existing",
    #     ff_factory + "/",
    #     profile_dir + "/",
    # ):
    #     error("Failed to copy files from " + ff_factory + " to " + profile_dir)
    #     quit(1)

    # if not run("firefox", "--first-startup", "--new-instance", "--profile", ff_tmp_dir):
    #     error("Failed to generate a temporary Firefox profile with the generated extensions")
    #     quit(1)
