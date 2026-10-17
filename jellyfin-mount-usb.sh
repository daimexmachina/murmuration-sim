#!/usr/bin/env bash
# jellyfin-mount-usb.sh — attach a USB disk as the Jellyfin media library at /srv/media.
#
# Usage:
#   ./jellyfin-mount-usb.sh --list                  # show candidate USB disks (no root needed)
#   sudo ./jellyfin-mount-usb.sh --device /dev/sda1 # mount an existing filesystem (non-destructive)
#   sudo ./jellyfin-mount-usb.sh --device /dev/sda1 --format --yes   # FORMAT as ext4 (label MEDIA) then mount
#   sudo ./jellyfin-mount-usb.sh --unmount          # unmount and remove the managed fstab entry
#
# What it does:
#   1. Picks the USB disk (auto-detects if exactly one; --device overrides).
#   2. Refuses to touch the root / boot / recovery devices.
#   3. (--format only) makes a fresh ext4 filesystem labelled MEDIA.
#   4. Reads the filesystem UUID and writes an idempotent, nofail fstab entry.
#   5. daemon-reload, mount -a, verifies, and recreates movies/tv/music/photos owned by daim.
#
set -euo pipefail

MOUNTPOINT=/srv/media
LABEL=MEDIA
FSTYPE=ext4
MARK="jellyfin-media (managed by jellyfin-mount-usb.sh)"
FSTAB=/etc/fstab

die(){ echo "ERROR: $*" >&2; exit 1; }
need_root(){ [[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root: sudo $0 $*"; }

cmd_list(){
  echo "== USB disks =="
  lsblk -o NAME,SIZE,TYPE,TRAN,FSTYPE,LABEL,MOUNTPOINT | awk 'NR==1||/usb/'
  echo
  echo "== all block devices =="
  lsblk -o NAME,SIZE,TYPE,TRAN,FSTYPE,LABEL,MOUNTPOINT
}

find_dev(){
  # shellcheck disable=SC2016
  local devs
  devs=$(lsblk -rno NAME,TRAN,TYPE | awk '$2=="usb" && $3=="disk"{print $1}')
  mapfile -t arr < <(printf '%s\n' "$devs" | sed '/^$/d')
  (( ${#arr[@]}==1 )) || die "found ${#arr[@]} USB disks; pass --device /dev/sdXN (see --list)"
  echo "/dev/${arr[0]}"
}

is_protected(){
  local base; base=$(lsblk -rno PKNAME "$1" 2>/dev/null | head -1)
  local name=$1
  [[ -n $base ]] && name=/dev/$base
  # never touch whatever backs /, /boot, or /mnt/recovery
  for m in / /boot/firmware /mnt/recovery; do
    local src; src=$(findmnt -no SOURCE --target "$m" 2>/dev/null || true)
    case "$src" in *"$name"*) return 0;; esac
  done
  return 1
}

cmd_unmount(){
  need_root "$@"
  sudo -n true 2>/dev/null || true
  if mountpoint -q "$MOUNTPOINT"; then umount "$MOUNTPOINT"; fi
  if grep -qF "$MARK" "$FSTAB"; then
    cp -a "$FSTAB" "${FSTAB}.bak.$(date +%s)"
    sed -i "\|$MARK|d" "$FSTAB"
    echo "removed managed fstab entry"
  fi
  systemctl daemon-reload
  echo "done"
}

main(){
  local dev="" do_format=0 assume_yes=0
  while (( $# )); do
    case "$1" in
      --list) cmd_list; return 0;;
      --unmount) cmd_unmount "$@"; return 0;;
      --device) dev=${2:-}; shift 2;;
      --format) do_format=1; shift;;
      --yes|-y) assume_yes=1; shift;;
      -h|--help) sed -n '2,20p' "$0"; return 0;;
      *) die "unknown arg: $1";;
    esac
  done
  need_root "$@"

  [[ $dev == /dev/* ]] || { dev=$(find_dev); echo "auto-detected: $dev"; }
  [[ -b $dev ]] || die "$dev is not a block device"
  is_protected "$dev" && die "$dev backs the OS; refusing"

  if (( do_format )); then
    if (( ! assume_yes )); then
      read -rp "$dev will be ERASED and formatted ext4. Type ERASE to continue: " a
      [[ $a == ERASE ]] || die "aborted"
    fi
    echo "> mkfs.$FSTYPE -L $LABEL $dev"
    mkfs."$FSTYPE" -F -L "$LABEL" "$dev"
    partprobe "$dev" 2>/dev/null || true
    sleep 1
  fi

  local uuid fstype
  uuid=$(blkid -s UUID -o value "$dev" || true)
  fstype=$(blkid -s TYPE -o value "$dev" || true)
  [[ -n $uuid ]] || die "no filesystem/UUID found on $dev (use --format to create one)"
  echo "filesystem: $fstype  uuid=$uuid"

  mkdir -p "$MOUNTPOINT"
  if ! grep -q "UUID=$uuid" "$FSTAB"; then
    cp -a "$FSTAB" "${FSTAB}.bak.$(date +%s)"
    printf 'UUID=%s  %s  %s  defaults,nofail,x-systemd.device-timeout=10,noatime  0 2  # %s\n' \
      "$uuid" "$MOUNTPOINT" "$fstype" "$MARK" >> "$FSTAB"
    echo "added fstab entry"
  else
    echo "fstab entry already present"
  fi

  systemctl daemon-reload
  mount -a
  mountpoint -q "$MOUNTPOINT" || die "mount failed; check 'dmesg' and '$FSTAB'"
  echo "mounted: $dev -> $MOUNTPOINT"
  df -h "$MOUNTPOINT" | tail -1

  mkdir -p "$MOUNTPOINT"/{movies,tv,music,photos}
  chown -R daim:daim "$MOUNTPOINT" 2>/dev/null || true
  echo "library dirs ready:"; ls -la "$MOUNTPOINT"
  echo
  echo "Next: in Jellyfin dashboard add libraries pointing at $MOUNTPOINT/movies, /tv, /music, /photos"
}

main "$@"
