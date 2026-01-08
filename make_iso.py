#!/usr/bin/env python3

import atexit
import os
import random
import shutil
import string
import subprocess
import time
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from colorama import Fore, Style


# General utilities
# ----------------------------------------------------------------------------


def green(msg: str) -> str:
    return Fore.GREEN + Style.BRIGHT + msg + Style.RESET_ALL


def blue(msg: str) -> str:
    return Fore.BLUE + Style.BRIGHT + msg + Style.RESET_ALL


def red(msg: str) -> str:
    return Fore.RED + Style.BRIGHT + msg + Style.RESET_ALL


def event(msg: str) -> None:
    print(green("==> ") + msg)


def sub_event(msg: str) -> None:
    print(blue("  -> ") + msg)


def error(msg: str) -> None:
    print(red(msg))


def sep() -> str:
    return "-" * os.get_terminal_size().columns


def run(*args, quiet: bool = True, env: Dict[str, str] | None = None) -> bool:
    return subprocess.run(args, capture_output=quiet, env=env).returncode == 0


def get(*args) -> str | None:
    result = subprocess.run(args, capture_output=True)
    if result.returncode == 0:
        return result.stdout.decode().strip()
    return None


def remove(path: str) -> bool:
    return run("sudo", "rm", "-rf", path)


def copy(src: str, dst: str) -> bool:
    try:
        shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)
    except os.error as err:
        error("Error: Failed to copy " + src + " to " + dst + ": " + str(err))
        return False
    return True


def cd(dst: str) -> bool:
    try:
        os.chdir(dst)
    except os.error as err:
        error("Error: Failed to change directory to " + dst + ": " + str(err))
        return False
    return True


def append(dst: str, line: str) -> bool:
    try:
        with open(dst, "a") as file:
            file.write(line + "\n")
    except Exception as err:
        error("Error: Failed to append to " + dst + ": " + str(err))
        return False
    return True


def read_lines(src: str) -> list[str] | None:
    try:
        with open(src, "r") as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        return list()
    except Exception as err:
        error("Error: Failed to read lines from " + src + ": " + str(err))
        return None


def write(dst: str, content: str) -> bool:
    try:
        dir: str = os.path.dirname(dst)
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(dst, "w") as file:
            file.write(content)
    except Exception as err:
        error("Error: Failed to write to " + dst + ": " + str(err))
        return False
    return True


# ----------------------------------------------------------------------------


class Dir:
    def __init__(self, path: str) -> None:
        self.path = path


class TempDir(Dir):
    def __init__(self) -> None:
        temp_dir: str | None = get("mktemp", "-d")
        self.good = temp_dir is not None
        super().__init__(str(temp_dir))
        atexit.register(self.cleanup)

    def cleanup(self) -> None:
        if self.good:
            remove(self.path)
            self.good = False


@dataclass
class Dependencies:
    depends: list[str]
    make_depends: list[str]
    check_depends: list[str]
    opt_depends: list[str]


class PackageBuilder:
    def __init__(
        self,
        recipe_dir: str | None = None,
    ) -> None:
        if recipe_dir:
            self.recipe_dir = Dir(recipe_dir)

            self.build_dir = TempDir()
            self.good = self.build_dir.good

            if self.good:
                self.good = copy(self.recipe_dir.path, self.build_dir.path)
        else:
            self.recipe_dir = TempDir()
            self.good = self.recipe_dir.good
            self.build_dir = self.recipe_dir

    def download(self, url: str) -> bool:
        return run("git", "clone", url, self.build_dir.path)

    def get_dependencies(self) -> Dependencies | None:
        depends = get(
            "bash",
            "-ec",
            "source " + self.build_dir.path + "/PKGBUILD; echo ${depends[@]%:*};",
        )
        if depends is None:
            return None

        make_depends = get(
            "bash",
            "-ec",
            "source " + self.build_dir.path + "/PKGBUILD; echo ${makedepends[@]%:*};",
        )
        if make_depends is None:
            return None

        check_depends = get(
            "bash",
            "-ec",
            "source " + self.build_dir.path + "/PKGBUILD; echo ${checkdepends[@]%:*};",
        )
        if check_depends is None:
            return None

        opt_depends = get(
            "bash",
            "-ec",
            "source " + self.build_dir.path + "/PKGBUILD; echo ${optdepends[@]%:*};",
        )
        if opt_depends is None:
            return None

        return Dependencies(
            depends.split(),
            make_depends.split(),
            check_depends.split(),
            opt_depends.split(),
        )

    def build(
        self,
        deps: Dependencies,
        dep_handler: Callable[[str, bool], bool],
        makepkg_env: Dict[str, str],
        install: bool,
        check_deps: bool,
    ) -> bool:
        # Get package name
        name = get(
            "bash",
            "-ec",
            "source " + self.build_dir.path + "/PKGBUILD; echo $pkgname;",
        )
        if name is None:
            error("Error: Failed to read package name")
            return False
        name = str(name)

        for dep in deps.make_depends:
            if not dep_handler(dep, True):
                error("Error: Failed to handle build dependency for: " + name)
                return False

        for dep in deps.check_depends:
            if not dep_handler(dep, True):
                error("Error: Failed to handle check dependency for: " + name)
                return False

        for dep in deps.depends:
            if not dep_handler(dep, False):  # Do not install depends
                error("Error: Failed to handle required dependency for: " + name)
                return False

        for dep in deps.opt_depends:
            if not dep_handler(dep, False):  # Do not install optdepends
                error("Error: Failed to handle optional dependency for: " + name)

        # makepkg requires that the PKGBUILD be in the working directory.
        if not cd(self.build_dir.path):
            return False

        # Optional extra arguments for makepkg
        extra_args: List[str] = list()
        if install:
            extra_args.append("--install")
            extra_args.append("--noconfirm")
        if not check_deps:
            extra_args.append("--nodeps")

        # Build the package with makepkg.
        if not run(
            "makepkg",
            "--clean",
            "--force",
            "--nocheck",
            *extra_args,
            quiet=False,
            env=makepkg_env,
        ):
            error("Error: Failed to build package: " + name)
            return False

        return True


class PackageRepoMaker:
    def __init__(
        self,
        profile_dir: str,
        cache_dir: str,
        db_dir: str,
        local_packages_dir: str,
        added_packages_file_path: str,
        packager: str,
    ) -> None:
        self.profile_dir = profile_dir
        self.root_dir = os.path.join(profile_dir, "airootfs")
        self.cache_dir = cache_dir
        self.dbpath = db_dir
        self.local_packages_dir = local_packages_dir
        self.added_packages_file_path = added_packages_file_path
        self.packager = packager

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        if not os.path.exists(self.dbpath):
            os.makedirs(self.dbpath)

        db_dst = os.path.join(self.dbpath, "sync")
        if not os.path.exists(db_dst):
            self.good = copy("/var/lib/pacman/sync", db_dst)
        else:
            self.good = True

    def _pacman(self, *args, quiet: bool = False) -> bool:
        return run(
            "sudo",
            "pacman",
            "--noconfirm",
            *args,
            quiet=quiet,
        )

    def _fresh_pacman(self, *args, quiet: bool = False) -> bool:
        return run(
            "sudo",
            "pacman",
            "--root",
            self.root_dir,
            "--cachedir",
            self.cache_dir,
            "--dbpath",
            self.dbpath,
            "--noconfirm",
            *args,
            quiet=quiet,
        )

    def _is_already_added(self, package: str, installed: bool) -> bool:
        added_packages = read_lines(self.added_packages_file_path)
        if added_packages is None:
            return False
        if package not in added_packages:
            return False
        if installed:
            if not self._pacman("-Qi", package, quiet=True):
                return False
        return True

    def _is_official_package(self, package: str) -> bool:
        if not self._fresh_pacman("-Sp", package, quiet=True):
            return False
        return True

    def _add_official_package(self, package: str, install: bool) -> bool:
        if not self._fresh_pacman("-Sw", package):
            return False
        if not append(self.added_packages_file_path, package):
            return False
        if install:
            if not self._pacman("-S", package):
                return False
        return True

    def _is_aur_package(self, package: str) -> bool:
        return run(
            "git",
            "ls-remote",
            "--exit-code",
            "https://aur.archlinux.org/" + package + ".git",
        )

    def _get_makepkg_env(self, build_dir: str, cache_dir: str) -> Dict[str, str]:
        makepkg_env = os.environ.copy()
        makepkg_env["SRCDEST"] = build_dir
        makepkg_env["SRCPKGDEST"] = build_dir
        makepkg_env["BUILDDIR"] = build_dir
        makepkg_env["PACKAGER"] = self.packager
        makepkg_env["PKGDEST"] = cache_dir
        return makepkg_env

    def _get_aur_package(self, package: str, install: bool) -> bool:
        package_builder = PackageBuilder()
        if not package_builder.good:
            error("Error: Failed to initialize the packager for: " + package)
            return False

        if not package_builder.download(
            "https://aur.archlinux.org/" + package + ".git"
        ):
            error("Error: Failed to download package recipe for: " + package)
            return False

        deps = package_builder.get_dependencies()
        if deps is None:
            error("Error: Failed to get package dependencies")
            return False

        makepkg_env = self._get_makepkg_env(
            package_builder.build_dir.path, self.cache_dir
        )

        result: bool = package_builder.build(
            deps, self.add_package, makepkg_env, install=install, check_deps=True
        )
        if not result:
            return False

        if not append(self.added_packages_file_path, package):
            return False

        return True

    def _is_local_package(self, package: str) -> bool:
        return os.path.isdir(self.local_packages_dir + "/" + package)

    def _get_local_package(self, package: str, install: bool) -> bool:
        package_builder = PackageBuilder(
            recipe_dir=self.local_packages_dir + "/" + package,
        )
        if not package_builder.good:
            error("Error: Failed to initialize the packager for: " + package)
            return False

        deps = package_builder.get_dependencies()
        if deps is None:
            error("Error: Failed to get package dependencies")
            return False

        makepkg_env = self._get_makepkg_env(
            package_builder.build_dir.path, self.cache_dir
        )

        result: bool = package_builder.build(
            deps, self.add_package, makepkg_env, install=install, check_deps=False
        )
        if not result:
            return False

        if not append(self.added_packages_file_path, package):
            return False

        return True

    def add_package(self, package: str, install: bool) -> bool:
        if self._is_already_added(package, installed=install):
            return True

        event(package)

        # Search the official package repositories (or wherever /etc/pacman.conf tells pacman to look).
        if self._is_official_package(package):
            green("[official package]")
            if not self._add_official_package(package, install=install):
                error("Error: Failed to add official package: " + package)
                return False
            return True

        # Search the AUR.
        if self._is_aur_package(package):
            green("[AUR package]")
            if not self._get_aur_package(package, install=install):
                error("Error: Failed to add AUR package: " + package)
                return False
            return True

        # Search the local package directory.
        if self._is_local_package(package):
            green("[local package]")
            if not self._get_local_package(package, install=install):
                error("Error: Failed to add local package: " + package)
                return False
            return True

        error("Error: Failed to resolve package: " + package)
        return False

    def make_repo(self, name: str) -> bool:
        # Accumulate all packages into a list.
        packages: List[str] = []
        for file in os.listdir(self.cache_dir):
            file_path = self.cache_dir + "/" + file
            if not os.path.isfile(file_path):
                continue
            if not file.endswith(".pkg.tar.zst"):
                continue
            packages.append(file_path)

        # Make an offline package repository.
        repo_path: str = os.path.join(self.cache_dir, name + ".db.tar.zst")
        if os.path.exists(repo_path):
            remove(os.path.join(self.cache_dir, name + ".db"))
            remove(repo_path)
            remove(os.path.join(self.cache_dir, name + ".files"))
            remove(os.path.join(self.cache_dir, name + ".files.tar.zst"))
        if not run("repo-add", "--new", repo_path, *packages, quiet=False):
            error("Error: Failed to make repo")
            return False

        return True


if __name__ == "__main__":
    # Ensure this script is running on Linux. Other operating systems are not supported.
    if get("uname", "-s") != "Linux":
        error("Error: Incompatible operating system")
        quit(1)

    # The package repository name.
    package_repo_name: str = "offline"

    # Who is building the packages in this package database?
    packager_name: Optional[str] = get("git", "config", "get", "user.name")
    if not packager_name:
        error(
            "Error: Packager name not found. Set the 'user.name' field in your Git configuration."
        )
        quit(1)
    packager_email: Optional[str] = get("git", "config", "get", "user.email")
    if not packager_email:
        error(
            "Error: Packager email not found. Set the 'user.email' field in your Git configuration."
        )
        quit(1)
    packager: str = packager_name + " <" + packager_email + ">"

    # Paths
    project_root_dir: str = os.path.dirname(__file__)
    local_packages_dir: str = os.path.join(project_root_dir, "local_packages")
    profile_orig_dir: str = os.path.join(project_root_dir, "profile")
    work_dir: str = os.path.join(project_root_dir, "working")
    profile_dir: str = os.path.join(work_dir, "profile")
    cache_dir: str = os.path.join(profile_dir, "airootfs", "offline")
    db_dir: str = os.path.join(work_dir, "offline_db")
    added_packages_file_path: str = os.path.join(work_dir, "added_packages")
    mkarchiso_dir: str = os.path.join(work_dir, "mkarchiso")
    out_dir: str = os.path.join(project_root_dir, "out")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not os.path.exists(profile_dir):
        if not copy(profile_orig_dir, profile_dir):
            error("Error: Failed to copy the profile directory to a temporary location")
            quit(1)

    live_iso_packages: Optional[str] = get("cat", profile_dir + "/packages.x86_64")
    if not live_iso_packages:
        error("Error: Failed to get the list of packages installed on the live ISO.")
        quit(1)

    # Which additional packages are being added to the repository?
    extra_packages: list[str] = ["moos", "moos-xorg", "moos-headless", "moos-sshd-conf"]

    # Construct a list of all packages to add to the repository.
    packages: list[str] = extra_packages
    for pkg in live_iso_packages.split():
        if pkg not in packages:
            packages.append(pkg)

    # Make a package repository containing the specified packages and place it in the profile directory.

    repo = PackageRepoMaker(
        profile_dir,
        cache_dir,
        db_dir,
        local_packages_dir,
        added_packages_file_path,
        packager,
    )
    if not repo.good:
        error("Error: Failed to initialize a fresh package repository")
        quit(1)

    for pack in packages:
        if not repo.add_package(package=pack, install=False):
            quit(1)

    if not repo.make_repo(package_repo_name):
        error("Error: Failed to build the offline repository")
        quit(1)

    # Make the ISO

    pacman_tmp_dir = TempDir()
    pacman_tmp_db_dir = os.path.join(pacman_tmp_dir.path, "db")
    pacman_tmp_cache_dir = os.path.join(pacman_tmp_dir.path, "cache")

    if not write(
        os.path.join(profile_dir, "pacman.conf"),
        "[options]\n"
        f"RootDir = {pacman_tmp_dir}\n"
        f"DBPath = {pacman_tmp_db_dir}\n"
        f"CacheDir = {pacman_tmp_cache_dir}\n"
        "HoldPkg = pacman glibc\n"
        "Architecture = auto\n"
        "SigLevel = Never\n"
        "\n"
        "[offline]\n"
        f"Server = file://{profile_dir}/airootfs/offline/\n",
    ):
        error("Error: Failed to generate a custom pacman.conf for constructing the ISO")
        quit(1)

    sshd_port: int = random.randint(10234, 60535)

    if not write(
        os.path.join(
            profile_dir, "airootfs", "etc", "ssh", "sshd_config.d", "10-moosiso.conf"
        ),
        "Port " + str(sshd_port) + "\n"
        "PermitRootLogin yes\n"
        "PasswordAuthentication yes\n"
        "PermitEmptyPasswords yes\n",
    ):
        error(
            "Error: Failed to generate the SSH daemon configuration for the ISO live environment"
        )
        quit(1)

    hotspot_con_name: str = "moos-hotspot"
    hotspot_ssid: str = "moos-live"
    hotspot_password: str = "".join(
        [random.choice(string.ascii_lowercase) for i in range(10)]
    )
    hotspot_service_name: str = "moos-hotspot.service"
    hotspot_service_ref_path: str = os.path.join(
        "etc", "systemd", "system", hotspot_service_name
    )
    hotspot_service_path: str = os.path.join(
        profile_dir, "airootfs", hotspot_service_ref_path
    )
    hotspot_service_symlink_path: str = os.path.join(
        profile_dir,
        "airootfs",
        "etc",
        "systemd",
        "system",
        "multi-user.target.wants",
        hotspot_service_name,
    )

    if not write(
        hotspot_service_path,
        "[Unit]\n"
        "Description=Create a WiFi hotspot (Access Point) with NetworkManager\n"
        "Requires=NetworkManager.service\n"
        "After=NetworkManager.service\n"
        "\n"
        "[Service]\n"
        "Type=oneshot\n"
        f'ExecStart=/usr/bin/env bash -c \'(nmcli connection show "{hotspot_con_name}" && nmcli connection delete "{hotspot_con_name}") || true\'\n'
        f'ExecStart=/usr/bin/env bash -c \'nmcli device wifi hotspot con-name "{hotspot_con_name}" ssid "{hotspot_ssid}" password "{hotspot_password}"\'\n'
        f"ExecStart=/usr/bin/env bash -c 'nmcli connection modify \"{hotspot_con_name}\" connection.autoconnect yes'\n"
        f"ExecStart=/usr/bin/env bash -c 'nmcli connection modify \"{hotspot_con_name}\" connection.autoconnect-priority 999'\n"
        f"ExecStart=/usr/bin/env bash -c 'nmcli connection up {hotspot_con_name}'\n"
        "\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n",
    ):
        error(
            "Error: Failed to generate the SSH daemon configuration for the ISO live environment"
        )
        quit(1)

    if not os.path.islink(hotspot_service_symlink_path):
        if not run(
            "ln",
            "-s",
            hotspot_service_ref_path,
            hotspot_service_symlink_path,
            quiet=False,
        ):
            error("Error: Failed to enable the hotspot service")
            quit(1)

    if not run(
        "sudo",
        "mkarchiso",
        "-v",
        "-r",
        "-w",
        mkarchiso_dir,
        "-o",
        out_dir,
        profile_dir,
        quiet=False,
    ):
        error("Error: ISO construction failed")
        quit(1)

    if not write(os.path.join(out_dir, "hotspot_ssid"), hotspot_ssid):
        error("Error: Failed to write the hotspot SSID to a file")

    if not write(os.path.join(out_dir, "hotspot_password"), hotspot_password):
        error("Error: Failed to write the hotspot password to a file")

    if not write(os.path.join(out_dir, "ssh_port"), str(sshd_port)):
        error("Error: Failed to write the SSH port to a file")

    print(green("ISO constructed successfully"))
    print("WiFi Hotspot SSID: " + green(hotspot_ssid))
    print("WiFi Hotspot Password: " + green(hotspot_password))
    print("SSH Port: " + green(str(sshd_port)))

    quit(0)
