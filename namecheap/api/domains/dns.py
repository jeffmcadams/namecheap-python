"""
DNS-related operations for domains API
"""

from typing import Callable, Dict, List, Protocol, runtime_checkable

import tldextract


@runtime_checkable
class DnsClient(Protocol):
    """Protocol for the DNS client"""

    _make_request: Callable
    normalize_api_response: Callable


# Constants for default values
DEFAULT_TTL = "1800"
DEFAULT_MX_PREF = "10"
DEFAULT_RECORD_NAME = "@"
DEFAULT_RECORD_TYPE = "A"

# Common error codes applicable to multiple DNS methods
COMMON_DNS_ERRORS = {
    "2016166": {
        "explanation": "Domain is not associated with your account",
        "fix": "Ensure this domain is registered and active in your Namecheap account.",
    },
    "3031510": {
        "explanation": "Enom error when ErrorCount is not 0",
        "fix": "Check the specific error message from the provider and address accordingly. This often indicates a service issue.",
    },
    "3050900": {
        "explanation": "Unknown error from provider",
        "fix": "Contact Namecheap support for assistance with this error.",
    },
    "2030288": {
        "explanation": "Domain is not using Namecheap DNS servers",
        "fix": "Set the domain to use Namecheap's default DNS servers before using this API method",
    },
    "UNKNOWN_ERROR": {
        "explanation": "Failed to retrieve DNS host records",
        "fix": "Verify that the domain exists in your Namecheap account and your API credentials have sufficient permissions. If the problem persists, try enabling debug mode for more details.",
    },
}


class DnsAPI:
    """DNS API methods for domains namespace"""

    def __init__(self, client: DnsClient) -> None:
        """
        Initialize the DNS API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def get_hosts(self, domain: str) -> List[Dict[str, object]]:
        """
        Retrieves DNS host record settings for the requested domain.

        Args:
            domain: Domain name to retrieve DNS settings for
                    (example: example.com)

        Returns:
            List of normalized DNS records with consistent field names:
            [
                {
                    "HostId": "12345",
                    "Name": "@",
                    "Type": "A",
                    "Address": "10.0.0.1",
                    "TTL": "1800",
                    "MXPref": "10",  # Only for MX records
                    "IsActive": True,
                },
                ...
            ]

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate input
        if not domain or not isinstance(domain, str):
            raise ValueError("Domain must be a non-empty string")

        # Use tldextract to split the domain
        extracted = tldextract.extract(domain)
        sld = extracted.domain
        tld = extracted.suffix

        # Define error codes specific to this endpoint
        error_codes = {
            "2050166": {
                "explanation": "Failed to retrieve DNS host records",
                "fix": "Verify that '{domain}' exists in your Namecheap account",
            },
            "2019166": {
                "explanation": "Failed to retrieve DNS host records",
                "fix": "Verify that '{domain}' exists in your Namecheap account",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to retrieve DNS host records",
                "fix": "Verify that '{domain}' exists in your Namecheap account and is using Namecheap DNS servers",
            },
        }

        # Set up context variables for error messages
        context = {"domain": domain}

        # Make request with centralized error handling
        params = {"SLD": sld, "TLD": tld}

        # Call the API with error handling integrated
        response = self.client._make_request(
            "namecheap.domains.dns.getHosts",
            params,
            error_codes=error_codes,
            context=context,
        )

        # The ResponseList type is guaranteed by specifying return_type="list"
        # normalize_api_response will consistently return List[Dict[str, object]]
        # which is directly compatible with our return type
        result = self.client.normalize_api_response(
            response=response,
            result_key="DomainDNSGetHostsResult.host",
            return_type="list",
        )

        # Ensure we return the expected type
        if isinstance(result, list):
            return result

        # If not a list, return an empty list
        return []

    def set_hosts(
        self, domain_name: str, hosts: List[Dict[str, str]]
    ) -> Dict[str, object]:
        """
        Set DNS host records for a domain

        Args:
            domain_name: The domain name to set host records for
            hosts: List of normalized host record dictionaries with keys:
                  - Name: Name of the host record (e.g., "@", "www")
                  - Type: Type of record (A, AAAA, CNAME, MX, TXT, etc.)
                  - Address: Value of the record
                  - MXPref: MX preference (required for MX records)
                  - TTL: Time to live in seconds (min 60, max 86400, default 1800)

        Returns:
            Dictionary with status information:
            {
                "IsSuccess": True,  # Whether the operation was successful
                "Domain": "example.com",  # The domain name
                "Warnings": ""  # Any warnings returned by the API
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate inputs
        if not domain_name:
            raise ValueError("Domain name must be a non-empty string")

        if not hosts:
            raise ValueError("Hosts must be a non-empty list")

        # Validate each host record by checking for expected keys
        for i, host in enumerate(hosts):
            # Required fields
            if "Address" not in host:
                raise ValueError(
                    f"Host record at index {i} is missing required 'Address' field"
                )

            # Check TTL range if provided
            if "TTL" in host:
                try:
                    ttl = int(host["TTL"])
                    if ttl < 60 or ttl > 86400:
                        raise ValueError(
                            f"Host record at index {i} has invalid TTL (must be between 60 and 86400)"
                        )
                except ValueError:
                    raise ValueError(
                        f"Host record at index {i} has invalid TTL (must be an integer)"
                    )

            # MX record validation
            if host.get("Type", "").upper() == "MX" and "MXPref" not in host:
                raise ValueError(
                    f"MX record at index {i} is missing required 'MXPref' field"
                )

        # Error codes for setHosts method
        # https://www.namecheap.com/support/api/methods/domains-dns/set-hosts/
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2015280": {
                "explanation": "Invalid record type",
                "fix": "Check that all DNS record types are valid (A, AAAA, CNAME, MX, TXT, URL, URL301, FRAME)",
            },
            "2015166": {
                "explanation": "Failed to update domain",
                "fix": "Verify the domain is registered and DNS settings can be modified",
            },
            "2016166": {
                "explanation": "Domain is not using Namecheap DNS servers",
                "fix": "Set the domain to use Namecheap's DNS servers before setting host records",
            },
            "4023330": {
                "explanation": "Unable to process request",
                "fix": "Check that the request is properly formatted and all required fields are included",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to set DNS host records",
                "fix": "Verify that '{domain}' exists in your account and is using Namecheap DNS servers",
            },
        }

        # Use tldextract to split the domain
        extracted = tldextract.extract(domain_name)
        sld = extracted.domain
        tld = extracted.suffix

        # Set up context variables for error messages
        context = {"domain": domain_name}

        # Base parameters
        params = {"SLD": sld, "TLD": tld}

        # Convert normalized host records to Namecheap API format
        for i, host in enumerate(hosts):
            # 1-based index for API
            idx = i + 1

            # Required fields
            params[f"HostName{idx}"] = host.get("Name", DEFAULT_RECORD_NAME)
            params[f"RecordType{idx}"] = host.get("Type", DEFAULT_RECORD_TYPE)
            params[f"Address{idx}"] = host.get("Address", "")

            # Optional fields with defaults
            params[f"TTL{idx}"] = host.get("TTL", DEFAULT_TTL)

            # Priority is required for MX records
            if host.get("Type", "").upper() == "MX" or "MXPref" in host:
                params[f"MXPref{idx}"] = host.get("MXPref", DEFAULT_MX_PREF)

        # Make the API request
        response = self.client._make_request(
            "namecheap.domains.dns.setHosts",
            params,
            error_codes=error_codes,
            context=context,
        )

        # Normalize the response - we're using return_type="dict" (default)
        # which guarantees a dictionary return type via overloaded signature
        result = self.client.normalize_api_response(
            response=response, result_key="DomainDNSSetHostsResult"
        )

        # Ensure we return the expected type
        if isinstance(result, dict):
            return result

        # If not a dict, return empty dict
        return {}

    def set_default(self, domain_name: str) -> Dict[str, object]:
        """
        Set default Namecheap DNS servers for a domain

        Args:
            domain_name: The domain name to set default DNS servers for

        Returns:
            Dictionary with status information:
            {
                "Domain": "example.com",
                "IsSuccess": True,
                "Warnings": ""
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate input
        if not domain_name or not isinstance(domain_name, str):
            raise ValueError("Domain name must be a non-empty string")

        # Use tldextract to split the domain
        extracted = tldextract.extract(domain_name)
        sld = extracted.domain
        tld = extracted.suffix

        # Error codes for setDefault method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account",
            },
            "2015166": {
                "explanation": "Failed to update domain",
                "fix": "This may be a temporary issue or the domain may be locked",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to set default DNS servers",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account",
            },
        }

        params = {"SLD": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.dns.setDefault",
            params,
            error_codes,
            {"domain_name": domain_name},
        )

        # Normalize the response - we're using return_type="dict" (default)
        # which guarantees a dictionary return type via overloaded signature
        result = self.client.normalize_api_response(
            response=response, result_key="DomainDNSSetDefaultResult"
        )

        # Ensure we return the expected type
        if isinstance(result, dict):
            return result

        # If not a dict, return empty dict
        return {}

    def set_custom(self, domain_name: str, nameservers: List[str]) -> Dict[str, object]:
        """
        Set custom DNS servers for a domain

        Args:
            domain_name: The domain name to set DNS servers for
            nameservers: List of DNS server hostnames (min 2, max 12)

        Returns:
            Dictionary with status information:
            {
                "Domain": "example.com",
                "IsSuccess": True,
                "Warnings": ""
            }

        Raises:
            ValueError: If the number of nameservers is invalid
            NamecheapException: If the API returns an error
        """
        # Validate inputs
        if not domain_name or not isinstance(domain_name, str):
            raise ValueError("Domain name must be a non-empty string")

        if not nameservers or not isinstance(nameservers, list):
            raise ValueError("Nameservers must be a non-empty list")

        if len(nameservers) < 2:
            raise ValueError("At least 2 nameservers are required")

        if len(nameservers) > 12:
            raise ValueError("Maximum of 12 nameservers allowed")

        # Validate each nameserver format
        for i, ns in enumerate(nameservers):
            if not isinstance(ns, str) or not ns.strip():
                raise ValueError(f"Nameserver at index {i} must be a non-empty string")

            # Check for duplicate nameservers
            if nameservers.count(ns) > 1:
                raise ValueError(f"Duplicate nameserver found: {ns}")

        # Use tldextract to split the domain
        extracted = tldextract.extract(domain_name)
        sld = extracted.domain
        tld = extracted.suffix

        # Error codes for setCustom method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account",
            },
            "2015166": {
                "explanation": "Failed to update domain",
                "fix": "This may be a temporary issue or the domain may be locked",
            },
            "2011146": {
                "explanation": "Invalid nameserver format",
                "fix": "Nameservers must be valid hostnames (e.g., ns1.example.com)",
            },
            "2011147": {
                "explanation": "Insufficient nameservers",
                "fix": "At least 2 nameservers are required",
            },
            "2011148": {
                "explanation": "Too many nameservers",
                "fix": "Maximum of 12 nameservers allowed",
            },
            "2011149": {
                "explanation": "Duplicate nameserver entries",
                "fix": "Each nameserver must be unique",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to set custom DNS servers",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account",
            },
        }

        params = {"SLD": sld, "TLD": tld}

        # Add nameservers to parameters
        for i, nameserver in enumerate(nameservers):
            params[f"Nameserver{i+1}"] = nameserver

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.dns.setCustom",
            params,
            error_codes,
            {"domain_name": domain_name},
        )

        # Normalize the response - we're using return_type="dict" (default)
        # which guarantees a dictionary return type via overloaded signature
        result = self.client.normalize_api_response(
            response=response, result_key="DomainDNSSetCustomResult"
        )

        # Ensure we return the expected type
        if isinstance(result, dict):
            return result

        # If not a dict, return empty dict
        return {}

    def get_list(self, domain_name: str) -> Dict[str, object]:
        """
        Get a list of DNS servers for a domain

        Args:
            domain_name: The domain name to get DNS servers for

        Returns:
            Dictionary with DNS server information:
            {
                "Domain": "example.com",
                "IsUsingOurDNS": True,
                "Nameservers": ["dns1.registrar-servers.com", "dns2.registrar-servers.com"]
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate input
        if not domain_name or not isinstance(domain_name, str):
            raise ValueError("Domain name must be a non-empty string")

        # Use tldextract to split the domain
        extracted = tldextract.extract(domain_name)
        sld = extracted.domain
        tld = extracted.suffix

        # Error codes for getList method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get DNS server list",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account",
            },
        }

        params = {"SLD": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.dns.getList",
            params,
            error_codes,
            {"domain_name": domain_name},
        )

        # Normalize the main response
        result = self.client.normalize_api_response(
            response=response, result_key="DomainDNSGetListResult"
        )

        # Extract nameservers (this is still needed as nameservers are in a special format)
        nameservers: List[str] = []
        if "Nameserver" in response.get("DomainDNSGetListResult", {}):
            ns_data = response["DomainDNSGetListResult"]["Nameserver"]
            nameservers = ns_data if isinstance(ns_data, list) else [ns_data]

        # Ensure we're working with a dictionary
        if not isinstance(result, dict):
            result = {}

        # Create a new dictionary with the correct type
        dns_result: Dict[str, object] = {}

        # Copy values from result if it's a dictionary
        if isinstance(result, dict):
            for key, value in result.items():
                dns_result[key] = value

        # Add nameservers if not already present
        if "Nameservers" not in dns_result:
            dns_result["Nameservers"] = nameservers

        return dns_result

    def get_email_forwarding(self, domain_name: str) -> Dict[str, object]:
        """
        Get email forwarding settings for a domain

        Args:
            domain_name: The domain name to get email forwarding settings for

        Returns:
            Dictionary with email forwarding information:
            {
                "domain": "example.com",
                "forwards": [
                    {
                        "mailbox": "info",  # The part before the @ symbol
                        "forward_to": "user@example.org"
                    },
                    ...
                ]
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate input
        if not domain_name or not isinstance(domain_name, str):
            raise ValueError("Domain name must be a non-empty string")

        # Use tldextract to split the domain
        extracted = tldextract.extract(domain_name)
        sld = extracted.domain
        tld = extracted.suffix

        # Error codes for getEmailForwarding method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account",
            },
            "2011147": {
                "explanation": "Email forwarding not enabled",
                "fix": "Enable email forwarding for the domain first",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get email forwarding settings",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account",
            },
        }

        params = {"DomainName": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.dns.getEmailForwarding",
            params,
            error_codes,
            {"domain_name": domain_name},
        )

        # Use normalized API response for consistency
        forwards_list: List[Dict[str, str]] = []
        result: Dict[str, object] = {"domain": domain_name, "forwards": forwards_list}

        # Extract domain from result if available
        if (
            "DomainEmailForwarding" in response
            and "@Domain" in response["DomainEmailForwarding"]
        ):
            result["domain"] = response["DomainEmailForwarding"]["@Domain"]

        # Process forwards using normalize_api_response for consistency
        if "Forward" in response.get("DomainEmailForwarding", {}):
            forwards_data = response["DomainEmailForwarding"]["Forward"]

            # Define field mapping for normalization
            field_mapping = {"@MailBox": "mailbox", "@ForwardTo": "forward_to"}

            # Handle both single item and list
            if isinstance(forwards_data, list):
                for forward in forwards_data:
                    normalized: Dict[str, str] = {}
                    for api_field, norm_field in field_mapping.items():
                        if api_field in forward:
                            normalized[norm_field] = forward[api_field]
                    forwards_list.append(normalized)
            else:
                # Single forwarding entry
                single_forward: Dict[str, str] = {}
                for api_field, norm_field in field_mapping.items():
                    if api_field in forwards_data:
                        single_forward[norm_field] = forwards_data[api_field]
                forwards_list.append(single_forward)

        return result

    def set_email_forwarding(
        self, domain_name: str, forwards: List[Dict[str, str]]
    ) -> Dict[str, object]:
        """
        Set email forwarding for a domain

        Args:
            domain_name: The domain name to set email forwarding for
            forwards: List of email forwarding dictionaries, each with:
                - mailbox: The mailbox part of the email address (before @)
                - forward_to: The email address to forward to

        Returns:
            Dictionary with email forwarding status:
            {
                "Domain": "example.com",
                "IsSuccess": True,
                "Warnings": ""
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate inputs
        if not domain_name or not isinstance(domain_name, str):
            raise ValueError("Domain name must be a non-empty string")

        if not isinstance(forwards, list):
            raise ValueError("Forwards must be a list")

        # Validate each forward entry
        for i, forward in enumerate(forwards):
            if not isinstance(forward, dict):
                raise ValueError(f"Forward at index {i} must be a dictionary")

            if "mailbox" not in forward:
                raise ValueError(
                    f"Forward at index {i} is missing required 'mailbox' field"
                )

            if "forward_to" not in forward:
                raise ValueError(
                    f"Forward at index {i} is missing required 'forward_to' field"
                )

            if (
                not isinstance(forward["mailbox"], str)
                or not forward["mailbox"].strip()
            ):
                raise ValueError(
                    f"Forward at index {i} has invalid 'mailbox' (must be a non-empty string)"
                )

            if (
                not isinstance(forward["forward_to"], str)
                or not forward["forward_to"].strip()
            ):
                raise ValueError(
                    f"Forward at index {i} has invalid 'forward_to' (must be a non-empty string)"
                )

            # Basic email validation for forward_to
            if "@" not in forward["forward_to"]:
                raise ValueError(
                    f"Forward at index {i} has invalid 'forward_to' email format"
                )

        # Use tldextract to split the domain
        extracted = tldextract.extract(domain_name)
        sld = extracted.domain
        tld = extracted.suffix

        # Error codes for setEmailForwarding method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account",
            },
            "2011147": {
                "explanation": "Email forwarding not enabled",
                "fix": "Enable email forwarding for the domain first",
            },
            "2011331": {
                "explanation": "Invalid email format",
                "fix": "Ensure all email addresses are in valid format",
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to set email forwarding",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account",
            },
        }

        params = {"DomainName": sld, "TLD": tld}

        # Add forwards to parameters
        for i, forward in enumerate(forwards):
            idx = i + 1
            params[f"MailBox{idx}"] = forward.get("mailbox", "")
            params[f"ForwardTo{idx}"] = forward.get("forward_to", "")

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.dns.setEmailForwarding",
            params,
            error_codes,
            {"domain_name": domain_name},
        )

        # Normalize the response - we're using return_type="dict" (default)
        # which guarantees a dictionary return type via overloaded signature
        result = self.client.normalize_api_response(
            response=response, result_key="DomainEmailForwardingResult"
        )

        # Ensure we return the expected type
        if isinstance(result, dict):
            return result

        # If not a dict, return empty dict
        return {}
