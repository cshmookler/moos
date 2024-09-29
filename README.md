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

## **TODO**

- [X] Automatically setup the user environment.
- [X] Setup firefox and install extensions.
- [X] Add a default neovim configuration.
- [ ] Remove screen flicker when the screen is locked.
- [ ] Install virtual machine utilities.
- [ ] Enable the firewall.
- [ ] Enable speach synthesis in Firefox.
- [ ] Resolve issues with Zoom (cannot annotate and screen randomly turns black)
- [ ] Improve documentation.
- [ ] Replace pulseaudio with pipewire.
- [ ] Replace Xorg with Wayland.
- [ ] Provide options for other languages (aside from English).
