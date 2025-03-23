"""
API module for direct 1:1 mapping to Namecheap API endpoints
"""

# Import all API modules to make them available through the api namespace
from .domains import DomainsAPI
from .ssl import SslAPI
from .users import UsersAPI

__all__ = ["DomainsAPI", "UsersAPI", "SslAPI"]
