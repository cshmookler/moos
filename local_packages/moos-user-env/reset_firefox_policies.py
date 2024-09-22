#!/usr/bin/python

import getpass
import os
import subprocess


def error(msg: str) -> None:
    print("Error: " + msg)


def run(*args, cwd: str | None = None) -> bool:
    return subprocess.run(args, cwd=cwd).returncode == 0


if __name__ == "__main__":
    user = getpass.getuser()
    ff_factory = "/etc/user_env/firefox"
    ff_conf_dir = "/etc/firefox"

    if user != "root":
        error("This script must be run as root")
        quit(1)

    if not run(
        "rsync",
        "--archive",
        ff_factory + "/",
        ff_conf_dir + "/"
    ):
        error("Failed to copy files from " + ff_factory + " to " + ff_conf_dir)
        quit(1)

    print("Successfully updated the global firefox policies")
