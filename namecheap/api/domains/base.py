"""
Base domain operations for the Namecheap API
"""
from typing import Any, Dict, List, Optional, Tuple

# Common error codes shared across domain operations
COMMON_DOMAIN_ERRORS = {
    "2019166": {
        "explanation": "Domain not found",
        "fix": "Verify the domain exists and is spelled correctly"
    },
    "2016166": {
        "explanation": "Domain is not associated with your account",
        "fix": "Check that the domain is registered with your Namecheap account"
    },
    "2030166": {
        "explanation": "Domain name not available",
        "fix": "The domain may be taken or not available for registration"
    },
    "UNKNOWN_ERROR": {
        "explanation": "Domain operation failed",
        "fix": "Verify all parameters are correct and try again"
    }
}


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

    def check(self, domains: List[str]) -> List[Dict[str, Any]]:
        """
        Check if domains are available for registration

        Args:
            domains: List of domain names to check (e.g., ["example.com", "example.net"])

        Returns:
            List of domain availability results:
            [
                {
                    "Domain": "example.com",
                    "Available": False,
                    "IsPremiumName": True,  # Whether this is a premium domain
                    "PremiumRegistrationPrice": "10.99",  # Registration price if available
                    "IcannFee": "0.18"  # ICANN fee if available
                },
                ...
            ]

        Raises:
            NamecheapException: If the API returns an error
        """
        if not domains:
            return []

        error_codes = {
            "2030166": {
                "explanation": "Invalid request syntax",
                "fix": "Check that domain names are properly formatted"
            },
            "2030180": {
                "explanation": "TLD is not supported",
                "fix": "This TLD is not supported for availability check"
            },
            "2030283": {
                "explanation": "Too many domain names provided",
                "fix": "Maximum of 50 domains can be checked at once"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to check domain availability",
                "fix": "Check the domain formats and try again"
            }
        }

        # Prepare domain string, comma-separated
        domain_list = ",".join(domains)

        # Make API request
        response = self.client._make_request(
            "namecheap.domains.check",
            {"DomainList": domain_list},
            error_codes=error_codes
        )

        # Use the normalize_api_response method
        return self.client.normalize_api_response(
            response=response,
            result_key="DomainCheckResult",
            return_type="list"
        )

    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "NAME",
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of domains in the user's account

        Args:
            page: Page number to retrieve (default: 1)
            page_size: Number of domains per page (default: 20, max: 100)
            sort_by: Field to sort by (default: "NAME", options: NAME, EXPIRE, CREATE)
            filters: Optional filters for the domain list, can include:
                    - ListType: ALL, EXPIRING, EXPIRED (default: ALL)
                    - SearchTerm: Search term for domain names
                    - DeadFromDate: Date from which to include expired domains
                    - DeadToDate: Date until which to include expired domains
                    - ExpireFromDate: Date from which to include expiring domains
                    - ExpireToDate: Date until which to include expiring domains

        Returns:
            Dictionary with domain list information:
            {
                "domains": [
                    {
                        "ID": "12345",
                        "Name": "example.com",
                        "User": "username",
                        "Created": "2020-01-01",
                        "Expires": "2022-01-01",
                        "IsExpired": False,
                        "IsLocked": True,
                        "AutoRenew": False,
                        "WhoisGuard": "ENABLED",
                        ... other fields ...
                    },
                    ...
                ],
                "paging": {
                    "total_items": 100,
                    "total_pages": 5,
                    "current_page": 1,
                    "page_size": 20
                }
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for domain list
        error_codes = {
            **COMMON_DOMAIN_ERRORS,
            "2012166": {
                "explanation": "Failed to retrieve domain list",
                "fix": "Check that your account has domains"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to retrieve domain list",
                "fix": "Check API credentials and try again"
            }
        }

        # Base parameters
        params = {
            "Page": page,
            "PageSize": page_size,
            "SortBy": sort_by,
        }

        # Add optional filters if provided
        if filters:
            for key, value in filters.items():
                params[key] = value

        # Make API request
        response = self.client._make_request(
            "namecheap.domains.getList",
            params,
            error_codes=error_codes
        )

        # Normalize the domains list
        domains = self.client.normalize_api_response(
            response=response,
            result_key="DomainGetListResult.Domain",
            datetime_fields=["Created", "Expires"],
            return_type="list"
        )

        # Get paging information
        paging_info = response.get("DomainGetListResult", {})
        paging = {
            "total_items": int(paging_info.get("@TotalItems", 0)),
            "total_pages": int(paging_info.get("@TotalPages", 0)),
            "current_page": int(paging_info.get("@CurrentPage", 0)),
            "page_size": int(paging_info.get("@PageSize", 0))
        }

        return {
            "domains": domains,
            "paging": paging
        }

    def get_contacts(self, domain_name: str) -> Dict[str, Any]:
        """
        Get contact information for a domain

        Args:
            domain_name: The domain name to get contact information for

        Returns:
            Dictionary with contact information for the domain:
            {
                "domain": "example.com",
                "registrant": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    ...
                },
                "tech": { ... },
                "admin": { ... },
                "aux_billing": { ... }
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for getting domain contacts
        error_codes = {
            **COMMON_DOMAIN_ERRORS,
            "4019337": {
                "explanation": "Unable to retrieve domain contacts",
                "fix": "The domain contacts may not be accessible or properly configured"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get domain contacts",
                "fix": "Verify that '{domain_name}' exists and is registered with Namecheap"
            }
        }

        sld, tld = self._split_domain_name(domain_name)
        params = {"DomainName": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.getContacts",
            params,
            error_codes,
            {"domain_name": domain_name}
        )

        # Contact types to extract
        contact_types = ["Registrant", "Tech", "Admin", "AuxBilling"]

        # Field mapping for contact details
        contact_field_mapping = {
            "FirstName": "first_name",
            "LastName": "last_name",
            "Organization": "organization",
            "JobTitle": "job_title",
            "Address1": "address1",
            "Address2": "address2",
            "City": "city",
            "StateProvince": "state",
            "StateProvinceChoice": "state_choice",
            "PostalCode": "postal_code",
            "Country": "country",
            "Phone": "phone",
            "PhoneExt": "phone_ext",
            "Fax": "fax",
            "EmailAddress": "email",
        }

        result = {
            "domain": domain_name
        }

        # Extract contact information for each type
        if "DomainContactsResult" in response:
            for contact_type in contact_types:
                contact_data = response["DomainContactsResult"].get(
                    contact_type, {})
                contact_info = {}

                for api_field, norm_field in contact_field_mapping.items():
                    if api_field in contact_data:
                        contact_info[norm_field] = contact_data[api_field]

                result[contact_type.lower()] = contact_info

        return result

    def get_info(self, domain_name: str) -> Dict[str, Any]:
        """
        Get information about a domain

        API Documentation: https://www.namecheap.com/support/api/methods/domains/get-info/

        Error Codes:
            5019169: Unknown exceptions
            2030166: Domain name not available
            2019166: Username not available
            2016166: Access denied

        Args:
            domain_name: The domain name to get information for

        Returns:
            Dictionary with domain information

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for getting domain info
        error_codes = {
            **COMMON_DOMAIN_ERRORS,
            "5019169": {
                "explanation": "Unknown exception occurred",
                "fix": "Try again later or contact Namecheap support"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get domain information",
                "fix": "Verify that '{domain_name}' exists and is registered with Namecheap"
            }
        }

        sld, tld = self._split_domain_name(domain_name)
        params = {"DomainName": sld, "TLD": tld}

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.domains.getInfo",
            params,
            error_codes,
            {"domain_name": domain_name}
        )

    def get_tld_list(self) -> Dict[str, Any]:
        """
        Get a list of available TLDs

        Returns:
            Dictionary with TLD information:
            {
                "tlds": [
                    {
                        "Name": ".com",
                        "MinRegisterYears": 1,
                        "MaxRegisterYears": 10,
                        "IsSupportsIDN": True
                    },
                    ...
                ]
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for getting TLD list
        error_codes = {
            **COMMON_DOMAIN_ERRORS,
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get TLD list",
                "fix": "Try again later or contact Namecheap support"
            }
        }

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.getTldList",
            {},
            error_codes=error_codes
        )

        # Get TLDs from response
        tlds = self.client.normalize_api_response(
            response=response,
            result_key="Tlds.Tld",
            return_type="list"
        )

        return {
            "tlds": tlds
        }

    def renew(
        self, domain_name: str, years: int = 1, promotion_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Renew a domain

        API Documentation: https://www.namecheap.com/support/api/methods/domains/renew/

        Error Codes:
            2015166: Failed to update years for your domain
            4023166: Error occurred while renewing domain
            4022337: Error in refunding funds

        Args:
            domain_name: The domain name to renew
            years: Number of years to renew the domain for (default: 1)
            promotion_code: Promotional (coupon) code for the domain renewal

        Returns:
            Dictionary with domain renewal information

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for domain renewal
        error_codes = {
            **COMMON_DOMAIN_ERRORS,
            "2015166": {
                "explanation": "Failed to update years for your domain",
                "fix": "Verify that the domain is eligible for renewal"
            },
            "4023166": {
                "explanation": "Error occurred while renewing domain",
                "fix": "Check your account balance and domain status"
            },
            "4022337": {
                "explanation": "Error in refunding funds",
                "fix": "Contact Namecheap support for assistance with refund issues"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to renew domain",
                "fix": "Verify that '{domain_name}' exists and is eligible for renewal"
            }
        }

        sld, tld = self._split_domain_name(domain_name)
        params = {"DomainName": sld, "TLD": tld, "Years": years}

        if promotion_code:
            params["PromotionCode"] = promotion_code

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.domains.renew",
            params,
            error_codes,
            {"domain_name": domain_name}
        )
