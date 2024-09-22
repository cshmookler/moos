#!/usr/bin/python

import json
import os
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
    if len(sys.argv) <= 2:
        error("Not enough arguments")
        quit(1)

    ff_base_policies_file: str = sys.argv[1]
    ff_conf_dir: str = sys.argv[2]

    if not os.path.isabs(ff_conf_dir) or not os.path.isabs(ff_base_policies_file):
        error("All given path must be absolute")
        quit(1)

    ff_extensions_dir = ff_conf_dir + "/extensions"
    ff_policies_dir = ff_conf_dir + "/policies"

    os.makedirs(ff_extensions_dir, exist_ok=True)
    os.makedirs(ff_policies_dir, exist_ok=True)

    lookup_url: str = "https://addons.mozilla.org/api/v5/addons/addon/"

    remote_ids: List[str] = [
        "ublock-origin",
        "darkreader",
        "vimium-ff",
        "redirector",
        "new-tab-suspender",
        "hide-youtube-shorts",
    ]

    with open(ff_base_policies_file, "r") as file:
        ff_policies = json.load(file)

    if "policies" not in ff_policies:
        ff_policies["policies"] = {}
    if "ExtensionSettings" not in ff_policies["policies"]:
        ff_policies["policies"]["ExtensionSettings"] = {}

    for remote_id in remote_ids:
        response_str = get("curl", lookup_url + remote_id + "/")
        if not response_str:
            error(
                "Failed to retrieve json data for " + remote_id + " from " + lookup_url
            )
            quit(1)

        response = json.loads(response_str)
        try:
            guid = response["guid"]
            download_url = response["current_version"]["file"]["url"]
        except KeyError:
            error("Invalid json data for " + remote_id + " from " + url)
            quit(1)

        extension_file = ff_extensions_dir + "/" + guid + ".xpi"

        if not run(
            "curl",
            "--output",
            extension_file,
            download_url,
        ):
            error("Failed to get " + remote_id + " from " + download_url)
            quit(1)

        ff_policies["policies"]["ExtensionSettings"][guid] = {
            "install_url": "file:///etc/firefox/extensions/" + guid + ".xpi",
            "installation_mode": "normal_installed",
        }

    ff_policies_file = ff_policies_dir + "/policies.json"

    with open(ff_policies_file, "w") as file:
        json.dump(ff_policies, file, indent=4)

