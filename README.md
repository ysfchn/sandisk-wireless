# sandisk-wireless

Back in the day, Sandisk had a product line of flash drives with Wi-Fi capability named "Connect Wireless", so in addition of accessing contents over USB it was also exposing a Wi-Fi access point to share its contents.

There are three variants of them, which all of them are no longer sale for years and their respective mobile apps were already discontinued and no longer available on app stores.

They are still usable to this day since the drives itself work locally and doesn't need phoning any remote server to function, only their mobile apps did for firmware updates.

They were rare to find so I was curious about how far they can be hacked and found myself getting them in the end. If you are planning to get one of yourself just to sake of using them in its intended way, I would recommend against it, since a proper NAS setup would bring more freedom rather than relying on a very old drive with most likely to have full of vulnerabilities and containing a proprietary locked web server software on top of it and is limited to USB 2.0 speeds, which it wouldn't ever go near to maximum of it, due to them requiring microSD.

This repository contains several Python scripts to manage these devices with HTTP requests (as a replacement to its mobile apps) and inspect their firmware files. As a goal to make scripts have small footprint and clean code, no external dependency is required other than built-in Python libraries.

## Devices

Sandisk lists their discontinued devices in their [support page](https://web.archive.org/web/20251207131629/https://support-en.sandisk.com/app/answers/detailweb/a_id/48741), and devices in this Wireless product line listed are:

|  Product  |  Model prefix  |  Variants  |  FCC  |  Last manufactured  |  Last support  | Android package name |
|:----------|:--------------:|:----------:|:-----:|:-------:|:---------:|:---------:|
| [Wireless Flash Drive](./wireless_flash_drive/) | SDWS2 | SDWS2-0**16G**<br>SDWS2-0**32G**<br>SDWS2-0**64G** | [R4V-SDWS2](https://fccid.io/R4V-SDWS2) <br> <sup>[Label image](https://fccid.io/R4V-SDWS2/Label/lable-2031553.pdf)</sup> | [October 2015](https://support-en.sandisk.com/app/answers/detailweb/a_id/48977) | March 18, 2021 | `com.sandisk.aircruzer` |
| [Wireless Stick](./wireless_stick/) | SWDS4 | SDWS4-0**16G**<br>SDWS4-0**32G**<br>SDWS4-0**64G**<br>SDWS4-**128G**<br>SDWS4-**200G**[^1]<br>SDWS4-**256G** | [R4V-SDWS4](https://fccid.io/R4V-SDWS4) <br> <sup>[Label image](https://fccid.io/R4V-SDWS4/Label/Label-2663491.pdf)</sup> | June 2018 | January 31, 2024 | `com.sandisk.connect` |
| [Wireless Media](./wireless_media/) | SWDS1 | SWDS1-0**16G**<br>SWDS1-0**32G**<br>SDWS1-0**64G** | [R4V-SDWS1](https://fccid.io/R4V-SDWS1) <br> <sup>[Label image](https://fccid.io/R4V-SDWS1/Label/Label-Location-pdf-2028664.pdf)</sup> | February 2017 | September 1, 2021 | `com.sandisk.scotti` |

### Wireless Flash Drive & Stick

For Wireless Flash Drive & Wireless Stick, both are produced by "Wearable, Inc." for Sandisk, and is the clone of [Maxell Airstash](https://maxell.com.au/shop/storage-devices/wireless-storage/airstash-usb-wireless-storage/) product with Sandisk branding added on top of it, as the web server assets and software licenses mentions Airstash.

64 GB and higher variants has exFAT support, assuming due to exFAT license fee, so you will need to flash the firmware that matches with the storage of your device. For 16/32 GB variants, the drive comes with FAT32 formatted instead and doesn't have exFAT support.

Wearable Inc. was later [acquired by Western Digital on June 2018.](https://en.wikipedia.org/wiki/Western_Digital#:~:text=37%5D-,In,platform)

See more about [Wireless Flash Drive](./wireless_flash_drive/) and [Wireless Stick](./wireless_stick/) in their respective pages.

### Wireless Media

Wireless Media is entirely a different product than other two.

This one is an interesting case, as unlike previous two models which are derivated from Airstash, this one runs on its own software and is the most hackable one as it [is possible to gain root access on its Linux system.](./wireless_media/).

See the linked page above for more about Wireless Media.

## License

This program is licensed under [GNU General Public License version 3](./LICENSE).

It is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See GPLv3 license for details.

This program is not supported, sponsored, affiliated, approved, or endorsed in any way with Sandisk, Maxell and/or Western Digital. All other mentioned trademarks are the property of respective owners.

[^1]: https://web.archive.org/web/20260207115404/https://support-in.wd.com/app/products/product-detailweb/p/6788
