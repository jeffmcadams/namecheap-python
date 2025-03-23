"""
Exceptions for the Namecheap API client
"""

from typing import Dict, Optional, Callable, Any, Union, List


class NamecheapException(Exception):
    """
    Exception raised for errors related to Namecheap API operations.

    Attributes:
        code: Error code from Namecheap API or a custom error code
        message: Error message
        explanation: Optional explanation of what went wrong
        fix: Optional suggestion on how to fix the issue
        raw_response: Optional raw API response for debugging
        client: Reference to the client that raised the exception
    """

    def __init__(
        self,
        code: str,
        message: str,
        client,
        explanation: Optional[str] = None,
        fix: Optional[str] = None,
        raw_response: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.explanation = explanation
        self.fix = fix
        self.raw_response = raw_response
        self.client = client

        self.client.log(
            "API.ERROR",
            f"API Error {self.code}: {self.message}",
            "DEBUG",
            {
                "code": self.code,
                "explanation": self.explanation,
                "fix": self.fix,
                "has_raw_response": bool(self.raw_response)
            }
        )

        # Create the string representation
        super().__init__(str(self))

    def __str__(self) -> str:
        """String representation of the exception with all available information"""
        parts = []
        parts.append(f"Error {self.code}: {self.message}")

        if self.explanation:
            parts.append(f"Explanation: {self.explanation}")

        if self.fix:
            parts.append(f"Fix: {self.fix}")

        # Include raw response if client debug mode is on
        if self.client.debug and self.raw_response:
            parts.append("\nRaw API response:")
            parts.append(
                self.raw_response[:1000] + ("..." if len(self.raw_response) > 1000 else ""))

        return "\n".join(parts)

    def print_guidance(self) -> None:
        """Print helpful guidance for specific error types"""
        if "IP is not in the whitelist" in self.message:
            self.client.log(
                "API.WHITELIST",
                "IP whitelist error detected",
                "INFO",
                {
                    "Instructions": (
                        "Please whitelist your IP in your Namecheap API settings:\n"
                        "1. Log in to Namecheap\n"
                        "2. Go to Profile > Tools\n"
                        "3. Find 'Namecheap API Access' under Business & Dev Tools\n"
                        "4. Add this IP to the Whitelisted IPs list\n"
                        "5. Update your .env file with this IP"
                    )
                }
            )


def format_error_with_context(message: str, context: Dict[str, Any]) -> str:
    """
    Format an error message by replacing placeholders with context variables.

    Args:
        message: The message with placeholders in the format {variable_name}
        context: Dictionary of context variables to substitute

    Returns:
        Formatted message with placeholders replaced by context values
    """
    if not message or not context:
        return message

    # Replace placeholders in the message with context values
    for key, value in context.items():
        placeholder = f"{{{key}}}"
        if placeholder in message:
            message = message.replace(placeholder, str(value))

    return message


# Type for error code mappings used by modules
ErrorCodeMapping = Dict[str, Dict[str, str]]
