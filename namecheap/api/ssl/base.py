"""
SSL API operations
"""

from typing import Any, Dict, Optional

# Common error codes shared across SSL certificate operations
COMMON_SSL_ERRORS = {
    "1011102": {
        "explanation": "API Key is invalid or API access has not been enabled",
        "fix": "Please verify your API key and ensure API access is enabled at https://ap.www.namecheap.com/settings/tools/apiaccess/",
    },
    "1011125": {
        "explanation": "API command name is invalid",
        "fix": "Check the API command name in your request",
    },
    "1016144": {
        "explanation": "API user authentication failed",
        "fix": "Verify your API user credentials and ensure your client IP is whitelisted",
    },
    "3050900": {
        "explanation": "Unknown error from provider",
        "fix": "Contact Namecheap support for assistance with this error",
    },
    "UNKNOWN_ERROR": {
        "explanation": "An unknown error occurred",
        "fix": "Please check your request parameters and try again. If the issue persists, contact Namecheap support.",
    },
}


class SslAPI:
    """SSL API methods"""

    def __init__(self, client: Any) -> None:
        """
        Initialize the SSL API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def get_list(
        self,
        list_type: str = "",
        keyword: str = "",
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        sort_by: str = "",
    ) -> Dict[str, Any]:
        """
        Get list of SSL certificates for the user

        Args:
            list_type: Type of list to return (optional)
            keyword: Keyword to filter by (optional)
            page: Page number to return (optional)
            page_size: Number of items per page (optional)
            sort_by: Field to sort by (optional)

        Returns:
            Dictionary containing list of SSL certificates
        """
        # Set up error codes specific to this endpoint
        error_codes = {
            **COMMON_SSL_ERRORS,
            "2015280": {
                "explanation": "Invalid list type",
                "fix": "Please use a valid list type such as 'All', 'Processing', etc.",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to retrieve SSL certificate list",
                "fix": "Please check your request parameters and try again",
            },
        }

        # Build parameters
        params = {}
        if list_type:
            params["ListType"] = list_type
        if keyword:
            params["SearchTerm"] = keyword
        if page is not None:
            params["Page"] = str(page)
        if page_size is not None:
            params["PageSize"] = str(page_size)
        if sort_by:
            params["SortBy"] = sort_by

        # Make API request
        response = self.client._make_request(
            "namecheap.ssl.getList", params, error_codes=error_codes
        )

        # Process pagination info
        if "Paging" in response:
            old_paging = response.pop("Paging", {})
            # Create a new dictionary with correct types
            new_paging = {}
            if "TotalItems" in old_paging:
                new_paging["TotalItems"] = int(old_paging["TotalItems"])
            if "CurrentPage" in old_paging:
                new_paging["CurrentPage"] = int(old_paging["CurrentPage"])
            # Copy any other fields
            for key, value in old_paging.items():
                if key not in ["TotalItems", "CurrentPage"]:
                    new_paging[key] = value
            # Add the new paging back to the response
            response["Paging"] = new_paging

        # Return normalized response
        result: Dict[str, Any] = self.client.normalize_api_response(response=response)
        return result

    def create(
        self, certificate_type: str, years: int, promotion_code: str = ""
    ) -> Dict[str, Any]:
        """
        Create a new SSL certificate

        Args:
            certificate_type: Type of SSL certificate to create
            years: Number of years to register the certificate for
            promotion_code: Promotional/coupon code (optional)

        Returns:
            Dictionary containing information about the created certificate
        """
        # Validate inputs
        if not certificate_type:
            raise ValueError("Certificate type is required")
        if not years or not isinstance(years, int) or years < 1:
            raise ValueError("Years must be a positive integer")

        # Set up error codes specific to this endpoint
        error_codes = {
            **COMMON_SSL_ERRORS,
            "2015280": {
                "explanation": "Invalid certificate type",
                "fix": "Please use a valid certificate type",
            },
            "2030175": {
                "explanation": "Failed to create certificate",
                "fix": "Please check certificate type and other parameters",
            },
            "3012230": {
                "explanation": "Invalid promo code",
                "fix": "Please provide a valid promotional code or leave it blank",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to create SSL certificate",
                "fix": "Please check your request parameters and try again",
            },
        }

        # Build parameters
        params = {"Type": certificate_type, "Years": years}
        if promotion_code:
            params["PromotionCode"] = promotion_code

        # Make API request
        response = self.client._make_request(
            "namecheap.ssl.create", params, error_codes=error_codes
        )

        # Return normalized response
        result: Dict[str, Any] = self.client.normalize_api_response(
            response=response, result_key="SSLCreateResult"
        )
        return result

    def get_info(self, certificate_id: int) -> Dict[str, Any]:
        """
        Get information about a specific SSL certificate

        Args:
            certificate_id: ID of the certificate to get info for

        Returns:
            Dictionary containing information about the certificate
        """
        # Validate inputs
        if not certificate_id or not isinstance(certificate_id, int):
            raise ValueError("Certificate ID must be a positive integer")

        # Set up error codes specific to this endpoint
        error_codes = {
            **COMMON_SSL_ERRORS,
            "2030166": {
                "explanation": "Certificate not found",
                "fix": "Please check the certificate ID",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to retrieve SSL certificate info",
                "fix": "Please check your request parameters and try again",
            },
        }

        # Build parameters
        params = {"CertificateID": certificate_id}

        # Make API request
        response = self.client._make_request(
            "namecheap.ssl.getInfo", params, error_codes=error_codes
        )

        # Return normalized response
        result: Dict[str, Any] = self.client.normalize_api_response(
            response=response, result_key="SSLGetInfoResult"
        )
        return result

    def activate(
        self,
        certificate_id: int,
        csr: str,
        web_server_type: str,
        approver_email: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Activate an SSL certificate

        Args:
            certificate_id: ID of the certificate to activate
            csr: Certificate Signing Request content
            web_server_type: Type of web server
            approver_email: Email address to approve the certificate
            **kwargs: Additional parameters such as:
                - HTTPDCValidation (bool)
                - AdminFirstName, AdminLastName, AdminEmail, etc.

        Returns:
            Dictionary containing information about the activation result
        """
        # Validate inputs
        if not certificate_id or not isinstance(certificate_id, int):
            raise ValueError("Certificate ID must be a positive integer")
        if not csr or not isinstance(csr, str):
            raise ValueError("CSR must be a non-empty string")
        if not web_server_type or not isinstance(web_server_type, str):
            raise ValueError("Web server type must be a non-empty string")
        if not approver_email or not isinstance(approver_email, str):
            raise ValueError("Approver email must be a non-empty string")

        # Set up error codes specific to this endpoint
        error_codes = {
            **COMMON_SSL_ERRORS,
            "2011330": {
                "explanation": "Certificate already activated",
                "fix": "This certificate has already been activated",
            },
            "2030166": {
                "explanation": "Certificate not found",
                "fix": "Please check the certificate ID",
            },
            "2030330": {
                "explanation": "Invalid CSR format",
                "fix": "Please provide a valid Certificate Signing Request",
            },
            "2030331": {
                "explanation": "Invalid approver email",
                "fix": "Please provide a valid approver email address",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to activate SSL certificate",
                "fix": "Please check your request parameters and try again",
            },
        }

        # Build parameters
        params = {
            "CertificateID": certificate_id,
            "CSR": csr,
            "WebServerType": web_server_type,
            "ApproverEmail": approver_email,
        }

        # Add any additional parameters
        for key, value in kwargs.items():
            params[key] = value

        # Make API request
        response = self.client._make_request(
            "namecheap.ssl.activate", params, error_codes=error_codes
        )

        # Return normalized response
        result: Dict[str, Any] = self.client.normalize_api_response(
            response=response, result_key="SSLActivateResult"
        )
        return result

    def resend_approver_email(self, certificate_id: int) -> Dict[str, Any]:
        """
        Resend the approver email for an SSL certificate

        Args:
            certificate_id: ID of the certificate

        Returns:
            Dictionary containing information about the result
        """
        # Validate inputs
        if not certificate_id or not isinstance(certificate_id, int):
            raise ValueError("Certificate ID must be a positive integer")

        # Set up error codes specific to this endpoint
        error_codes = {
            **COMMON_SSL_ERRORS,
            "2030166": {
                "explanation": "Certificate not found",
                "fix": "Please check the certificate ID",
            },
            "2011330": {
                "explanation": "Invalid certificate status",
                "fix": "This certificate may not be in a state where approver email can be resent",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to resend approver email",
                "fix": "Please check your request parameters and try again",
            },
        }

        # Build parameters
        params = {"CertificateID": certificate_id}

        # Make API request
        response = self.client._make_request(
            "namecheap.ssl.resendApproverEmail", params, error_codes=error_codes
        )

        # Return normalized response
        result: Dict[str, Any] = self.client.normalize_api_response(
            response=response, result_key="SSLResendApproverEmailResult"
        )
        return result
