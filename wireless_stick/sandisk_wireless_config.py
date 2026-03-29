# pyright: basic

from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from hashlib import md5, sha1
from http.client import HTTPResponse
import re
from sys import stderr
from time import sleep
from typing import Annotated, Dict, Mapping, NamedTuple, Optional, List, Sequence, Type, TypeVar, Union, cast, get_args, get_origin
from urllib.parse import unquote, urlencode, urlunsplit
from urllib.request import Request, urlopen, HTTPError
import xml.etree.ElementTree as ET

class NullableEnum:
    @classmethod
    def _missing_(cls, _): return getattr(cls, "UNKNOWN")

class RequestResponse(NamedTuple):
    status: int
    body: bytes
    headers: Dict[str, str]

def do_request(
    address: str,
    path: str,
    method: str,
    query: Optional[Mapping[str, Union[str, bytes]]] = None,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Union[Dict, bytes]] = None
) -> RequestResponse:
    request_url = urlunsplit(("http", address, "/" + path.removeprefix("/"), "" if not query else urlencode(query), ""))
    encoded_body = body if isinstance(body, bytes) or (body is None) else urlencode(body).encode("utf-8")
    new_headers = headers or dict()
    if not (isinstance(body, bytes) or (body is None)):
        new_headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = Request(url = request_url, method = method, unverifiable = True, data = encoded_body, headers = new_headers)
    try:
        resp = cast(HTTPResponse, urlopen(req))
        return RequestResponse(status = resp.status, body = resp.read(), headers = dict(resp.headers))
    except HTTPError as he:
        return RequestResponse(status = he.status or -1, body = he.read(), headers = dict(he.headers))

class DeviceType(NullableEnum, Enum):
    # AirStash
    A01 = "A01"
    A02 = "A02"
    # Wireless Flash Drive
    FD_128K = "A02S" # 16GB/32GB variant
    FD_256K = "A02E" # 64GB variant
    # Wireless Stick
    WS_V1 = "A03S" # 16GB/32GB variant
    WS_V2 = "A03E" # 64GB/128GB/200GB variant
    UNKNOWN = ""

class LastErrorInfo(NamedTuple):
    message: str
    source: str
    line: int
    version: Optional[int]
    address: Optional[int]
    counter: Optional[int]
    timestamp: Optional[int]

class MACAddress(str):
    DIRECT_CONNECT_MAC_PREFIX = "D0:E4:0B:"
    HOME_CONNECT_MAC_PREFIX = "D2:E4:0B:"

    def __new__(cls, content: str):
        mac = str(content).upper()
        if mac.count(":") != 5:
            raise ValueError(f"doesn't appear to be a valid mac: {mac}")
        if not all((int(x, 16) <= 0xFF for x in mac.split(":"))):
            raise ValueError(f"doesn't appear to be a valid mac: {mac}")
        return str.__new__(cls, mac)

    @property
    def as_home(self):
        if self.startswith(self.DIRECT_CONNECT_MAC_PREFIX):
            return self.HOME_CONNECT_MAC_PREFIX + self.removeprefix(self.DIRECT_CONNECT_MAC_PREFIX)
        return self

    @property
    def as_direct(self):
        if self.startswith(self.HOME_CONNECT_MAC_PREFIX):
            return self.DIRECT_CONNECT_MAC_PREFIX + self.removeprefix(self.HOME_CONNECT_MAC_PREFIX)
        return self

    @property
    def as_int(self):
        return int.from_bytes(bytes.fromhex(self.as_direct.replace(":", "")), "big")

    def to_model(self):
        # TODO: might be incorrect
        value = self.as_int
        if value < 0xD0_E4_0B_00_0F_00:
            return DeviceType.A01
        elif (value >= 0xD0_E4_0B_00_0F_00) and (value <= 0xD0_E4_0B_03_99_FF):
            return DeviceType.A02
        elif (value >= 0xD0_E4_0B_F5_D6_00) and (value <= 0xD0_E4_0B_FB_9F_FF):
            return DeviceType.FD_128K
        elif (value >= 0xD0_E4_0B_FB_E0_00) and (value <= 0xD0_E4_0B_FE_FF_FF):
            return DeviceType.WS_V1
        elif (value >= 0xD0_E4_0B_F5_D5_FF) and (value <= 0xD0_E4_0B_80_50_00):
            return DeviceType.WS_V2

class WiFiSecurity(Enum):
    WPA2 = "wpa2"
    WPA = "wpa"
    WEP = "wep"
    PUBLIC = "none"

class SettingsPushState(Enum):
    SUCCESS = "ok" # Changes saved successfully.
    SUCCESS_PENDING_RESTART = "ok:pending"
    BAD_REQUEST = "bad" # Couldn't register a new network for some reason (?).
    ERROR_ENTRY_FULL = "full" # Couldn't register a new network because maximum limit has been reached.
    ERROR_ENTRY_DUPLICATE = "duplicate" # Couldn't register a new network because it is already exists.
    ERROR_ENTRY_NONEXIST = "notfound" # Couldn't remove a saved network because it doesn't already exists.

class NetworkScanState(NullableEnum, Enum):
    SCANNING = "scanning"
    LOCKED = "locked"
    NONE = "none"
    UNKNOWN = ""

class Coex(NamedTuple):
    mac: bytes
    name: str
    current: bool

class Settings(NamedTuple):
    class NetworkInfo(NamedTuple):
        ssid: str
        security: WiFiSecurity
        rssi: int
        connected: bool
        saved: bool

    class Device(NamedTuple):
        class SecurityLevel(NullableEnum, Enum):
            NONE = "none"
            ALL = "all"
            UNKNOWN = ""

        version: str
        buildmodel: str
        numericversion: int
        model: str
        hostname: str
        serial: Annotated[bytes, "mac"]
        timeout: int
        auth: SecurityLevel
        ssid: str
        authhash: bytes = b""
        wpapsk: bytes = b""

    class Feature(NamedTuple):
        security: int = 0
        cachent: int = 0
        coex: int = 0
        firmwareupdate: int = 0
        restart: int = 0
        exfat: int = 0

    class Bitrate(NamedTuple):
        warn: int
        critical: int

    class AppVersion(NamedTuple):
        android: str = ""
        ios: str = ""

    class Battery(NamedTuple):
        class BatteryStatus(NullableEnum, Enum):
            CHARGING = "charging"
            FULL = "charged"
            HIGH = "high"
            MEDIUM = "med"
            LOW = "low"
            CRITICAL = "critical"
            UNKNOWN = "unknown"

        status: BatteryStatus
        voltage: int

    class AccessPoint(NamedTuple):
        enabled: bool
        clients: int = -1

    class Card(NamedTuple):
        class CardStatus(NullableEnum, Enum):
            MOUNTED = "mounted"
            UNFORMATTED = "unformatted"
            FS_ERROR = "fserror"
            ERROR = "carderror"
            UNKNOWN = ""

        class CardFileSystem(NullableEnum, Enum):
            FAT16 = "fat16"
            FAT32 = "fat32"
            EXFAT = "exfat"
            NTFS = "ntfs"
            HFS = "hfs"
            UNKNOWN = ""

        status: CardStatus
        format: CardFileSystem
        serial: bytes
        path: str
        label: str
        free: int
        total: int
        blocksize: int
        readonly: Annotated[bool, "protected"] = False

    class Client(NamedTuple):
        class ClientStatus(NullableEnum, Enum):
            CONNECTING = "connecting"
            CONNECTED = "connected"
            FAILED = "failed"
            UNKNOWN = "unknown"

        ssid: str
        ip: str
        status: ClientStatus
        method: Annotated[bool, "sidelink"] = False

    class PendingFirmware(NamedTuple):
        build: int = 0

    class LastError(NamedTuple):
        file: str = ""
        description: str = ""
        line: int = -1
        version: int = -1
        address: str = "" # might be a bytes or int
        pc: bytes = b""
        timestamp: int = -1

    device: Device
    feature: Feature
    bitrate: Bitrate
    app_version: AppVersion
    battery: Battery
    access_point: AccessPoint
    cards: List[Card]
    sidelink: bool
    pendingfirmware: Optional[PendingFirmware]
    lasterror: Optional[LastError]
    client: Optional[Client]

T = TypeVar("T", bound = tuple)

def xml_to_namedtuple(el: Optional[ET.Element], ntp: Type[T], *, skip_falsy: bool = False, use_attributes: Union[bool, Sequence[str]] = False) -> T:
    if el is None:
        raise ValueError("no element was provided")
    data = dict()
    for key, expected_type in ntp.__annotations__.items():
        should_attrib = key in ((key,) if use_attributes is True else use_attributes or ())
        default = cast(Type[NamedTuple], ntp)._field_defaults.get(key, Ellipsis)
        type_orig = get_origin(expected_type)
        type_args = get_args(expected_type)
        got_value = el.attrib.get(key) if should_attrib else el.findtext(f"./{key}")
        if skip_falsy and not got_value:
            got_value = None
        
        resolved = Ellipsis
        if (got_value is None) and (default != Ellipsis):
            resolved = default
        elif (got_value is not None):
            extra_args = []
            if type_orig is Annotated:
                expected_type = type_args[0]
                extra_args.extend(type_args[1:])
            if ((expected_type is str) or (expected_type is int)) or (issubclass(expected_type, Enum)):
                resolved = expected_type(got_value)
            elif (expected_type is bool):
                resolved = ((got_value == "true") or (got_value == "1")) or (got_value in extra_args)
            elif (expected_type is bytes):
                resolved = bytes.fromhex(got_value if "mac" not in extra_args else got_value.replace(":", ""))
            else:
                raise TypeError(f"Unsupported type: {expected_type} for key {key}")
        if resolved is not Ellipsis:
            data[key] = resolved
    return ntp(**data)


WPA_REGEX = re.compile(r"^(?P<asc>[\x20-\x7e]{8,63})$")

WEP_REGEX = re.compile("^(?:" +
    r"(?P<asc>[\x20-\x7e]{05}|[\x20-\x7e]{13}|[\x20-\x7e]{29})|" +
    r"(?P<hex>[0-9A-Fa-f]{10}|[0-9A-Fa-f]{26}|[0-9A-Fa-f]{58})|"
+ ")$")


def create_pbkdf2_wpapsk_key(ssid: bytes, password: bytes) -> bytes:
    """
    Creates a PBKDF2 WPA-PSK value from a SSID and password.
    Adapted from `hashlib.pbkdf2_hmac()`
    """
    inner = sha1()
    outer = sha1()
    
    passbytes = bytearray()
    passbytes.extend(password if len(password) <= 64 else sha1(password).digest())
    passbytes.extend(bytes(64 - len(passbytes)))

    inner.update(bytes(x ^ 0x36 for x in passbytes))
    outer.update(bytes(x ^ 0x5C for x in passbytes))

    def psuedo_random(data: bytes):
        icpy = inner.copy()
        ocpy = outer.copy()
        icpy.update(data)
        ocpy.update(icpy.digest())
        return ocpy.digest()

    output = bytearray()
    loop = 1
    while len(output) < 32:
        prev = psuedo_random(ssid + loop.to_bytes(4, 'big'))
        rkey = int.from_bytes(prev, 'big')
        for _ in range(4096 - 1):
            prev = psuedo_random(prev)
            rkey ^= int.from_bytes(prev, 'big')
        loop += 1
        output.extend(rkey.to_bytes(inner.digest_size, 'big'))
    return bytes(output[:32])


def validate_wifi_password(security: WiFiSecurity, password: str) -> bytes:
    """
    Checks whether the given password satisfies the requirements of the specified Wi-Fi 
    security model, and returns a WiFiPasswordValidationStatus reporting the validation outcome.
    """
    # WEP security
    if security == WiFiSecurity.WEP:
        match = WEP_REGEX.fullmatch(password)
        if not match:
            raise ValueError("invalid WEP password, it must be a ASCII string with one of lengths: 5, 13 or 29.")
        return bytes.fromhex(match.group("hex") or "") or match.group("asc").encode("ascii")
    # WPA-PSK password must only include printable ASCII characters
    elif (security == WiFiSecurity.WPA2) or (security == WiFiSecurity.WPA):
        match = WPA_REGEX.fullmatch(password)
        if not match:
            raise ValueError("invalid WPA password, it must be a ASCII string with a length of between 8 and 63 inclusive.")
        return match.group("asc").encode("ascii")
    return bytes()


class WirelessDrive:
    def __init__(self, hostname: str) -> None:
        self.hostname = hostname


    def remove_network(self, ssid: str):
        """
        Removes an existing network. Requires version >= 669.
        """
        query = dict(
            group = "saved",
            action = "delete",
            ssid = ssid.encode("ISO-8859-15").decode("utf-8")
        )
        return self.post_settings(query)


    def connect_network(self, ssid: str):
        """
        Connect to an already saved network. Requires version >= 669.
        """
        query = dict(
            group = "saved", 
            action = "connect", 
            ssid = ssid.encode("ISO-8859-15").decode("utf-8")
        )
        return self.post_settings(query)


    def set_sidelink_mode(self, mode: bool):
        """
        Change home network mode. Requires version >= 669.
        """
        return self.post_settings(dict(
            sidelinken = "true" if mode else "false"
        ))


    def set_ap_mode(self, mode: bool):
        """
        Change AP mode. Requires version >= 657.
        """
        return self.post_settings(dict(
            ap = "true" if mode else "false"
        ))

    
    def set_timeout(self, value: int):
        """
        Sets power saving timeout. Requires version >= 586.
        """
        if value > 2147483647:
            raise ValueError("setting a higher timeout than int32 limit causes device to soft-brick")
        return self.post_settings(dict(
            timeout = str(max(value, 0))
        ))


    def set_channel(self, value: int):
        """
        Sets the WLAN channel of the device to a zero-indexed channel number. 
        Channels #13 and #14 should be avoided in North America.

        Requires version >= 574. See more about WLAN channels:
        https://en.wikipedia.org/wiki/List_of_WLAN_channels#2.4_GHz_(802.11b/g/n/ax/be)
        """
        if (value < 0) or (value > 13):
            raise ValueError("channel number must be between 0 and 13 inclusive")
        return self.post_settings(dict(
            channel = str(value)
        ))


    def save_network(self, ssid: str, security: WiFiSecurity, password: str, legacy: bool = False):
        """
        Connects to a Wi-Fi access point with given its SSID and password.
        To a save network without overriding existing one, set `legacy` to False, however this will require device version >= 669.
        Otherwise set `legacy` to False since the device must override the existing network (meaning only one network at the same time)
        """
        query : Dict[str, Union[str, bytes]] = dict(
            group = "saved",
            action = "save",
            ssid = ssid.encode("ISO-8859-15").decode("utf-8"),
            security =
                "wep" if security == WiFiSecurity.WEP else
                "wpa" if (security == WiFiSecurity.WPA) or (security == WiFiSecurity.WPA2) else
                "none"
        )
        wifi_pass = validate_wifi_password(security, password)
        if security == WiFiSecurity.WEP:
            query["password"] = wifi_pass
        elif (security == WiFiSecurity.WPA) or (security == WiFiSecurity.WPA2):
            query["password"] = create_pbkdf2_wpapsk_key(ssid.encode("ISO-8859-15"), wifi_pass)
        return self.post_settings(query)


    def set_ap_password(self, ssid: Optional[str], security: WiFiSecurity, password: str, same_as_admin: Optional[bool] = None):
        """
        Set AP password. Using WPA2 is supported on build.code >= 703.
        """
        query : Dict[str, Union[str, bytes]] = dict(
            security =
                "wep" if security == WiFiSecurity.WEP else
                "wpa" if (security == WiFiSecurity.WPA) or (security == WiFiSecurity.WPA2) else
                "none"
        )
        if ssid and (len(ssid) > 32):
            raise ValueError("ssid can't be longer than 32 characters")
        if ((security == WiFiSecurity.WPA) or (security == WiFiSecurity.WPA2)) and not ssid:
            raise ValueError("an ssid is required for setting wpa passwords")
        if ssid:
            query["ssid"] = ssid
        wifi_pass = validate_wifi_password(security, password)
        if security != WiFiSecurity.PUBLIC:
            if security == WiFiSecurity.WEP:
                query["password"] = wifi_pass
            else:
                assert ssid
                query["password"] = create_pbkdf2_wpapsk_key(ssid.encode("ISO-8859-15"), wifi_pass)
        if same_as_admin is True:
            query["auth"] = "all"
            query["authowner"] = "owner"
            query["authhash"] = md5(f"owner:{ssid}:{password}".encode("ISO-8859-1")).digest().hex()
        elif same_as_admin is False:
            query["auth"] = "none"
        return self.post_settings(query, post_restart = True)


    def get_coex(self) -> List[Coex]:
        """
        Get a list of saved coex entries.
        """
        response = do_request(self.hostname, "/settings.xml", "GET",
            query = dict(group = "coex")
        )
        assert response.status == 200, "failed response"
        xmldata = ET.XML(response.body)
        assert xmldata.tag == "coexlist", f"unexpected xml tag '{xmldata.tag}'"
        result = []
        for el in xmldata.findall("./coex"):
            result.append(Coex(mac = bytes.fromhex(el.attrib["mac"]), name = el.attrib["name"], current = el.attrib.get("current") == "current"))
        return result


    def set_coex(self, name: Optional[str] = None):
        """
        Sets the currently connected device's MAC address as coex device, or removes it if name is not provided.
        TODO: Found in source code, not sure what does it really do.
        """
        query = dict(group = "coex", action = "save" if name else "delete")
        if name:
            query["name"] = name
        return self.post_settings(query)

    
    def get_networks(self, saved: bool) -> Union[List[Settings.NetworkInfo], NetworkScanState]:
        """
        Get a list of scanned networks, or get a list of saved networks instead if `saved` is True.
        """
        response = do_request(self.hostname, "/settings.xml", "GET",
            query = dict(group = "saved" if saved else "scan")
        )
        assert response.status == 200, "failed response"
        xmldata = ET.XML(response.body)
        if not saved:
            if xmldata.tag == "status":
                return NetworkScanState(xmldata.text)
        assert xmldata.tag == "ssidlist", f"unexpected xml tag '{xmldata.tag}'"

        result : List[Settings.NetworkInfo] = []
        for ssid in xmldata.findall("./ssid"):
            network = Settings.NetworkInfo(
                ssid = unquote(ssid.attrib["name"]).encode("ISO-8859-15").decode("utf-8"),
                security = WiFiSecurity(ssid.attrib["security"]),
                rssi = int(ssid.attrib.get("rssi", "") or -1),
                # This won't be True for when listing all saved networks even if there is a 
                # saved network that the device is currently connected to.
                # So, it only applies for scanned networks.
                connected = ssid.attrib.get("connected", "") == "connected",
                saved = bool(saved)
            )
            # Only include networks that has a SSID.
            if not network.ssid:
                continue
            result.append(network)
        return result


    def scan_networks(self, blocking: bool):
        """
        Scan for new networks, if blocking is True, blocks until a list of networks found.
        """

        def _block_for_scan(interval: float) -> List[Settings.NetworkInfo]:
            sleep(interval)
            networks = self.get_networks(saved = False)
            if type(networks) is NetworkScanState:
                if networks == NetworkScanState.SCANNING:
                    return _block_for_scan(2.0)
                elif networks == NetworkScanState.LOCKED:
                    return _block_for_scan(4.0)
                else:
                    self.post_settings(dict(group = "scan"))
                    return _block_for_scan(4.0)
            return cast(List[Settings.NetworkInfo], networks)

        saved_list = cast(List[Settings.NetworkInfo], self.get_networks(saved = True))
        self.post_settings(dict(group = "scan"))

        if blocking:
            # If the device is currently connected to a network,
            # then don't add the same SSID again.
            result : List[Settings.NetworkInfo] = []
            with ThreadPoolExecutor(max_workers=1) as executor:
                fut = executor.submit(_block_for_scan, 2.0)
                result.extend(fut.result())
            for old in saved_list:
                exist_in_new = next((new for new in result if new.ssid == old.ssid), None)
                if exist_in_new:
                    result.remove(exist_in_new)
                    result.append(Settings.NetworkInfo(*exist_in_new[:-1], saved = True))
                result.append(old)
            return result

    
    def push_firmware(self, file: bytes, is_xml: bool, is_wfd_v2: bool):
        """
        Uploads a firmware file to the device.

        is_xml: Must be True if settings.feature.firmwareupdate == 2
        is_wfd_v2: Must be True if settings.model == DeviceType.WS_V2, only is in effect when is_xml is False.
        """

        path: str = f"/files/{'AIRST.DF2' if not is_wfd_v2 else 'wfd.df3'}" if not is_xml else "/settings.xml"
        assert path, "firmware parameters are invalid!"

        response = do_request(self.hostname, path, "PUT",
            query = None if not is_xml else dict(group = "firmware"),
            body = file
        )
        print(response.body, file = stderr)
        if response.status == 507:
            raise ValueError("disk full")
        assert response.status in (200, 201, 204), f"status was {response.status}"
        return response


    def post_settings(self, query: Mapping[str, Union[bytes, str]], post_restart: bool = False):
        """
        Set device settings.
        """
        response = do_request(self.hostname, "/settings.xml", "POST",
            body = {**query, **(dict() if not post_restart else dict(restart = "allowed"))}
        )
        xmldata = ET.XML(response.body)
        assert xmldata.tag == "status"
        # Is there a pending reboot?
        extra = xmldata.attrib.get("restart", "") or None
        assert (extra is None) or (extra == "pending")
        return SettingsPushState((xmldata.text or "") + (":pending" if extra else ""))


    def get_settings(self):
        """
        Fetch settings from the device.
        """
        response = do_request(self.hostname, "/settings.xml", "GET")
        assert response.status == 200, "failed response"

        settings = ET.XML(response.body)
        assert settings.tag == "settings"

        device = xml_to_namedtuple(settings, Settings.Device, skip_falsy = True)
        feature = xml_to_namedtuple(settings.find("./features"), Settings.Feature)
        bitrate = xml_to_namedtuple(settings.find("./bitrate"), Settings.Bitrate, use_attributes = True)
        app_version = xml_to_namedtuple(settings.find("./appversion"), Settings.AppVersion)
        battery = xml_to_namedtuple(settings.find("./battery"), Settings.Battery, use_attributes = True)
        access_point = xml_to_namedtuple(settings.find("./ap"), Settings.AccessPoint, use_attributes = ("enabled", "clients",))
        sidelink = settings.find("./sidelink")
        sidelink = False if sidelink is None else sidelink.attrib.get("enabled") == "true"
        sxml = settings.find("./client")
        client = None if sxml is None else xml_to_namedtuple(sxml, Settings.Client, use_attributes = True)
        pxml = settings.find("./pendingfirmware")
        pendingfirmware = None if pxml is None else xml_to_namedtuple(pxml, Settings.PendingFirmware, use_attributes = True, skip_falsy = True)
        cards : List[Settings.Card] = []
        for card in settings.findall("./cards/card"):
            if card.attrib["status"].lower() == "none":
                continue
            cards.append(xml_to_namedtuple(card, Settings.Card, use_attributes = True))
        exml = settings.find("./storederror")
        storederror = None if exml is None else xml_to_namedtuple(exml, Settings.LastError, skip_falsy = True, use_attributes = True)
        
        return Settings(device, feature, bitrate, app_version, battery, access_point, cards, sidelink, pendingfirmware, storederror, client)