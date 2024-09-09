#!/usr/bin/bash

success() {
    echo -e "\e[32;1m$1\e[0m"
}

error() {
    echo -e "\e[31;1mError: $1.\e[0m"
}

THIS_DIR=$(pwd)
WORK_DIR="$THIS_DIR/.work"
PROFILE_DIR="$THIS_DIR/profile"

pacman_conf() {
    echo "[options]"
    echo "HoldPkg = pacman glibc"
    echo "Architecture = auto"
    echo "SigLevel = Never"
    echo ""
    echo "[offline]"
    echo "Server = file://$PROFILE_DIR/airootfs/offline/"
    echo ""
    echo "[core]"
    echo "Include = /etc/pacman.d/mirrorlist"
    echo ""
    echo "[extra]"
    echo "Include = /etc/pacman.d/mirrorlist"
}

if ! pacman_conf > "$PROFILE_DIR/pacman.conf"; then
    error "Failed to generate custom pacman.conf"
    exit 1
fi

AUTO_MOOS_DIR="$PROFILE_DIR/airootfs/root/.auto_moos/"
if ! mkdir -p "$AUTO_MOOS_DIR" && cp "$THIS_DIR/packages" "$AUTO_MOOS_DIR/packages"; then
    error "Failed to create the packages file for auto_moos"
    exit 1
fi

if ! sudo mkarchiso -v -r -w "$WORK_DIR" -o "$THIS_DIR" "$PROFILE_DIR"; then
    error "ISO construction failed"
    exit 1
fi

success "ISO construction succeeded"
exit 0
