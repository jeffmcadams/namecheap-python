"""
Base domain operations for the Namecheap API
"""

from typing import Dict, List, Optional, TypedDict

import tldextract

from ...base import BaseClient

# Define proper types for the API responses


class DomainCheckResult(TypedDict):
    Domain: str
    Available: bool
    IsPremiumName: bool
    PremiumRegistrationPrice: str
    IcannFee: str


class ContactInfo(TypedDict, total=False):
    first_name: str
    last_name: str
    organization: str
    job_title: str
    address1: str
    address2: str
    city: str
    state: str
    state_choice: str
    postal_code: str
    country: str
    phone: str
    phone_ext: str
    fax: str
    email: str


class PagingInfo(TypedDict):
    total_items: int
    total_pages: int
    current_page: int
    page_size: int


class DomainInfo(TypedDict, total=False):
    ID: str
    Name: str
    User: str
    Created: str
    Expires: str
    IsExpired: bool
    IsLocked: bool
    AutoRenew: bool
    WhoisGuard: str


class DomainListResult(TypedDict):
    domains: List[DomainInfo]
    paging: PagingInfo


class DomainContactsResult(TypedDict):
    domain: str
    registrant: ContactInfo
    tech: ContactInfo
    admin: ContactInfo
    auxbilling: ContactInfo


class TldInfo(TypedDict, total=False):
    Name: str
    MinRegisterYears: int
    MaxRegisterYears: int
    IsSupportsIDN: bool


class TldListResult(TypedDict):
    tlds: List[TldInfo]


# Common error codes shared across domain operations
COMMON_DOMAIN_ERRORS = {
    "2019166": {
        "explanation": "Domain not found",
        "fix": "Verify the domain exists and is spelled correctly",
    },
    "2016166": {
        "explanation": "Domain is not associated with your account",
        "fix": "Check that the domain is registered with your Namecheap account",
    },
    "2030166": {
        "explanation": "Domain name not available",
        "fix": "The domain may be taken or not available for registration",
    },
    "UNKNOWN_ERROR": {
        "explanation": "Domain operation failed",
        "fix": "Verify all parameters are correct and try again",
    },
}


class DomainsBaseAPI:
    """Base API methods for domains namespace"""

    def __init__(self, client: BaseClient) -> None:
        """
        Initialize the domains API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def check(self, domains: List[str]) -> List[Dict[str, object]]:
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
                "fix": "Check that domain names are properly formatted",
            },
            "2030180": {
                "explanation": "TLD is not supported",
                "fix": "This TLD is not supported for availability check",
            },
            "2030283": {
                "explanation": "Too many domain names provided",
                "fix": "Maximum of 50 domains can be checked at once",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to check domain availability",
                "fix": "Check the domain formats and try again",
            },
        }

        # Prepare domain string, comma-separated
        domain_list = ",".join(domains)

        # Make API request
        response = self.client._make_request(
            "namecheap.domains.check",
            {"DomainList": domain_list},
            error_codes=error_codes,
        )

        # Use the normalize_api_response method to get results
        results = self.client.normalize_api_response(
            response=response, 
            result_key="DomainCheckResult", 
            boolean_fields=["Available", "IsPremiumName"],
            return_type="list"
        )

        # Results are now properly typed as ResponseList (List[Dict[str, object]])
        return results

    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "NAME",
        filters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, object]:
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
                "fix": "Check that your account has domains",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to retrieve domain list",
                "fix": "Check API credentials and try again",
            },
        }

        # Base parameters
        params = {
            "Page": str(page),
            "PageSize": str(page_size),
            "SortBy": sort_by,
        }

        # Add optional filters if provided
        if filters:
            for key, value in filters.items():
                params[key] = value

        # Make API request
        response = self.client._make_request(
            "namecheap.domains.getList", params, error_codes=error_codes
        )

        # Normalize the domains list
        domains_raw = self.client.normalize_api_response(
            response=response,
            result_key="DomainGetListResult.Domain",
            datetime_fields=["Created", "Expires"],
            return_type="list",
        )

        # No casting needed
        domains = domains_raw

        # Get paging information
        paging_info = response.get("DomainGetListResult", {})

        # Define helper function to parse integers safely
        def parse_int(value: object) -> int:
            if value is None:
                return 0

            try:
                return int(str(value))
            except (ValueError, TypeError):
                return 0

        # Build paging info with proper typing
        paging: Dict[str, object] = {
            "total_items": parse_int(
                paging_info.get("@TotalItems")
                if isinstance(paging_info, dict)
                else None
            ),
            "total_pages": parse_int(
                paging_info.get("@TotalPages")
                if isinstance(paging_info, dict)
                else None
            ),
            "current_page": parse_int(
                paging_info.get("@CurrentPage")
                if isinstance(paging_info, dict)
                else None
            ),
            "page_size": parse_int(
                paging_info.get("@PageSize") if isinstance(paging_info, dict) else None
            ),
        }

        # Construct a compatible dictionary with explicit type annotation
        result: Dict[str, object] = {"domains": domains, "paging": paging}
        return result

    def get_contacts(self, domain_name: str) -> Dict[str, object]:
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
                "fix": "The domain contacts may not be accessible or properly configured",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get domain contacts",
                "fix": "Verify that '{domain_name}' exists and is registered with Namecheap",
            },
        }

        extract = tldextract.extract(domain_name)
        sld, tld = extract.domain, extract.suffix
        params = {"DomainName": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.getContacts",
            params,
            error_codes,
            {"domain_name": domain_name},
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

        # Return a structurally compatible dictionary
        result: Dict[str, object] = {
            "domain": domain_name,
            "registrant": {},
            "tech": {},
            "admin": {},
            "auxbilling": {},
        }

        # Extract contact information for each type
        domain_contacts = response.get("DomainContactsResult", {})
        if domain_contacts:
            for contact_type in contact_types:
                # Get contact data safely
                contact_data: Dict[str, object] = {}
                if (
                    isinstance(domain_contacts, dict)
                    and contact_type in domain_contacts
                ):
                    contact_value = domain_contacts[contact_type]
                    if isinstance(contact_value, dict):
                        contact_data = contact_value
                    else:
                        contact_data = {}

                # Create a new contact_info dictionary with only the fields defined in ContactInfo
                temp_contact_info: Dict[str, str] = {}
                for api_field, norm_field in contact_field_mapping.items():
                    if isinstance(contact_data, dict) and api_field in contact_data:
                        value = contact_data[api_field]
                        if isinstance(value, str):
                            temp_contact_info[norm_field] = value
                        elif value is not None:
                            temp_contact_info[norm_field] = str(value)

                # Set the contact info to the appropriate field based on the type
                key = contact_type.lower()
                if key == "registrant":
                    registrant_info: ContactInfo = {}
                    if "first_name" in temp_contact_info:
                        registrant_info["first_name"] = temp_contact_info["first_name"]
                    if "last_name" in temp_contact_info:
                        registrant_info["last_name"] = temp_contact_info["last_name"]
                    if "organization" in temp_contact_info:
                        registrant_info["organization"] = temp_contact_info[
                            "organization"
                        ]
                    if "job_title" in temp_contact_info:
                        registrant_info["job_title"] = temp_contact_info["job_title"]
                    if "address1" in temp_contact_info:
                        registrant_info["address1"] = temp_contact_info["address1"]
                    if "address2" in temp_contact_info:
                        registrant_info["address2"] = temp_contact_info["address2"]
                    if "city" in temp_contact_info:
                        registrant_info["city"] = temp_contact_info["city"]
                    if "state" in temp_contact_info:
                        registrant_info["state"] = temp_contact_info["state"]
                    if "state_choice" in temp_contact_info:
                        registrant_info["state_choice"] = temp_contact_info[
                            "state_choice"
                        ]
                    if "postal_code" in temp_contact_info:
                        registrant_info["postal_code"] = temp_contact_info[
                            "postal_code"
                        ]
                    if "country" in temp_contact_info:
                        registrant_info["country"] = temp_contact_info["country"]
                    if "phone" in temp_contact_info:
                        registrant_info["phone"] = temp_contact_info["phone"]
                    if "phone_ext" in temp_contact_info:
                        registrant_info["phone_ext"] = temp_contact_info["phone_ext"]
                    if "fax" in temp_contact_info:
                        registrant_info["fax"] = temp_contact_info["fax"]
                    if "email" in temp_contact_info:
                        registrant_info["email"] = temp_contact_info["email"]
                    result["registrant"] = registrant_info
                elif key == "tech":
                    tech_info: ContactInfo = {}
                    if "first_name" in temp_contact_info:
                        tech_info["first_name"] = temp_contact_info["first_name"]
                    if "last_name" in temp_contact_info:
                        tech_info["last_name"] = temp_contact_info["last_name"]
                    if "organization" in temp_contact_info:
                        tech_info["organization"] = temp_contact_info["organization"]
                    if "job_title" in temp_contact_info:
                        tech_info["job_title"] = temp_contact_info["job_title"]
                    if "address1" in temp_contact_info:
                        tech_info["address1"] = temp_contact_info["address1"]
                    if "address2" in temp_contact_info:
                        tech_info["address2"] = temp_contact_info["address2"]
                    if "city" in temp_contact_info:
                        tech_info["city"] = temp_contact_info["city"]
                    if "state" in temp_contact_info:
                        tech_info["state"] = temp_contact_info["state"]
                    if "state_choice" in temp_contact_info:
                        tech_info["state_choice"] = temp_contact_info["state_choice"]
                    if "postal_code" in temp_contact_info:
                        tech_info["postal_code"] = temp_contact_info["postal_code"]
                    if "country" in temp_contact_info:
                        tech_info["country"] = temp_contact_info["country"]
                    if "phone" in temp_contact_info:
                        tech_info["phone"] = temp_contact_info["phone"]
                    if "phone_ext" in temp_contact_info:
                        tech_info["phone_ext"] = temp_contact_info["phone_ext"]
                    if "fax" in temp_contact_info:
                        tech_info["fax"] = temp_contact_info["fax"]
                    if "email" in temp_contact_info:
                        tech_info["email"] = temp_contact_info["email"]
                    result["tech"] = tech_info
                elif key == "admin":
                    admin_info: ContactInfo = {}
                    if "first_name" in temp_contact_info:
                        admin_info["first_name"] = temp_contact_info["first_name"]
                    if "last_name" in temp_contact_info:
                        admin_info["last_name"] = temp_contact_info["last_name"]
                    if "organization" in temp_contact_info:
                        admin_info["organization"] = temp_contact_info["organization"]
                    if "job_title" in temp_contact_info:
                        admin_info["job_title"] = temp_contact_info["job_title"]
                    if "address1" in temp_contact_info:
                        admin_info["address1"] = temp_contact_info["address1"]
                    if "address2" in temp_contact_info:
                        admin_info["address2"] = temp_contact_info["address2"]
                    if "city" in temp_contact_info:
                        admin_info["city"] = temp_contact_info["city"]
                    if "state" in temp_contact_info:
                        admin_info["state"] = temp_contact_info["state"]
                    if "state_choice" in temp_contact_info:
                        admin_info["state_choice"] = temp_contact_info["state_choice"]
                    if "postal_code" in temp_contact_info:
                        admin_info["postal_code"] = temp_contact_info["postal_code"]
                    if "country" in temp_contact_info:
                        admin_info["country"] = temp_contact_info["country"]
                    if "phone" in temp_contact_info:
                        admin_info["phone"] = temp_contact_info["phone"]
                    if "phone_ext" in temp_contact_info:
                        admin_info["phone_ext"] = temp_contact_info["phone_ext"]
                    if "fax" in temp_contact_info:
                        admin_info["fax"] = temp_contact_info["fax"]
                    if "email" in temp_contact_info:
                        admin_info["email"] = temp_contact_info["email"]
                    result["admin"] = admin_info
                elif key == "auxbilling":
                    auxbilling_info: ContactInfo = {}
                    if "first_name" in temp_contact_info:
                        auxbilling_info["first_name"] = temp_contact_info["first_name"]
                    if "last_name" in temp_contact_info:
                        auxbilling_info["last_name"] = temp_contact_info["last_name"]
                    if "organization" in temp_contact_info:
                        auxbilling_info["organization"] = temp_contact_info[
                            "organization"
                        ]
                    if "job_title" in temp_contact_info:
                        auxbilling_info["job_title"] = temp_contact_info["job_title"]
                    if "address1" in temp_contact_info:
                        auxbilling_info["address1"] = temp_contact_info["address1"]
                    if "address2" in temp_contact_info:
                        auxbilling_info["address2"] = temp_contact_info["address2"]
                    if "city" in temp_contact_info:
                        auxbilling_info["city"] = temp_contact_info["city"]
                    if "state" in temp_contact_info:
                        auxbilling_info["state"] = temp_contact_info["state"]
                    if "state_choice" in temp_contact_info:
                        auxbilling_info["state_choice"] = temp_contact_info[
                            "state_choice"
                        ]
                    if "postal_code" in temp_contact_info:
                        auxbilling_info["postal_code"] = temp_contact_info[
                            "postal_code"
                        ]
                    if "country" in temp_contact_info:
                        auxbilling_info["country"] = temp_contact_info["country"]
                    if "phone" in temp_contact_info:
                        auxbilling_info["phone"] = temp_contact_info["phone"]
                    if "phone_ext" in temp_contact_info:
                        auxbilling_info["phone_ext"] = temp_contact_info["phone_ext"]
                    if "fax" in temp_contact_info:
                        auxbilling_info["fax"] = temp_contact_info["fax"]
                    if "email" in temp_contact_info:
                        auxbilling_info["email"] = temp_contact_info["email"]
                    result["auxbilling"] = auxbilling_info

        return result

    def get_info(self, domain_name: str) -> Dict[str, object]:
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
                "fix": "Try again later or contact Namecheap support",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get domain information",
                "fix": "Verify that '{domain_name}' exists and is registered with Namecheap",
            },
        }

        extract = tldextract.extract(domain_name)
        sld, tld = extract.domain, extract.suffix
        params = {"DomainName": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.getInfo",
            params,
            error_codes,
            {"domain_name": domain_name},
        )
        return response

    def get_tld_list(self) -> Dict[str, object]:
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
                "fix": "Try again later or contact Namecheap support",
            },
        }

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.getTldList", {}, error_codes=error_codes
        )

        # Get TLDs from response
        tlds_raw = self.client.normalize_api_response(
            response=response, result_key="Tlds.Tld", return_type="list"
        )

        # No casting needed
        tlds = tlds_raw

        result: Dict[str, object] = {"tlds": tlds}
        return result

    def renew(
        self, domain_name: str, years: int = 1, promotion_code: Optional[str] = None
    ) -> Dict[str, object]:
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
                "fix": "Verify that the domain is eligible for renewal",
            },
            "4023166": {
                "explanation": "Error occurred while renewing domain",
                "fix": "Check your account balance and domain status",
            },
            "4022337": {
                "explanation": "Error in refunding funds",
                "fix": "Contact Namecheap support for assistance with refund issues",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to renew domain",
                "fix": "Verify that '{domain_name}' exists and is eligible for renewal",
            },
        }

        extract = tldextract.extract(domain_name)
        sld, tld = extract.domain, extract.suffix
        params = {"DomainName": sld, "TLD": tld, "Years": str(years)}

        if promotion_code:
            params["PromotionCode"] = promotion_code

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.renew", params, error_codes, {"domain_name": domain_name}
        )
        return response
