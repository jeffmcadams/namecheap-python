"""
Base client for Namecheap API
"""

import xml.etree.ElementTree as ET
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, TypeVar, Callable, cast

import requests
import xmltodict
import logging

from .exceptions import NamecheapException

# Type for the generic response
T = TypeVar('T', Dict[str, Any], List[Dict[str, Any]])


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

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure the Namecheap logger with appropriate settings"""
        # Get the logger for Namecheap
        self.logger = logging.getLogger("namecheap")

        # Set log level based on debug flag - only show ERROR or higher in non-debug mode
        self.logger.setLevel(logging.DEBUG if self.debug else logging.ERROR)

        # Only configure handlers if none exist (avoid duplicate handlers)
        if not self.logger.handlers and not self.logger.parent.handlers:
            # Console handler
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG if self.debug else logging.ERROR)

            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s [%(name)s.%(where)s] %(levelname)s: %(message)s'
            )
            console.setFormatter(formatter)

            # Add handlers to logger
            self.logger.addHandler(console)

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

    def log(self, where: str, message: str, level: str = "DEBUG", data: Optional[Dict[str, Any]] = None) -> None:
        """
        Centralized logging method for all Namecheap API operations.

        Args:
            where: Component/section generating the log (e.g., "API.REQUEST", "CLIENT.INIT")
            message: The log message
            level: Log level (e.g., "DEBUG", "INFO", "ERROR")
            data: Optional dictionary of additional data to include
        """
        # Convert level string to logging level
        log_level = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }.get(level, logging.INFO)

        # Skip DEBUG logs in non-debug mode
        if log_level == logging.DEBUG and not self.debug:
            return

        # Format data for logging
        log_data = {}
        if data:
            if isinstance(data, dict):
                for key, value in sorted(data.items()):
                    if key in ("ApiKey", "Password") and isinstance(value, str):
                        log_data[key] = "******"
                    else:
                        log_data[key] = value

        # Create the log entry with extra context
        extra = {"where": where}
        if log_data:
            message = f"{message}\nData: {log_data}"

        # Log with appropriate level
        self.logger.log(log_level, message, extra=extra)

    def normalize_api_response(
        self,
        response: Dict[str, Any],
        result_key: Optional[str] = None,
        field_mapping: Optional[Dict[str, str]] = None,
        boolean_fields: Optional[List[str]] = None,
        datetime_fields: Optional[List[str]] = None,
        return_type: str = "dict"
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generic API response normalizer that standardizes Namecheap API responses

        Args:
            response: Raw API response dictionary
            result_key: Key to extract from response (e.g., "DomainDNSGetHostsResult" or "DomainDNSGetHostsResult.host")
                     Use dot notation to access nested keys
            field_mapping: Optional mapping to rename fields {'HostId': 'id'} (default: None, keep original names)
            boolean_fields: Optional list of additional fields to convert to boolean (default: None)
                          Fields with 'Is' prefix or containing true/false values are automatically converted
            datetime_fields: Optional list of fields to parse as datetime objects (default: None)
            return_type: Type of return value: "dict" for a single object, "list" for a list of objects

        Returns:
            Normalized response with consistent field names and types as either a dict or list of dicts
        """
        if response is None:
            if return_type == "list":
                return []
            return {}

        # Extract data from nested structure if result_key is provided
        data = response
        if result_key:
            for key in result_key.split('.'):
                if key in data:
                    data = data[key]
                else:
                    if return_type == "list":
                        return []
                    return {}

        # Initialize defaults
        field_mapping = field_mapping or {}
        boolean_fields = boolean_fields or []
        datetime_fields = datetime_fields or []

        # Handle single item vs list
        if return_type == "list":
            # Ensure data is a list
            if not isinstance(data, list):
                data = [data] if data else []

            normalized_items = []
            for item in data:
                normalized = self._normalize_item(
                    item,
                    field_mapping,
                    boolean_fields,
                    datetime_fields
                )
                normalized_items.append(normalized)
            return normalized_items
        else:
            # Single item normalization
            return self._normalize_item(
                data,
                field_mapping,
                boolean_fields,
                datetime_fields
            )

    def _normalize_item(
        self,
        item: Dict[str, Any],
        field_mapping: Dict[str, str],
        boolean_fields: List[str],
        datetime_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Normalize a single item using the provided mappings and type conversions

        Args:
            item: Item to normalize
            field_mapping: Field name mapping (optional)
            boolean_fields: Additional fields to convert to boolean
            datetime_fields: Fields to convert to datetime

        Returns:
            Normalized dictionary
        """
        result = {}

        # Process all fields in the item
        for key, value in item.items():
            # Remove @ prefix if present
            clean_key = key[1:] if key.startswith('@') else key

            # Apply mapping if provided
            if key in field_mapping:
                clean_key = field_mapping[key]

            # Store the value with proper type conversion
            result[clean_key] = value

        # Auto-detect and convert boolean fields
        for key in result:
            value = result[key]

            # Convert fields with "Is" prefix to boolean
            if key.startswith("Is") or key in boolean_fields:
                if isinstance(value, str):
                    result[key] = value.lower() in (
                        'true', 'yes', 'enabled', '1')

            # Convert fields with true/false values to boolean
            elif isinstance(value, str) and value.lower() in ('true', 'false'):
                result[key] = value.lower() == 'true'

        # Convert datetime fields
        for field in datetime_fields:
            if field in result and isinstance(result[field], str):
                try:
                    # Try different datetime formats
                    for fmt in [
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%d %H:%M:%S',
                        '%m/%d/%Y',
                        '%Y-%m-%d'
                    ]:
                        try:
                            result[field] = datetime.datetime.strptime(
                                result[field], fmt)
                            break
                        except ValueError:
                            continue
                except Exception:
                    # Keep as string if parsing fails
                    pass

        return result

    def _make_request(
        self, command: str, params: Optional[Dict[str, Any]] = None,
        error_codes: Optional[Dict[str, Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the Namecheap API with centralized error handling

        Args:
            command: The API command to execute (e.g., "namecheap.domains.check")
            params: Additional parameters for the API request
            error_codes: Dictionary mapping error codes to explanations and fixes
            context: Additional context variables to include in formatted messages

        Returns:
            Parsed response from the API

        Raises:
            NamecheapException: If the API returns an error
            requests.RequestException: If there's an issue with the HTTP request
        """
        context = context or {}
        request_params = self._get_base_params()
        request_params["Command"] = command

        if params:
            request_params.update(params)

        # Create debug-safe params (hide sensitive info)
        debug_params = request_params.copy()
        self.log(
            "API.REQUEST",
            f"Sending request to {self.base_url} with command {command}",
            "DEBUG",
            debug_params
        )

        try:
            response = requests.get(self.base_url, params=request_params)

            preview = response.text[:500]
            if len(response.text) > 500:
                preview += "..."

            self.log(
                "API.RESPONSE",
                f"Received response with status {response.status_code}",
                "DEBUG",
                {"Content-Length": len(response.text), "Preview": preview}
            )

            response.raise_for_status()
            return self._parse_response(response, error_codes, context)
        except NamecheapException:
            # Exception already created in _parse_response with proper context
            raise
        except requests.RequestException as e:
            # Handle HTTP errors
            self.log("API.ERROR", f"HTTP request failed: {str(e)}", "ERROR")

            raise NamecheapException(
                "CONNECTION_ERROR",
                f"Failed to connect to Namecheap API: {str(e)}",
                self
            )

    def _parse_response(
        self, response: requests.Response,
        error_codes: Optional[Dict[str, Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse the API response and handle errors.

        Args:
            response: The HTTP response from the API
            error_codes: Optional dict mapping error codes to helpful messages
            context: Optional dict with context about the request to add to error messages

        Returns:
            Dict containing the parsed API response

        Raises:
            NamecheapException: If the API returns an error response
        """
        try:
            # Parse XML response to dict
            response_dict = xmltodict.parse(response.text)

            # Extract API response
            api_response = response_dict.get("ApiResponse", {})

            # Get response status
            status = api_response.get("@Status", "UNKNOWN")

            # If status is ERROR, raise exception
            if status == "ERROR":
                errors = api_response.get("Errors", {})
                error = errors.get("Error", {})

                # Handle case with multiple errors
                if isinstance(error, list):
                    error = error[0]

                error_num = error.get("@Number", "UNKNOWN_ERROR")
                error_msg = error.get("#text", "Unknown error occurred")

                # Look up a better error message if available
                if error_codes and error_num in error_codes:
                    error_info = error_codes[error_num]
                    error_explanation = error_info.get("explanation", "")
                    error_fix = error_info.get("fix", "")

                    # Format message with context
                    if context:
                        for k, v in context.items():
                            # Try to replace tokens in the message
                            placeholder = "{" + k + "}"
                            if error_explanation and placeholder in error_explanation:
                                error_explanation = error_explanation.replace(
                                    placeholder, str(v))
                            if error_fix and placeholder in error_fix:
                                error_fix = error_fix.replace(
                                    placeholder, str(v))
                else:
                    error_explanation = None
                    error_fix = None

                # Get the command response for more details
                command_response = api_response.get("CommandResponse", {})

                # Debug: Print full response for errors
                if self.debug:
                    print(
                        f"\n[NAMECHEAP.API.ERROR] (ERROR) API Error: {error_num}: {error_msg}")
                    print(f"Full XML Response:\n{response.text[:2000]}" +
                          ("..." if len(response.text) > 2000 else ""))

                # Raise exception with details
                raise NamecheapException(
                    client=self,
                    code=error_num,
                    message=error_msg,
                    explanation=error_explanation,
                    fix=error_fix,
                    raw_response=response.text
                )

            # Return the command response section if successful
            command_response = api_response.get("CommandResponse", {})
            return command_response

        except Exception as e:
            # If not a NamecheapException, wrap it
            if not isinstance(e, NamecheapException):
                raise NamecheapException(
                    client=self,
                    code="PARSE_ERROR",
                    message=f"Failed to parse API response: {str(e)}",
                    raw_response=response.text if hasattr(
                        response, 'text') else None
                )
            raise

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
