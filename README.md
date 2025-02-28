# The Mouse-Optional Operating System (MOOS)

A modern operating system that keeps your hands on the keyboard. Based on Arch Linux.

## Releases

Releases will be available after version 1.0.0. For now, follow the instructions below to manually build from source.

## Build from source

An existing MOOS or Arch Linux installation is required to build a MOOS live ISO from source.

### 1.&nbsp; Install the following required packages on your existing installation

```bash
sudo pacman -S base-devel archiso git python
```

### 2.&nbsp; Register your name and email with Git

Some packages may need to be built from scratch using makepkg. Your name and email are used to identify you as the packager.

> Note: Change "FirstName LastName" and "email@example.com" with your real name and email before running these commands.

```bash
git config set user.name "FirstName LastName"
git config set user.email "email@example.com"
```

### 3.&nbsp; Clone this repository with Git

```bash
git clone https://github.com/cshmookler/moos.git
cd moos
```

### 4.&nbsp; Make the offline package repository

The installer built into the MOOS live ISO is capable of working entirely offline. All necessary packages must be downloaded in advance and placed within the filesystem of the live ISO.

```bash
./make_offline_repo.py
```

### 5.&nbsp; Make the live ISO

```bash
./make_iso.sh
```

### 6.&nbsp; Troubleshooting

A discrepancy between packages installed globally on your system and the version placed into the offline repository may cause the 'make_iso.sh' script to fail.

#### Example:

```
:: File /var/cache/pacman/pkg/moos-filesystem-2024.09.14-1-any.pkg.tar.zst is corrupted (invalid or corrupted package (checksum)).
Do you want to delete it? [Y/n] 
:: File /var/cache/pacman/pkg/yay-12.4.2-1-x86_64.pkg.tar.zst is corrupted (invalid or corrupted package (checksum)).
Do you want to delete it? [Y/n] 
:: File /var/cache/pacman/pkg/neovim-symlinks-5-1-any.pkg.tar.zst is corrupted (invalid or corrupted package (checksum)).
Do you want to delete it? [Y/n] 
:: File /var/cache/pacman/pkg/moos-cpp-result-1.1.2-1-any.pkg.tar.zst is corrupted (invalid or corrupted package (checksum)).
Do you want to delete it? [Y/n] 
:: File /var/cache/pacman/pkg/moos-system-state-0.23.0-1-any.pkg.tar.zst is corrupted (invalid or corrupted package (checksum)).
Do you want to delete it? [Y/n] 
:: File /var/cache/pacman/pkg/moos-us-keys-tty-20250222-1-any.pkg.tar.zst is corrupted (invalid or corrupted package (checksum)).
Do you want to delete it? [Y/n] 
:: File /var/cache/pacman/pkg/moos-run-20241106-1-any.pkg.tar.zst is corrupted (invalid or corrupted package (checksum)).
Do you want to delete it? [Y/n] 
:: File /var/cache/pacman/pkg/moos-20250222-1-any.pkg.tar.zst is corrupted (invalid or corrupted package (checksum)).
Do you want to delete it? [Y/n] 
error: failed to commit transaction (invalid or corrupted package)
Errors occurred, no packages were upgraded.
==> ERROR: Failed to install packages to new root
Error: ISO construction failed.
```

#### Fix:

Delete the 'work' directory.

```bash
sudo rm -rf work
```

Re-run the 'make_iso.sh' script.  The issue should resolve itself.

```bash
./make_iso.sh
```

## **TODO**

- [X] Automatically setup the user environment.
- [X] Setup firefox and install extensions.
- [X] Add a default neovim configuration.
- [X] Allow remote login through SSH in the live ISO.
- [X] Automatically create a hotspot when running in headless mode.
- [ ] Remove screen flicker when the screen is locked.
- [X] Install virtual machine utilities.
- [ ] Enable the firewall.
- [ ] Enable speach synthesis in Firefox.
- [ ] Resolve issues with Zoom (cannot annotate and screen randomly turns black)
- [ ] Improve documentation.
- [ ] Replace pulseaudio with pipewire.
- [ ] Replace Xorg with Wayland.
- [ ] Provide options for other languages (aside from English).
