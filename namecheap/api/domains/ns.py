"""
Nameserver operations for domains API
"""
from typing import Any, Dict, List, Optional
import tldextract

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

    def __init__(self, client):
        """
        Initialize the nameserver API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def create(self, domain_name: str, nameserver: str, ip: str) -> Dict[str, Any]:
        """
        Creates a new nameserver

        API Documentation: https://www.namecheap.com/support/api/methods/domains-ns/create/

        Error Codes:
            2019166: Domain not found
            2011153: Email address is invalid
            2011163: Phone is invalid
            2011177: Nameserver is invalid
            2011178: IP Address is invalid
            2011280: TLD is invalid

        Args:
            domain_name: Domain to create the nameserver for
            nameserver: Nameserver to create
            ip: IP address for the nameserver

        Returns:
            Normalized dictionary with nameserver creation result:
            {
                "success": True,  # Whether the operation was successful
                "domain": "example.com",  # The domain name
                "nameserver": "ns1.example.com",  # The nameserver that was created
                "ip": "10.0.0.1"  # The IP address that was set
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate input
        if not domain_name or not isinstance(domain_name, str):
            raise ValueError("Domain name must be a non-empty string")

        if not nameserver or not isinstance(nameserver, str):
            raise ValueError("Nameserver must be a non-empty string")

        if not ip or not isinstance(ip, str):
            raise ValueError("IP address must be a non-empty string")

        # Error codes for nameserver creation
        error_codes = {
            **COMMON_NS_ERRORS,
            "2011153": {
                "explanation": "Email address is invalid",
                "fix": "Provide a valid email address"
            },
            "2011163": {
                "explanation": "Phone is invalid",
                "fix": "Provide a valid phone number"
            },
            "2011178": {
                "explanation": "IP Address is invalid",
                "fix": "Provide a valid IP address in the correct format"
            },
            "2011280": {
                "explanation": "TLD is invalid",
                "fix": "Verify the TLD is supported and spelled correctly"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Nameserver creation failed",
                "fix": "Verify that '{domain_name}' exists and all parameters are correct"
            }
        }

        # Set up context variables for error messages
        context = {"domain_name": domain_name, "nameserver": nameserver}

        # Extract domain parts
        extract = tldextract.extract(domain_name)
        sld = extract.domain
        tld = extract.suffix

        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver,
            "IP": ip
        }

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.ns.create",
            params,
            error_codes,
            context
        )

        # Use the generic normalization utility
        result = self.client.normalize_api_response(
            response=response,
            result_key="DomainNSCreateResult"
        )

        return result

    def delete(self, domain_name: str, nameserver: str) -> Dict[str, Any]:
        """
        Deletes a nameserver

        API Documentation: https://www.namecheap.com/support/api/methods/domains-ns/delete/

        Error Codes:
            2019166: Domain not found
            2016166: Domain is not associated with your account
            2011177: Nameserver is invalid
            3031510: Error deleting nameserver
            3031511: Nameserver does not exist

        Args:
            domain_name: Domain the nameserver is associated with
            nameserver: Nameserver to delete

        Returns:
            Normalized dictionary with nameserver deletion result:
            {
                "success": True,  # Whether the operation was successful
                "domain": "example.com",  # The domain name
                "nameserver": "ns1.example.com"  # The nameserver that was deleted
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate input
        if not domain_name or not isinstance(domain_name, str):
            raise ValueError("Domain name must be a non-empty string")

        if not nameserver or not isinstance(nameserver, str):
            raise ValueError("Nameserver must be a non-empty string")

        # Error codes for nameserver deletion
        error_codes = {
            **COMMON_NS_ERRORS,
            "3031510": {
                "explanation": "Error deleting nameserver",
                "fix": "There was a problem with the nameserver deletion request"
            },
            "3031511": {
                "explanation": "Nameserver does not exist",
                "fix": "The specified nameserver does not exist for this domain"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Nameserver deletion failed",
                "fix": "Verify that '{domain_name}' exists and nameserver '{nameserver}' is valid"
            }
        }

        # Set up context variables for error messages
        context = {"domain_name": domain_name, "nameserver": nameserver}

        # Extract domain parts
        extract = tldextract.extract(domain_name)
        sld = extract.domain
        tld = extract.suffix

        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver
        }

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.ns.delete",
            params,
            error_codes,
            context
        )

        # Use the generic normalization utility
        result = self.client.normalize_api_response(
            response=response,
            result_key="DomainNSDeleteResult"
        )

        return result

    def update(self, domain_name: str, nameserver: str, old_ip: str, new_ip: str) -> Dict[str, Any]:
        """
        Updates the IP address of a registered nameserver

        API Documentation: https://www.namecheap.com/support/api/methods/domains-ns/update/

        Error Codes:
            2019166: Domain not found
            2016166: Domain is not associated with your account
            2011153: Nameserver not found
            2011154: Nameserver is not valid for this domain
            2011155: Invalid IP address
            2011177: Nameserver is invalid

        Args:
            domain_name: Domain the nameserver is associated with
            nameserver: Nameserver to update
            old_ip: Old IP address
            new_ip: New IP address

        Returns:
            Normalized dictionary with nameserver update result:
            {
                "success": True,  # Whether the operation was successful
                "domain": "example.com",  # The domain name
                "nameserver": "ns1.example.com",  # The nameserver that was updated
                "old_ip": "10.0.0.1",  # The old IP address
                "ip": "10.0.0.2"  # The new IP address
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate input
        if not domain_name or not isinstance(domain_name, str):
            raise ValueError("Domain name must be a non-empty string")

        if not nameserver or not isinstance(nameserver, str):
            raise ValueError("Nameserver must be a non-empty string")

        if not old_ip or not isinstance(old_ip, str):
            raise ValueError("Old IP address must be a non-empty string")

        if not new_ip or not isinstance(new_ip, str):
            raise ValueError("New IP address must be a non-empty string")

        # Error codes for nameserver update
        error_codes = {
            **COMMON_NS_ERRORS,
            "2011153": {
                "explanation": "Nameserver not found",
                "fix": "Verify that the nameserver exists for this domain"
            },
            "2011154": {
                "explanation": "Nameserver is not valid for this domain",
                "fix": "The nameserver cannot be updated for this domain"
            },
            "2011155": {
                "explanation": "Invalid IP address",
                "fix": "Provide a valid IP address in the correct format"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Nameserver update failed",
                "fix": "Verify that '{domain_name}' exists and all parameters are correct"
            }
        }

        # Set up context variables for error messages
        context = {"domain_name": domain_name, "nameserver": nameserver}

        # Extract domain parts
        extract = tldextract.extract(domain_name)
        sld = extract.domain
        tld = extract.suffix

        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver,
            "OldIP": old_ip,
            "IP": new_ip
        }

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.ns.update",
            params,
            error_codes,
            context
        )

        # Use the generic normalization utility
        result = self.client.normalize_api_response(
            response=response,
            result_key="DomainNSUpdateResult"
        )

        return result

    def get_info(self, domain_name: str, nameserver: str) -> Dict[str, Any]:
        """
        Retrieves information about a registered nameserver

        API Documentation: https://www.namecheap.com/support/api/methods/domains-ns/get-info/

        Error Codes:
            2019166: Domain not found
            2016166: Domain is not associated with your account
            2011177: Nameserver is invalid

        Args:
            domain_name: Domain the nameserver is associated with
            nameserver: Nameserver to get information for

        Returns:
            Normalized dictionary with nameserver information:
            {
                "nameserver": "ns1.example.com",  # The nameserver name
                "ip": "10.0.0.1",  # The IP address
                "domain": "example.com",  # The domain name
                "statuses": ["OK"]  # List of status strings
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        # Validate input
        if not domain_name or not isinstance(domain_name, str):
            raise ValueError("Domain name must be a non-empty string")

        if not nameserver or not isinstance(nameserver, str):
            raise ValueError("Nameserver must be a non-empty string")

        # Error codes for getting nameserver info
        error_codes = {
            **COMMON_NS_ERRORS,
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get nameserver information",
                "fix": "Verify that '{domain_name}' exists and nameserver '{nameserver}' is valid"
            }
        }

        # Set up context variables for error messages
        context = {"domain_name": domain_name, "nameserver": nameserver}

        # Extract domain parts
        extract = tldextract.extract(domain_name)
        sld = extract.domain
        tld = extract.suffix

        params = {
            "SLD": sld,
            "TLD": tld,
            "Nameserver": nameserver
        }

        # Make the API call with centralized error handling
        response = self.client._make_request(
            "namecheap.domains.ns.getInfo",
            params,
            error_codes,
            context
        )

        # Use the generic normalization utility
        result = self.client.normalize_api_response(
            response=response,
            result_key="DomainNSInfoResult"
        )

        return result
