# Wireless Stick (SWDS4)

> [!NOTE]
> Not to be confused with [Wireless Flash Drive (SDWS2)](../wireless_flash_drive/) devices which has a replacable microSD card slot from outside. This Wireless Stick (SWDS4) doesn't have that.

Even though you can't replace its storage from outside on these devices, [this device actually contains a "removable" microSD card too](https://web.archive.org/web/20210126233130/https://preview.redd.it/y390ycfsjod61.jpg?width=4624&format=pjpg&auto=webp&s=50927e151b107c5ff2cf0c6ae8623729c17fc117) (from this [archived Reddit post](https://web.archive.org/web/20240920191647/https://old.reddit.com/r/a:t5_29c4wc/comments/l5e41c/sandisk_sdws4064gg46_connect_wireless_stick/)) (also [these internal photos from FCC](https://fccid.io/R4V-SDWS4/Internal-Photos/Internal-photos-2663499.pdf)) plugged in the slot found on the board. Note the "Ultra Plus" branding, which is separate from regular known "Ultra" branded cards. I will talk more about the potential of replacing the microSD card later. 

The microSD is not accessible from the outside, so you will need to disassemble the drive to access the card after removing the upper layer sticked on the board. Then to take out the card, press onto it and slide to the direction where the flash drive's USB is currently pointing.

Since it is a valid use case to reformat the drive (it is still a flash drive at the end of the day), it won't end up wiping the firmware on the device so it very likely that the ROM runs off on its internal onboard flash, the microSD card only contains files you put in it.

See also [this topic on Hak5 forums about this device.](https://forums.hak5.org/topic/30273-hack-a-sandisk-32g-wifi-enabled-flash-drive/)

The category for Wireless Stick devices does still exists on [official Sandisk Forums.](https://forums.sandisk.com/c/wireless-memory/sandisk-connect-wireless-stick/195) as of writing this.

## Managing the drive

In factory settings, the device does broadcast an Wi-Fi access point with no password, once you connect to it, you can change the SSID and password as you like.

Sandisk recommends using its official app to manage the drive; however, this is more for convenience than out of necessity, and, the app is already no longer available so once you've found the HTTP endpoints, you won't have any need in the official app other than its GUI.

And the drive even contains a web interface to browse the files in it, you can just visit the gateway IP of the device, which should be `172.25.63.1`. Not only that, it implements WebDAV commands as a way of managing the files, (`dav://172.25.63.1/files`) which however is [not full compliant](https://github.com/iterate-ch/cyberduck/issues/7902). Trying to be a little quick while browsing files over WebDAV usually ended with connection refused errors for me, so better to wait for the device until file operations gets completed before starting another operation. 

The device generates thumbnails of the media that are uploaded and has a sort of cache of it, so uploading large media might cause issues too.

At the same time, you can access files only over Wi-Fi or only over USB. If the drive gets plugged in a USB port of a computer for example (through mass storage), it stops serving files & streaming over Wi-Fi, and will give "no card inserted" error message (even if it still has a microSD inserted in it) when visiting the web interface.

Device configuration can be retrieved by sending a HTTP GET request to `/settings.xml`. That is the same endpoint that the official mobile app uses to send and receive configuration of the device.

Setting configuration is done by sending a HTTP POST request to the same path, encoded in form data. Though, the accepted parameters are very limited, see the provided [`sandisk_wireless_config.py` script](./sandisk_wireless_config.py) to retrieve or/and manage the device settings without needing to use the old discontinued official app.

```python
from sandisk_wireless_config import *

drive = WirelessDrive("172.25.63.1")
settings = drive.get_settings()
print(settings)
```

## The infamous Sandisk Ultra Plus card

I've tried replacing the microSD card of the device with few other microSD cards that I have (from Sandisk or from another brand) but none of them has worked, the device just "fails" to boot with some LED sequence. Setting volume serial number and cloning partitions didn't work either, so I presume the device is very picky about the model of the microSD card and does only accept that specific "Ultra Plus" microSD that it came with it.

My initial thought was if that Ultra Plus card was manufactured only for this device and not to be sold to end user, knowing I haven't come across to that card ever before, but it turns [out that it can be bought](https://web.archive.org/web/20260414172946/https://www.target.com/p/sandisk-ultra-plus-128gb-microsd-memory-card/-/A-50582292), so might be exclusive to specific countries/regions then.

There is also [this Reddit post](https://www.reddit.com/r/a:t5_32was/comments/8n6r9u/sandisk_connect_wireless_stick_newer_edition_sd/) posted years ago asking how to replace the microSD card of this device but got no helpful replies.

So that made me think if it is checking for [CID](https://www.cameramemoryspeed.com/sd-memory-card-faq/reading-sd-card-cid-serial-psn-internal-numbers/) instead, therefore I got the CID of the card that the device came with and an regular non-Plus Ultra card that I already have:

```
$ cat /sys/block/mmcblk1/device/cid
```

Above command only works if your computer has a built-in SD card slot, USB readers won't expose the lower level interface of SD cards.

* Sandisk Ultra Plus 32 GB (that included in Wireless Stick): `035344534c33324780f4e525dd00fc00`
* Sandisk Ultra 32 GB (that I already had): `035344534c333247805d45110f011900`

Linux reported CID with checksum field zero-ed out for me, because the last byte is supposed to be a [CRC7 checksum](https://my-cool-projects.blogspot.com/2013/06/sd-card-crc-algorithm-explained-in.html) rather than `0x00`.

## Factory reset

To reset settings to factory default values, turn the Wireless Stick off, and press and hold the power button down for about 15 seconds. The LED then should flash red and green while it is resetting.

Factory resetting the drive doesn't reformat the storage, but all internet related settings will be reset to default values. Resetting will not wipe or change the firmware.

## Crashes & soft-bricks

Setting invalid configuration may crash or softbrick the device, however the device can be recovered from the both just fine. For crashes, the device just reboots itself and it will store its error reason in `storederror` element in settings XML if booting succeded.

However, I've found a way to render the device not being able to boot. It turns out setting power sleep timeout to larger than 32-bit integer upper limit makes the device crash and ending up not being able to boot properly since it couldn't recover itself from that. It only did rapidly blink white LED and shutdown immediately, and continued to do the same in each time the device powered on. But as I've mentioned, it is still possible to save the device from this state by just factory resetting the settings by holding the power button until you see a green LED. Factory resetting won't cause your files being formatted, files inside the drive does stay intact.

## Firmwares

Some firmware versions are already [archived](https://web.archive.org/web/*/http://downloads.sandisk.com/firmware/ws/*) on Archive.org, this device uses `.DF3` files specifically, there are also `.DF2` files archived which is only for [Wireless Flash Drive (SDWS2)](../wireless_flash_drive/) devices, **not for this one!**

The Android app made for this drive (`com.sandisk.connect`) also bundles the firmware files inside the APK too (in resources folder: `/res/raw`), so you can extract firmwares from it if you still have that app installed on your phone.

```
$ 7z e -bso0 -o"output" "sandisk.apk" "res/raw/*.df3"
```

Here are the direct Archive.org links of firmwares:

* [`wfd2034s.df3`](https://web.archive.org/web/20250707144819if_/http://downloads.sandisk.com/firmware/connectv2/wfd2034s.df3)
* [`wfd2034e.df3`](https://web.archive.org/web/20250707144829if_/http://downloads.sandisk.com:80/firmware/connectv2/wfd2034e.df3)
* [`wfd2038s.df3`](https://web.archive.org/web/20200110172035if_/http://downloads.sandisk.com:80/firmware/ws/wfd2038s.df3)
* [`wfd2038e.df3`](https://web.archive.org/web/20160224193922if_/http://downloads.sandisk.com:80/firmware/ws/wfd2038e.df3)
* [`wfd2050s.df3`](https://web.archive.org/web/20160515082212if_/http://downloads.sandisk.com/firmware/ws/wfd2050s.df3)
* [`wfd2050e.df3`](https://web.archive.org/web/20160515082212if_/http://downloads.sandisk.com/firmware/ws/wfd2050e.df3)

### Knowing the right file

Sandisk claims these firmware variants are not interchangeable, so **only use the firmware variant** that matches with the capacity of the drive you have:

* 16/32 GB models has this firmware file naming: `wfd2050s.df3`
* 64 GB and upper models has this firmware file naming: `wfd2050e.df3` (note the `e` suffix for `exFAT` instead of `s`)

64 GB and higher variants has exFAT support, assuming due to exFAT license fee, so there are exFAT and non-exFAT variants of the same firmware version.

For 16/32 GB variants, the drive comes with FAT32 formatted out-of-box instead and **doesn't have exFAT support.**

I don't know what happens if you try to flash a exFAT-supported firmware to a non-exFAT supporting model, I didn't want to risk it, so you are on your own if you want to try that, but I would recommend against it.

### Reverse engineering

I couldn't manage the decode the firmware file in full, some I don't know the meaning of most of the bytes inside it, but from what I've gathered so far, it is possible to unpack the assets that used in its web server, but nothing noteworthy other than that.

See [`sandisk_wireless_df3.py` script](./sandisk_wireless_df3.py) for more details. It can be run from terminal as a CLI program.

```bash
# To only analyze the firmware and validate it without doing anything more
python3 sandisk_wireless_df3.py ./wfd2050s.df3

# Dumps the firmware contents to a non-existing directory.
python3 sandisk_wireless_df3.py ./wfd2050s.df3 --dump dumped_contents

# Un-dumps the firmware contents from an already dumped directory to a new firmware file.
# If directory contents weren't changed, it should end up repacking the firmware which is 1:1 same with the input firmware.
# The original firmware is still required since there are metadata and other raw flash blocks needs to be carried over.
python3 sandisk_wireless_df3.py ./wfd2050s.df3 --dump dumped_contents --output new_firmware.df3
```

Thanks to [this post](https://forums.hak5.org/topic/41479-sandisk-wireless-connect-16g-flash-drive/) ([archive 1](https://web.archive.org/web/20250409165759/https://forums.hak5.org/topic/41479-sandisk-wireless-connect-16g-flash-drive/), [archive 2](https://archive.md/NTENm)) who published an AutoIt script to unpack files in `.DF3` firmwares.

### Upgrade instructions

_Firmware upgrade instructions written below can also be found on this archived [Sandisk Support page](https://web.archive.org/web/20160515082212/http://kb.sandisk.com/app/answers/detail/a_id/17556):_

Make sure you have the [right firmware version](#knowing-the-right-file) first!

To flash a firmware, copy the firmware file and put it in the root of the device, and eject it from your computer. Once it has started to install, LEDs should flash rapidly. Make sure that the device has sufficient battery power during flashing to avoid permanent damage.

Flashing firmwares can also be triggered by sending a HTTP PUT request to `/settings.xml?group=firmware` with the firmware file as request body. During flashing, the device will alternate between blue and white LED. If flashing was failed (invalid firmware), it will be reverted, and the device will blink red LED while it is still on and continue to run normally. Rebooting the device will clear the blinking red LED.