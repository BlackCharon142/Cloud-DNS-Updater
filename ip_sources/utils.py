import ipaddress
from typing import List, Optional

def validate_ip_address(ip: str, version: Optional[int] = None) -> bool:
    """Validate an IP address"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        if version and ip_obj.version != version:
            return False
        return True
    except ValueError:
        return False

def compare_ip_lists(ip_list1: List[str], ip_list2: List[str]) -> bool:
    """Compare two lists of IPs, ignoring order"""
    return set(ip_list1) == set(ip_list2)