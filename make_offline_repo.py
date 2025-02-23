#!/usr/bin/python

import atexit
import os
import shutil
import subprocess
import time
from argparse import ArgumentParser, Namespace
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
    except os.error:
        error("Error: Failed to copy " + src + " to " + dst)
        return False
    return True


def cd(dst: str) -> bool:
    try:
        os.chdir(dst)
    except os.error:
        error("Error: Failed to change directory to " + dst)
        return False
    return True


# ----------------------------------------------------------------------------


class Dir:
    def __init__(self, path: str) -> None:
        self.path = path


class TempDir:
    def __init__(self) -> None:
        temp_dir: str | None = get("mktemp", "-d")
        self.good = temp_dir != None
        self.path = str(temp_dir)
        atexit.register(self.cleanup)

    def cleanup(self) -> None:
        if self.good:
            remove(self.path)
            self.good = False


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

    def build(
        self,
        dep_handler: Callable[[str], bool],
        makepkg_env: Dict[str, str],
        install: bool = False,
        check_deps: bool = True,
    ) -> bool:
        # Get package name
        name = get(
            "bash",
            "-ec",
            "source " + self.build_dir.path + "/PKGBUILD; echo $pkgname;",
        )
        if name == None:
            error("Error: Failed to read package name")
            return False
        name = str(name)

        # Get required package dependencies
        dependencies_str = get(
            "bash",
            "-ec",
            "source " + self.build_dir.path + "/PKGBUILD;"
            "echo ${makedepends[@]%:*};"
            "echo ${checkdepends[@]%:*};"
            "echo ${depends[@]%:*};",
        )
        if dependencies_str == None:
            error("Error: Failed to read the required package dependencies")
            return False
        dependencies = str(dependencies_str).split()

        # Get optional package dependencies
        optional_dependencies_str = get(
            "bash",
            "-ec",
            "source " + self.build_dir.path + "/PKGBUILD; echo ${optdepends[@]%:*};",
        )
        if optional_dependencies_str == None:
            error("Error: Failed to read the optional package dependencies")
            return False
        optional_dependencies = str(optional_dependencies_str).split()

        # Handle required package dependencies
        for dep in dependencies:
            if not dep_handler(dep):
                error("Error: Failed to handle dependency for: " + name)
                return False

        # Handle required package dependencies
        for dep in optional_dependencies:
            if not dep_handler(dep):
                error("Error: Failed to handle optional dependency for: " + name)

        # makepkg requires that the PKGBUILD be in the working directory.
        if not cd(self.build_dir.path):
            return False

        # Optional extra arguments for makepkg
        extra_args: List[str] = []
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
            *extra_args,
            quiet=False,
            env=makepkg_env,
        ):
            error("Error: Failed to build package: " + name)
            return False

        return True


class PackageRepoMaker:
    def __init__(
        self, dst: str, db_dir: str, local_packages_dir: str, packager: str
    ) -> None:
        self.dst = dst
        if not os.path.exists(self.dst):
            os.makedirs(self.dst)

        self.packager = packager
        self.local_packages_dir = local_packages_dir

        self.added_packages: Dict[str, bool] = {}

        self.dbpath = db_dir
        if not os.path.exists(self.dbpath):
            os.makedirs(self.dbpath)

        # Update the system-wide package database so dependencies can be installed.
        self.good = self._pacman("-Sy")

        # Populate a fresh package database for use when downloading packages.
        if self.good:
            self.good = self._fresh_pacman("-Sy")

    def _pacman(self, *args, quiet: bool = False) -> bool:
        return run("sudo", "pacman", "--noconfirm", *args, quiet=quiet)

    def _fresh_pacman(self, *args, quiet: bool = False) -> bool:
        return run(
            "sudo",
            "pacman",
            "--cache",
            self.dst,
            "--dbpath",
            self.dbpath,
            "--noconfirm",
            *args,
            quiet=quiet,
        )

    def _is_already_added(self, package: str) -> bool:
        return package in self.added_packages

    def _is_already_installed(self, package: str) -> bool:
        return self._pacman("-Qi", package, quiet=True)

    def _is_official_package_addable(self, package: str) -> bool:
        return self._fresh_pacman("-Sp", package, quiet=True)

    def _is_official_package_installable(self, package: str) -> bool:
        return self._pacman("-Sp", package, quiet=True)

    def _add_official_package(self, package: str) -> bool:
        result: bool = self._fresh_pacman("-Sw", package)
        if result:
            self.added_packages[package] = True
        return result

    def _install_official_package(self, package: str) -> bool:
        return self._pacman("-S", package)

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

    def _get_aur_package(self, package: str, install: bool = False) -> bool:
        package_builder = PackageBuilder()
        if not package_builder.good:
            error("Error: Failed to initialize the packager for: " + package)
            return False

        if not package_builder.download(
            "https://aur.archlinux.org/" + package + ".git"
        ):
            error("Error: Failed to download package recipe for: " + package)
            return False

        cache_dir: str = package_builder.build_dir.path if install else self.dst
        makepkg_env = self._get_makepkg_env(package_builder.build_dir.path, cache_dir)

        result: bool = package_builder.build(
            self.add_package_dependency, makepkg_env, install=install
        )
        if result and not install:
            self.added_packages[package] = True
        return result

    def _is_local_package(self, package: str) -> bool:
        return os.path.isdir(self.local_packages_dir + "/" + package)

    def _get_local_package(self, package: str, install: bool = False) -> bool:
        package_builder = PackageBuilder(
            recipe_dir=self.local_packages_dir + "/" + package,
        )
        if not package_builder.good:
            error("Error: Failed to initialize the packager for: " + package)
            return False

        cache_dir: str = package_builder.build_dir.path if install else self.dst
        makepkg_env = self._get_makepkg_env(package_builder.build_dir.path, cache_dir)

        result: bool = package_builder.build(
            self.add_package_dependency,
            makepkg_env,
            install=install,
            check_deps=False,
        )
        if result and not install:
            self.added_packages[package] = True
        return result

    def install_dependency(self, package: str) -> bool:
        if self._is_already_installed(package):
            return True

        # Search the official package repositories (or wherever /etc/pacman.conf tells pacman to look).
        if self._is_official_package_installable(package):
            return self._install_official_package(package)

        # Search the AUR.
        if self._is_aur_package(package):
            return self._get_aur_package(package, install=True)

        # Search the local package directory.
        if self._is_local_package(package):
            return self._get_local_package(package, install=False)

        error("Error: Failed to resolve package: " + package)
        return False

    def add_package_dependency(self, package: str) -> bool:
        sub_event(package)
        if not self.install_dependency(package):
            error("Error: Failed to install dependency: " + package)
            return False
        return self.add_package(package)

    def add_package(self, package: str) -> bool:
        if self._is_already_added(package):
            return True

        # Search the official package repositories (or wherever /etc/pacman.conf tells pacman to look).
        if self._is_official_package_addable(package):
            return self._add_official_package(package)

        # Search the AUR.
        if self._is_aur_package(package):
            return self._get_aur_package(package)

        # Search the local package directory.
        if self._is_local_package(package):
            return self._get_local_package(package)

        error("Error: Failed to resolve package: " + package)
        return False

    def make_repo(self, name: str) -> bool:
        # Accumulate all packages into a list.
        packages: List[str] = []
        for file in os.listdir(self.dst):
            file_path = self.dst + "/" + file
            if not os.path.isfile(file_path):
                continue
            if not file.endswith(".pkg.tar.zst"):
                continue
            packages.append(file_path)

        # Make an offline package repository.
        if not run(
            "repo-add",
            self.dst + "/" + name + ".db.tar.zst",
            *packages,
            quiet=False,
        ):
            error("Error: Failed to make repo")
            return False

        return True


def make_repo(
    name: str,
    packager: str,
    packages: List[str],
    dst: str,
    db_dir: str,
    local_packages_dir: str,
) -> bool:
    repo = PackageRepoMaker(dst, db_dir, local_packages_dir, packager)
    if not repo.good:
        error("Error: Failed to initialize a fresh package repository")
        return False

    for pack in packages:
        event(pack)
        if not repo.add_package(pack):
            return False

    return repo.make_repo(name)


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

    # Declare paths relative to the initial working directory.
    work_dir: str = os.getcwd()
    local_packages_dir: str = work_dir + "/local_packages"
    profile_dir: str = work_dir + "/profile"
    db_dir: str = work_dir + "/offline_db"
    offline_repo_dir: str = profile_dir + "/airootfs/offline"

    live_iso_packages: Optional[str] = get("cat", profile_dir + "/packages.x86_64")
    if not live_iso_packages:
        error("Error: Failed to get the list of packages installed on the live ISO.")
        quit(1)

    # Which additional packages are being added to the repository?
    extra_packages: list[str] = ["moos", "moos-xorg", "moos-sshd-conf"]

    # Construct a list of all packages to add to the repository.
    packages: list[str] = extra_packages
    for pkg in live_iso_packages.split():
        if pkg not in packages:
            packages.append(pkg)

    # Make a package repository containing the specified packages and place it in the profile directory.
    if not make_repo(
        name=package_repo_name,
        packager=packager,
        packages=packages,
        dst=offline_repo_dir,
        db_dir=db_dir,
        local_packages_dir=local_packages_dir,
    ):
        quit(1)

    quit(0)
