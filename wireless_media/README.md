# Wireless Media (SWDS1)

This might be the most promising one in terms of being hackable, as it has a open telnet access to its Linux shell.

According to [this topic](https://forums.hak5.org/topic/35884-sandisk-wireless-media-drive-root-crackand-other-useful-info/) [(archive)](https://web.archive.org/web/20250715204033/https://forums.hak5.org/topic/35884-sandisk-wireless-media-drive-root-crackand-other-useful-info/), the `root` password isn't secure and too easy to crack already:

```
sqn1351
```

SSH connections seems to be refused by the device, so I haven't be able to spend much time into it about enabling SSH back, until then, we have full access with telnet.

`cat /proc/cpuinfo`:

```
Processor       : ARMv7 Processor rev 5 (v7l)
BogoMIPS        : 799.53
Features        : swp half thumb fastmult vfp edsp neon vfpv3 
CPU implementer : 0x41
CPU architecture: 7
CPU variant     : 0x2
CPU part        : 0xc08
CPU revision    : 5

Hardware        : Freescale MX50 Platform - Nimbus@QSI(WG7311-2A) Ver: 1.1.8
Revision        : 50011
Serial          : 0000000000000000
```

`uname -a`:

```
Linux Media_Drive 2.6.35.3-899-g9b1a262 #18 PREEMPT Tue May 28 14:14:33 CST 2013 armv7l GNU/Linux
```

`ls /sys/devices/platform`:

```
busfreq.0     mc13892_adc.1      mxc_rtc.0  mxc_zq_calib    mxsdhci.0      power
fec.0         mc13892_battery.1  mxc_sdma   mxcintuart.0    mxsdhci.1      reg-fixed-voltage
fsl-ehci.0    mc13892_light.1    mxc_spi.0  mxcintuart.1    mxsdhci.2      regulatory.0
fsl-usb2-otg  mc13892_rtc.1      mxc_spi.2  mxcintuart.2    pmic_leds.103  uevent
fsl-usb2-udc  mx5_pm.0           mxc_ssi.0  mxcpwrkey.0     pmic_leds.114  usb_wakeup.0
fsl_rngc.0    mxc_dvfs_core.0    mxc_ssi.1  mxs-dma-apbh.0  pmic_leds.98
leds-gpio     mxc_pwm.0          mxc_wdt.0  mxs-perfmon.0   pmic_power.1
```

`cat /proc/cmdline`:

```
console=ttymxc0,115200 console=ttymxc0,115200 root=/dev/mmcblk0p2 rootwait rw
```

## Kernel source

Required by GPL license, Sandisk has Linux source code published on [`SanDisk-Open-Source/wireless-media-drive`](https://github.com/SanDisk-Open-Source/wireless-media-drive) repository, though the latest commit saying version `2.9` and the last firmware from Internet Archive being `3.04` might indicate that they violated GPL license [again](https://forums.hak5.org/topic/35884-sandisk-wireless-media-drive-root-crackand-other-useful-info/#comment-262215).

## Firmwares

Internet Archive only has version `3.04` [archived](https://web.archive.org/web/*/http://downloads.sandisk.com/firmware/wmd/*) from Sandisk website, which can be [downloaded here](https://web.archive.org/web/20250610152013*/http://downloads.sandisk.com/firmware/wmd/sandiskmediafirmware-3-04.img).

I also found this version `2.93` mirrored [on this website](https://web.archive.org/web/20260329142753/https://www.touslesdrivers.com/index.php?v_page=23&v_code=42087&v_langue=en) ([archived firmware download here](https://web.archive.org/web/20260329141831/https://fichiers.touslesdrivers.com/42087/sandiskmediafirmware-2-93.img))

### Reverse engineering

The file format is just 152 bytes followed by a standard EXT2 Linux filesystem containing rootfs. See [`sandisk_wireless_wmd.py` script](./sandisk_wireless_wmd.py) to analyze the header. It can be run from terminal as a CLI program.

```bash
# To only analyze the firmware and validate it without doing anything more
python3 sandisk_wireless_wmd.py ./sandiskmediafirmware-3-04.img

# Dumps the EXT2 filesystem image inside firmware to given path. (meaning it will just strip the first 152 bytes)
python3 sandisk_wireless_wmd.py ./sandiskmediafirmware-3-04.img --image ext2_data.img
```

Extracting the firmware is not implemented in the script since EXT2 is already a standard format and can be extracted (with 7zip) & inspected or mounted with various tools.

To mount the firmware file directly in Linux and explore its contents to an existing empty folder, you can tell `mount` command to skip first 152 bytes, so it becomes a valid EXT2 filesystem:

```bash
sudo mount -o loop,offset=152 -t ext2 ./sandiskmediafirmware-3-04.img mount-folder
```

To unmount back:

```bash
sudo umount ./sandiskmediafirmware-3-04.img
# Specifying the path of the mounted directory works too
```