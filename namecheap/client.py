"""
Namecheap API Python client

A Python wrapper for interacting with the Namecheap API.
"""

from typing import Any, Dict, List, Optional

from .base import BaseClient
from .api.domains import DomainsAPI
from .api.users import UsersAPI
from .api.ssl import SslAPI
from .enhanced.domains import EnhancedDomainsAPI
from .enhanced.dns import EnhancedDnsAPI


class EnhancedNamespace:
    """Namespace for enhanced functionality"""

    def __init__(self, client):
        """
        Initialize the enhanced namespace

        Args:
            client: The Namecheap API client instance
        """
        self.client = client
        self.domains = EnhancedDomainsAPI(client)
        self.dns = EnhancedDnsAPI(client)


class NamecheapClient(BaseClient):
    """
    Client for interacting with the Namecheap API

    This client provides:
    1. Direct 1:1 mapping to the Namecheap API (client.domains.check, etc.)
    2. Enhanced functionality through client.enhanced namespace
    """

    def __init__(
        self,
        api_user: Optional[str] = None,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        client_ip: Optional[str] = None,
        sandbox: Optional[bool] = None,
        debug: bool = False,
        load_env: bool = True,
    ):
        """
        Initialize the Namecheap API client

        Args:
            api_user: Your Namecheap username for API access
            api_key: Your API key generated from Namecheap account
            username: Your Namecheap username (typically the same as api_user)
            client_ip: The whitelisted IP address making the request
            sandbox: Whether to use the sandbox environment (default: read from env or True)
            debug: Whether to enable debug logging (default: False)
            load_env: Whether to load credentials from environment variables (default: True)
        """
        super().__init__(
            api_user=api_user,
            api_key=api_key,
            username=username,
            client_ip=client_ip,
            sandbox=sandbox,
            debug=debug,
            load_env=load_env,
        )

        # Initialize API namespaces
        self.domains = DomainsAPI(self)
        self.users = UsersAPI(self)
        self.ssl = SslAPI(self)

        # Initialize enhanced functionality
        self.enhanced = EnhancedNamespace(self)
