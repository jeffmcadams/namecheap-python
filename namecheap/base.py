"""
Base client for Namecheap API
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import requests

from .exceptions import NamecheapException


class BaseClient:
    """
    Base client handling authentication and requests
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
