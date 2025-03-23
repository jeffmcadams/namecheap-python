"""
Enhanced domain operations
"""
from typing import Any, Dict, List, Optional, Set


class EnhancedDomainsAPI:
    """
    Enhanced domain operations that combine multiple API calls
    """

    def __init__(self, client):
        """
        Initialize enhanced domain operations

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def check_with_pricing(self, domains: List[str]) -> Dict[str, Any]:
        """
        Check domain availability with comprehensive pricing information

        This combines domains.check and users.getPricing to provide
        pricing information for all domains, not just premium ones.

        Args:
            domains: List of domains to check availability

        Returns:
            Enhanced dictionary with availability and pricing information

        Raises:
            NamecheapException: If the API returns an error
        """
        # Get basic availability info
        availability_result = self.client.domains.check(domains)

        # Extract unique TLDs from domains with available domains
        tlds = set()
        available_domains = []

        # First pass: identify available domains and collect their TLDs
        domain_results = availability_result.get("DomainCheckResult", [])
        if not isinstance(domain_results, list):
            domain_results = [domain_results]

        for domain_info in domain_results:
            if isinstance(domain_info, dict) and domain_info.get("Available", False):
                domain = domain_info.get("Domain", "")
                available_domains.append(domain)
                if "." in domain:
                    tld = "." + domain.split(".", 1)[1]
                    tlds.add(tld)

        # Get pricing info only for TLDs of available domains
        pricing_info = {}
        for tld in tlds:
            try:
                # Remove the dot for the API call
                tld_name = tld[1:] if tld.startswith(".") else tld

                # Get pricing for the TLD using the client's _make_request method
                price_response = self.client._make_request(
                    command="namecheap.users.getPricing",
                    params={
                        "ProductType": "DOMAIN",
                        "ActionName": "REGISTER",
                        "ProductName": tld_name,
                        "ProductCategory": "domains"
                    }
                )

                # Extract pricing data based on the actual response structure
                if "UserGetPricingResult" in price_response:
                    result = price_response["UserGetPricingResult"]

                    # Navigate through the nested structure
                    if "ProductType" in result and isinstance(result["ProductType"], dict):
                        product_type = result["ProductType"]

                        if "ProductCategory" in product_type and isinstance(product_type["ProductCategory"], dict):
                            product_category = product_type["ProductCategory"]

                            if "Product" in product_category and isinstance(product_category["Product"], dict):
                                product = product_category["Product"]

                                if "Price" in product:
                                    prices = product["Price"]
                                    if not isinstance(prices, list):
                                        prices = [prices]

                                    # Find the 1 year price
                                    for price_data in prices:
                                        if (price_data.get("Duration") == "1" and
                                            price_data.get("DurationType") == "YEAR" and
                                                "Price" in price_data):
                                            try:
                                                price_value = float(
                                                    price_data["Price"])
                                                if self.client.debug:
                                                    print(
                                                        f"Found price for {tld}: ${price_value}")
                                                pricing_info[tld] = price_value
                                                break
                                            except (ValueError, TypeError):
                                                pass
            except Exception as e:
                if self.client.debug:
                    print(f"Error getting pricing for {tld}: {str(e)}")

        # Combine the results
        result = {"DomainCheckResult": []}

        # Second pass: build the final result objects
        for domain_info in domain_results:
            if not isinstance(domain_info, dict):
                continue

            domain = domain_info.get("Domain", "")
            is_available = domain_info.get("Available", False)
            is_premium = domain_info.get("IsPremiumName", False)

            # Create enhanced result - always include the Price field
            enhanced_info = {
                "Domain": domain,
                "Available": is_available,
                "IsPremiumName": is_premium,
                "Price": 0.0  # Default price is zero
            }

            # Update price if domain is available
            if is_available:
                tld = "." + domain.split(".", 1)[1] if "." in domain else ""
                regular_price = pricing_info.get(tld, 0.0)
                premium_price = float(domain_info.get(
                    "PremiumRegistrationPrice", 0.0))

                if is_premium and premium_price > 0:
                    enhanced_info["Price"] = premium_price
                else:
                    enhanced_info["Price"] = regular_price

            result["DomainCheckResult"].append(enhanced_info)

        return result

    def search_available(
        self,
        keyword: str,
        tlds: Optional[List[str]] = None,
        include_premium: bool = False
    ) -> Dict[str, Any]:
        """
        Search for available domains based on a keyword

        Args:
            keyword: The keyword to search for
            tlds: List of TLDs to check (default: [.com, .net, .org, .info, .biz])
            include_premium: Whether to include premium domains in results

        Returns:
            Dictionary with available domains and their prices

        Raises:
            NamecheapException: If the API returns an error
        """
        if not tlds:
            tlds = [".com", ".net", ".org", ".info", ".biz"]

        # Generate domains to check
        domains_to_check = [f"{keyword}{tld}" for tld in tlds]

        # Get availability and pricing
        results = self.check_with_pricing(domains_to_check)

        # Filter available domains
        available_domains = []
        for domain in results.get("DomainCheckResult", []):
            if domain.get("Available", False):
                if not domain.get("IsPremiumName", False) or include_premium:
                    available_domains.append(domain)

        return {"AvailableDomains": available_domains}
