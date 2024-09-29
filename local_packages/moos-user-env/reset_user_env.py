#!/usr/bin/python

import getpass
import os
import subprocess


def error(msg: str) -> None:
    print("Error: " + msg)


def run(*args, cwd: str | None = None) -> bool:
    return subprocess.run(args, cwd=cwd).returncode == 0


if __name__ == "__main__":
    home = os.path.expanduser("~")
    user = getpass.getuser()
    env_factory = "/etc/user_env/env"

    if user == "root":
        error("Running this script as root is prohibited")
        quit(1)

    if not run(
        "rsync",
        "--archive",
        "--chown=" + user + ":" + user,
        env_factory + "/",
        home + "/",
    ):
        error("Failed to copy files from " + env_factory + " to " + home)
        quit(1)

    print("Successfully reset the environment for " + user)
