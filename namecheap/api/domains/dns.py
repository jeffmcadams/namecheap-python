"""
DNS-related operations for domains API
"""
from typing import Any, Dict, List, Optional

# Common error codes applicable to multiple DNS methods
COMMON_DNS_ERRORS = {
    "2019166": {
        "explanation": "Domain not found or incorrect domain format",
        "fix": "Verify the domain name exists and is spelled correctly."
    },
    "2016166": {
        "explanation": "Domain is not associated with your account",
        "fix": "Ensure this domain is registered and active in your Namecheap account."
    },
    "2013166": {
        "explanation": "Domain is not active",
        "fix": "Check that the domain is active in your Namecheap account (not expired or pending)"
    },
    "3031510": {
        "explanation": "Enom error when ErrorCount is not 0",
        "fix": "Check the specific error message from the provider and address accordingly. This often indicates a service issue."
    },
    "3050900": {
        "explanation": "Unknown error from provider",
        "fix": "Contact Namecheap support for assistance with this error."
    },
    "2030288": {
        "explanation": "Domain is not using Namecheap DNS servers",
        "fix": "Set the domain to use Namecheap's default DNS servers before using this API method"
    },
    "UNKNOWN_ERROR": {
        "explanation": "Failed to retrieve DNS host records",
        "fix": "Verify that the domain exists in your Namecheap account and your API credentials have sufficient permissions. If the problem persists, try enabling debug mode for more details."
    }
}


class DnsAPI:
    """DNS API methods for domains namespace"""

    def __init__(self, client):
        """
        Initialize the DNS API

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

    def get_hosts(self, domain: str) -> List[Dict[str, Any]]:
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
        sld, tld = self._split_domain_name(domain)

        # Define error codes specific to this endpoint
        error_codes = {
            "2050166": {
                "explanation": "Failed to retrieve DNS host records",
                "fix": "Verify that '{domain}' exists in your Namecheap account"
            },
            "2019166": {
                "explanation": "Failed to retrieve DNS host records",
                "fix": "Verify that '{domain}' exists in your Namecheap account"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to retrieve DNS host records",
                "fix": "Verify that '{domain}' exists in your Namecheap account and is using Namecheap DNS servers"
            }
        }

        # Set up context variables for error messages
        context = {"domain": domain}

        # Make request with centralized error handling
        params = {
            "SLD": sld,
            "TLD": tld
        }

        # Call the API with error handling integrated
        response = self.client._make_request(
            "namecheap.domains.dns.getHosts",
            params,
            error_codes=error_codes,
            context=context
        )

        # Use the simplified normalized API response method
        return self.client.normalize_api_response(
            response=response,
            result_key="DomainDNSGetHostsResult.host",
            return_type="list"
        )

    def set_hosts(self, domain_name: str, hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        # Error codes for setHosts method
        # https://www.namecheap.com/support/api/methods/domains-dns/set-hosts/
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2015280": {
                "explanation": "Invalid record type",
                "fix": "Check that all DNS record types are valid (A, AAAA, CNAME, MX, TXT, URL, URL301, FRAME)"
            },
            "2015166": {
                "explanation": "Failed to update domain",
                "fix": "Verify the domain is registered and DNS settings can be modified"
            },
            "2016166": {
                "explanation": "Domain is not using Namecheap DNS servers",
                "fix": "Set the domain to use Namecheap's DNS servers before setting host records"
            },
            "4023330": {
                "explanation": "Unable to process request",
                "fix": "Check that the request is properly formatted and all required fields are included"
            },
            "2015280": {
                "explanation": "Invalid DNS host record",
                "fix": "Check that the host record parameters are valid"
            },
            "2015166": {
                "explanation": "Failed to update domain",
                "fix": "Verify the domain is active and can be modified"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to set DNS host records",
                "fix": "Verify that '{domain}' exists in your account and is using Namecheap DNS servers"
            }
        }

        # Split domain into SLD and TLD
        sld, tld = self._split_domain_name(domain_name)

        # Set up context variables for error messages
        context = {"domain": domain_name}

        # Base parameters
        params = {
            "SLD": sld,
            "TLD": tld
        }

        # Convert normalized host records to Namecheap API format
        for i, host in enumerate(hosts):
            # 1-based index for API
            idx = i + 1

            # Required fields
            params[f"HostName{idx}"] = host.get("Name", "@")  # @ is default
            params[f"RecordType{idx}"] = host.get("Type", "A")  # A is default
            params[f"Address{idx}"] = host.get("Address", "")

            # Optional fields with defaults
            params[f"TTL{idx}"] = host.get("TTL", "1800")  # Default TTL

            # Priority is required for MX records
            if host.get("Type", "").upper() == "MX" or "MXPref" in host:
                params[f"MXPref{idx}"] = host.get(
                    "MXPref", "10")  # Default priority

        # Make the API request
        response = self.client._make_request(
            "namecheap.domains.dns.setHosts",
            params,
            error_codes=error_codes,
            context=context
        )

        # Get the result
        return self.client.normalize_api_response(
            response=response,
            result_key="DomainDNSSetHostsResult"
        )

    def set_default(self, domain_name: str) -> Dict[str, Any]:
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
        # Error codes for setDefault method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account"
            },
            "2015166": {
                "explanation": "Failed to update domain",
                "fix": "This may be a temporary issue or the domain may be locked"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to set default DNS servers",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account"
            }
        }

        sld, tld = self._split_domain_name(domain_name)
        params = {"SLD": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.dns.setDefault",
            params,
            error_codes,
            {"domain_name": domain_name}
        )

        # Normalize the response
        return self.client.normalize_api_response(
            response=response,
            result_key="DomainDNSSetDefaultResult"
        )

    def set_custom(self, domain_name: str, nameservers: List[str]) -> Dict[str, Any]:
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
        # Error codes for setCustom method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account"
            },
            "2015166": {
                "explanation": "Failed to update domain",
                "fix": "This may be a temporary issue or the domain may be locked"
            },
            "2011146": {
                "explanation": "Invalid nameserver format",
                "fix": "Nameservers must be valid hostnames (e.g., ns1.example.com)"
            },
            "2011147": {
                "explanation": "Insufficient nameservers",
                "fix": "At least 2 nameservers are required"
            },
            "2011148": {
                "explanation": "Too many nameservers",
                "fix": "Maximum of 12 nameservers allowed"
            },
            "2011149": {
                "explanation": "Duplicate nameserver entries",
                "fix": "Each nameserver must be unique"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to set custom DNS servers",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account"
            }
        }

        if len(nameservers) < 2:
            raise ValueError("At least 2 nameservers are required")
        if len(nameservers) > 12:
            raise ValueError("Maximum of 12 nameservers allowed")

        sld, tld = self._split_domain_name(domain_name)
        params = {"SLD": sld, "TLD": tld}

        # Add nameservers to parameters
        for i, nameserver in enumerate(nameservers):
            params[f"Nameserver{i+1}"] = nameserver

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.dns.setCustom",
            params,
            error_codes,
            {"domain_name": domain_name}
        )

        # Normalize the response
        return self.client.normalize_api_response(
            response=response,
            result_key="DomainDNSSetCustomResult"
        )

    def get_list(self, domain_name: str) -> Dict[str, Any]:
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
        # Error codes for getList method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get DNS server list",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account"
            }
        }

        sld, tld = self._split_domain_name(domain_name)
        params = {"SLD": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.dns.getList",
            params,
            error_codes,
            {"domain_name": domain_name}
        )

        # Normalize the main response
        result = self.client.normalize_api_response(
            response=response,
            result_key="DomainDNSGetListResult"
        )

        # Extract nameservers (this is still needed as nameservers are in a special format)
        nameservers = []
        if "Nameserver" in response.get("DomainDNSGetListResult", {}):
            ns_data = response["DomainDNSGetListResult"]["Nameserver"]
            if isinstance(ns_data, list):
                nameservers = ns_data
            else:
                nameservers = [ns_data]

        # Add nameservers if not already present
        if "Nameservers" not in result:
            result["Nameservers"] = nameservers

        return result

    def get_email_forwarding(self, domain_name: str) -> Dict[str, Any]:
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
        # Error codes for getEmailForwarding method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account"
            },
            "2011147": {
                "explanation": "Email forwarding not enabled",
                "fix": "Enable email forwarding for the domain first"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get email forwarding settings",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account"
            }
        }

        sld, tld = self._split_domain_name(domain_name)
        params = {"DomainName": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.dns.getEmailForwarding",
            params,
            error_codes,
            {"domain_name": domain_name}
        )

        # Field mapping for email forwarding entries
        field_mapping = {
            "@MailBox": "mailbox",
            "@ForwardTo": "forward_to"
        }

        # Get the domain from the result
        domain = response.get("DomainEmailForwarding", {}
                              ).get("@Domain", domain_name)

        # Extract and normalize the forwarding entries
        forwards = []
        if "Forward" in response.get("DomainEmailForwarding", {}):
            forwarding_data = response["DomainEmailForwarding"]["Forward"]
            if isinstance(forwarding_data, list):
                for forward in forwarding_data:
                    normalized = {}
                    for api_field, norm_field in field_mapping.items():
                        if api_field in forward:
                            normalized[norm_field] = forward[api_field]
                    forwards.append(normalized)
            else:
                # Single forwarding entry
                normalized = {}
                for api_field, norm_field in field_mapping.items():
                    if api_field in forwarding_data:
                        normalized[norm_field] = forwarding_data[api_field]
                forwards.append(normalized)

        return {
            "domain": domain,
            "forwards": forwards
        }

    def set_email_forwarding(self, domain_name: str, forwards: List[Dict[str, str]]) -> Dict[str, Any]:
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
        # Error codes for setEmailForwarding method
        error_codes = {
            **COMMON_DNS_ERRORS,
            "2016166": {
                "explanation": "Domain not found or access denied",
                "fix": "Verify the domain exists and is registered with your Namecheap account"
            },
            "2011147": {
                "explanation": "Email forwarding not enabled",
                "fix": "Enable email forwarding for the domain first"
            },
            "2011331": {
                "explanation": "Invalid email format",
                "fix": "Ensure all email addresses are in valid format"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to set email forwarding",
                "fix": "Verify that '{domain_name}' exists in your Namecheap account"
            }
        }

        sld, tld = self._split_domain_name(domain_name)
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
            {"domain_name": domain_name}
        )

        # Normalize the response
        return self.client.normalize_api_response(
            response=response,
            result_key="DomainEmailForwardingResult"
        )
