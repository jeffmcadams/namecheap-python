"""
Domain transfer operations for domains API
"""
from typing import Any, Dict, List, Optional


class TransferAPI:
    """Transfer API methods for domains namespace"""

    def __init__(self, client):
        """
        Initialize the transfer API

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

    def create(
        self,
        domain_name: str,
        years: int = 1,
        epp_code: Optional[str] = None,
        promotion_code: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Transfers a domain to Namecheap

        Args:
            domain_name: Domain to transfer
            years: Number of years to renew during transfer (default: 1)
            epp_code: EPP/Auth code for the domain
            promotion_code: Promotion code for the transfer
            **kwargs: Additional parameters to pass to the API

        Returns:
            Dictionary with transfer creation result

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)
        params = {
            "DomainName": domain_name,
            "Years": years
        }

        if epp_code:
            params["EPPCode"] = epp_code

        if promotion_code:
            params["PromotionCode"] = promotion_code

        # Add any additional parameters
        params.update(kwargs)

        return self.client._make_request("namecheap.domains.transfer.create", params)

    def get_status(self, transfer_id: int) -> Dict[str, Any]:
        """
        Gets the status of a domain transfer

        Args:
            transfer_id: The transfer ID to check

        Returns:
            Dictionary with transfer status information

        Raises:
            NamecheapException: If the API returns an error
        """
        params = {"TransferID": transfer_id}
        return self.client._make_request("namecheap.domains.transfer.getStatus", params)

    def update_status(self, transfer_id: int, resubmit: bool = False) -> Dict[str, Any]:
        """
        Updates the status of a domain transfer

        Args:
            transfer_id: The transfer ID to update
            resubmit: Whether to resubmit the transfer

        Returns:
            Dictionary with transfer update result

        Raises:
            NamecheapException: If the API returns an error
        """
        params = {
            "TransferID": transfer_id,
            "Resubmit": "true" if resubmit else "false"
        }
        return self.client._make_request("namecheap.domains.transfer.updateStatus", params)

    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "TRANSFERDATE",
        list_type: str = "ALL"
    ) -> Dict[str, Any]:
        """
        Gets the list of domain transfers

        Args:
            page: Page number to return (default: 1)
            page_size: Number of transfers to return per page (default: 20)
            sort_by: Column to sort by (TRANSFERDATE, TRANSFERDATE_DESC, DOMAINNAME, DOMAINNAME_DESC)
            list_type: Type of transfers to list (ALL, INPROGRESS, CANCELLED, COMPLETED)

        Returns:
            Dictionary with transfer list information

        Raises:
            ValueError: If parameters are invalid
            NamecheapException: If the API returns an error
        """
        if page_size > 100:
            raise ValueError("Maximum page size is 100")

        valid_sort_options = [
            "TRANSFERDATE",
            "TRANSFERDATE_DESC",
            "DOMAINNAME",
            "DOMAINNAME_DESC"
        ]
        if sort_by not in valid_sort_options:
            raise ValueError(f"sort_by must be one of {valid_sort_options}")

        valid_list_types = ["ALL", "INPROGRESS", "CANCELLED", "COMPLETED"]
        if list_type not in valid_list_types:
            raise ValueError(f"list_type must be one of {valid_list_types}")

        params = {
            "Page": page,
            "PageSize": page_size,
            "SortBy": sort_by,
            "ListType": list_type
        }

        return self.client._make_request("namecheap.domains.transfer.getList", params)
