#!/usr/bin/python

from configparser import ConfigParser
import getpass
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
    home = os.path.expanduser("~")
    user = getpass.getuser()
    factory = "/etc/user_env"
    env_factory = factory + "/env"
    ff_factory = factory + "/firefox"
    ff_dir = home + "/.mozilla/firefox"
    ff_profiles = ff_dir + "/profiles.ini"

    if user == "root":
        error("Running this script as root is prohibited")
        quit(1)

    if not run(
        "rsync",
        "--archive",
        "--ignore-existing",
        "--chown=" + user + ":" + user,
        env_factory + "/",
        home + "/",
    ):
        error("Failed to copy files from " + env_factory + " to " + home)
        quit(1)

    if not os.path.exists(ff_profiles):
        print("Creating the default profile for Firefox...")
        if not run(
            "firefox",
            "--first-startup",
            "--headless",
            "--screenshot",
            "/dev/null",
            "about:blank",
        ):
            error("Failed to create a profile for Firefox at " + ff_dir)
            quit(1)

    parser = ConfigParser()
    parser.read(ff_profiles)

    profile_dir: Optional[str] = None
    for section in parser.sections():
        if section.startswith("Install"):
            profile_dir = ff_dir + "/" + parser[section]["Default"] + "/"
    if profile_dir is None:
        error(
            "Failed to find the path to the default profile for Firefox in "
            + ff_profiles
        )
        quit(1)
    print("Firefox profile path: " + profile_dir)

    if not run(
        "rsync",
        "--archive",
        "--ignore-existing",
        ff_factory + "/",
        profile_dir + "/",
    ):
        error("Failed to copy files from " + ff_factory + " to " + profile_dir)
        quit(1)

    extension_prefs_file = profile_dir + "/extension-preferences.json"
    with open(extension_prefs_file, "r") as file:
        extension_prefs = json.load(file)

    # extensions_file = profile_dir + "/extensions.json"
    # with open(extensions_file, "r") as file:
    #     extensions = json.load(file)

    extension_dir = profile_dir + "/extensions"

    for ext in os.listdir(extension_dir):
        ext_id = ext.removesuffix(".xpi")

        extension_prefs[ext_id] = {
            "permissions": ["internal:privateBrowsingAllowed"],
            "origins": [],
        }

        # found = False
        # for i in range(len(extensions["addons"])):
        #     if extensions["addons"][i]["id"] == ext_id:
        #         # json.load(extension_dir)
        #         # extensions["addons"][i]["active"] = True
        #         # extensions["addons"][i]["userDisabled"] = False
        #         # extensions["addons"][i]["seen"] = True
        #         found = True
        # if not found:
        #     error("Failed to find " + ext_id + " in " + extensions_file)
        #     quit(1)

    with open(extension_prefs_file, "w") as file:
        json.dump(extension_prefs, file)

    # with open(extensions_file, "w") as file:
    #     json.dump(extensions, file)

    print("Successfully updated the environment for " + user)
