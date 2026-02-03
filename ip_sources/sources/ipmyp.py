from typing import Dict, Optional
import aiohttp
import re
import json
from ..base_source import IPSource

class IPMypSource(IPSource):
    """Source using ipmyp.ir service with AJAX request"""
    
    def __init__(self):
        super().__init__(name="ipmyp.ir", priority=1)
    
    async def ping(self, session: aiohttp.ClientSession) -> bool:
        try:
            async with session.get("https://ipmyp.ir", timeout=self.timeout) as response:
                self.is_working = response.status == 200
                return self.is_working
        except:
            self.is_working = False
            return False
    
    async def get_ips(self, session: aiohttp.ClientSession) -> Dict[str, Optional[str]]:
        results = {'ipv4': None, 'ipv6': None}
        
        try:
            # Step 1: Get the initial page
            async with session.get("https://ipmyp.ir", timeout=self.timeout) as response:
                if response.status != 200:
                    return results
                
                html = await response.text()
                
                # Find the root element first
                root_pattern = r'<div[^>]*id="ipvj-lite-root"[^>]*>'
                root_match = re.search(root_pattern, html, re.IGNORECASE)
                
                if not root_match:
                    return results
                
                # Extract data-ajax and data-nonce attributes (order independent)
                ajax_url_match = re.search(r'data-ajax="([^"]+)"', root_match.group(0))
                nonce_match = re.search(r'data-nonce="([^"]+)"', root_match.group(0))
                
                if not ajax_url_match or not nonce_match:
                    return results
                
                ajax_url = ajax_url_match.group(1)
                nonce = nonce_match.group(1)
            
            # Step 2: Make the AJAX request
            form_data = aiohttp.FormData()
            form_data.add_field('action', 'ipvj_lite_lookup')
            form_data.add_field('nonce', nonce)
            # No 'ip' parameter to get our own IP
            
            async with session.post(
                ajax_url,
                data=form_data,
                headers={
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': 'https://ipmyp.ir/',
                    'Origin': 'https://ipmyp.ir'
                },
                timeout=self.timeout
            ) as ajax_response:
                if ajax_response.status != 200:
                    return results
                
                data = await ajax_response.json()
                
                if data.get('success') and 'data' in data:
                    ip = data['data'].get('ip')
                    if ip and self._validate_ip(ip, 4):
                        results['ipv4'] = ip
            
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            pass
        except Exception as e:
            pass
        
        return results
    
    def _validate_ip(self, ip: str, version: int) -> bool:
        """Helper method to validate IP format"""
        try:
            return bool(self._extract_ip_from_response(ip, version))
        except:
            return False