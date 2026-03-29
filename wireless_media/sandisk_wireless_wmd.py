# pyright: basic

#
#    Copyright (C) 2025 Yusuf Cihan
#    @ysfchn https://ysfchn.com
#
#    This program is a free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
There is also a Wireless Media Drive, which its telnet & ftp access is left open making it way
easier to play around with it. For "root" user, the password is "sqn1351". It's firmware file is
an EXT2 filesystem followed after 152 bytes, which then can be mounted to the host system. [^1]

See also "sandisk_wireless_df3.py" file for Wireless Stick drives.

[^1]: https://forums.hak5.org/topic/35884-sandisk-wireless-media-drive-root-crackand-other-useful-info/
(archive 1: https://web.archive.org/web/20250715204033/https://forums.hak5.org/topic/35884-sandisk-wireless-media-drive-root-crackand-other-useful-info/)
"""

from argparse import ArgumentParser, ArgumentTypeError
from io import BytesIO
import subprocess
from typing import NamedTuple, Optional, Type, Tuple, cast
from sys import stderr
from pathlib import Path
from datetime import datetime
from zlib import crc32
import struct

UIMAGE_MAGIC = bytes((0x27, 0x05, 0x19, 0x56))
GZIP_MAGIC = bytes((0x1f, 0x8b, 0x08, 0x00))

# https://formats.kaitai.io/uimage/
# TODO: Unused
class UImageHeader(NamedTuple):
    header_crc: int
    timestamp: datetime
    data_length: int
    load_addr: int
    entry_addr: int
    data_crc: int
    os_type: int
    arch_type: int
    image_type: int
    comp_type: int
    name: str

    @classmethod
    def from_bytes(cls: "Type[UImageHeader]", data: bytes) -> "UImageHeader":
        assert len(data) == 64, f"uimage header must be 64 in length, not {len(data)}"
        assert data[0:4] == UIMAGE_MAGIC, f"no uimage header was detected, got 0x{data[0:4].hex()}"
        # Check if header CRC32 is correct.
        calculated = crc32(data[0:4] + bytes(4) + data[8:64])
        result = cls(
            header_crc = int.from_bytes(data[4:8], "big"),
            timestamp = datetime.fromtimestamp(int.from_bytes(data[8:12], "big")),
            data_length = int.from_bytes(data[12:16], "big"),
            load_addr = int.from_bytes(data[16:20], "big"),
            entry_addr = int.from_bytes(data[20:24], "big"),
            data_crc = int.from_bytes(data[24:28], "big"),
            os_type = int.from_bytes(data[28:29], "big"),
            arch_type = int.from_bytes(data[29:30], "big"),
            image_type = int.from_bytes(data[30:31], "big"),
            comp_type = int.from_bytes(data[31:32], "big"),
            name = data[32:64].decode("utf-8")
        )
        assert calculated == result.header_crc, f"mismatched uimage header crc32, expected {result.header_crc} but got {calculated}"
        return result

    def __repr__(self) -> str:
        return \
            f"time={self.timestamp.isoformat()} length={self.data_length} load=0x{self.load_addr:x} entry=0x{self.entry_addr:x} " + \
            f"os={self.os_type} arch={self.arch_type} comp={self.comp_type} itype={self.image_type} name='{self.name}' crc={self.data_crc}"


# https://wiki.osdev.org/Ext2
class EXTHeader(NamedTuple):
    inodes_count: int
    blocks_count: int
    r_blocks_count: int
    free_blocks_count: int
    free_inodes_count: int
    first_data_block: int
    log_block_size: int
    log_frag_size: int
    blocks_per_group: int
    frags_per_group: int
    inodes_per_group: int
    mtime: int
    wtime: int
    mnt_count: int
    mnt_max_count: int
    magic: bytes
    state: int
    errors: int
    minor_version: int
    check_previous: int
    check_interval: int
    system_id: int
    major_version: int
    rsb_uid: int
    rsb_gid: int
    # Extended superblock:
    first_ino: int
    inode_size: int
    block_group: int
    feature_compat: int
    feature_incompat: int
    feature_ro_compat: int
    uuid: bytes
    volume_name: bytes
    path_volume: bytes
    compress: int
    alc_files: int
    alc_dirs: int
    unused: int
    journal_id: bytes
    journal_inode: int
    journal_dev: int
    head_inode: int

    @classmethod
    def from_bytes(cls: "Type[EXTHeader]", data: bytes) -> "EXTHeader":
        sup = "IIIIIIIIIIIIIhh2sHHHIIIIHH"
        sup_ext = "IHHIII16s16s64sIBBH16sIII"
        ext = cls(*struct.unpack_from("<" + sup + sup_ext, data))
        assert ext.magic == b"\x53\xEF", "ext magic doesn't match"
        return ext

class WMDFirmware(NamedTuple):
    version: str
    file_size: int
    timestamp: datetime
    vendor: bytes
    ext_header: EXTHeader

def parse_wmd_firmware_header(firmware: Path):
    """
    Reads an Sandisk Media Drive (SWDS1) firmware header from given firmware path.
    There is a standard EXT2 filesystem following after a custom header (152 bytes), so this function
    won't read the entire file, since the whole firmware is about ~100 MB.
    """
    handle = firmware.open("rb")
    handle.seek(0, 2)
    total_size = handle.tell()
    handle.seek(0)

    HEADER_SIZE = 152
    vendor = BytesIO(handle.read(HEADER_SIZE))

    magic = vendor.read(4)
    assert magic == bytes([0x57, 0xAE, 0x2D, 0x64]), f"invalid magic? got {magic.hex(' ')}"

    # TODO: Skip these bytes now, we don't know their purpose yet, the first 4 bytes here might be CRC?
    unknown = vendor.read(8)

    timestamp = datetime.fromtimestamp(int.from_bytes(vendor.read(4), "little"))

    size_without_header = int.from_bytes(vendor.read(4), "little")
    assert (size_without_header + HEADER_SIZE) == total_size, f"firmware reports {size_without_header + HEADER_SIZE} bytes but file has {total_size}"

    # The version is stored in 2 bytes, first byte is the major,
    # and the second byte is the minor.
    # 02 5D -> 2.93 // 03 04 -> 3.04
    major, minor = cast(Tuple[str, str], map(str, vendor.read(2)))
    version = major + "." + minor.rjust(2, "0")

    assert vendor.read(2) == bytes(2), "unexpected bytes at header"
    assert vendor.read(9) == b"Qwifi.img", "unexpected bytes found for name"
    assert sum(vendor.read(119)) == 0, "unexpected bytes found when null bytes was expected after name"
    assert vendor.read() == bytes(0), "got more vendor bytes than expected, check the code"
    assert (total_size % 1024) == HEADER_SIZE, "file size must be multiple of 1024 after vendor header"

    assert sum(handle.read(1024)) == 0, "unexpected bytes before ext2 superblock"

    info = WMDFirmware(
        version = version,
        file_size = total_size,
        timestamp = timestamp,
        vendor = unknown,
        ext_header = EXTHeader.from_bytes(handle.read(1024)),
    )

    handle.close()

    print(f"version: {info.version}", file = stderr)
    print(f"timestamp: {info.timestamp}", file = stderr)
    print(f"total size: {info.file_size} ({size_without_header} without header)", file = stderr)
    print(f"unknown bytes: {unknown.hex(' ')}", file = stderr)
    print(f"ext header: {info.ext_header}", file = stderr)
    return info


def to_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    elif not v.replace(" ", ""):
        return None
    else:
        raise ArgumentTypeError("a boolean value was expected")


def main():
    parser = ArgumentParser()
    parser.add_argument("firmware", help = "Path of the input firmware file.", type = Path)
    parser.add_argument("--image", "-i", help = "Path of the output EXT2 image. If not provided, just parses the firmware. If --mount is also provided, this will be the directory that image will mount to.", type = Path, required = False)
    parser.add_argument("--mount", "-m", help = "If given, mounts the EXT2 image to directory provided with --image.", type = to_bool, const = True, nargs = "?", default = None)
    data = parser.parse_args()
    input_firmware = cast(Path, data.firmware).resolve()
    image_path = None if not data.image else cast(Path, data.image).resolve()
    is_mount = cast(Optional[bool], data.mount)
    if not input_firmware.is_file():
        print(f"input firmware '{str(input_firmware or '<not provided>')}' must be an existing firmware file!", file = stderr)
        exit(1)
    if image_path:
        if image_path.exists() and (is_mount != False): # noqa: E712
            print(f"image path '{str(image_path)}' must be an non-existing path if provided!", file = stderr)
            exit(1)
        elif (not image_path.exists()) and (is_mount == False): # noqa: E712
            print(f"image path '{str(image_path)}' must be an existing path when unmounting!", file = stderr)
            exit(1)
        if is_mount:
            image_path.mkdir()
    if (is_mount is not None) and (not image_path):
        print(f"image path '{str(image_path)}' must be provided when mounting!", file = stderr)
        exit(1)
    _ = parse_wmd_firmware_header(input_firmware)
    if image_path and (is_mount is None):
        with image_path.open("wb") as f:
            with input_firmware.open("rb") as inp:
                inp.seek(152)
                while (data := inp.read(1024)):
                    f.write(data)
        print(f"written to {str(image_path)}", file = stderr)
        print("\nmount image to an existing empty folder with:", file = stderr)
        print(f"    sudo mount -o loop,ro -t ext2 '{str(image_path.relative_to(Path.cwd()))}' mount-folder", file = stderr)
        print("\nunmount image with its image or folder path:", file = stderr)
        print(f"    sudo umount '{str(image_path.relative_to(Path.cwd()))}'", file = stderr)
    elif image_path and is_mount:
        subprocess.run(["sudo", "mount", "-o", "loop,offset=152", "-t", "ext2", str(input_firmware), str(image_path)], stdout = stderr, encoding = "utf-8", check = True)
    elif image_path:
        subprocess.run(["sudo", "umount", str(image_path)], stdout = stderr, encoding = "utf-8", check = True)
        subprocess.run(["rm", "-d", str(image_path)], stdout = stderr, encoding = "utf-8", check = True)


if __name__ == "__main__":
    main()