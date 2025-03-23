"""
SSL API operations
"""
from typing import Any, Dict, List, Optional

# Common error codes shared across SSL certificate operations
COMMON_SSL_ERRORS = {
    "1010104": {
        "explanation": "Parameter Command is missing",
        "fix": "Ensure the API command is properly specified"
    },
    "1011105": {
        "explanation": "Parameter ClientIP is invalid",
        "fix": "Provide a valid client IP address"
    },
    "2011294": {
        "explanation": "Parameter CertificateID is invalid",
        "fix": "Verify the certificate ID is correct"
    },
    "2011300": {
        "explanation": "Invalid SSL Certificate Type",
        "fix": "Use a supported SSL certificate type"
    },
    "2011301": {
        "explanation": "Certificate not found",
        "fix": "Verify the certificate ID exists in your account"
    },
    "UNKNOWN_ERROR": {
        "explanation": "SSL operation failed",
        "fix": "Verify all parameters are correct and try again"
    }
}


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

        API Documentation: https://www.namecheap.com/support/api/methods/ssl/get-list/

        Error Codes:
            2011300: Invalid SSL Certificate Type

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
        # Error codes for getting SSL certificate list
        error_codes = {
            **COMMON_SSL_ERRORS,
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get SSL certificate list",
                "fix": "Verify all parameters are valid and try again"
            }
        }

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

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.ssl.getList",
            params,
            error_codes,
            {}
        )

    def create(
        self,
        years: int,
        certificate_type: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Create a new SSL certificate

        API Documentation: https://www.namecheap.com/support/api/methods/ssl/create/

        Error Codes:
            2011295: Approver email is invalid
            2011296: Invalid CSR - Wildcard not supported with this type of certificate
            2011297: Invalid WebServerType

        Args:
            years: Years of validity
            certificate_type: Type of SSL certificate
            **kwargs: Additional parameters for the API

        Returns:
            Dictionary with certificate creation result

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for creating an SSL certificate
        error_codes = {
            **COMMON_SSL_ERRORS,
            "2011295": {
                "explanation": "Approver email is invalid",
                "fix": "Provide a valid approver email address"
            },
            "2011296": {
                "explanation": "Invalid CSR - Wildcard not supported with this type of certificate",
                "fix": "Ensure the CSR matches the certificate type"
            },
            "2011297": {
                "explanation": "Invalid WebServerType",
                "fix": "Use a supported web server type"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to create SSL certificate",
                "fix": "Verify all parameters are correct and try again"
            }
        }

        params = {
            "Years": years,
            "Type": certificate_type
        }

        # Add optional parameters
        params.update(kwargs)

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.ssl.create",
            params,
            error_codes,
            {"certificate_type": certificate_type}
        )

    def get_info(self, certificate_id: int) -> Dict[str, Any]:
        """
        Get information about an SSL certificate

        API Documentation: https://www.namecheap.com/support/api/methods/ssl/get-info/

        Error Codes:
            2011300: Invalid SSL Certificate Type
            2011301: Certificate not found

        Args:
            certificate_id: The certificate ID

        Returns:
            Dictionary with certificate information

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for getting SSL certificate info
        error_codes = {
            **COMMON_SSL_ERRORS,
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get certificate information",
                "fix": "Verify that certificate ID '{certificate_id}' exists"
            }
        }

        params = {"CertificateID": certificate_id}

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.ssl.getInfo",
            params,
            error_codes,
            {"certificate_id": certificate_id}
        )

    def parse_csr(self, csr: str) -> Dict[str, Any]:
        """
        Parse a Certificate Signing Request (CSR)

        API Documentation: https://www.namecheap.com/support/api/methods/ssl/parse-csr/

        Error Codes:
            2011300: Invalid CSR

        Args:
            csr: The CSR text

        Returns:
            Dictionary with parsed CSR information

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for parsing CSR
        error_codes = {
            **COMMON_SSL_ERRORS,
            "2011300": {
                "explanation": "Invalid CSR",
                "fix": "Check that the CSR is properly formatted"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to parse CSR",
                "fix": "Verify that the CSR is valid and try again"
            }
        }

        params = {"csr": csr}

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.ssl.parseCSR",
            params,
            error_codes,
            {}
        )

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

        API Documentation: https://www.namecheap.com/support/api/methods/ssl/activate/

        Error Codes:
            2011295: Approver email is invalid
            2011296: Invalid CSR - Wildcard not supported with this type of certificate
            2011300: Invalid SSL Certificate Type

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
        # Error codes for activating an SSL certificate
        error_codes = {
            **COMMON_SSL_ERRORS,
            "2011295": {
                "explanation": "Approver email is invalid",
                "fix": "Provide a valid approver email address"
            },
            "2011296": {
                "explanation": "Invalid CSR - Wildcard not supported with this type of certificate",
                "fix": "Ensure the CSR matches the certificate type"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to activate certificate",
                "fix": "Verify that certificate ID '{certificate_id}' exists and all parameters are correct"
            }
        }

        params = {
            "CertificateID": certificate_id,
            "CSR": csr,
            "WebServerType": web_server_type,
            "ApproverEmail": approver_email
        }

        # Add optional parameters
        params.update(kwargs)

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.ssl.activate",
            params,
            error_codes,
            {"certificate_id": certificate_id}
        )
