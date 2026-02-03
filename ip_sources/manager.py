import aiohttp
import asyncio
from typing import List, Dict, Optional, Tuple
import logging

from ip_sources.base_source import IPSource
from .sources import SOURCES_REGISTRY  # We'll create this registry

logger = logging.getLogger(__name__)

class IPSourceManager:
    """Manages multiple IP detection sources with priority-based selection"""
    
    def __init__(
        self, 
        source_names: Optional[List[str]] = None,
        exclude_sources: Optional[List[str]] = None
    ):
        """
        Initialize IP source manager
        
        Args:
            source_names: List of source names to include. If None or empty, include all.
            exclude_sources: List of source names to exclude.
        """
        self.all_sources = self._initialize_all_sources()
        self.sources = self._filter_sources(source_names, exclude_sources)
        self.working_sources: List[IPSource] = []
    
    def _initialize_all_sources(self) -> List[IPSource]:
        """Initialize all available IP sources from registry"""
        sources = []
        for name, source_class in SOURCES_REGISTRY.items():
            try:
                source = source_class()
                sources.append(source)
            except Exception as e:
                logger.warning(f"Failed to initialize source {name}: {e}")
        return sources
    
    def _filter_sources(
        self, 
        include_names: Optional[List[str]], 
        exclude_names: Optional[List[str]]
    ) -> List[IPSource]:
        """Filter sources based on include/exclude lists"""
        filtered_sources = []
        
        # Start with all sources if no include list is provided
        if not include_names:
            filtered_sources = self.all_sources.copy()
        else:
            # Include only specified sources
            include_set = set(name.lower() for name in include_names)
            for source in self.all_sources:
                if source.name.lower() in include_set:
                    filtered_sources.append(source)
        
        # Apply exclude filter
        if exclude_names:
            exclude_set = set(name.lower() for name in exclude_names)
            filtered_sources = [
                source for source in filtered_sources 
                if source.name.lower() not in exclude_set
            ]
        
        return filtered_sources
    
    async def discover_working_sources(
        self, 
        session: aiohttp.ClientSession, 
        timeout: int = 10
    ) -> List[str]:
        """Ping all sources to find which ones are working"""
        # Set timeout for all sources
        for source in self.sources:
            source.timeout = timeout
        
        tasks = [source.ping(session) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        self.working_sources = []
        working_names = []
        
        for source, result in zip(self.sources, results):
            if not isinstance(result, Exception) and result:
                self.working_sources.append(source)
                working_names.append(source.name)
                logger.info(f"Source {source.name} (priority {source.priority}) is working")
            else:
                logger.warning(f"Source {source.name} is not reachable")
        
        # Sort by priority (lower number = higher priority)
        self.working_sources.sort(key=lambda x: x.priority)
        
        logger.info(f"Found {len(self.working_sources)} working sources")
        return working_names
    
    async def get_current_ip(
        self, 
        session: aiohttp.ClientSession, 
        ip_version: int = 4,
        timeout: int = 10
    ) -> Optional[str]:
        """
        Get current IP using all working sources, with priority-based selection
        
        Args:
            ip_version: 4 for IPv4, 6 for IPv6
            
        Returns:
            Selected IP address or None if no sources could provide it
        """
        if not self.working_sources:
            await self.discover_working_sources(session)
        
        if not self.working_sources:
            logger.error("No working IP sources available")
            return None
        
        # Get IPs from all working sources concurrently
        tasks = [source.get_ips(session) for source in self.working_sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect IPs by priority
        ip_candidates = []
        
        for source, result in zip(self.working_sources, results):
            if isinstance(result, Exception):
                logger.warning(f"Source {source.name} failed: {result}")
                continue
            
            key = 'ipv4' if ip_version == 4 else 'ipv6'
            ip = result.get(key)
            
            if ip:
                ip_candidates.append({
                    'ip': ip,
                    'source': source.name,
                    'priority': source.priority
                })
                logger.debug(f"Source {source.name} returned {key}: {ip}")
        
        if not ip_candidates:
            logger.error(f"No sources could provide IPv{ip_version} address")
            return None
        
        # Group IPs by value
        ip_groups = {}
        for candidate in ip_candidates:
            ip = candidate['ip']
            if ip not in ip_groups:
                ip_groups[ip] = []
            ip_groups[ip].append(candidate)
        
        # Find the most common IP
        if len(ip_groups) == 1:
            # All sources agree
            selected_ip = list(ip_groups.keys())[0]
            logger.info(f"All sources agree on IP: {selected_ip}")
            return selected_ip
        
        # Sources disagree - use priority-based selection
        logger.warning(f"Sources disagree on IPs: {list(ip_groups.keys())}")
        
        # For each IP, get the highest priority source that reported it
        ip_priority = {}
        for ip, candidates in ip_groups.items():
            # Get the highest priority (lowest number) for this IP
            highest_priority = min(c['priority'] for c in candidates)
            ip_priority[ip] = highest_priority
        
        # Select IP with highest priority (lowest number)
        selected_ip = min(ip_priority.items(), key=lambda x: x[1])[0]
        
        logger.info(f"Selected IP {selected_ip} based on priority")
        return selected_ip
    
    async def get_all_ips(self, session: aiohttp.ClientSession) -> Dict[str, Optional[str]]:
        """Get both IPv4 and IPv6 addresses"""
        if not self.working_sources:
            await self.discover_working_sources(session)
        
        ipv4 = await self.get_current_ip(session, ip_version=4)
        ipv6 = await self.get_current_ip(session, ip_version=6)
        
        return {
            'ipv4': ipv4,
            'ipv6': ipv6
        }
    
    def get_working_sources_info(self) -> List[Dict]:
        """Get information about working sources"""
        return [
            {
                'name': source.name,
                'priority': source.priority,
                'working': source.is_working
            }
            for source in self.sources
        ]