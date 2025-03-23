"""
Base domain operations for the Namecheap API
"""
from typing import Any, Dict, List, Optional, Tuple


class DomainsBaseAPI:
    """Base API methods for domains namespace"""

    def __init__(self, client):
        """
        Initialize the domains API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def _split_domain_name(self, domain_name: str) -> Tuple[str, str]:
        """
        Split a domain name into its SLD and TLD parts

        Args:
            domain_name: Full domain name (e.g., "example.com")

        Returns:
            Tuple containing (SLD, TLD) parts (e.g., ("example", "com"))
        """
        parts = domain_name.split(".")
        sld = parts[0]
        tld = ".".join(parts[1:])
        return sld, tld

    def check(self, domains: List[str]) -> Dict[str, Any]:
        """
        Check if domains are available for registration

        Args:
            domains: List of domains to check availability (max 50)

        Returns:
            Dictionary with availability information for each domain.
            The result is a dictionary with a "DomainCheckResult" key that contains
            a list of dictionaries, each with domain information including:
            - Domain: domain name
            - Available: whether the domain is available (boolean)
            - IsPremiumName: whether the domain is a premium name (boolean)
            - PremiumRegistrationPrice: price for premium domains

        Raises:
            ValueError: If more than 50 domains are provided
            NamecheapException: If the API returns an error
        """
        if len(domains) > 50:
            raise ValueError(
                "Maximum of 50 domains can be checked in a single API call")

        # Format the domain list according to API requirements
        domain_list = ",".join(domains)
        params = {"DomainList": domain_list}

        # Make the API request
        return self.client._make_request("namecheap.domains.check", params)

    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "NAME",
        list_type: str = "ALL",
        search_term: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of domains in the user's account

        Args:
            page: Page number to return (default: 1)
            page_size: Number of domains to return per page (default: 20, max: 100)
            sort_by: Column to sort by (NAME, NAME_DESC, EXPIREDATE, EXPIREDATE_DESC, CREATEDATE, CREATEDATE_DESC)
            list_type: Type of domains to list (ALL, EXPIRING, EXPIRED)
            search_term: Keyword to look for in the domain list

        Returns:
            Dictionary with domain list information

        Raises:
            ValueError: If page_size is greater than 100
            NamecheapException: If the API returns an error
        """
        if page_size > 100:
            raise ValueError("Maximum page size is 100")

        valid_sort_options = [
            "NAME",
            "NAME_DESC",
            "EXPIREDATE",
            "EXPIREDATE_DESC",
            "CREATEDATE",
            "CREATEDATE_DESC",
        ]
        if sort_by not in valid_sort_options:
            raise ValueError(f"sort_by must be one of {valid_sort_options}")

        valid_list_types = ["ALL", "EXPIRING", "EXPIRED"]
        if list_type not in valid_list_types:
            raise ValueError(f"list_type must be one of {valid_list_types}")

        params = {
            "Page": page,
            "PageSize": page_size,
            "SortBy": sort_by,
            "ListType": list_type,
        }

        if search_term:
            params["SearchTerm"] = search_term

        return self.client._make_request("namecheap.domains.getList", params)

    def get_contacts(self, domain_name: str) -> Dict[str, Any]:
        """
        Get contact information for a domain

        Args:
            domain_name: The domain name to get contact information for

        Returns:
            Dictionary with contact information for the domain

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {"DomainName": sld, "TLD": tld}
        return self.client._make_request("namecheap.domains.getContacts", params)

    def get_info(self, domain_name: str) -> Dict[str, Any]:
        """
        Get information about a domain

        Args:
            domain_name: The domain name to get information for

        Returns:
            Dictionary with domain information

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {
            "DomainName": sld,
            "TLD": tld,
        }
        return self.client._make_request("namecheap.domains.getInfo", params)

    def get_tld_list(self) -> Dict[str, Any]:
        """
        Get a list of available TLDs

        Returns:
            Dictionary with TLD information

        Raises:
            NamecheapException: If the API returns an error
        """
        return self.client._make_request("namecheap.domains.getTldList")

    def renew(
        self, domain_name: str, years: int = 1, promotion_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Renew a domain

        Args:
            domain_name: The domain name to renew
            years: Number of years to renew the domain for (default: 1)
            promotion_code: Promotional (coupon) code for the domain renewal

        Returns:
            Dictionary with domain renewal information

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {"DomainName": sld, "TLD": tld, "Years": years}

        if promotion_code:
            params["PromotionCode"] = promotion_code

        return self.client._make_request("namecheap.domains.renew", params)
