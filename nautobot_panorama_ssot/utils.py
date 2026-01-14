from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)


class PanoramaClientError(Exception):
    pass


class PanoramaClient:
    """
    Thin Panorama XML API client.

    Constructor parameters:
      - base_url: e.g. "https://panorama.example.com"
      - api_key: (preferred) if available
      - username/password: optional; if api_key not provided, keygen will be attempted
      - verify_ssl: boolean
      - timeout: seconds
      - log_xml: if True, will emit returned XML to logger.debug (be careful with secrets)
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 30,
        log_xml: bool = False,
        logger_: Optional[logging.Logger] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.log_xml = log_xml
        self.logger = logger_ or logger

        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.timeout = timeout

        # ensure we have an API key
        if not self.api_key:
            if username and password:
                self.api_key = self._generate_api_key(username, password)
            else:
                raise PanoramaClientError("PanoramaClient requires an api_key or username+password")

    # ---- internal helpers ----
    def _request(self, params: Dict[str, str]) -> ET.Element:
        # Always include the key and type for config queries
        params = params.copy()
        params["key"] = self.api_key
        if "type" not in params:
            params["type"] = "config"

        url = f"{self.base_url}/api/"
        r = self.session.get(url, params=params, timeout=self.timeout)

        if r.status_code != 200:
            raise PanoramaClientError(f"Panorama HTTP {r.status_code}: {r.text}")

        if self.log_xml:
            # Redact the API key for security
            safe_params = params.copy()
            safe_params["key"] = "***REDACTED***"
            self.logger.debug("Panorama XML response (params=%s):\n%s", safe_params, r.text)

        try:
            root = ET.fromstring(r.text)
        except ET.ParseError as exc:
            raise PanoramaClientError(f"XML parse error: {exc}") from exc

        # check status element if present
        status = root.attrib.get("status")
        if status and status != "success":
            err = root.find(".//msg")
            err_text = err.text if err is not None else root.text or "unknown"
            raise PanoramaClientError(f"Panorama HTTP {r.status_code}: {r.text}")

        return root

    def _generate_api_key(self, user: str, password: str) -> str:
        """Call keygen to get API key from username/password."""
        params = {"type": "keygen", "user": user, "password": password}
        url = f"{self.base_url}/api/"
        r = self.session.get(url, params=params, timeout=self.timeout)
        if r.status_code != 200:
            raise PanoramaClientError(f"Keygen HTTP {r.status_code}: {r.text}")
        try:
            root = ET.fromstring(r.text)
        except ET.ParseError as exc:
            raise PanoramaClientError(f"Keygen XML parse error: {exc}") from exc

        # Panorama keygen returns <result><key>THEKEY</key></result> on success
        key_elem = root.find(".//key")
        if key_elem is None or not key_elem.text:
            raise PanoramaClientError("API key not found in keygen response")
        return key_elem.text.strip()

    # ---- xml helpers ----
    @staticmethod
    def _entry_to_dict(entry_elem: ET.Element) -> Dict[str, Any]:
        """
        Convert a Panorama <entry name="...">..</entry> into a dict.
        Includes sub-elements as keys. Does not fully flatten complicated nested XML,
        but supports common Panorama shapes (ip-netmask, fqdn, ip-range, description, protocol children).
        """
        data: Dict[str, Any] = {}
        # name attribute
        name = entry_elem.attrib.get("name") or entry_elem.attrib.get("@name")
        data["name"] = name or ""
        
        # loop children
        for child in list(entry_elem):
            # If child has children, collect a nested dict or list
            if list(child):
                # special-case: member lists (member tags)
                if all(grand.tag == "member" for grand in child):
                    data[child.tag] = [g.text for g in child if g.text]
                else:
                    # convert to dict shallow
                    sub = {}
                    for grand in child:
                        if list(grand):
                            # further nested -- represent as dict
                            sub[grand.tag] = PanoramaClient._entry_to_dict(grand)
                        else:
                            sub[grand.tag] = grand.text
                    data[child.tag] = sub
            else:
                data[child.tag] = child.text
                
        return data

    def _collect_entries(self, root: ET.Element, xpath_target: str) -> List[Dict[str, Any]]:
        """
        Given a parsed XML root returned from a Panorama config GET, find relevant <entry> elements
        and return list of dicts via _entry_to_dict.
        NOTE: root should be the <response> element from Panorama API.
        """
        results: List[Dict[str, Any]] = []
        # Panorama nests: <response><result>...<entry name="...">...
        # Find all entries under the result subtree
        for entry in root.findall(".//entry"):
            results.append(self._entry_to_dict(entry))
        return results

    def get_device_groups(self) -> List[str]:
        """Get list of device group names from Panorama."""
        xpath = "/config/devices/entry[@name='localhost.localdomain']/device-group"
        try:
            root = self._request({"action": "get", "xpath": xpath})
            device_groups = []
            for entry in root.findall(".//entry"):
                name = entry.attrib.get("name")
                if name:
                    device_groups.append(name)
            return device_groups
        except Exception as exc:
            self.logger.warning(f"Failed to get device groups: {exc}")
            return ["shared"]

    # ---- public getters ----
    def get_address_objects(self, device_group: str) -> List[Dict[str, Any]]:
        """
        Return list of address objects for device_group.
        Each dict will have at least 'name' and other keys like 'ip-netmask', 'ip-range', 'fqdn', 'description'.
        """
        # Try different XPath patterns
        xpaths_to_try = [
            f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{device_group}']/address",
            f"/config/devices/entry/device-group/entry[@name='{device_group}']/address",
            f"/config/shared/address" if device_group == "shared" else None,
        ]
        
        entries = []
        for xpath in xpaths_to_try:
            if xpath is None:
                continue
            try:
                root = self._request({"action": "get", "xpath": xpath})
                entries = self._collect_entries(root, xpath)
                if entries:
                    self.logger.debug(f"Found {len(entries)} address objects using xpath: {xpath}")
                    break
            except Exception as e:
                self.logger.debug(f"Failed to get address objects with xpath {xpath}: {e}")
                continue
        
        if not entries:
            self.logger.warning(f"No address objects found in device-group '{device_group}' (tried {len([x for x in xpaths_to_try if x])} XPath patterns)")
        
        # Process entries to extract value from ip-netmask, fqdn, ip-range, etc.
        for entry in entries:
            if "ip-netmask" in entry:
                entry["value"] = entry["ip-netmask"]
            elif "fqdn" in entry:
                entry["value"] = entry["fqdn"]
            elif "ip-range" in entry:
                entry["value"] = entry["ip-range"]
                
        return entries

    def get_address_groups(self, device_group: str) -> List[Dict[str, Any]]:
        xpath = f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{device_group}']/address-group"
        root = self._request({"action": "get", "xpath": xpath})
        entries = self._collect_entries(root, xpath)
        
        # Process static/dynamic members
        for entry in entries:
            if "static" in entry and isinstance(entry["static"], dict):
                entry["static"] = entry["static"].get("member", [])
            if "dynamic" in entry and isinstance(entry["dynamic"], dict):
                entry["dynamic_filter"] = entry["dynamic"].get("filter")
                
        return entries

    def get_service_objects(self, device_group: str) -> List[Dict[str, Any]]:
        xpath = f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{device_group}']/service"
        root = self._request({"action": "get", "xpath": xpath})
        entries = self._collect_entries(root, xpath)
        
        # Extract protocol and port
        for entry in entries:
            if "protocol" in entry and isinstance(entry["protocol"], dict):
                # protocol might be {'tcp': {'port': '80'}} or {'udp': {'port': '53'}}
                for proto, details in entry["protocol"].items():
                    entry["protocol"] = proto
                    if isinstance(details, dict) and "port" in details:
                        entry["port"] = details["port"]
                    break
                    
        return entries

    def get_service_groups(self, device_group: str) -> List[Dict[str, Any]]:
        xpath = f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{device_group}']/service-group"
        root = self._request({"action": "get", "xpath": xpath})
        entries = self._collect_entries(root, xpath)
        
        # Process members
        for entry in entries:
            if "members" in entry and isinstance(entry["members"], dict):
                entry["members"] = entry["members"].get("member", [])
                
        return entries

    def get_zones(self, device_group: str) -> List[Dict[str, Any]]:
        """
        Get zones for a device group. 
        Note: Zones might be in templates, but we'll try device-group first.
        """
        xpath = f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{device_group}']/zone"
        root = self._request({"action": "get", "xpath": xpath})
        return self._collect_entries(root, xpath)

    def get_applications(self, device_group: str) -> List[Dict[str, Any]]:
        xpath = f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{device_group}']/application"
        root = self._request({"action": "get", "xpath": xpath})
        return self._collect_entries(root, xpath)

    def get_application_groups(self, device_group: str) -> List[Dict[str, Any]]:
        xpath = f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{device_group}']/application-group"
        root = self._request({"action": "get", "xpath": xpath})
        entries = self._collect_entries(root, xpath)
        
        # Process members
        for entry in entries:
            if "members" in entry and isinstance(entry["members"], dict):
                entry["members"] = entry["members"].get("member", [])
                
        return entries

    def get_policies(self, device_group: str) -> List[Dict[str, Any]]:
        xpath = f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{device_group}']/pre-rulebase/security/policies"
        root = self._request({"action": "get", "xpath": xpath})
        return self._collect_entries(root, xpath)

    def get_policy_rules(self, device_group: str) -> List[Dict[str, Any]]:
        xpath = f"/config/devices/entry[@name='localhost.localdomain']/device-group/entry[@name='{device_group}']/pre-rulebase/security/rules"
        root = self._request({"action": "get", "xpath": xpath})
        return self._collect_entries(root, xpath)
