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
A script to read & unpack firmware files of Sandisk's discontinued Wireless Stick series from 2015.
The devices are clone of AirStash devices with Sandisk's branding & modifications added on top of it.

Since the device itself does no longer being sold and its firmware format is proprietary,
there is very few information about these available on the internet, so I've tried my
best to research to gather much info as possible.

If you're a looking for copies of the firmware files,

1)  The discontinued (and pulled off from the app stores) Sandisk Connect Drive app 
    contains firmware files stored in the APK itself, so you can just grab the APK from a
    random APK mirror website and unpack it. (in "res/raw" folder)

2)  Luckily, Internet Archive has some archived copies. Though the below link also lists
    firmwares for other Sandisk devices, so you will need to filter links that ending with
    ".df3" and ".df2" firmwares.
    https://web.archive.org/web/*/http://downloads.sandisk.com/firmware/*

".DF2" files are only for "Wireless Flash Drive (SDWS2)", and
".DF3" files are only for "Wireless Stick (SWDS4)".

This script only focuses on .DF3 firmwares entirely, so don't bother trying with .DF2 files,
since they have a different format.

Thanks to this user who created an AutoIt script for the device, it very helped me to
create this script:
https://forums.hak5.org/topic/41479-sandisk-wireless-connect-16g-flash-drive/

The same forum also has some discussion about the device:
https://forums.hak5.org/topic/30273-hack-a-sandisk-32g-wifi-enabled-flash-drive/

"""

import struct
from argparse import ArgumentParser
from hashlib import sha1
from sys import stderr
from io import BytesIO
from pathlib import Path
from typing import Sequence, Union, cast, Tuple, Dict, NamedTuple, List

# Firmware binaries doesn't contain the name of the files, it is hardcoded inside the drive, and thus it doesn't seem
# we can add a new file to the firmware, just replace the existing ones where they should be expected.
#
# These file names are found by looking at the static files served by the web server.

FILE_SHA1_MAPPINGS : Dict[str, Dict[str, Union[Sequence[int], int]]] = {
    "licenses.txt": {"6fc839d06fb56a6304bffa952300ad2adbb419be": (2034, 2050,)},
    "nocard.html": {"e4f30e2ef923db65ba964d2235d4d00d70de8d9c": 2050, "296d60f15525be03293a47815a1e1c4682ba94c2": 2034},
    "settings.html": {"216ffe22b7d94ebca31475136e12e011caed3e3c": 2050, "975b433649319a918b7f2c9e4e4e3a09f0f80e6f": 2034},
    "video.html": {"a0cddb24e97c22788308f42d5db2e85db1b6ad00": 2050, "198317b02094c5cfb67ba4f6ace175ac0282d8ac": 2034},
    "battery/charging0.png": {"6e246dc644b300231dfe492febeb990db88a16f2": 2050},
    "battery/charging1.png": {"31cb12c7177002ed8232c97bed6f8668d7f7b2ef": 2050},
    "battery/charging2.png": {"78bc05b1d62c576c565ac277e1c5969d5d2253a8": 2050},
    "battery/charging3.png": {"8618bb1c56c73aa760b4a28406a778deeaa18504": 2050},
    "battery/critical0.png": {"ae732c815a088fbe66e5fea1122b45e0909a7f0a": 2050},
    "battery/critical1.png": {"11a11bce0199c0552376600f9001490612db7bfc": 2050},
    "battery/high.png": {"91b30dd8a6eb9bda03f855394e204dfdafc5941e": 2050},
    "battery/low.png": {"c8e44366b426bf692aac7a8f52e027689325992f": 2050},
    "battery/medium.png": {"15d9e1d01ad263ac1820d49809770bd9abd25a9d": 2050},
    "folder_check_icon.png": {"49e162ef5f775c57e5ab16161d66fb62bcf86077": 2050},
    "folder_nocheck_icon.png": {"784d36ffeea0943b17435a75b90e9858e1fefa55": 2050},
    "mejs/silverlightmediaelement.xap": {"98c1a8a1ef247c16504caf801717fb1bacf8ade0": (2034, 2050,)},
    "mejs/mediaelement-and-player.min.js": {"0c0b7dc6a27d74d86ea308ed6147f68d6d16e8d7": (2034, 2050,)},
    "mejs/flashmediaelement.swf": {"be1eb3ce24451297ddc83ef1609c63ce21fbe1df": (2034, 2050,)},
    "mejs/bigplay.svg": {"5eac4a76ca86f9776a6d04d1ae5a466b3faf9add": (2034, 2050,)},
    "mejs/bigplay.png": {"4b85a8fb707e051c705f03efb15f910b4cfbec30": (2034, 2050,)},
    "mejs/mediaelementplayer.min.css": {"d53c8c7f6ac7b0624b5450294886fc5ac3244e7f": (2034, 2050,)},
    "mejs/controls.svg": {"b348ebbee79eff5451362fbbd4c23e3418eceeb0": (2034, 2050,)},
    "mejs/controls.png": {"577269a774800b7c0a733062cbaf4a82a8f877c4": (2034, 2050,)},
    "mejs/loading.gif": {"6ee38113a9e2fc074c0d35ff5b25a47cce273d4d": (2034, 2050,)},
    "mejs/background.png": {"5ccc08a070eea534c880ba63aadbbdea4b4ec947": (2034, 2050,)},
    "js/jquery.min.js": {"b66ed708717bf0b4a005a4d0113af8843ef3b8ff": (2034, 2050,)},
    "js/sort.js": {"b76a76061bec88a0207a13e085f4e0e29330b9f7": 2050, "0fe59cb5fcc4bddef3542579f33f563b7946188f": 2034},
    "js/dragdrop.js": {"4b30a53aa24ffd9f6d1a12db7ea2e978ca04d0e6": 2050},
    "js/video.js": {"6d39d0fcef15cce38519b55a54bc9dbc4d974f4f": (2034, 2050,)},
    "css/jquery-ui-core.min.css": {"316137cbbc4ed6da86ec2ecb05c0479181d76191": (2034, 2050,)},
    "css/jquery-ui-theme.min.css": {"7304c7fd5ed63535581b6fdb0be75997a88f0b5c": 2050},
    "js/jquery-ui.min.js": {"4cad9f125912719b17c9af3e17a3db842860d144": (2034, 2050,)},
    "js/settings.js": {"5ee45521f7646d1fa7a15fea1374125eb0af9125": 2050, "1324b166b50ab11af273153a648caa09409f41c1": 2034},
    "css/style.css": {"845d95b300fb5a1d4b6cb6e66dc3def9cb77b2ae": 2050, "296d5350a422e7599bb5b8a725e67626480ef0b1": 2034},
    "css/images/ui-icons_888888_256x240.png": {"d0144b794640e1126f782b5332c8539fe2d3aef4": 2050},
    "css/images/ui-icons_454545_256x240.png": {"6cb0b3a5c3cb2ee9fbaef3cb156c06bb4f15fc82": 2050},
    # TODO: Their file names are not cracked yet, needs bruteforcing asset path.
    "_unknown/unknown.bin": {"d4ae769b656b27f801836868807c0396377a34c0": 2050, "74d48c49a9984ca1f9c0fac6ccd18c32b658ea00": 2034},
    "_unknown/text.txt": {"ae8424f859c2e2ff19d333395422c1885690e87f": (2034, 2050,)},
}

class FilePath(NamedTuple):
    checksum: str
    path: str

class FirmwareInfo(NamedTuple):
    model: str
    version: int
    size: int
    blocks: List["FirmwareBlock"]
    files: List["FirmwareFile"]

class FirmwareBlock(NamedTuple):
    data: bytes

# Each file in the packed firmware represents their file extension as a byte value, these extensions
# were cracked by checking the file contents.
FILE_EXTENSIONS = {
    0: "bin", # not known
    1: "bin", # not known
    14: "swf",
    15: "xap",
    25: "gif",
    27: "png",
    28: "svg",
    33: "css",
    35: "html",
    36: "js",
    37: "txt",
}

class FirmwareFile(NamedTuple):
    data: bytes
    type: int
    size: int
    digest: str
    path: str
    is_unknown: bool

    def padding_byte(self):
        """
        When repacking the firmware with user inputted files, gets the byte to be used as a padding
        to make file size equal with the original file found in the firmware.
        """
        ext = FILE_EXTENSIONS.get(self.type)
        if ext in ("svg", "css", "html", "js", "txt"):
            return b"\x20"
        return b"\x00"

    def get_header(self):
        """
        Constructs a new header to be added on top of user inputted files, so the modified firmware
        can be unpacked again even if the checksum is different.
        """
        ext = FILE_EXTENSIONS.get(self.type)
        if ext in ("css", "js"):
            return f"/*--UNPACK_PATH:{self.path}-*/"
        elif ext in ("html", "svg"):
            return f"<!--UNPACK_PATH:{self.path}-->"


def parse_df3_firmware(firmware: Path):
    """
    Reads an Sandisk Wireless Stick (SDWS4) firmware file and returns a FirmwareInfo object
    containing information and list of sectors and files, which then can be iterated through
    to dump the filesystem contained in the firmware.

    The firmware doesn't contain the filenames of files in the filesystem, assuming they
    are hardcoded in ROM, so this function tries to decipher the names of the files based
    on their checksum and which HTTP path are they served from in the web server.
    """
    buffer = BytesIO()
    buffer.write(firmware.read_bytes())
    total_size = buffer.tell()
    buffer.seek(0)

    # The byte structure is simply follows:
    # AA BB BB .. ..
    # AA -> ID of the sector
    # BB -> Length of the sector (big-endian)

    def get_next_sector(eid: int, elen: int):
        sid = int.from_bytes(buffer.read(1), "big")
        # Check if the obtained byte matches with given value to make sure it is a valid file.
        assert eid == sid, f"current sector id mismatch, got {sid} but expected {eid}, is it a valid firmware?"
        slen = int.from_bytes(buffer.read(2), "big")
        assert slen == elen, f"current sector length mismatch, got {slen} but expected {elen}, is it a valid firmware?"
        return buffer.read(slen)
    
    # First 3 bytes of the file is equal to [01 00 08], so, 
    # taking above information into the account:
    # 01 -> The ID of the sector
    # 00 08 (= 8) -> Sector is 8 bytes long
    model = get_next_sector(1, 8).strip(b"\x00").decode("ascii")

    # The version code is represented as an integer, then followed by an ASCII encoded string
    # of the same version number. For example, if first 4 bytes are 00 00 08 02 (= 2050), then 
    # the next 4 byte must be "2050" in ASCII.
    version_int, version_ascii, empty = cast(Tuple[int, bytes, bytes], struct.unpack_from(">I4s28s", get_next_sector(2, 36)))
    assert sum(empty) == 0, "unexpected bytes found when null bytes was expected after version"
    assert str(version_int).encode("ascii") == version_ascii, f"version names doesn't match, {version_int} != {version_ascii}"

    info = FirmwareInfo(
        model = model, version = version_int, size = total_size, blocks = [], files = []
    )

    print(f"model: {info.model}", file = stderr)
    print(f"version: {info.version}", file = stderr)
    print(f"file size: {info.size}", file = stderr)

    # Findings:
    # wfd2050s.df3 @ 0x001032FF - WiFi driver and firmware version

    # I couldn't get to know about meaning of these bytes, but as far I've tested with several
    # firmware revisions, these sectors are always the same, so we can just seek & validate through it.
    sectors = (
        (3, 4), (4, 1), (5, 96), (6, 16), (7, 117), (7, 117), (7, 117), (10, 96)
    )
    for sector_id, sector_length in sectors:
        info.blocks.append(FirmwareBlock(get_next_sector(sector_id, sector_length)))
    print(f"read through {buffer.tell()} bytes", file = stderr)
    assert sum(buffer.read(934)) == 0, "unexpected bytes found when null bytes was expected"

    # Individual file contents in the firmware start at where [FF FF FF FF 00 00] byte pattern
    # is first appears, so we just skip to seek there and start reading file entries.
    boundary = bytes((0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00))
    start = buffer.getvalue().find(boundary)
    assert start != -1, "couldn't find the start of the file entry header"
    
    info.blocks.append(FirmwareBlock(buffer.read(start - buffer.tell())))
    buffer.read(len(boundary))
    print(f"header found at {hex(buffer.tell())}", file = stderr)

    # Parse header to read the file entries, each file entry takes up 12 bytes, 
    # therefore the number of bytes must be multiple of 12.
    header_size = int.from_bytes(buffer.read(2), "big")
    print(f"header size is {header_size} bytes", file = stderr)
    header = buffer.read(header_size)
    assert (len(header) % 12) == 0, f"invalid header size, got {header_size}, which is not a multiple of 12"

    start_offset = buffer.tell() - header_size
    entries : List[Tuple[int, int, int]] = []

    # bytes 0-4 is the incremental index (starts from 1)
    # bytes 4-8 is the offset (starting from 0xFFFFFFFF0000 boundary (included), so first file offset will equal to the boundary + header size)
    # bytes 8-12 is the file type (see the extension code mapping above)
    for i in range(len(header) // 12):
        f_index, f_offset, f_type = cast(Tuple[int, int, int], struct.unpack(">III", header[i * 12:i * 12 + 12]))
        assert f_index == (i + 1), f"file indexes doesn't match, expected {i + 1} but got {f_index}"
        entries.append((f_index, f_offset, f_type))

    for fi, fo, ft in entries:
        index = int.from_bytes(buffer.read(4), "big")
        size = int.from_bytes(buffer.read(4), "big")
        assert start_offset + fo == buffer.tell(), f"file #{fi} reports unexpected offset"
        assert index == fi, f"file indexes doesn't match, expected {fi} but got {index}"
        
        file_data = buffer.read(size)
        file_ext = FILE_EXTENSIONS.get(ft, None)
        digest = sha1(file_data).digest().hex()
        print(f"file #{fi}, ext: {file_ext or 'UNKNOWN!'} ({ft}), size: {size}, offset: {hex(start_offset + fo)}", file = stderr)
        guessed_path = guess_filename(digest, info.version)
        if not guessed_path:
            print(f"warning: file path is not known for hash {digest}", file = stderr)
        info.files.append(FirmwareFile(file_data, ft, size, digest, guessed_path or f"_unknown_/{digest}", bool(guessed_path)))

    assert buffer.read() == bytes(8), "invalid bytes found at the end"
    return info


def repack_firmware(info: FirmwareInfo, input_directory: Path):
    """
    Repacks the firmware by collecting files in previously parsed firmware and replacing them by the same files
    found in input directory, and adds the missing padding if input files are smaller than original files.
    """
    if not input_directory.is_dir():
        raise ValueError("input path must be an directory, not file")
    file_list = []
    for f in info.files:
        input_path = input_directory.joinpath(f.path)
        if not input_path.is_file():
            print(f"warning: file path is not a valid file or doesn't exists: {str(input_path)}, using original file from the firmware", file = stderr)
            file_list.append(f)
            continue
        input_bytes = input_path.read_bytes()
        digest = sha1(input_bytes).digest().hex()
        is_unchanged = digest == f.digest
        print(f"collected: {f.path}, hash: {digest}, size: {len(input_bytes)} bytes ({'UNCHANGED' if is_unchanged else 'EDITED: ' + str(f.size - len(input_bytes)) + ' bytes less'})", file = stderr)
        file_list.append(FirmwareFile(data = input_bytes, type = f.type, size = f.size, digest = digest, path = f.path, is_unknown = f.is_unknown))
    return FirmwareInfo(model = info.model, version = info.version, size = info.size, blocks = info.blocks, files = file_list)


def unparse_df3_firmware(firmware: FirmwareInfo):
    """
    Converts the previously parsed FirmwareInfo object into bytes, re-creating the whole
    firmware. This means `unparse_df3_firmware(parse_df3_firmware(firmware_file)) == firmware_file`
    is `True` if given FirmwareInfo object is same.
    """
    buffer = BytesIO()

    def put_next_sector(eid: int, edata: bytes):
        buffer.write(eid.to_bytes(1, "big"))
        buffer.write(len(edata).to_bytes(2, "big"))
        buffer.write(edata)

    put_next_sector(1, firmware.model.encode("ascii").ljust(8, b"\x00"))
    put_next_sector(2, 
        firmware.version.to_bytes(4, "big") + \
        str(firmware.version).encode("ascii").ljust(32, b"\x00")
    )

    sectors = (
        (3, 4), (4, 1), (5, 96), (6, 16), (7, 117), (7, 117), (7, 117), (10, 96)
    )
    sector_data = bytearray()
    if not (len(firmware.blocks) == len(sectors) + 1):
        raise AssertionError(f"expected {len(sectors) + 1} sector")
    for i, sector in enumerate(sectors):
        sector_id, sector_length = sector
        sector_data = firmware.blocks[i].data
        if len(sector_data) != sector_length:
            raise AssertionError(f"unexpected sector length at sector #{i} (expected {sector_length}, got {len(sector_data)})")
        put_next_sector(sector_id, sector_data)

    buffer.write(bytes(934))
    buffer.write(firmware.blocks[len(sectors)].data)
    boundary = bytes((0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00))
    buffer.write(boundary)
    
    header_size = (len(firmware.files) * 12)
    buffer.write(header_size.to_bytes(2, "big"))
    start_offset = header_size + len(boundary) + 2
    for j, file in enumerate(firmware.files):
        buffer.write((j + 1).to_bytes(4, "big"))
        buffer.write(start_offset.to_bytes(4, "big"))
        buffer.write(file.type.to_bytes(4, "big"))
        start_offset += file.size + 8

    for k, file in enumerate(firmware.files):
        buffer.write((k + 1).to_bytes(4, "big"))
        buffer.write(file.size.to_bytes(4, "big"))
        if len(file.data) > file.size:
            raise ValueError(f"input file {file.path} is larger ({len(file.data)} bytes) than the original file ({file.size} bytes) found in the firmware, it won't fit!")
        buffer.write(file.data + (file.padding_byte() * (file.size - len(file.data))))

    buffer.write(bytes(8))
    return buffer.getvalue()


def guess_filename(digest: str, version: int):
    """
    Returns the known filename of the given firmware file SHA256 digest.
    The returned path is relative to the /static/ path served from the device IP.
    For example, "licenses.txt" is located in "http://{IP}/static/licenses.txt" in the device.
    """
    for path, variants in FILE_SHA1_MAPPINGS.items():
        allowed_versions = variants.get(digest)
        if not allowed_versions:
            continue
        if type(allowed_versions) is int:
            if allowed_versions == version:
                return path
        else:
            for item in cast(Sequence[int], allowed_versions):
                if item == version:
                    return path
        raise ValueError("checksum does exists but versions doesn't. please make sure to report it!")


def main():
    parser = ArgumentParser()
    parser.add_argument("firmware", help = "Path of the input firmware file.", type = Path)
    parser.add_argument("--dump", "-d", help = "Path of the output directory with dumped files. If not provided, just parses the firmware.", type = Path, required = False)
    parser.add_argument("--output", "-o", help = "Path of the new generated firmare by collecting files from --dump path (if provided).", type = Path, required = False)
    data = parser.parse_args()
    input_firmware = cast(Path, data.firmware).resolve()
    dump_path = None if not data.dump else cast(Path, data.dump).resolve()
    new_firmware = None if not data.output else cast(Path, data.output).resolve()
    if not input_firmware.is_file():
        print(f"input firmware '{str(input_firmware or '<not provided>')}' must be an existing firmware file!", file = stderr)
        exit(1)
    if new_firmware:
        if new_firmware.exists():
            print(f"output firmware '{str(new_firmware)}' must be an non-existing file!", file = stderr)
            exit(1)
    if dump_path:
        if not new_firmware:
            if dump_path.exists():
                print(f"dump path '{str(dump_path)}' must be an non-existing directory when just dumping!", file = stderr)
                exit(1)
            dump_path.mkdir()
        else:
            if not dump_path.is_dir():
                print(f"dump path '{str(dump_path)}' must be an existing directory when generating a new firmware!", file = stderr)
                exit(1)
    firmware_info = parse_df3_firmware(input_firmware)
    if input_firmware.read_bytes() != unparse_df3_firmware(firmware_info):
        raise AssertionError("can't regenerate the 1:1 same firmware with the parsed firmware, this is a parsing issue, please make sure to report it!")
    if dump_path and not new_firmware:
        for i in firmware_info.files:
            ip = dump_path.joinpath(i.path)
            ip.parent.mkdir(parents = True, exist_ok = True)
            with dump_path.joinpath(i.path).open("wb") as d:
                d.write(i.data)
    elif dump_path and new_firmware:
        generated = repack_firmware(firmware_info, dump_path)
        unparsed = unparse_df3_firmware(generated)
        new_firmware.open("wb").write(unparsed)
    elif not dump_path and new_firmware:
        print("warning: output firmware provided without an input directory, copying the same file", file = stderr)
        new_firmware.open("wb").write(unparse_df3_firmware(firmware_info))


if __name__ == "__main__":
    main()