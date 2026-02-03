import aiohttp
import ipaddress
import asyncio
from abc import ABC, abstractmethod

class DNSProvider(ABC):
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.session = session
    
    @abstractmethod
    async def validate_domain(self, domain: str) -> None:
        """Validate the domain exists with the provider"""
        pass
    
    @abstractmethod
    async def update_dns_record(
        self, 
        domain: str, 
        record: str, 
        record_type: str, 
        new_ip: str
    ) -> None:
        """Update the DNS record with the new IP"""
        pass