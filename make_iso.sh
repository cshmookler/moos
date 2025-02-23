#!/usr/bin/bash

success() {
    echo -e "\e[32;1m$1\e[0m"
}

error() {
    echo -e "\e[31;1mError: $1.\e[0m"
}

THIS_DIR=$(pwd)
PROFILE_DIR="$THIS_DIR/profile"
WORK_DIR="$THIS_DIR/build/work"
OUT_DIR="$THIS_DIR/build"

_pacman_conf() {
    echo "[options]"
    echo "HoldPkg = pacman glibc"
    echo "Architecture = auto"
    echo "SigLevel = Never"
    echo "ParallelDownloads = 5"
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

if ! _pacman_conf > "$PROFILE_DIR/pacman.conf"; then
    error "Failed to generate custom pacman.conf"
    exit 1
fi

_random() {
    value=''
    for i in {1..9}; do
        value="$((RANDOM % 10))$value"
    done
    echo $value
}

_sshd_port=$(((10#$(_random) % 50000) + 10000))

_sshd_config() {
    echo "Port $_sshd_port"
    echo "PermitRootLogin yes"
    echo "PasswordAuthentication yes"
    echo "PermitEmptyPasswords yes"
}

if ! _sshd_config > "$PROFILE_DIR/airootfs/etc/ssh/sshd_config.d/10-archiso.conf"; then
    error "Failed to generate custom pacman.conf"
    exit 1
fi

if ! sudo mkarchiso -v -r -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE_DIR"; then
    error "ISO construction failed"
    exit 1
fi

success "ISO construction succeeded"
success "SSH Port: $_sshd_port"
exit 0
