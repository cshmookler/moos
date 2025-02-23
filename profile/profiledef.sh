#!/usr/bin/env bash

iso_name="moos"
iso_publisher="Caden Shmookler <https://github.com/cshmookler>"
iso_application="MOOS"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m%d)"
iso_label="$iso_application"_"$iso_version"
install_dir="moos"
buildmodes=('iso')
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito'
           'uefi-ia32.grub.esp' 'uefi-x64.grub.esp'
           'uefi-ia32.grub.eltorito' 'uefi-x64.grub.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="erofs"
# airootfs_image_tool_options=('-zlzma,109' -E 'ztailpacking')
# bootstrap_tarball_compression=(zstd -c -T0 --long -19)
bootstrap_tarball_compression=(zstd -c -T0)
file_permissions=(
  ["/etc/shadow"]="0:0:400"
)
