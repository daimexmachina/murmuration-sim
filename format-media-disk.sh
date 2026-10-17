#!/usr/bin/env bash
# format-media-disk.sh — DESTRUCTIVE. Erases the Samsung T7 Shield (/dev/sda)
# and creates a fresh GPT + single full-disk exFAT partition labelled MEDIA.
#
# Run this YOURSELF in a terminal on the Pi:
#     sudo bash /home/daim/workspace/format-media-disk.sh
#
# It refuses to run unless /dev/sda is the expected Samsung PSSD T7 Shield,
# and unless every partition is unmounted. Double-check the serial below
# against the drive in your hand before typing YES.
#
set -euo pipefail

DISK=/dev/sda
EXPECT_MODEL="PSSD T7 Shield"
LABEL=MEDIA

die(){ echo "ABORT: $*" >&2; exit 1; }
[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root: sudo bash $0"

# ---- identify & verify -------------------------------------------------
[[ -b $DISK ]] || die "$DISK is not a block device"
MODEL=$(lsblk -dno MODEL "$DISK" | xargs)
SERIAL=$(lsblk -dno SERIAL "$DISK" | xargs)
SIZE=$(lsblk -dno SIZE "$DISK" | xargs)
echo "Target: $DISK  model='$MODEL'  serial='$SERIAL'  size=$SIZE"
[[ "$MODEL" == "$EXPECT_MODEL" ]] || die "model '$MODEL' != expected '$EXPECT_MODEL'"

# never touch a disk that backs / , /boot or /mnt/recovery
for m in / /boot/firmware /mnt/recovery; do
  src=$(findmnt -no SOURCE --target "$m" 2>/dev/null || true)
  case "$src" in *"$DISK"*) die "$DISK backs $m";; esac
done

# ---- unmount everything on it -----------------------------------------
for p in "$DISK"?*; do
  [[ -e $p ]] || continue
  if findmnt -no TARGET "$p" >/dev/null 2>&1; then
    echo "unmounting $p"; umount "$p" || die "could not unmount $p"
  fi
done
lsblk -no MOUNTPOINT "$DISK" | grep -q . && die "still mounted"
echo "not mounted -> OK"

# ---- confirm -----------------------------------------------------------
cat <<EOF

  !! THIS WILL ERASE EVERYTHING ON $DISK ($SIZE, serial $SERIAL) !!
  Partition table -> GPT
  Single partition -> exFAT, label "$LABEL" (readable on macOS + the Pi)

EOF
read -rp 'Type ERASE-MEDIA to continue: ' a
[[ $a == ERASE-MEDIA ]] || die "typed '$a', not ERASE-MEDIA"

# ---- do it -------------------------------------------------------------
echo "> wipefs";  wipefs -a "$DISK"
echo "> mklabel gpt"; parted -s "$DISK" mklabel gpt
echo "> mkpart";      parted -s "$DISK" mkpart "$LABEL" 1MiB 100%
udevadm settle; sleep 2
# settle the node name (usually sda1)
PART=$(lsblk -rno NAME,TYPE "$DISK" | awk '$2=="part"{print "/dev/"$1; exit}')
[[ -b $PART ]] || die "partition node not found"
echo "> mkfs.exfat -L $LABEL  $PART"
mkfs.exfat -L "$LABEL" "$PART"
sync
udevadm settle

echo
echo "=== DONE ==="
blkid "$PART"
lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID "$DISK"
echo
echo "Tell Hermes it's formatted and he'll mount it at /srv/media and wire up the Jellyfin library."
