from typing import Dict, Optional
import aiohttp
from ..base_source import IPSource

class IdentMeSource(IPSource):
    """Source using ident.me service"""
    
    def __init__(self):
        super().__init__(name="ident.me", priority=2)
    
    async def ping(self, session: aiohttp.ClientSession) -> bool:
        try:
            async with session.get("https://v4.ident.me", timeout=self.timeout) as response:
                self.is_working = response.status == 200
                return self.is_working
        except:
            self.is_working = False
            return False
    
    async def get_ips(self, session: aiohttp.ClientSession) -> Dict[str, Optional[str]]:
        results = {'ipv4': None, 'ipv6': None}
        
        try:
            # IPv4
            async with session.get("https://v4.ident.me", timeout=self.timeout) as response:
                if response.status == 200:
                    text = await response.text()
                    results['ipv4'] = self._extract_ip_from_response(text, 4)
            
            # IPv6
            async with session.get("https://v6.ident.me", timeout=self.timeout) as response:
                if response.status == 200:
                    text = await response.text()
                    results['ipv6'] = self._extract_ip_from_response(text, 6)
                    
        except:
            pass
        
        return results