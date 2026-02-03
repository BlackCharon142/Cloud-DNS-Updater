from typing import Dict, Optional
import aiohttp
import re
from ..base_source import IPSource

class IPNumberiaSource(IPSource):
    """Source using ipnumberia.com service"""
    
    def __init__(self):
        super().__init__(name="ipnumberia.com", priority=0)
    
    async def ping(self, session: aiohttp.ClientSession) -> bool:
        try:
            async with session.get("https://ipnumberia.com", timeout=self.timeout) as response:
                self.is_working = response.status == 200
                return self.is_working
        except:
            self.is_working = False
            return False
    
    async def get_ips(self, session: aiohttp.ClientSession) -> Dict[str, Optional[str]]:
        results = {'ipv4': None, 'ipv6': None}
        
        try:
            async with session.get("https://ipnumberia.com", timeout=self.timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Extract IP using regex - looking for both patterns in the HTML
                    # Pattern 1: <div class="ip">89.219.90.11</div>
                    ip_pattern1 = r'<div\s+class="ip">([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})</div>'
                    
                    # Pattern 2: In the table cell <td>89.219.90.11</td>
                    ip_pattern2 = r'<td>([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})</td>'
                    
                    # Try pattern 1 first (more specific)
                    match1 = re.search(ip_pattern1, html)
                    if match1:
                        ip = match1.group(1)
                        if self._validate_ip(ip, 4):
                            results['ipv4'] = ip
                    
                    # If pattern 1 didn't work, try pattern 2
                    if not results['ipv4']:
                        match2 = re.search(ip_pattern2, html)
                        if match2:
                            ip = match2.group(1)
                            if self._validate_ip(ip, 4):
                                results['ipv4'] = ip
                    
                    # Note: ipnumberia.com only shows IPv4
                    
        except Exception as e:
            # Log the error but don't crash
            pass
        
        return results
    
    def _validate_ip(self, ip: str, version: int) -> bool:
        """Helper method to validate IP format"""
        try:
            # Use the parent class method
            return bool(self._extract_ip_from_response(ip, version))
        except:
            return False