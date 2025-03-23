"""
Domains API namespace
"""

from .base import DomainsBaseAPI
from .dns import DnsAPI
from .ns import NsAPI
from .transfer import TransferAPI


class DomainsAPI(DomainsBaseAPI):
    """
    Domains API client providing access to all domains-related API endpoints

    This includes:
    - Basic domain operations (check, getList, etc.)
    - DNS management operations through the dns namespace
    - Nameserver operations through the ns namespace
    - Transfer operations through the transfer namespace
    """

    def __init__(self, client):
        super().__init__(client)

        # Initialize subnamespaces
        self.dns = DnsAPI(client)
        self.ns = NsAPI(client)
        self.transfer = TransferAPI(client)
