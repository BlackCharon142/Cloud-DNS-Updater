import aiohttp
import ipaddress
from abc import ABC, abstractmethod
from typing import Optional, Dict

class IPSource(ABC):
    """Base class for IP detection sources"""
    
    def __init__(self, name: str, priority: int = 5):
        self.name = name
        self.priority = priority  # 0-9, where 0 is highest priority
        self.timeout = 10  # Default timeout, can be overridden
        self.is_working = False
    
    @abstractmethod
    async def ping(self, session: aiohttp.ClientSession) -> bool:
        """Check if this source is currently working/reachable"""
        pass
    
    @abstractmethod
    async def get_ips(self, session: aiohttp.ClientSession) -> Dict[str, Optional[str]]:
        """
        Retrieve IP addresses from this source
        
        Returns:
            Dict with keys 'ipv4' and/or 'ipv6', values are IP strings or None
        """
        pass
    
    def _extract_ip_from_response(self, text: str, version: int) -> Optional[str]:
        """Helper to extract and validate IP from text response"""
        if not text:
            return None
        
        # Clean the response
        text = text.strip()
        
        # Try to parse as IP
        try:
            ip = ipaddress.ip_address(text)
            if ip.version == version:
                return str(ip)
        except ValueError:
            # Try to find IP in text (some services return HTML or JSON)
            import re
            if version == 4:
                pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            else:
                pattern = r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b'
            
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    ip = ipaddress.ip_address(match)
                    if ip.version == version:
                        return str(ip)
                except ValueError:
                    continue
        
        return None