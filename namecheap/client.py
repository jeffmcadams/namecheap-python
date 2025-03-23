"""
Namecheap API Python client

A Python wrapper for interacting with the Namecheap API.
"""

from typing import Dict, List, Union

from .api.domains import DomainsAPI
from .api.ssl import SslAPI
from .api.users import UsersAPI
from .base import BaseClient, ResponseDict, ResponseItem, ResponseList
from .enhanced.dns import EnhancedDnsAPI
from .enhanced.domains import EnhancedDomainsAPI


# Removed protocol imports that are no longer used

"""Client class definition removed as we're using direct imports and concrete types instead of Protocol"""


class EnhancedNamespace:
    """Namespace for enhanced functionality"""

    def __init__(self, client: "NamecheapClient") -> None:
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
        api_user: str,
        api_key: str,
        username: str,
        client_ip: str,
        sandbox: bool = True,
        debug: bool = False
    ) -> None:
        """
        Initialize the Namecheap API client

        Args:
            api_user: Namecheap API username
            api_key: Namecheap API key
            username: Namecheap account username
            client_ip: Client IP address
            sandbox: Whether to use the sandbox environment
            debug: Whether to enable debug mode
        """
        super().__init__(
            api_user, api_key, username, client_ip, sandbox, debug
        )

        # Initialize API namespaces
        self.domains = DomainsAPI(self)
        self.users = UsersAPI(self)
        self.ssl = SslAPI(self)

        # Initialize enhanced API functionality
        self.enhanced = EnhancedNamespace(self)
