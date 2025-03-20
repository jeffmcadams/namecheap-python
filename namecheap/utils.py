"""
Utility functions to help set up and use the Namecheap API client
"""

import os

# Import client and exceptions only when needed to avoid circular imports
from typing import TYPE_CHECKING, Any, Dict, Optional

import requests
from dotenv import find_dotenv, load_dotenv

if TYPE_CHECKING:
    from .client import NamecheapClient


def get_public_ip() -> Optional[str]:
    """
    Determine the current public IP address by querying multiple services

    Returns:
        Optional[str]: The public IP address or None if it couldn't be determined
    """
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://ident.me",
    ]

    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except Exception:
            continue

    return None


def setup_interactive() -> None:
    """
    Interactive setup wizard to configure Namecheap API credentials

    This function guides the user through setting up their .env file
    with the required Namecheap API credentials
    """
    env_path = find_dotenv()
    if not env_path:
        env_path = os.path.join(os.getcwd(), ".env")
        if not os.path.exists(env_path):
            with open(env_path, "w") as f:
                f.write("# Namecheap API Credentials\n")

    print("Namecheap API Setup Wizard")
    print("==========================")
    print("This wizard will help you set up your Namecheap API credentials.\n")
    print("You need the following information from your Namecheap account:")
    print("1. Your Namecheap username")
    print("2. Your API key from Profile > Tools > API Access")
    print("3. Your whitelisted IP address\n")

    # Get current IP
    current_ip = get_public_ip()
    if current_ip:
        print(f"Your current public IP address appears to be: {current_ip}")
        print(
            "Make sure this IP is whitelisted in your Namecheap API Access settings.\n"
        )

    # Load existing values if any
    load_dotenv()
    existing_user = os.environ.get("NAMECHEAP_API_USER", "")
    existing_key = os.environ.get("NAMECHEAP_API_KEY", "")
    # Note: We're not using this, but keeping for future use
    # existing_username = os.environ.get("NAMECHEAP_USERNAME", existing_user)
    existing_ip = os.environ.get("NAMECHEAP_CLIENT_IP", current_ip or "")
    existing_sandbox = os.environ.get("NAMECHEAP_USE_SANDBOX", "True")

    # Ask for values
    username = (
        input(f"Enter your Namecheap username [{existing_user}]: ") or existing_user
    )
    api_key = (
        input(
            f"Enter your API Key [{existing_key[:5] + '*****' if existing_key else ''}]: "
        )
        or existing_key
    )
    client_ip = (
        input(f"Enter your whitelisted IP address [{existing_ip}]: ") or existing_ip
    )

    use_sandbox = input(
        f"Use sandbox environment for testing? (y/n) [{existing_sandbox.lower() == 'true' and 'y' or 'n'}]: "
    )
    sandbox = "True" if use_sandbox.lower() in ("", "y", "yes") else "False"

    # Write to .env file
    with open(env_path, "w") as f:
        f.write("# Namecheap API Credentials\n")
        f.write(f"NAMECHEAP_API_USER={username}\n")
        f.write(f"NAMECHEAP_API_KEY={api_key}\n")
        f.write(f"NAMECHEAP_USERNAME={username}\n")
        f.write(f"NAMECHEAP_CLIENT_IP={client_ip}\n")
        f.write(f"NAMECHEAP_USE_SANDBOX={sandbox}\n")

    print("\nCredentials saved to .env file.")

    # Offer to test the connection
    test_now = input("\nWould you like to test the API connection now? (y/n): ")
    if test_now.lower() in ("y", "yes"):
        success = test_api_connection()
        if success:
            print("\n✅ API connection successful! You're all set.")
        else:
            print(
                "\n❌ API connection failed. Please check your credentials and try again."
            )
    else:
        print("\nYou can test your connection later with:")
        print("  from namecheap.utils import test_api_connection")
        print("  test_api_connection()")


def get_credentials() -> Dict[str, Any]:
    """
    Load Namecheap API credentials from environment variables or .env file

    Returns:
        Dict[str, Any]: Dictionary with credentials

    Raises:
        ValueError: If any required credentials are missing
    """
    load_dotenv()

    # Get required variables
    api_user = os.environ.get("NAMECHEAP_API_USER")
    api_key = os.environ.get("NAMECHEAP_API_KEY")
    username = os.environ.get("NAMECHEAP_USERNAME", api_user)
    client_ip = os.environ.get("NAMECHEAP_CLIENT_IP")

    # Check if sandbox mode is enabled
    sandbox_env = os.environ.get("NAMECHEAP_USE_SANDBOX", "True")
    sandbox = sandbox_env.lower() in ("true", "yes", "1")

    # Check for missing credentials
    missing = []
    if not api_user:
        missing.append("NAMECHEAP_API_USER")
    if not api_key:
        missing.append("NAMECHEAP_API_KEY")
    if not username:
        missing.append("NAMECHEAP_USERNAME")
    if not client_ip:
        missing.append("NAMECHEAP_CLIENT_IP")

    if missing:
        raise ValueError(f"Missing required credentials: {', '.join(missing)}")

    return {
        "api_user": api_user,
        "api_key": api_key,
        "username": username,
        "client_ip": client_ip,
        "sandbox": sandbox,
    }


def create_client_from_env(debug: bool = False) -> "NamecheapClient":
    """
    Create a NamecheapClient instance using credentials from environment variables

    Args:
        debug: Whether to enable debug logging (default: False)

    Returns:
        NamecheapClient: Initialized client

    Raises:
        ValueError: If any required credentials are missing
    """
    # Import here to avoid circular imports
    from .client import NamecheapClient

    creds = get_credentials()

    return NamecheapClient(
        api_user=creds["api_user"],
        api_key=creds["api_key"],
        username=creds["username"],
        client_ip=creds["client_ip"],
        sandbox=creds["sandbox"],
        debug=debug,
    )


def test_api_connection(client: Optional["NamecheapClient"] = None) -> bool:
    """
    Test connection to the Namecheap API by performing some read-only operations

    Args:
        client: Optional client instance. If not provided, one will be created from environment

    Returns:
        bool: True if all tests passed, False otherwise
    """
    # Import here to avoid circular imports
    from .client import NamecheapClient

    try:
        if client is None:
            try:
                creds = get_credentials()
                client = NamecheapClient(
                    api_user=creds["api_user"],
                    api_key=creds["api_key"],
                    username=creds["username"],
                    client_ip=creds["client_ip"],
                    sandbox=creds["sandbox"],
                    debug=True,  # Enable debug for testing
                )
            except ValueError as e:
                print(f"Error: {e}")
                print("Please run setup_interactive() to configure your credentials.")
                return False

        # Define tests to run
        tests = [
            ("Domain Availability Check", _test_domains_check),
            ("TLD List", _test_tld_list),
        ]

        print(
            f"Testing Namecheap API connection (sandbox={client.base_url == client.SANDBOX_API_URL})"
        )
        print("-" * 50)

        # Run tests
        passed = 0
        for name, test_func in tests:
            print(f"\nRunning test: {name}")
            try:
                if test_func(client):
                    print(f"✅ {name} - Success")
                    passed += 1
                else:
                    print(f"❌ {name} - Failed")
            except Exception as e:
                print(f"❌ {name} - Error: {e}")

        # Print summary
        print("\n" + "-" * 50)
        print(f"Test Summary: {passed}/{len(tests)} tests passed")

        return passed == len(tests)

    except Exception as e:
        print(f"Error testing API connection: {e}")
        return False


def _test_domains_check(client: "NamecheapClient") -> bool:
    """Test domain availability check API call"""
    try:
        print("Testing domain availability check...")
        # Use domains that are very unlikely to be registered
        domains = ["example123456789.com", "randomdomain987654.org"]
        result = client.domains_check(domains)

        # Validate response format
        domain_results = result.get("DomainCheckResult", [])
        if not isinstance(domain_results, list):
            domain_results = [domain_results]

        print("Domain check results:")
        for domain in domain_results:
            name = domain.get("Domain", "")
            available = "Yes" if domain.get("Available") else "No"
            print(f"  {name}: {available}")

        return True
    except Exception as e:
        # Import here to handle circular imports
        from .exceptions import NamecheapException

        if isinstance(e, NamecheapException):
            print(f"API Error ({e.code}): {e.message}")

            # Provide helpful guidance for common error codes
            if (
                "API Key is invalid" in e.message
                or "API access has not been enabled" in e.message
            ):
                print("\nTROUBLESHOOTING TIPS:")
                print("1. Verify your API key is correct in your .env file")
                print(
                    "2. Ensure API access is enabled at: https://ap.www.namecheap.com/settings/tools/apiaccess/"
                )
                print(
                    "3. Make sure your IP address is whitelisted in the Namecheap API settings"
                )
                print("4. Check that your username (Namecheap account name) is correct")
                print("\nRun 'python setup-api.py' to reconfigure your API settings.")
            elif "IP is not in the whitelist" in e.message:
                # Use the print_guidance method for consistent messaging
                e.print_guidance()
        else:
            print(f"Error: {e}")

        return False


def _test_tld_list(client: "NamecheapClient") -> bool:
    """Test getting TLD list from API"""
    try:
        print("Getting available TLD list...")
        result = client.domains_get_tld_list()

        # Validate response format
        tlds = result.get("Tlds", {}).get("Tld", [])
        if not isinstance(tlds, list):
            tlds = [tlds]

        print(f"Found {len(tlds)} TLDs")
        # Print a sample of TLDs
        print("Sample TLDs:")
        for tld in tlds[:5]:
            print(f"  {tld}")

        return True
    except Exception as e:
        # Import here to handle circular imports
        from .exceptions import NamecheapException

        if isinstance(e, NamecheapException):
            print(f"API Error ({e.code}): {e.message}")

            # Provide helpful guidance for common error codes
            if (
                "API Key is invalid" in e.message
                or "API access has not been enabled" in e.message
            ):
                print("\nTROUBLESHOOTING TIPS:")
                print("1. Verify your API key is correct in your .env file")
                print(
                    "2. Ensure API access is enabled at: https://ap.www.namecheap.com/settings/tools/apiaccess/"
                )
                print(
                    "3. Make sure your IP address is whitelisted in the Namecheap API settings"
                )
                print("4. Check that your username (Namecheap account name) is correct")
                print("\nRun 'python setup-api.py' to reconfigure your API settings.")
            elif "IP is not in the whitelist" in e.message:
                # Use the print_guidance method for consistent messaging
                e.print_guidance()
        else:
            print(f"Error: {e}")

        return False
