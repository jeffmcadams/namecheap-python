"""
Nameserver operations for domains API
"""
from typing import Dict, List, Optional, TypedDict, Union, cast

import tldextract

from ...base import BaseClient, ResponseDict
from ...exceptions import NamecheapException

# Define proper types for nameserver operations


class NameserverInfo(TypedDict, total=False):
    Nameserver: str
    IP: str
    IsDefault: bool
    IsDNSOnly: bool


class NameserversResult(TypedDict):
    nameservers: List[NameserverInfo]
    domain: str


class NameserverCreateResult(TypedDict):
    domain: str
    nameserver: str
    ip: str


class NameserverUpdateResult(TypedDict):
    domain: str
    nameserver: str
    old_ip: str
    new_ip: str


class NameserverDeleteResult(TypedDict):
    domain: str
    nameserver: str


# Common error codes shared across nameserver operations
COMMON_NS_ERRORS = {
    "2019166": {
        "explanation": "Domain not found",
        "fix": "Verify the domain exists and is spelled correctly"
    },
    "2016166": {
        "explanation": "Domain is not associated with your account",
        "fix": "Check that the domain is registered with your Namecheap account"
    },
    "2011177": {
        "explanation": "Nameserver is invalid",
        "fix": "Ensure the nameserver has proper format (e.g., ns1.example.com)"
    },
    "UNKNOWN_ERROR": {
        "explanation": "Operation failed",
        "fix": "Verify that '{domain_name}' exists and all parameters are correct"
    }
}


class NsAPI:
    """Nameserver API methods for domains namespace"""

    def __init__(self, client: BaseClient) -> None:
        """
        Initialize the nameserver API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def get_list(self, domain_name: str) -> NameserversResult:
        """
        Get nameservers for a domain

        API Documentation: https://www.namecheap.com/support/api/methods/domains-ns/get-list/

        Args:
            domain_name: The domain name to get nameservers for

        Returns:
            Dictionary with nameserver information:
            {
                "nameservers": [
                    {"Nameserver": "dns1.example.com"},
                    {"Nameserver": "dns2.example.com"},
                    ...
                ],
                "domain": "example.com"
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        error_codes = {
            **COMMON_NS_ERRORS,
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get nameservers",
                "fix": "Verify that '{domain_name}' exists and is registered with Namecheap"
            }
        }

        extract = tldextract.extract(domain_name)
        sld, tld = extract.domain, extract.suffix
        params = {"DomainName": sld, "TLD": tld}

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.ns.getList",
            params,
            error_codes,
            {"domain_name": domain_name}
        )

        # Extract the nameservers from the response
        nameserver_list: List[Dict[str, str]] = []

        # Extract data from response, using dict access only when we know it's a dict
        ns_result = response.get("DomainNSInfoResult")
        
        # Create safe dictionary to work with
        ns_dict = {}
        if isinstance(ns_result, dict):
            ns_dict = ns_result
        
        # Get nameserver data with proper typing
        ns_data = ns_dict.get("Nameserver", [])

        # Convert to list if single item
        if not isinstance(ns_data, list):
            ns_data = [ns_data] if ns_data else []

        # Create properly typed nameserver info objects
        nameservers: List[NameserverInfo] = []
        for ns in ns_data:
            if isinstance(ns, dict):
                ns_info: NameserverInfo = {}
                if ns.get("Name"):
                    ns_info["Nameserver"] = ns["Name"]
                elif ns.get("@Name"):
                    ns_info["Nameserver"] = ns["@Name"]
                # Add IP if present
                if ns.get("IP"):
                    ns_info["IP"] = ns["IP"]

                # Only add if we have a nameserver name
                if "Nameserver" in ns_info:
                    nameservers.append(ns_info)
            elif isinstance(ns, str):
                nameservers.append({"Nameserver": ns})

        result: NameserversResult = {
            "nameservers": nameservers,
            "domain": domain_name
        }
        return result

    def create(self, domain_name: str, nameserver: str, ip: str) -> NameserverCreateResult:
        """
        Create a new nameserver for a domain

        API Documentation: https://www.namecheap.com/support/api/methods/domains-ns/create/

        Args:
            domain_name: The domain name to create a nameserver for
            nameserver: The nameserver to create (e.g., "ns1.example.com")
            ip: The IP address for the nameserver

        Returns:
            Dictionary with creation result:
            {
                "domain": "example.com",
                "nameserver": "ns1.example.com",
                "ip": "192.0.2.1"
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for creating nameservers
        error_codes = {
            **COMMON_NS_ERRORS,
            "2011170": {
                "explanation": "Parameter Ns was not specified",
                "fix": "Ensure nameserver parameter is provided"
            },
            "2011171": {
                "explanation": "Parameter Ns is invalid",
                "fix": "Ensure nameserver is in a valid format (e.g., ns1.example.com)"
            },
            "2011173": {
                "explanation": "Parameter Ip was not specified",
                "fix": "Ensure IP address is provided"
            },
            "2011172": {
                "explanation": "Parameter Ip is invalid",
                "fix": "Ensure IP is in a valid IPv4 format (e.g., 192.0.2.1)"
            },
            "2011174": {
                "explanation": "Nameserver already exists",
                "fix": "The nameserver '{nameserver}' already exists for domain '{domain_name}'"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to create nameserver",
                "fix": "Verify all parameters and try again"
            }
        }

        extract = tldextract.extract(domain_name)
        sld, tld = extract.domain, extract.suffix
        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver,
            "IP": ip
        }

        # Make the API call with centralized error handling
        _ = self.client._make_request(
            "namecheap.domains.ns.create",
            params,
            error_codes,
            {"domain_name": domain_name, "nameserver": nameserver}
        )

        # If we got here, the API call was successful
        # Return the result with the provided information
        result: NameserverCreateResult = {
            "domain": domain_name,
            "nameserver": nameserver,
            "ip": ip
        }
        return result

    def update(
        self, domain_name: str, nameserver: str, old_ip: str, new_ip: str
    ) -> NameserverUpdateResult:
        """
        Update a nameserver for a domain

        API Documentation: https://www.namecheap.com/support/api/methods/domains-ns/update/

        Args:
            domain_name: The domain name to update a nameserver for
            nameserver: The nameserver to update (e.g., "ns1.example.com")
            old_ip: The current IP address for the nameserver
            new_ip: The new IP address for the nameserver

        Returns:
            Dictionary with update result:
            {
                "domain": "example.com",
                "nameserver": "ns1.example.com",
                "old_ip": "192.0.2.1",
                "new_ip": "192.0.2.2"
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for updating nameservers
        error_codes = {
            **COMMON_NS_ERRORS,
            "2011170": {
                "explanation": "Parameter Ns was not specified",
                "fix": "Ensure nameserver parameter is provided"
            },
            "2011171": {
                "explanation": "Parameter Ns is invalid",
                "fix": "Ensure nameserver is in a valid format (e.g., ns1.example.com)"
            },
            "2011172": {
                "explanation": "Parameter IP is invalid",
                "fix": "Ensure IP is in a valid IPv4 format (e.g., 192.0.2.1)"
            },
            "2011173": {
                "explanation": "Parameter IP was not specified",
                "fix": "Ensure new IP address is provided"
            },
            "2011175": {
                "explanation": "Nameserver doesn't exist",
                "fix": "The nameserver '{nameserver}' doesn't exist for domain '{domain_name}'"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to update nameserver",
                "fix": "Verify all parameters and try again"
            }
        }

        extract = tldextract.extract(domain_name)
        sld, tld = extract.domain, extract.suffix
        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver,
            "OldIP": old_ip,
            "IP": new_ip
        }

        # Make the API call with centralized error handling
        _ = self.client._make_request(
            "namecheap.domains.ns.update",
            params,
            error_codes,
            {"domain_name": domain_name, "nameserver": nameserver}
        )

        # If we got here, the API call was successful
        # Return the result with the provided information
        result: NameserverUpdateResult = {
            "domain": domain_name,
            "nameserver": nameserver,
            "old_ip": old_ip,
            "new_ip": new_ip
        }
        return result

    def delete(self, domain_name: str, nameserver: str) -> NameserverDeleteResult:
        """
        Delete a nameserver for a domain

        API Documentation: https://www.namecheap.com/support/api/methods/domains-ns/delete/

        Args:
            domain_name: The domain name to delete a nameserver for
            nameserver: The nameserver to delete (e.g., "ns1.example.com")

        Returns:
            Dictionary with deletion result:
            {
                "domain": "example.com",
                "nameserver": "ns1.example.com"
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        error_codes = {
            **COMMON_NS_ERRORS,
            "2011170": {
                "explanation": "Parameter Ns was not specified",
                "fix": "Ensure nameserver parameter is provided"
            },
            "2011171": {
                "explanation": "Parameter Ns is invalid",
                "fix": "Ensure nameserver is in a valid format (e.g., ns1.example.com)"
            },
            "2011175": {
                "explanation": "Nameserver doesn't exist",
                "fix": "The nameserver '{nameserver}' doesn't exist for domain '{domain_name}'"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to delete nameserver",
                "fix": "Verify all parameters and try again"
            }
        }

        extract = tldextract.extract(domain_name)
        sld, tld = extract.domain, extract.suffix
        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver
        }

        # Make the API call with centralized error handling
        _ = self.client._make_request(
            "namecheap.domains.ns.delete",
            params,
            error_codes,
            {"domain_name": domain_name, "nameserver": nameserver}
        )

        # If we got here, the API call was successful
        # Return the result with the provided information
        result: NameserverDeleteResult = {
            "domain": domain_name,
            "nameserver": nameserver
        }
        return result

    def get_info(self, domain_name: str, nameserver: str) -> Dict[str, str]:
        """
        Gets information about a nameserver

        This is a helper method that queries the nameserver list and returns
        information for a specific nameserver.

        Args:
            domain_name: Domain to query nameservers for
            nameserver: Specific nameserver to get information about

        Returns:
            Dictionary with nameserver information:
            {
                "Nameserver": "ns1.example.com",
                "IP": "192.0.2.1"  # Only present if IP is assigned
            }

        Raises:
            NamecheapException: If the API returns an error or nameserver not found
        """
        # Get all nameservers
        ns_list = self.get_list(domain_name)

        # Find the specific nameserver
        nameservers = ns_list["nameservers"] if isinstance(ns_list, dict) else []
        for ns in nameservers:
            if isinstance(ns, dict) and ns.get("Nameserver") == nameserver:
                # Ensure we return a Dict[str, str]
                result: Dict[str, str] = {}
                if isinstance(ns, dict):
                    for key, value in ns.items():
                        if isinstance(value, str):
                            result[key] = value
                        elif value is not None:
                            result[key] = str(value)
                return result

        # Nameserver not found
        raise NamecheapException(
            f"Nameserver '{nameserver}' not found for domain '{domain_name}'",
            "Verify that the nameserver exists for this domain",
            "2011175"  # Using a general "nameserver not found" error code
        )

    def get(self, domain_name: str, nameserver: str, ip: str = "") -> Dict[str, str]:
        """
        Get details for a single nameserver associated with a domain

        API Documentation: https://www.namecheap.com/support/api/methods/domains-ns/get/

        Args:
            domain_name: The domain name to query
            nameserver: The specific nameserver to get information for
            ip: Optional IP address to filter results

        Returns:
            Information about the specified nameserver:
            {
                "Nameserver": "ns1.example.com",
                "IP": "192.0.2.1" (optional)
            }

        Raises:
            NamecheapException: If the API returns an error or nameserver not found
        """
        # Get the list of all nameservers
        ns_list = self.get_list(domain_name)

        # Find the specific nameserver
        nameservers = ns_list["nameservers"] if isinstance(ns_list, dict) else []
        for ns in nameservers:
            if isinstance(ns, dict) and ns.get("Nameserver") == nameserver:
                # If IP is specified, make sure it matches
                if ip and "IP" in ns and ns["IP"] != ip:
                    continue
                # Ensure we return a Dict[str, str]
                result: Dict[str, str] = {}
                if isinstance(ns, dict):
                    for key, value in ns.items():
                        if isinstance(value, str):
                            result[key] = value
                        elif value is not None:
                            result[key] = str(value)
                return result

        # If we get here, the nameserver wasn't found
        raise NamecheapException(
            f"Nameserver '{nameserver}' not found for domain '{domain_name}'",
            "Verify that the nameserver exists and is correctly specified",
            "2011175"  # Using a general "nameserver not found" error code
        )
