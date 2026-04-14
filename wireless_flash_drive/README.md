# Wireless Flash Drive (SDWS2)

This one doesn't have an on-board flash storage, it instead comes with a Sandisk microSD plugged in its external microSD slot out-of-box (you will get a 32 GB microSD card for the 32 GB model) which can be replaced with another card.

I don't own this device, and I couldn't find information if it can accept a non-Sandisk microSD card. That's all I can tell about this one.

## Web server

From what I can tell, [Wireless Stick (SWDS4)](../wireless_stick/) mobile app (`com.sandisk.connect`) seems to have support for this Wireless Flash Drives too, so you can try checking out the same [`sandisk_wireless_config.py` script](../wireless_stick/sandisk_wireless_config.py) and see if it works for you too.

## Firmwares

You can find firmwares on [archive.org](https://web.archive.org/web/*/http://downloads.sandisk.com/firmware/wfd/*), this device uses `.DF2` files specifically, there are also `.DF3` files archived which is only for [Wireless Stick (SWDS4)](../wireless_stick/) devices, not for this one!

The Android app made for this drive (`com.sandisk.aircruzer`) also bundles the firmware files inside the APK too (in resources folder: `/res/raw`), so you can extract firmwares from it if you still have that app installed on your phone.

```
$ 7z e -bso0 -o"output" "sandisk.apk" "res/raw/*.df2"
```

### Reverse engineering

Couldn't determine the byte format, seems a raw flash dump or something packed?

### Upgrade instructions

_Firmware upgrade instructions written below can also be found on this [Sandisk Support page](https://support-en.sandisk.com/app/answers/detailweb/a_id/41388) ([archive 1](https://web.archive.org/web/20250409170927/https://support-en.sandisk.com/app/answers/detailweb/a_id/41388), [archive 2](https://archive.is/W1bC6)):_

> 64 GB and higher variants has exFAT support, assuming due to exFAT license fee, so there are exFAT and non-exFAT variants of the same firmware version. For 16/32 GB variants, the drive comes with FAT32 formatted instead and doesn't have exFAT support.

Sandisk claims these firmware variants are not interchangeable, so **only use the firmware variant** that matches with the capacity of the drive you have:

* 16/32 GB models has this firmware file naming: `wfd1105.df2`
* 64 GB models has this firmware file naming: `wfd1105e.df2` (note the `e` suffix here, for `exFAT`)

To flash a firmware, copy the firmware file and put it in the root of the device, and eject it from your computer. Once it has started to install, LEDs should flash rapidly. Make sure that the device has sufficient battery power during flashing to avoid permanent damage.

