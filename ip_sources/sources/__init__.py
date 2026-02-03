from .identme import IdentMeSource
from .icanhazip import ICanHazIPSource
from .checkip_amazonaws import CheckIPAmazonAWSSource
from .ipify import IpifySource
from .ipnumberia import IPNumberiaSource  # Add this line
from .ipmyp import IPMypSource  # Add this line

# Registry of all available sources
SOURCES_REGISTRY = {
    'ident.me': IdentMeSource,
    'icanhazip.com': ICanHazIPSource,
    'checkip.amazonaws.com': CheckIPAmazonAWSSource,
    'ipify.org': IpifySource,
    'ipnumberia.com': IPNumberiaSource,  # Add this line
    'ipmyp.ir': IPMypSource,  # Add this line
}

# For backward compatibility, also export individual classes
__all__ = [
    'IdentMeSource',
    'ICanHazIPSource',
    'CheckIPAmazonAWSSource',
    'IpifySource',
    'IPNumberiaSource',  # Add this line
    'IPMypSource',  # Add this line
    'SOURCES_REGISTRY',
]