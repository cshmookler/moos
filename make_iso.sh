#!/usr/bin/env bash

success() {
    echo -e "\e[32;1m$1\e[0m"
}

error() {
    echo -e "\e[31;1mError: $1.\e[0m"
}

THIS_DIR=$(pwd)
PROFILE_DIR="$THIS_DIR/profile"
WORK_DIR="$THIS_DIR/work"
OUT_DIR="$THIS_DIR/out"

_pacman_conf() {
    echo "[options]"
    echo "HoldPkg = pacman glibc"
    echo "Architecture = auto"
    echo "SigLevel = Never"
    echo ""
    echo "[offline]"
    echo "Server = file://$PROFILE_DIR/airootfs/offline/"
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

_sshd_conf() {
    echo "Port $_sshd_port"
    echo "PermitRootLogin yes"
    echo "PasswordAuthentication yes"
    echo "PermitEmptyPasswords yes"
}

if ! _sshd_conf > "$PROFILE_DIR/airootfs/etc/ssh/sshd_config.d/10-moosiso.conf"; then
    error "Failed to generate custom pacman.conf"
    exit 1
fi

_hotspot_password=$(tr -dc '[:graph:]' </dev/urandom | head -c 10)

_hotspot_conf() {
    echo "[Unit]"
    echo "Description=Create a WiFi hotspot (Access Point) with NetworkManager"
    echo "Requires=NetworkManager.service"
    echo "After=NetworkManager.service"
    echo ""
    echo "[Service]"
    echo "Type=oneshot"
    echo "ExecStart=/usr/bin/env bash -c '(nmcli connection show moos-hotspot && nmcli connection delete moos-hotspot) || true'"
    echo "ExecStart=/usr/bin/env bash -c 'nmcli device wifi hotspot con-name moos-hotspot ssid moos-live password \"$_hotspot_password\"'"
    echo "ExecStart=/usr/bin/env bash -c 'nmcli connection modify moos-hotspot connection.autoconnect yes'"
    echo "ExecStart=/usr/bin/env bash -c 'nmcli connection modify moos-hotspot ipv4.addresses 10.0.0.1/24'"
    echo "ExecStart=/usr/bin/env bash -c 'nmcli connection up moos-hotspot'"
    echo ""
    echo "[Install]"
    echo "WantedBy=multi-user.target"
}

if ! _hotspot_conf > "$PROFILE_DIR/airootfs/etc/systemd/system/moos-hotspot.service"; then
    error "Failed to generate custom pacman.conf"
    exit 1
fi

if ! sudo mkarchiso -v -r -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE_DIR"; then
    error "ISO construction failed"
    exit 1
fi

echo "$_hotspot_password" | sudo tee "$OUT_DIR/hotspot_password"
echo "$_sshd_port" | sudo tee "$OUT_DIR/ssh_port"

success "ISO construction succeeded"
success "WiFi Hotspot Password: $_hotspot_password"
success "SSH Port: $_sshd_port"

exit 0
