"""
Exceptions for the Namecheap API client
"""


class NamecheapException(Exception):
    """Exception raised for Namecheap API errors"""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        self.current_ip = None
        self.is_whitelist_error = "IP is not in the whitelist" in message

        # Build the base error message
        base_message = f"Namecheap API Error {code}: {message}"

        # For whitelist errors, get the current IP and enhance the message
        if self.is_whitelist_error:
            # Import here to avoid circular imports
            from .utils import get_public_ip

            self.current_ip = get_public_ip()
            if self.current_ip:
                base_message += f"\n\nYour current IP ({self.current_ip}) is not whitelisted. Please add it at:"
                base_message += (
                    "\nhttps://ap.www.namecheap.com/settings/tools/apiaccess/"
                )

        super().__init__(base_message)

    def print_guidance(self) -> None:
        """Print helpful guidance for specific error types"""
        if self.is_whitelist_error and self.current_ip:
            print(f"Your current public IP address is: {self.current_ip}")
            print("\nPlease whitelist this IP in your Namecheap API settings:")
            print("1. Log in to Namecheap")
            print("2. Go to Profile > Tools")
            print("3. Find 'Namecheap API Access' under Business & Dev Tools")
            print("4. Add this IP to the Whitelisted IPs list")
            print("5. Update your .env file with this IP")
