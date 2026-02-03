import aiohttp
import ipaddress
import asyncio
from typing import List, Optional
from providers import get_provider
from ip_sources import IPSourceManager

class DNSUpdater:
    def __init__(
        self, 
        provider: str, 
        api_key: str, 
        domain: str, 
        records: list, 
        session: aiohttp.ClientSession,
        ip_version: int = 4,
        source_names: Optional[List[str]] = None,
        exclude_sources: Optional[List[str]] = None,
        source_timeout: int = 10
    ):
        self.provider = get_provider(provider)(api_key, session)
        self.domain = domain
        self.records = records
        self.session = session
        self.ip_version = ip_version
        self.source_timeout = source_timeout
        
        # Initialize IP source manager with selected sources
        self.ip_manager = IPSourceManager(
            source_names=source_names,
            exclude_sources=exclude_sources
        )
    
    async def validate_domain(self) -> None:
        """Validate the domain exists with the provider"""
        await self.provider.validate_domain(self.domain)
    
    async def get_current_ip(self) -> str:
        """Get the current public IP address using selected sources"""
        # Discover working sources first
        await self.ip_manager.discover_working_sources(
            self.session,
            timeout=self.source_timeout
        )
        
        # Get IP from sources with priority-based selection
        ip = await self.ip_manager.get_current_ip(
            self.session, 
            self.ip_version,
            timeout=self.source_timeout
        )
        
        if not ip:
            raise ValueError(f"Could not retrieve IPv{self.ip_version} address from any source")
        
        return ip
    
    async def update_dns_records(self, new_ip: str) -> None:
        """Update all DNS records with the new IP"""
        # Determine record type based on IP version
        ip_version = ipaddress.ip_address(new_ip).version
        record_type = 'a' if ip_version == 4 else 'aaaa'
        
        # Update records concurrently
        tasks = []
        for record in self.records:
            task = self.provider.update_dns_record(
                domain=self.domain,
                record=record,
                record_type=record_type,
                new_ip=new_ip
            )
            tasks.append(task)
        
        # Run all updates concurrently with timeout
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors
        for record, result in zip(self.records, results):
            if isinstance(result, Exception):
                print(f"Error updating record {record}: {result}")