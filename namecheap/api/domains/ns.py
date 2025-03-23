"""
Nameserver operations for domains API
"""
from typing import Any, Dict, Optional


class NsAPI:
    """Nameserver API methods for domains namespace"""

    def __init__(self, client):
        """
        Initialize the nameserver API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def _split_domain_name(self, domain_name: str):
        """Split domain name into SLD and TLD parts"""
        parts = domain_name.split(".")
        sld = parts[0]
        tld = ".".join(parts[1:])
        return sld, tld

    def create(self, domain_name: str, nameserver: str, ip: str) -> Dict[str, Any]:
        """
        Creates a new nameserver

        Args:
            domain_name: Domain to create the nameserver for
            nameserver: Nameserver to create
            ip: IP address for the nameserver

        Returns:
            Dictionary with nameserver creation result

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver,
            "IP": ip
        }
        return self.client._make_request("namecheap.domains.ns.create", params)

    def delete(self, domain_name: str, nameserver: str) -> Dict[str, Any]:
        """
        Deletes a nameserver

        Args:
            domain_name: Domain the nameserver is associated with
            nameserver: Nameserver to delete

        Returns:
            Dictionary with nameserver deletion result

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver
        }
        return self.client._make_request("namecheap.domains.ns.delete", params)

    def update(self, domain_name: str, nameserver: str, old_ip: str, new_ip: str) -> Dict[str, Any]:
        """
        Updates the IP address of a registered nameserver

        Args:
            domain_name: Domain the nameserver is associated with
            nameserver: Nameserver to update
            old_ip: Old IP address
            new_ip: New IP address

        Returns:
            Dictionary with nameserver update result

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver,
            "OldIP": old_ip,
            "IP": new_ip
        }
        return self.client._make_request("namecheap.domains.ns.update", params)

    def get_info(self, domain_name: str, nameserver: str) -> Dict[str, Any]:
        """
        Retrieves information about a registered nameserver

        Args:
            domain_name: Domain the nameserver is associated with
            nameserver: Nameserver to get information for

        Returns:
            Dictionary with nameserver information

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver
        }
        return self.client._make_request("namecheap.domains.ns.getInfo", params)
