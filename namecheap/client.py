"""
Namecheap API Python client

A Python wrapper for interacting with the Namecheap API.
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import requests

from .exceptions import NamecheapException


class NamecheapClient:
    """
    Client for interacting with the Namecheap API
    """

    SANDBOX_API_URL = "https://api.sandbox.namecheap.com/xml.response"
    PRODUCTION_API_URL = "https://api.namecheap.com/xml.response"

    # API rate limits
    RATE_LIMIT_MINUTE = 20
    RATE_LIMIT_HOUR = 700
    RATE_LIMIT_DAY = 8000

    def __init__(
        self,
        api_user: Optional[str] = None,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        client_ip: Optional[str] = None,
        sandbox: Optional[bool] = None,
        debug: bool = False,
        load_env: bool = True,
    ):
        """
        Initialize the Namecheap API client

        If credentials are not provided directly, they will be loaded from environment variables
        when load_env=True (default):
            - NAMECHEAP_API_USER: Your Namecheap API username
            - NAMECHEAP_API_KEY: Your API key
            - NAMECHEAP_USERNAME: Your Namecheap username (typically the same as API_USER)
            - NAMECHEAP_CLIENT_IP: Your whitelisted IP address
            - NAMECHEAP_USE_SANDBOX: "True" for sandbox environment, "False" for production

        Args:
            api_user: Your Namecheap username for API access
            api_key: Your API key generated from Namecheap account
            username: Your Namecheap username (typically the same as api_user)
            client_ip: The whitelisted IP address making the request
            sandbox: Whether to use the sandbox environment (default: read from env or True)
            debug: Whether to enable debug logging (default: False)
            load_env: Whether to load credentials from environment variables (default: True)
                      If True, environment values are used as fallbacks for any parameters not provided

        Raises:
            ValueError: If required credentials are missing after attempting to load from environment
        """
        # Try to load environment variables if load_env is True
        if load_env:
            try:
                # Attempt to import dotenv for enhanced functionality
                from dotenv import find_dotenv, load_dotenv

                dotenv_path = find_dotenv(usecwd=True)
                if dotenv_path:
                    load_dotenv(dotenv_path)
            except ImportError:
                # dotenv package not installed, just use os.environ
                pass

            import os

            # Use provided values or fall back to environment variables
            self.api_user = api_user or os.environ.get("NAMECHEAP_API_USER")
            self.api_key = api_key or os.environ.get("NAMECHEAP_API_KEY")
            self.username = username or os.environ.get("NAMECHEAP_USERNAME")
            self.client_ip = client_ip or os.environ.get("NAMECHEAP_CLIENT_IP")

            # Handle sandbox setting
            if sandbox is None:
                sandbox_value = os.environ.get("NAMECHEAP_USE_SANDBOX", "True")
                sandbox = sandbox_value.lower() in ("true", "yes", "1")
        else:
            # Use provided values directly
            self.api_user = api_user
            self.api_key = api_key
            self.username = username
            self.client_ip = client_ip

            # Default to sandbox mode if not specified
            if sandbox is None:
                sandbox = True

        # Validate required credentials
        missing_vars = []
        if not self.api_user:
            missing_vars.append("api_user (NAMECHEAP_API_USER)")
        if not self.api_key:
            missing_vars.append("api_key (NAMECHEAP_API_KEY)")
        if not self.username:
            missing_vars.append("username (NAMECHEAP_USERNAME)")
        if not self.client_ip:
            missing_vars.append("client_ip (NAMECHEAP_CLIENT_IP)")

        if missing_vars:
            error_message = (
                f"Missing required Namecheap API credentials: {', '.join(missing_vars)}.\n\n"
                "Please either:\n"
                "1. Create a .env file in your project directory with these variables, or\n"
                "2. Set them as environment variables in your shell, or\n"
                "3. Pass them explicitly when creating the NamecheapClient instance\n\n"
                "Example .env file:\n"
                "NAMECHEAP_API_USER=your_username\n"
                "NAMECHEAP_API_KEY=your_api_key\n"
                "NAMECHEAP_USERNAME=your_username\n"
                "NAMECHEAP_CLIENT_IP=your_whitelisted_ip\n"
                "NAMECHEAP_USE_SANDBOX=True"
            )
            raise ValueError(error_message)

        # Set URL based on sandbox setting
        self.base_url = self.SANDBOX_API_URL if sandbox else self.PRODUCTION_API_URL
        self.debug = debug

    def _get_base_params(self) -> Dict[str, str]:
        """
        Get the base parameters required for all API requests

        Returns:
            Dict containing the base authentication parameters
        """
        # We know these are not None because we've checked in __init__
        assert self.api_user is not None
        assert self.api_key is not None
        assert self.username is not None
        assert self.client_ip is not None

        return {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.username,
            "ClientIp": self.client_ip,
        }

    def _make_request(
        self, command: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Namecheap API

        Args:
            command: The API command to execute (e.g., "namecheap.domains.check")
            params: Additional parameters for the API request

        Returns:
            Parsed response from the API

        Raises:
            NamecheapException: If the API returns an error
            requests.RequestException: If there's an issue with the HTTP request
        """
        request_params = self._get_base_params()
        request_params["Command"] = command

        if params:
            request_params.update(params)

        if self.debug:
            print(f"Making request to {self.base_url}")
            print(f"Parameters: {request_params}")

        response = requests.get(self.base_url, params=request_params)

        if self.debug:
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text[:1000]}...")

        response.raise_for_status()

        return self._parse_response(response.text)

    def _parse_response(self, xml_response: str) -> Dict[str, Any]:
        """
        Parse the XML response from the API into a Python dictionary

        Args:
            xml_response: The XML response from the API

        Returns:
            Parsed response as a dictionary

        Raises:
            NamecheapException: If the API returns an error
        """
        # Direct error handling for common error messages - handles the malformed XML case
        if "API Key is invalid or API access has not been enabled" in xml_response:
            raise NamecheapException(
                "1011102",
                "API Key is invalid or API access has not been enabled - Please verify your API key and ensure API access is enabled at https://ap.www.namecheap.com/settings/tools/apiaccess/",
            )
        elif "IP is not in the whitelist" in xml_response:
            raise NamecheapException(
                "1011147",
                "IP is not in the whitelist - Please whitelist your IP address in your Namecheap API settings",
            )

        # Fix common XML syntax errors
        xml_response = xml_response.replace("</e>", "</Error>")

        try:
            root = ET.fromstring(xml_response)
        except ET.ParseError as e:
            # Last resort error handling
            raise NamecheapException(
                "XML_PARSE_ERROR", f"Failed to parse XML response: {str(e)}"
            )

        # Check if there was an error
        status = root.attrib.get("Status")
        if status == "ERROR":
            errors = root.findall(".//Errors/Error")

            if errors and len(errors) > 0:
                # Get the first error details
                error = errors[0]
                error_text = error.text or "Unknown error"
                error_number = error.attrib.get("Number", "0")

                # Create descriptive error message based on common error codes
                if error_number == "1011102":
                    error_text = f"{error_text} - Please verify your API key and ensure API access is enabled at https://ap.www.namecheap.com/settings/tools/apiaccess/"
                elif error_number == "1011147":
                    error_text = f"{error_text} - Please whitelist your IP address in your Namecheap API settings"
                elif error_number == "1010900":
                    error_text = f"{error_text} - Please check your username is correct"

                raise NamecheapException(error_number, error_text)
            else:
                raise NamecheapException(
                    "UNKNOWN_ERROR",
                    "Unknown error occurred but no error details provided",
                )

        # Handle namespaces in the XML
        namespaces = {"ns": "http://api.namecheap.com/xml.response"}

        # Special handling for domains.check command
        requested_command = root.find(".//ns:RequestedCommand", namespaces)
        if (
            requested_command is not None
            and requested_command.text == "namecheap.domains.check"
        ):
            domain_results = []
            for domain_elem in root.findall(".//ns:DomainCheckResult", namespaces):
                # Always convert price to a number
                price_str = domain_elem.get("PremiumRegistrationPrice", "0")
                price = float(price_str) if price_str else 0.0

                domain_info = {
                    "Domain": domain_elem.get("Domain"),
                    "Available": domain_elem.get("Available") == "true",
                    "IsPremiumName": domain_elem.get("IsPremiumName") == "true",
                    "PremiumRegistrationPrice": price,
                }
                domain_results.append(domain_info)
            return {"DomainCheckResult": domain_results}

        # Standard parsing for other commands
        command_response = root.find(".//ns:CommandResponse", namespaces)
        if command_response is None:
            return {}

        return self._element_to_dict(command_response)

    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Convert an XML element to a Python dictionary

        Args:
            element: The XML element to convert

        Returns:
            Dictionary representation of the XML element
        """
        result: Dict[str, Any] = {}

        # Add element attributes
        for key, value in element.attrib.items():
            # Convert some common boolean-like values
            if value.lower() in ("true", "yes", "enabled"):
                result[key] = True
            elif value.lower() in ("false", "no", "disabled"):
                result[key] = False
            else:
                result[key] = value

        # Process child elements
        for child in element:
            child_data = self._element_to_dict(child)

            # Remove namespace from tag if present
            tag = child.tag
            if "}" in tag:
                tag = tag.split("}", 1)[1]  # Remove namespace part

            # Handle multiple elements with the same tag
            if tag in result:
                if isinstance(result[tag], list):
                    result[tag].append(child_data)
                else:
                    result[tag] = [result[tag], child_data]
            else:
                result[tag] = child_data

        # If the element has text and no children, just return the text value in a dict
        if element.text and element.text.strip() and len(result) == 0:
            text = element.text.strip()
            # Try to convert to appropriate types
            element_value: Any
            if text.isdigit():
                element_value = int(text)
            elif text.lower() in ("true", "yes", "enabled"):
                element_value = True
            elif text.lower() in ("false", "no", "disabled"):
                element_value = False
            else:
                element_value = text

            # Get the tag name without namespace
            tag = element.tag
            if "}" in tag:
                tag = tag.split("}", 1)[1]

            # Return a dict with the tag as key and the value
            return {tag: element_value}

        return result

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

    # Domain API Methods

    def domains_check(self, domains: List[str]) -> Dict[str, Any]:
        """
        Check if domains are available for registration

        Args:
            domains: List of domains to check availability (max 50)

        Returns:
            Dictionary with availability information for each domain.
            The result is a dictionary with a "DomainCheckResult" key that contains
            a list of dictionaries, each with domain information including:
            - Domain: domain name
            - Available: whether the domain is available (boolean)
            - IsPremiumName: whether the domain is a premium name (boolean)
            - PremiumRegistrationPrice: price for premium domains

        Raises:
            ValueError: If more than 50 domains are provided
            NamecheapException: If the API returns an error
        """
        if len(domains) > 50:
            raise ValueError(
                "Maximum of 50 domains can be checked in a single API call"
            )

        # Format the domain list according to API requirements
        domain_list = ",".join(domains)

        params = {"DomainList": domain_list}

        # Make the API request
        result = self._make_request("namecheap.domains.check", params)

        # Extract domain check results from the response and normalize format
        normalized_results = []

        # Handle direct access to DomainCheckResult
        if "DomainCheckResult" in result:
            domain_results = result["DomainCheckResult"]
            if not isinstance(domain_results, list):
                domain_results = [domain_results]
            normalized_results = domain_results
        # Handle nested structure
        elif "CommandResponse" in result and isinstance(
            result["CommandResponse"], dict
        ):
            command_resp = result["CommandResponse"]
            if "DomainCheckResult" in command_resp:
                domain_results = command_resp["DomainCheckResult"]
                if not isinstance(domain_results, list):
                    domain_results = [domain_results]
                normalized_results = domain_results

        # Normalize result values to standard format
        for domain in normalized_results:
            # Convert string boolean values to Python booleans
            if "Available" in domain and isinstance(domain["Available"], str):
                domain["Available"] = domain["Available"].lower() == "true"
            if "IsPremiumName" in domain and isinstance(domain["IsPremiumName"], str):
                domain["IsPremiumName"] = domain["IsPremiumName"].lower() == "true"

            # Handle attribute-style values from XML
            if "@Domain" in domain and "Domain" not in domain:
                domain["Domain"] = domain.pop("@Domain")
            if "@Available" in domain and "Available" not in domain:
                avail_val = domain.pop("@Available")
                domain["Available"] = avail_val.lower() == "true"
            if "@IsPremiumName" in domain and "IsPremiumName" not in domain:
                premium_val = domain.pop("@IsPremiumName")
                domain["IsPremiumName"] = premium_val.lower() == "true"
            if (
                "@PremiumRegistrationPrice" in domain
                and "PremiumRegistrationPrice" not in domain
            ):
                price_str = domain.pop("@PremiumRegistrationPrice")
                domain["PremiumRegistrationPrice"] = (
                    float(price_str) if price_str else 0.0
                )

        # Return a standardized result structure
        return {"DomainCheckResult": normalized_results}

    def domains_get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "NAME",
        list_type: str = "ALL",
        search_term: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of domains in the user's account

        Args:
            page: Page number to return (default: 1)
            page_size: Number of domains to return per page (default: 20, max: 100)
            sort_by: Column to sort by (NAME, NAME_DESC, EXPIREDATE, EXPIREDATE_DESC, CREATEDATE, CREATEDATE_DESC)
            list_type: Type of domains to list (ALL, EXPIRING, EXPIRED)
            search_term: Keyword to look for in the domain list

        Returns:
            Dictionary with domain list information

        Raises:
            ValueError: If page_size is greater than 100
            NamecheapException: If the API returns an error
        """
        if page_size > 100:
            raise ValueError("Maximum page size is 100")

        valid_sort_options = [
            "NAME",
            "NAME_DESC",
            "EXPIREDATE",
            "EXPIREDATE_DESC",
            "CREATEDATE",
            "CREATEDATE_DESC",
        ]
        if sort_by not in valid_sort_options:
            raise ValueError(f"sort_by must be one of {valid_sort_options}")

        valid_list_types = ["ALL", "EXPIRING", "EXPIRED"]
        if list_type not in valid_list_types:
            raise ValueError(f"list_type must be one of {valid_list_types}")

        params = {
            "Page": page,
            "PageSize": page_size,
            "SortBy": sort_by,
            "ListType": list_type,
        }

        if search_term:
            params["SearchTerm"] = search_term

        return self._make_request("namecheap.domains.getList", params)

    def domains_get_contacts(self, domain_name: str) -> Dict[str, Any]:
        """
        Get contact information for a domain

        Args:
            domain_name: The domain name to get contact information for

        Returns:
            Dictionary with contact information for the domain

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)

        params = {"DomainName": sld, "TLD": tld}

        return self._make_request("namecheap.domains.getContacts", params)

    def domains_create(
        self,
        domain_name: str,
        years: int = 1,
        registrant_info: Optional[Dict[str, str]] = None,
        tech_info: Optional[Dict[str, str]] = None,
        admin_info: Optional[Dict[str, str]] = None,
        aux_info: Optional[Dict[str, str]] = None,
        nameservers: Optional[List[str]] = None,
        add_free_whois_guard: bool = True,
        wg_enabled: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Register a new domain

        Args:
            domain_name: The domain name to register
            years: Number of years to register the domain for (default: 1)
            registrant_info: Registrant contact information (required)
            tech_info: Technical contact information (if not provided, registrant_info is used)
            admin_info: Administrative contact information (if not provided, registrant_info is used)
            aux_info: Billing/Auxiliary contact information (if not provided, registrant_info is used)
            nameservers: List of nameservers to use (comma-separated)
            add_free_whois_guard: Whether to add free WhoisGuard privacy protection (default: True)
            wg_enabled: Whether to enable WhoisGuard (default: True)
            **kwargs: Additional parameters to pass to the API

        Returns:
            Dictionary with domain registration information

        Raises:
            ValueError: If registrant_info is not provided
            NamecheapException: If the API returns an error
        """
        if not registrant_info:
            raise ValueError("registrant_info is required for domain registration")

        sld, tld = self._split_domain_name(domain_name)

        params = {
            "DomainName": sld,
            "TLD": tld,
            "Years": years,
            "AddFreeWhoisGuard": "yes" if add_free_whois_guard else "no",
            "WGEnabled": "yes" if wg_enabled else "no",
        }

        # Add nameservers if provided
        if nameservers:
            params["Nameservers"] = ",".join(nameservers)

        # Add contact information
        contacts = {
            "Registrant": registrant_info,
            "Tech": tech_info if tech_info else registrant_info,
            "Admin": admin_info if admin_info else registrant_info,
            "AuxBilling": aux_info if aux_info else registrant_info,
        }

        for contact_type, info in contacts.items():
            if info:
                for key, value in info.items():
                    params[f"{contact_type}{key}"] = value

        # Add any additional parameters
        params.update(kwargs)

        return self._make_request("namecheap.domains.create", params)

    def domains_get_tld_list(self) -> Dict[str, Any]:
        """
        Get a list of available TLDs

        Returns:
            Dictionary with TLD information

        Raises:
            NamecheapException: If the API returns an error
        """
        return self._make_request("namecheap.domains.getTldList")

    def domains_renew(
        self, domain_name: str, years: int = 1, promotion_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Renew a domain

        Args:
            domain_name: The domain name to renew
            years: Number of years to renew the domain for (default: 1)
            promotion_code: Promotional (coupon) code for the domain renewal

        Returns:
            Dictionary with domain renewal information

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)

        params = {"DomainName": sld, "TLD": tld, "Years": years}

        if promotion_code:
            params["PromotionCode"] = promotion_code

        return self._make_request("namecheap.domains.renew", params)

    def domains_get_info(self, domain_name: str) -> Dict[str, Any]:
        """
        Get information about a domain

        Args:
            domain_name: The domain name to get information for

        Returns:
            Dictionary with domain information

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)

        params = {
            "DomainName": sld,
            "TLD": tld,
        }

        return self._make_request("namecheap.domains.getInfo", params)

    def domains_dns_set_custom(
        self, domain_name: str, nameservers: List[str]
    ) -> Dict[str, Any]:
        """
        Set custom nameservers for a domain

        Args:
            domain_name: The domain name to set nameservers for
            nameservers: List of nameservers to use (max 12)

        Returns:
            Dictionary with status information

        Raises:
            ValueError: If more than 12 nameservers are provided
            NamecheapException: If the API returns an error
        """
        if len(nameservers) > 12:
            raise ValueError("Maximum of 12 nameservers can be set")

        sld, tld = self._split_domain_name(domain_name)

        params = {"DomainName": sld, "TLD": tld, "Nameservers": ",".join(nameservers)}

        return self._make_request("namecheap.domains.dns.setCustom", params)

    def domains_dns_set_default(self, domain_name: str) -> Dict[str, Any]:
        """
        Set default nameservers for a domain

        Args:
            domain_name: The domain name to set nameservers for

        Returns:
            Dictionary with status information

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)

        params = {
            "DomainName": sld,
            "TLD": tld,
        }

        return self._make_request("namecheap.domains.dns.setDefault", params)

    def domains_dns_get_hosts(self, domain_name: str) -> Dict[str, Any]:
        """
        Get DNS host records for a domain

        Args:
            domain_name: The domain name to get host records for

        Returns:
            Dictionary with host record information in a standardized format:
            {
                "DomainDNSGetHostsResult": {
                    "Domain": "example.com",
                    "IsUsingOurDNS": True,
                    "EmailType": "NONE",
                    "host": [
                        {
                            "Name": "@",
                            "Type": "A",
                            "Address": "192.0.2.1",
                            "MXPref": "10",
                            "TTL": "1800",
                            "HostId": "12345",
                            "IsActive": True
                        },
                        ...
                    ]
                }
            }

        Raises:
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)

        params = {
            "SLD": sld,
            "TLD": tld,
        }

        result = self._make_request("namecheap.domains.dns.getHosts", params)

        # Sample successful response:
        # {
        #   "Type": "namecheap.domains.dns.getHosts",
        #   "DomainDNSGetHostsResult": {
        #     "Domain": "example.com",
        #     "EmailType": "NONE",
        #     "IsUsingOurDNS": true,
        #     "host": [
        #       {
        #         "HostId": "123456",
        #         "Name": "@",
        #         "Type": "A",
        #         "Address": "192.0.2.1",
        #         "MXPref": "10",
        #         "TTL": "1800",
        #         "IsActive": true
        #       },
        #       {
        #         "HostId": "123457",
        #         "Name": "www",
        #         "Type": "CNAME",
        #         "Address": "example.com.",
        #         "MXPref": "10",
        #         "TTL": "1800",
        #         "IsActive": true
        #       }
        #     ]
        #   }
        # }

        # Normalize the response to ensure host is always a list
        if "DomainDNSGetHostsResult" in result:
            hosts_result = result["DomainDNSGetHostsResult"]

            if "host" in hosts_result:
                host_records = hosts_result["host"]
                # Convert single host record to a list for consistency
                if not isinstance(host_records, list):
                    hosts_result["host"] = [host_records]
            else:
                # No host records found, initialize with empty list
                hosts_result["host"] = []

        return result

    def domains_dns_set_hosts(
        self, domain_name: str, hosts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Set DNS host records for a domain

        Args:
            domain_name: The domain name to set host records for
            hosts: List of host record dictionaries with keys:
                  - HostName: Name of the host record (e.g., "@", "www")
                  - RecordType: Type of record (A, AAAA, CNAME, MX, TXT, URL, URL301, FRAME)
                  - Address: Value of the record
                  - MXPref: MX preference (required for MX records)
                  - TTL: Time to live in seconds (min 60, max 86400, default 1800)

        Returns:
            Dictionary with status information in a standardized format:
            {
                "DomainDNSSetHostsResult": {
                    "Domain": "example.com",
                    "IsSuccess": True
                }
            }

        Raises:
            ValueError: If any required host record fields are missing
            NamecheapException: If the API returns an error
        """
        sld, tld = self._split_domain_name(domain_name)

        params = {
            "SLD": sld,
            "TLD": tld,
        }

        valid_record_types = [
            "A",
            "AAAA",
            "CNAME",
            "MX",
            "TXT",
            "URL",
            "URL301",
            "FRAME",
        ]

        # Handle the case when hosts parameter is empty
        if not hosts:
            if self.debug:
                print("Warning: No host records provided for DNS update")

        # Normalize host record field names
        normalized_hosts = []
        for host in hosts:
            # Convert between the API format (HostName) and a more user-friendly format (Name)
            normalized_host = {}

            # Handle Name/HostName field
            if "Name" in host:
                normalized_host["HostName"] = host["Name"]
            elif "HostName" in host:
                normalized_host["HostName"] = host["HostName"]
            else:
                raise ValueError(
                    "Host record is missing required field 'Name' or 'HostName'"
                )

            # Handle Type/RecordType field
            if "Type" in host:
                normalized_host["RecordType"] = host["Type"]
            elif "RecordType" in host:
                normalized_host["RecordType"] = host["RecordType"]
            else:
                raise ValueError(
                    "Host record is missing required field 'Type' or 'RecordType'"
                )

            # Handle Address/Value field
            if "Value" in host:
                normalized_host["Address"] = host["Value"]
            elif "Address" in host:
                normalized_host["Address"] = host["Address"]
            else:
                raise ValueError(
                    "Host record is missing required field 'Value' or 'Address'"
                )

            # Handle MXPref/Priority field
            if normalized_host["RecordType"] == "MX":
                if "Priority" in host:
                    normalized_host["MXPref"] = host["Priority"]
                elif "MXPref" in host:
                    normalized_host["MXPref"] = host["MXPref"]
                else:
                    # Use default value for MX priority
                    normalized_host["MXPref"] = "10"

            # Handle TTL field
            if "TTL" in host:
                ttl = host["TTL"]
                # Convert to string if it's an integer
                if isinstance(ttl, int):
                    ttl = str(ttl)
                normalized_host["TTL"] = ttl
            else:
                # Use default TTL
                normalized_host["TTL"] = "1800"

            normalized_hosts.append(normalized_host)

        # Add host records to API parameters
        for i, host in enumerate(normalized_hosts):
            record_type = host["RecordType"]
            if record_type not in valid_record_types:
                raise ValueError(
                    f"Invalid record type '{record_type}'. Must be one of {valid_record_types}"
                )

            # If TTL is provided, validate it
            if "TTL" in host:
                try:
                    ttl = int(host["TTL"])
                    if ttl < 60 or ttl > 86400:
                        raise ValueError("TTL must be between 60 and 86400 seconds")
                except ValueError:
                    raise ValueError(
                        f"Invalid TTL value: {host['TTL']}. Must be an integer between 60 and 86400."
                    )

            params[f"HostName{i+1}"] = host["HostName"]
            params[f"RecordType{i+1}"] = host["RecordType"]
            params[f"Address{i+1}"] = host["Address"]

            if "MXPref" in host:
                params[f"MXPref{i+1}"] = host["MXPref"]
            if "TTL" in host:
                params[f"TTL{i+1}"] = host["TTL"]

        if self.debug:
            print(f"Setting {len(normalized_hosts)} host records for {domain_name}")

        result = self._make_request("namecheap.domains.dns.setHosts", params)

        # Sample successful response:
        # {
        #   "Type": "namecheap.domains.dns.setHosts",
        #   "DomainDNSSetHostsResult": {
        #     "Domain": "example.com",
        #     "IsSuccess": true
        #   }
        # }

        return result
