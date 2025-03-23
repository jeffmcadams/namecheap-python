"""
SSL API operations
"""
from typing import Any, Dict, List, Optional


class SslAPI:
    """SSL API methods"""

    def __init__(self, client):
        """
        Initialize the SSL API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        list_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the list of SSL certificates

        Args:
            page: Page number to return (default: 1)
            page_size: Number of certificates to return per page (default: 20, max: 100)
            sort_by: Column to sort by
            list_type: Type of certificates to list

        Returns:
            Dictionary with certificate list information

        Raises:
            ValueError: If page_size is greater than 100
            NamecheapException: If the API returns an error
        """
        if page_size > 100:
            raise ValueError("Maximum page size is 100")

        params = {
            "Page": page,
            "PageSize": page_size
        }

        if sort_by:
            params["SortBy"] = sort_by

        if list_type:
            params["ListType"] = list_type

        return self.client._make_request("namecheap.ssl.getList", params)

    def create(
        self,
        years: int,
        certificate_type: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create a new SSL certificate

        Args:
            years: Years of validity
            certificate_type: Type of SSL certificate
            **kwargs: Additional parameters for the API

        Returns:
            Dictionary with certificate creation result

        Raises:
            NamecheapException: If the API returns an error
        """
        params = {
            "Years": years,
            "Type": certificate_type
        }

        # Add optional parameters
        params.update(kwargs)

        return self.client._make_request("namecheap.ssl.create", params)

    def get_info(self, certificate_id: int) -> Dict[str, Any]:
        """
        Get information about an SSL certificate

        Args:
            certificate_id: The certificate ID

        Returns:
            Dictionary with certificate information

        Raises:
            NamecheapException: If the API returns an error
        """
        params = {"CertificateID": certificate_id}
        return self.client._make_request("namecheap.ssl.getInfo", params)

    def parse_csr(self, csr: str) -> Dict[str, Any]:
        """
        Parse a Certificate Signing Request (CSR)

        Args:
            csr: The CSR text

        Returns:
            Dictionary with parsed CSR information

        Raises:
            NamecheapException: If the API returns an error
        """
        params = {"csr": csr}
        return self.client._make_request("namecheap.ssl.parseCSR", params)

    def activate(
        self,
        certificate_id: int,
        csr: str,
        web_server_type: str,
        approver_email: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Activate an SSL certificate

        Args:
            certificate_id: The certificate ID
            csr: The CSR text
            web_server_type: Type of web server
            approver_email: Email address for domain approval
            **kwargs: Additional parameters for the API

        Returns:
            Dictionary with activation result

        Raises:
            NamecheapException: If the API returns an error
        """
        params = {
            "CertificateID": certificate_id,
            "CSR": csr,
            "WebServerType": web_server_type,
            "ApproverEmail": approver_email
        }

        # Add optional parameters
        params.update(kwargs)

        return self.client._make_request("namecheap.ssl.activate", params)
