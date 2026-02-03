from typing import Dict, Optional
import aiohttp
import json
from ..base_source import IPSource

class IpifySource(IPSource):
    """Source using ipify.org API"""
    
    def __init__(self):
        super().__init__(name="ipify.org", priority=3)
    
    async def ping(self, session: aiohttp.ClientSession) -> bool:
        try:
            async with session.get("https://api.ipify.org?format=json", timeout=self.timeout) as response:
                self.is_working = response.status == 200
                return self.is_working
        except:
            self.is_working = False
            return False
    
    async def get_ips(self, session: aiohttp.ClientSession) -> Dict[str, Optional[str]]:
        results = {'ipv4': None, 'ipv6': None}
        
        try:
            # IPv4
            async with session.get("https://api.ipify.org?format=json", timeout=self.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    results['ipv4'] = self._extract_ip_from_response(data.get('ip', ''), 4)
            
            # IPv6
            async with session.get("https://api6.ipify.org?format=json", timeout=self.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    results['ipv6'] = self._extract_ip_from_response(data.get('ip', ''), 6)
                    
        except:
            pass
        
        return results