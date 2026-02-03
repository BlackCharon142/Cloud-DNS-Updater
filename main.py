import argparse
import asyncio
import socket
import aiohttp
import logging
from typing import List
from dns_updater import DNSUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_source_list(source_string: str) -> List[str]:
    """Parse comma-separated source list string into a list"""
    if not source_string or source_string.lower() == 'all':
        return []  # Empty list means use all sources
    
    return [s.strip().lower() for s in source_string.split(',') if s.strip()]

async def main():
    parser = argparse.ArgumentParser(description='Dynamic DNS Client')
    
    # Required arguments (conditionally required)
    parser.add_argument('--provider', choices=['arvan'], 
                        help='DNS provider (arvan)')
    parser.add_argument('--key', help='API key for DNS provider')
    parser.add_argument('--domain', help='Domain name')
    parser.add_argument('--records', 
                        help='Comma-separated list of record names (subdomains)')
    
    # IP configuration
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-4', '--ipv4', action='store_true', 
                       help='Use IPv4 only')
    group.add_argument('-6', '--ipv6', action='store_true', 
                       help='Use IPv6 only')
    group.add_argument('-46', '--dual-stack', action='store_true',
                       help='Use both IPv4 and IPv6 (dual-stack)')
    
    # IP source selection
    parser.add_argument('--sources', default='all',
                       help='Comma-separated list of IP sources to use, or "all" for all available sources')
    parser.add_argument('--exclude-sources', default='',
                       help='Comma-separated list of IP sources to exclude')
    parser.add_argument('--source-timeout', type=int, default=10,
                       help='Timeout for IP source checking in seconds')
    
    # Timing configuration
    parser.add_argument('--interval', type=int, default=60, 
                       help='Interval in seconds between checks')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout in seconds for DNS operations')
    
    # Validation mode
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate configuration without starting the update loop')
    parser.add_argument('--list-sources', action='store_true',
                       help='List all available IP sources and exit')
    
    args = parser.parse_args()

    # If list-sources flag is set, show available sources and exit
    if args.list_sources:
        from ip_sources import IPSourceManager
        ip_manager = IPSourceManager()
        
        print("Available IP sources:")
        print("=====================")
        for source in ip_manager.get_working_sources_info():
            print(f"{source['name']} (priority: {source['priority']})")
        return
    
    # Determine IP version(s) to use
    if args.dual_stack:
        ip_versions = [4, 6]
    elif args.ipv6:
        ip_versions = [6]
    else:
        ip_versions = [4]  # Default to IPv4
    
    # Parse records
    records = [r.strip() for r in args.records.split(',')]
    
    # Parse source lists
    include_sources = parse_source_list(args.sources)
    exclude_sources = parse_source_list(args.exclude_sources)
    
    # Create TCP connector - use AF_UNSPEC to support both IPv4 and IPv6
    connector = aiohttp.TCPConnector(family=socket.AF_UNSPEC, limit=10)
    timeout = aiohttp.ClientTimeout(total=args.timeout)
    
    async with aiohttp.ClientSession(
        connector=connector, 
        timeout=timeout
    ) as session:
        
        # Create DNS updaters for each IP version
        updaters = []
        for ip_version in ip_versions:
            updater = DNSUpdater(
                provider=args.provider,
                api_key=args.key,
                domain=args.domain,
                records=records,
                session=session,
                ip_version=ip_version,
                source_names=include_sources,
                exclude_sources=exclude_sources,
                source_timeout=args.source_timeout
            )
            updaters.append(updater)
        
        # Validate configuration
        try:
            for updater in updaters:
                await updater.validate_domain()
            logger.info(f"Domain {args.domain} validated with {args.provider} provider")
        except Exception as e:
            logger.error(f"Domain validation failed: {e}")
            return
        
        # If only validation mode, exit here
        if args.validate_only:
            logger.info("Configuration validated successfully. Exiting.")
            return
        
        # Start update loop
        await run_update_loop(updaters, args.interval)

async def run_update_loop(updaters: List[DNSUpdater], interval: int):
    """Run the main update loop for all updaters"""
    # Store current IPs for each updater
    current_ips = {id(updater): None for updater in updaters}
    
    while True:
        for updater in updaters:
            try:
                # Get current public IP using multi-source system
                new_ip = await updater.get_current_ip()
                
                # Update DNS if IP changed
                if new_ip != current_ips[id(updater)]:
                    logger.info(f"IPv{updater.ip_version} changed from {current_ips[id(updater)] or 'none'} to {new_ip}")
                    current_ips[id(updater)] = new_ip
                    await updater.update_dns_records(new_ip)
                else:
                    logger.info(f"IPv{updater.ip_version} unchanged: {current_ips[id(updater)]}")
                
            except asyncio.TimeoutError:
                logger.error(f"IPv{updater.ip_version}: Request timed out. Retrying after delay.")
                await asyncio.sleep(min(interval, 30))
            except aiohttp.ClientError as e:
                logger.error(f"IPv{updater.ip_version}: Network error: {e}. Retrying after delay.")
                await asyncio.sleep(min(interval, 30))
            except Exception as e:
                logger.error(f"IPv{updater.ip_version}: Error occurred: {e}. Retrying after delay.")
                await asyncio.sleep(min(interval, 60))
        
        # Wait for next check
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())