# Wireless Stick (SWDS4)

Unlike [Wireless Flash Drive (SDWS2)](../wireless_flash_drive/), this one doesn't have a external microSD slot to make it easy to swap out the storage, however, this drive doesn't have an on-board flash storage either. Instead, [the device actually contains a removable microSD card](https://old.reddit.com/r/a:t5_29c4wc/comments/l5e41c/sandisk_sdws4064gg46_connect_wireless_stick/) branded "Sandisk Ultra Plus" (not to be confused with regular "Sandisk Ultra" which is being sold in the market) plugged in the slot.

The microSD is not accessible from the outside, so you will need to disassemble the drive to access the card after removing the upper layer sticked on the board. [See internal photos from FCC document.](https://fccid.io/R4V-SDWS4/Internal-Photos/Internal-photos-2663499.pdf) Then to take out the card, press onto it and while continuing to press, slide to the direction where the flash drive's USB is currently pointing to.

It seems that ROM runs off on its internal onboard flash, since the microSD card inside the device only contains the files that you stored on it and has no additional partitions that contains anything about the firmware, so reformatting the drive (same as it is a regular flash drive) is possible and it won't end up wiping the actual ROM running on the device.

At the same time, you can only access files over Wi-Fi or USB. If the drive gets plugged in a USB port of a computer for example (through mass storage), it stops serving files & streaming over Wi-Fi, and will tell "no card inserted" when visiting the web interface.

Aside from accessing files remotely over its discontinued mobile app or web interface, the device has WebDAV support (by using `/files` as a path), but it is [not full compliant](https://github.com/iterate-ch/cyberduck/issues/7902) and may refuse connections due to timeouts from time to time. The device generates thumbnails of the media that are uploaded, so uploading large media might cause issues too.

From what I can tell, the drive is very picky about the microSD card being plugged in, as I've tried with a regular "Sandisk Ultra" microSD by cloning the partitions and cloning the disk serial number but it didn't worked (the device just fails to boot). I didn't have another "Ultra Plus" card (it is also the first time I'm seeing a "Ultra Plus" Sandisk card, perhaps it was produced specifically for this drive and not meant to be sold?) so not sure if that would work. There is also [this Reddit post](https://www.reddit.com/r/a:t5_32was/comments/8n6r9u/sandisk_connect_wireless_stick_newer_edition_sd/) posted years ago asking how to replace the microSD card but got no help.

See also [this topic on Hak5 forums about this device.](https://forums.hak5.org/topic/30273-hack-a-sandisk-32g-wifi-enabled-flash-drive/)

There is still a category dedicated exists for [Wireless Stick on official Sandisk Forums](https://forums.sandisk.com/c/wireless-memory/sandisk-connect-wireless-stick/195).

## Factory reset

To reset settings to factory default values, turn the Wireless Stick off, and press and hold the power button down for about 15 seconds. The LED then should flash red and green while it is resetting. Factory resetting the drive doesn't reformat the storage, but all internet related settings will be reset to default values. Resetting will not change the firmware.

## Web server

Device configuration can be retrieved by sending a HTTP GET request to `/settings.xml`. There is no official schema available for the XML response, but the elements are pretty self-explanatory so their purposes are already known.

Setting configuration is done by sending a HTTP POST request to the same path, encoded in form data. Though, the accepted parameters are very limited, see the provided [`sandisk_wireless_config.py` script](./sandisk_wireless_config.py) to retrieve or/and manage the device settings without needing to use the old discontinued official app.

## Crashes & soft-bricks

Setting invalid configuration may crash or softbrick the device, however the device can be recovered from the both just fine. For crashes, the device just reboots itself and it will store its error reason in `storederror` element in settings XML if booting succeded.

However, there are some ways of rendering the device not being able to boot. One of ways is to setting sleep timeout minutes to larger than 32-bit integer upper limit. When the device cannot recover itself by reboot and ending up not being able to boot properly, it will rapidly blink white LED and shutdown immedidately, and it will continue doing the same in each time the device powered on. Though you can still factory reset settings (resetting won't reformat the storage) by holding the power button until you see a green LED.

## Firmwares

You can find firmwares on [archive.org](https://web.archive.org/web/*/http://downloads.sandisk.com/firmware/ws/*), this device uses `.DF3` files specifically, there are also `.DF2` files archived which is only for [Wireless Flash Drive (SDWS2)](../wireless_flash_drive/) devices, not for this one!

The Android app made for this drive (`com.sandisk.connect`) also bundles the firmware files inside the APK too (in resources folder: `/res/raw`), so you can extract firmwares from it if you still have that app installed on your phone.

### Reverse engineering

See [`sandisk_wireless_df3.py` script](./sandisk_wireless_df3.py) to unpack and repack firmwares and read its comments about the byte format.

Thanks to [this post](https://forums.hak5.org/topic/41479-sandisk-wireless-connect-16g-flash-drive/) ([archive 1](https://web.archive.org/web/20250409165759/https://forums.hak5.org/topic/41479-sandisk-wireless-connect-16g-flash-drive/), [archive 2](https://archive.md/NTENm)) who published an AutoIt script to unpack `.DF3` firmwares, I was able to learn more about the byte format and improve it further in a Python script.

### Upgrade instructions

_Firmware upgrade instructions written below can also be found on this archived [Sandisk Support page](https://web.archive.org/web/20160515082212/http://kb.sandisk.com/app/answers/detail/a_id/17556):_

> 64 GB and higher variants has exFAT support, assuming due to exFAT license fee, so there are exFAT and non-exFAT variants of the same firmware version. For 16/32 GB variants, the drive comes with FAT32 formatted instead and doesn't have exFAT support.

Sandisk claims these firmware variants are not interchangeable, so **only use the firmware variant** that matches with the capacity of the drive you have:

* 16/32 GB models has this firmware file naming: `wfd2050s.df3`
* 64 GB and upper models has this firmware file naming: `wfd2050e.df3` (note the `e` suffix for `exFAT` instead of `s`)

To flash a firmware, copy the firmware file and put it in the root of the device, and eject it from your computer. Once it has started to install, LEDs should flash rapidly. Make sure that the device has sufficient battery power during flashing to avoid permanent damage.

Flashing firmwares can also be done by sending a HTTP POST request to `/settings.xml?group=firmware` with the firmware as a body triggers a flash. During flashing, the device will alternate between blue and white LED. If flashing was failed (invalid firmware), it will be reverted, and the device will blink red LED while it is still on and running normally until it gets rebooted to clear red LED.