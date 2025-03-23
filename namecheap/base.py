"""
Base client for interacting with the Namecheap API
"""

import contextlib
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import (
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

import requests
import xmltodict

from .exceptions import NamecheapException

# Types for response data
JsonValue = Union[str, bool, int, float, None]

# Types for API responses - preserve structural compatibility with TypedDict
# Nested data structures to be used with normalize_api_response
T = TypeVar("T")  # Generic type var for flexibility
ResponseValue = Union[JsonValue, Dict[str, object], List[object]]
# We use structural compatibility to avoid casting
# A Dict[str, object] can be used where TypedDict is expected
ResponseDict = Dict[str, object]  # Raw API response dictionary
ResponseItem = Dict[str, object]  # Normalized dictionary item
ResponseList = List[Dict[str, object]]  # List of normalized items


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

    def _setup_logging(self) -> None:
        """
        Set up logging for the client
        """
        # Get the logger for Namecheap
        self.logger = logging.getLogger("namecheap")

        # Configure handler and formatter if not already set up
        if self.logger and not self.logger.handlers:
            # Create console handler with reasonable formatting
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Set the log level based on debug mode
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def _get_base_params(self) -> Dict[str, str]:
        """
        Get the base parameters required for all API requests

        Returns:
            Dict containing the base authentication parameters
        """
        # All credential checks are done in __init__, so we can safely use these values
        api_user = self.api_user if self.api_user is not None else ""
        api_key = self.api_key if self.api_key is not None else ""
        username = self.username if self.username is not None else ""
        client_ip = self.client_ip if self.client_ip is not None else ""

        return {
            "ApiUser": api_user,
            "ApiKey": api_key,
            "UserName": username,
            "ClientIp": client_ip,
        }

    def log(
        self,
        where: str,
        message: str,
        level: str = "DEBUG",
        data: Optional[Mapping[str, object]] = None,
    ) -> None:
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
            "CRITICAL": logging.CRITICAL,
        }.get(level, logging.INFO)

        # Skip DEBUG logs in non-debug mode
        if log_level == logging.DEBUG and not self.debug:
            return

        # Format data for logging
        log_data = {}
        if data:
            # data is already confirmed to be Mapping[str, object] by the type system
            for key, value in sorted(data.items()):
                # Check if key is sensitive and value is a string without using isinstance
                is_sensitive = key in ("ApiKey", "Password")
                should_mask = is_sensitive and hasattr(
                    value, "strip"
                )  # String-like check
                log_data[key] = "******" if should_mask else value

        # Create the log entry with extra context
        extra = {"where": where}
        if log_data:
            message = f"{message}\nData: {log_data}"

        # Log with appropriate level
        self.logger.log(log_level, message, extra=extra)

    @overload
    def normalize_api_response(
        self,
        response: ResponseDict,
        result_key: Optional[str] = None,
        field_mapping: Optional[Dict[str, str]] = None,
        boolean_fields: Optional[List[str]] = None,
        datetime_fields: Optional[List[str]] = None,
        return_type: Literal["dict"] = "dict",
    ) -> ResponseDict: ...

    @overload
    def normalize_api_response(
        self,
        response: ResponseDict,
        result_key: Optional[str] = None,
        field_mapping: Optional[Dict[str, str]] = None,
        boolean_fields: Optional[List[str]] = None,
        datetime_fields: Optional[List[str]] = None,
        return_type: Literal["list"] = "list",
    ) -> ResponseList: ...

    def normalize_api_response(
        self,
        response: ResponseDict,
        result_key: Optional[str] = None,
        field_mapping: Optional[Dict[str, str]] = None,
        boolean_fields: Optional[List[str]] = None,
        datetime_fields: Optional[List[str]] = None,
        return_type: str = "dict",
    ) -> Union[ResponseDict, ResponseList]:
        """
        Normalizes API responses to a consistent format.
        Uses the new extract_value and ensure_list methods.

        Args:
            response: The API response to normalize
            result_key: Optional dot-notation key to extract from the response
            field_mapping: Dictionary mapping API field names to normalized names
            boolean_fields: List of field names to convert to boolean
            datetime_fields: List of field names to convert to datetime
            return_type: Type of return value ("dict" or "list")

        Returns:
            Normalized API response as a dictionary or list of dictionaries
        """
        # Extract data directly using the new method
        data = self.extract_value(response, result_key or "", response)
        
        # If the result is supposed to be a list, ensure it's a list
        if return_type == "list":
            result_list = self.ensure_list(data)
            
            # Process each item according to field mappings and conversions
            normalized_list: ResponseList = []
            for item in result_list:
                if not isinstance(item, dict):
                    if isinstance(item, str):
                        normalized_list.append({"Value": item})
                    continue
                    
                # Convert and map fields
                normalized_item: Dict[str, object] = {}
                for key, value in item.items():
                    # Handle XML attributes (keys starting with @)
                    if key.startswith('@'):
                        # Remove the @ prefix for the normalized key
                        key_without_prefix = key[1:]
                        # Map field name if provided
                        normalized_key = field_mapping.get(key_without_prefix, key_without_prefix) if field_mapping else key_without_prefix
                    else:
                        # Map field name if provided
                        normalized_key = field_mapping.get(key, key) if field_mapping else key
                        
                    # Convert boolean fields
                    if boolean_fields and normalized_key in boolean_fields and isinstance(value, str):
                        value = value.lower() in ("true", "yes", "enabled", "1", "on")
                        
                    # Convert datetime fields
                    if datetime_fields and normalized_key in datetime_fields and isinstance(value, str):
                        with contextlib.suppress(ValueError, TypeError, AttributeError):
                            value = datetime.strptime(value, "%m/%d/%Y")
                            
                    normalized_item[normalized_key] = value
                
                normalized_list.append(normalized_item)
                
            return normalized_list
        else:  # dict type
            if not isinstance(data, dict):
                return {}
                
            # Process the dictionary according to field mappings and conversions
            normalized_dict: Dict[str, object] = {}
            for key, value in data.items():
                # Handle XML attributes (keys starting with @)
                if key.startswith('@'):
                    # Remove the @ prefix for the normalized key
                    key_without_prefix = key[1:]
                    # Map field name if provided
                    normalized_key = field_mapping.get(key_without_prefix, key_without_prefix) if field_mapping else key_without_prefix
                else:
                    # Map field name if provided
                    normalized_key = field_mapping.get(key, key) if field_mapping else key
                    
                # Convert boolean fields
                if boolean_fields and normalized_key in boolean_fields and isinstance(value, str):
                    value = value.lower() in ("true", "yes", "enabled", "1", "on")
                    
                # Convert datetime fields
                if datetime_fields and normalized_key in datetime_fields and isinstance(value, str):
                    with contextlib.suppress(ValueError, TypeError, AttributeError):
                        value = datetime.strptime(value, "%m/%d/%Y")
                        
                normalized_dict[normalized_key] = value
                
            return normalized_dict

    def _make_request(
        self,
        command: str,
        params: Optional[Mapping[str, object]] = None,
        error_codes: Optional[Mapping[str, Dict[str, str]]] = None,
        context: Optional[Mapping[str, object]] = None,
    ) -> ResponseDict:
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
            # Convert all values to strings for the API
            for key, value in params.items():
                request_params[key] = str(value)

        # Create debug-safe params (hide sensitive info)
        debug_params = request_params.copy()
        self.log(
            "API.REQUEST",
            f"Sending request to {self.base_url} with command {command}",
            "DEBUG",
            debug_params,
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
                {"Content-Length": len(response.text), "Preview": preview},
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
                self,
            )

    def _parse_response(
        self,
        response: requests.Response,
        error_codes: Optional[Mapping[str, Dict[str, str]]] = None,
        context: Optional[Mapping[str, object]] = None,
    ) -> ResponseDict:
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
            if self.debug:
                self.log("API.RESPONSE.RAW", "Raw XML response:", "DEBUG", {"content": response.text[:1000]})
                
            # Parse XML response to dict using xmltodict for simplicity and consistency
            response_dict = xmltodict.parse(response.text)

            if self.debug:
                import json
                self.log("API.RESPONSE.PARSED", "Parsed API response", "DEBUG", 
                         {"content": json.dumps(response_dict, default=str)[:1000]})

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
                                    placeholder, str(v)
                                )
                            if error_fix and placeholder in error_fix:
                                error_fix = error_fix.replace(placeholder, str(v))
                else:
                    error_explanation = None
                    error_fix = None

                # Log the error for debugging
                self.log(
                    "API.ERROR", 
                    f"API Error: {error_num}: {error_msg}", 
                    "ERROR",
                    {"explanation": error_explanation, "fix": error_fix, "response": response.text[:1000]}
                )

                # Raise exception with details
                raise NamecheapException(
                    client=self,
                    code=error_num,
                    message=error_msg,
                    explanation=error_explanation,
                    fix=error_fix,
                    raw_response=response.text,
                )

            # Return the command response section if successful
            command_response = api_response.get("CommandResponse", {})
            # Return it directly as a ResponseDict
            return command_response if isinstance(command_response, dict) else {}

        except Exception as e:
            # If not a NamecheapException, wrap it
            if not isinstance(e, NamecheapException):
                self.log(
                    "API.PARSE.ERROR", 
                    f"Failed to parse API response: {str(e)}", 
                    "ERROR",
                    {"response": response.text[:1000] if hasattr(response, "text") else None}
                )
                raise NamecheapException(
                    client=self,
                    code="PARSE_ERROR",
                    message=f"Failed to parse API response: {str(e)}",
                    raw_response=response.text if hasattr(response, "text") else None,
                )
            raise

    def extract_value(
        self,
        data: Dict[str, object], 
        path: str, 
        default: object = None, 
        value_type: Optional[Type] = None,
        log_context: Optional[str] = None
    ) -> object:
        """
        Extract a value from a parsed dictionary using dot notation path, with type checking.
        
        This is a robust utility for accessing nested values in API responses (XML or JSON).
        This function handles all the complexities of structured data access:
        - Array indexing (using numeric indices in the path)
        - XML attribute access (@ prefixed keys from xmltodict)
        - Type conversion and validation
        - Safe navigation with defaults
        
        Args:
            data: Dictionary containing parsed data
            path: Dot-notation path (e.g., "UserGetPricingResult.ProductType.@Name")
            default: Default value to return if the path is not found
            value_type: Optional type to validate against (int, bool, str, float, etc.)
            log_context: Optional context for debug logging
            
        Returns:
            The value at the specified path, or the default if not found or wrong type
            
        Examples:
            >>> extract_value(response, "UserGetPricingResult.ProductType.@Name", "")
            'domains'
            >>> extract_value(response, "DomainCheckResult.0.@Available", False, bool)
            True
        """
        if self.debug and log_context:
            self.log("API.EXTRACT", f"Extracting {path} from {log_context}", "DEBUG")
            
        if not data:
            return default
            
        # Handle array indexes in the path (like path.0.element)
        parts = path.split('.')
        current = data
        
        for part in parts:
            # Handle array indexing
            if part.isdigit() and isinstance(current, list):
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    if self.debug and log_context:
                        self.log("API.EXTRACT", f"Array index {index} out of bounds in {path}", "DEBUG")
                    return default
            # Regular dictionary key
            elif isinstance(current, dict) and part in current:
                current = current[part]
            # Not found
            else:
                if self.debug and log_context:
                    self.log("API.EXTRACT", f"Key {part} not found in path {path}", "DEBUG")
                return default
        
        # Type validation if requested
        if value_type is not None and not isinstance(current, value_type):
            # Special case for boolean values that might be strings
            if value_type is bool and isinstance(current, str):
                return current.lower() in ('true', 'yes', '1', 'enabled')
            # Try to convert numbers
            elif value_type in (int, float) and isinstance(current, str):
                try:
                    return value_type(current)
                except (ValueError, TypeError):
                    if self.debug and log_context:
                        self.log("API.EXTRACT", f"Failed to convert '{current}' to {value_type.__name__}", "DEBUG")
                    return default
            else:
                if self.debug and log_context:
                    current_type = type(current).__name__
                    self.log("API.EXTRACT", f"Type mismatch, expected {value_type.__name__}, got {current_type}", "DEBUG")
                return default
                
        return current

    def ensure_list(self, data: object) -> List[object]:
        """
        Normalize data that might be a single item or a list into a consistent list.
        
        API responses often represent a single result as a dict and multiple results as a list of dicts.
        This function ensures consistent handling by always returning a list.
        
        Args:
            data: Data that might be a single item or a list
            
        Returns:
            A list containing the input data, normalized
        """
        if data is None:
            return []
        if isinstance(data, list):
            return data
        return [data]

    def _element_to_dict(self, element: ET.Element) -> Dict[str, object]:
        """
        Convert an XML element to a Python dictionary

        Args:
            element: The XML element to convert

        Returns:
            Dictionary representation of the XML element
        """
        result: Dict[str, object] = {}

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
                # Get the current value
                current_value = result[tag]

                # Type check for list
                if isinstance(current_value, list):
                    # Safe to append since we've verified it's a list
                    result[tag] = current_value + [child_data]
                else:
                    # Convert to list with both values
                    result[tag] = [current_value, child_data]
            else:
                result[tag] = child_data

        # If the element has text and no children, just return the text value in a dict
        if element.text and element.text.strip() and len(result) == 0:
            text = element.text.strip()
            # Try to convert to appropriate types
            element_value: JsonValue
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
