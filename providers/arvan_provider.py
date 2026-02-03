import asyncio
import aiohttp
import logging
from .base_provider import DNSProvider

logger = logging.getLogger(__name__)

class ArvanProvider(DNSProvider):
    BASE_URL = "https://napi.arvancloud.ir/cdn/4.0"
    DEFAULT_TIMEOUT = 30  # seconds
    
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Apikey {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def validate_domain(self, domain: str) -> None:
        """Validate domain exists in ArvanCloud account"""
        url = f"{self.BASE_URL}/domains/{domain}"
        async with self.session.get(url, headers=self._get_headers()) as response:
            if response.status == 404:
                raise ValueError(f"Domain '{domain}' not found in your ArvanCloud account")
            response.raise_for_status()
    
    async def update_dns_record(
        self, 
        domain: str, 
        record: str, 
        record_type: str, 
        new_ip: str
    ) -> None:
        """Update or create DNS record in ArvanCloud"""
        # Prepare record data
        record_data = {
            "type": record_type,
            "name": record,
            "value": [{"ip": new_ip}],
            "ttl": 120,
            "cloud": False,
            "upstream_https": "default",
            "ip_filter_mode": {
                "count": "single",
                "order": "none",
                "geo_filter": "none"
            }
        }
        
        try:
            # Get existing records
            records_url = f"{self.BASE_URL}/domains/{domain}/dns-records"
            async with self.session.get(records_url, headers=self._get_headers()) as response:
                response.raise_for_status()
                records = await response.json()
            
            record_id = None
            
            # Find matching record
            for r in records["data"]:
                if r["name"] == record and r["type"] == record_type:
                    record_id = r["id"]
                    break
            
            # Update or create record
            if record_id:
                update_url = f"{self.BASE_URL}/domains/{domain}/dns-records/{record_id}"
                async with self.session.put(
                    update_url, 
                    headers=self._get_headers(), 
                    json=record_data
                ) as response:
                    response.raise_for_status()
                logger.info(f"Updated DNS record {record}.{domain} with IP {new_ip}")
            else:
                async with self.session.post(
                    records_url, 
                    headers=self._get_headers(), 
                    json=record_data
                ) as response:
                    response.raise_for_status()
                logger.info(f"Created DNS record {record}.{domain} with IP {new_ip}")
                
        except aiohttp.ClientResponseError as e:
            logger.error(f"Failed to update record {record}: {e.status} {e.message}")
        except asyncio.TimeoutError:
            logger.error(f"Timeout updating record {record}")
        except Exception as e:
            logger.error(f"Error updating record {record}: {str(e)}")