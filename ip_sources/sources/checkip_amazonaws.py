from typing import Dict, Optional
import aiohttp
from ..base_source import IPSource

class CheckIPAmazonAWSSource(IPSource):
    """Source using checkip.amazonaws.com service"""
    
    def __init__(self):
        super().__init__(name="checkip.amazonaws.com", priority=5)
    
    async def ping(self, session: aiohttp.ClientSession) -> bool:
        try:
            async with session.get("https://checkip.amazonaws.com", timeout=self.timeout) as response:
                self.is_working = response.status == 200
                return self.is_working
        except:
            self.is_working = False
            return False
    
    async def get_ips(self, session: aiohttp.ClientSession) -> Dict[str, Optional[str]]:
        results = {'ipv4': None, 'ipv6': None}
        
        try:
            async with session.get("https://checkip.amazonaws.com", timeout=self.timeout) as response:
                if response.status == 200:
                    text = await response.text()
                    results['ipv4'] = self._extract_ip_from_response(text, 4)
        except:
            pass
        
        return results