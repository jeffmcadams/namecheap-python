"""
Enhanced domain operations
"""
from typing import Any, Dict, List, Optional, Set
import tldextract


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
        domain_results = self.client.domains.check(domains)

        # Extract unique TLDs from available domains
        tlds = set()
        available_domains = []

        for domain_info in domain_results:
            if isinstance(domain_info, dict) and domain_info.get("Available", False):
                domain = domain_info.get("Domain", "")
                available_domains.append(domain)
                extract = tldextract.extract(domain)
                tld = f".{extract.suffix}"
                tlds.add(tld)

        # Get pricing info for TLDs of available domains
        pricing_info = self._get_tld_pricing(tlds)

        # Build the final result
        result = {"DomainCheckResult": []}
        for domain_info in domain_results:
            if not isinstance(domain_info, dict):
                continue

            domain = domain_info.get("Domain", "")
            is_available = domain_info.get("Available", False)
            is_premium = domain_info.get("IsPremiumName", False)

            enhanced_info = {
                "Domain": domain,
                "Available": is_available,
                "IsPremiumName": is_premium,
                "Price": 0.0  # Default price
            }

            # Update price if domain is available
            if is_available and "." in domain:
                enhanced_info["Price"] = self._determine_domain_price(
                    domain, domain_info, pricing_info
                )

            result["DomainCheckResult"].append(enhanced_info)

        return result

    def _get_tld_pricing(self, tlds: Set[str]) -> Dict[str, float]:
        """
        Get pricing information for a set of TLDs

        Args:
            tlds: Set of TLDs to get pricing for

        Returns:
            Dictionary mapping TLDs to their prices
        """
        pricing_info = {}
        for tld in tlds:
            try:
                # Remove the dot for the API call
                tld_name = tld[1:] if tld.startswith(".") else tld

                price_response = self.client.users.get_pricing(
                    product_type="DOMAIN",
                    action_name="REGISTER",
                    product_name=tld_name,
                    product_category="REGISTER"
                )

                price = self._extract_price_from_response(
                    price_response, tld_name)
                if price > 0:
                    pricing_info[tld] = price
                    self.client.log(
                        "PRICING.INFO",
                        f"Found price for {tld}: ${price}",
                        "DEBUG"
                    )
            except Exception as e:
                self.client.log(
                    "PRICING.ERROR",
                    f"Error getting pricing for {tld}",
                    "ERROR",
                    {"Error": str(e)}
                )

        return pricing_info

    def _extract_price_from_response(self, response: Dict[str, Any], tld_name: str) -> float:
        """
        Extract 1-year registration price from pricing API response

        Args:
            response: API response dictionary
            tld_name: TLD name without leading dot

        Returns:
            Price as float, or 0.0 if not found
        """
        if "UserGetPricingResult" not in response:
            return 0.0

        result = response["UserGetPricingResult"]

        # Log the raw result for debugging
        self.client.log(
            "PRICING.DEBUG",
            f"Raw pricing data for {tld_name}: {result}",
            "DEBUG"
        )

        if "ProductType" not in result:
            return 0.0

        product_type = result["ProductType"]
        if not isinstance(product_type, dict) or "ProductCategory" not in product_type:
            return 0.0

        # Get the REGISTER product category
        product_category = product_type["ProductCategory"]
        register_category = None

        if isinstance(product_category, list):
            for category in product_category:
                if isinstance(category, dict) and category.get("@Name", "").upper() == "REGISTER":
                    register_category = category
                    break
        elif isinstance(product_category, dict) and product_category.get("@Name", "").upper() == "REGISTER":
            register_category = product_category

        if not register_category or "Product" not in register_category:
            return 0.0

        # Find the product for our TLD
        product = register_category["Product"]
        tld_product = None

        if isinstance(product, list):
            for prod in product:
                if isinstance(prod, dict) and prod.get("@Name", "").lower() == tld_name.lower():
                    tld_product = prod
                    break
        elif isinstance(product, dict) and product.get("@Name", "").lower() == tld_name.lower():
            tld_product = product

        if not tld_product or "Price" not in tld_product:
            return 0.0

        # Get the 1-year price
        prices = tld_product["Price"]
        if not isinstance(prices, list):
            prices = [prices]

        for price_data in prices:
            if (price_data.get("@Duration") == "1" and
                    price_data.get("@DurationType", "").upper() == "YEAR"):
                try:
                    # Find price attribute regardless of capitalization
                    price_value_attr = None
                    for attr in price_data:
                        if attr.lstrip('@').lower() == "price":
                            price_value_attr = attr
                            break

                    if price_value_attr:
                        return float(price_data[price_value_attr])
                except (ValueError, TypeError):
                    pass

        return 0.0

    def _determine_domain_price(self, domain: str, domain_info: Dict[str, Any],
                                pricing_info: Dict[str, float]) -> float:
        """
        Determine the price for a domain

        Args:
            domain: Domain name
            domain_info: Domain availability info
            pricing_info: TLD pricing information

        Returns:
            Price as float
        """
        extract = tldextract.extract(domain)
        tld = f".{extract.suffix}"
        regular_price = pricing_info.get(tld, 0.0)
        premium_price = 0.0

        # Handle premium price if available
        if "PremiumRegistrationPrice" in domain_info:
            try:
                premium_price = float(domain_info.get(
                    "PremiumRegistrationPrice", "0.0"))
            except (ValueError, TypeError):
                premium_price = 0.0

        # Log the prices for debugging
        self.client.log(
            "PRICING.DEBUG",
            f"Domain: {domain}, Regular: ${regular_price}, Premium: ${premium_price}, IsPremium: {domain_info.get('IsPremiumName', False)}",
            "DEBUG"
        )

        # Determine final price
        if domain_info.get("IsPremiumName", False) and premium_price > 0:
            return premium_price
        elif regular_price > 0:
            return regular_price
        else:
            self.client.log(
                "PRICING.WARNING",
                f"No price found for {domain} with TLD {tld}",
                "WARNING"
            )
            return 0.0

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
