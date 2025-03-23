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

        # Extract unique TLDs from domains
        tlds = set()
        for domain in domains:
            tld = "." + domain.split(".", 1)[1]
            tlds.add(tld)

        # Get pricing info for all TLDs
        pricing_result = self.client.users.get_pricing(
            product_type="DOMAIN",
            product_category="REGISTER",
            product_name=list(tlds)
        )

        # Prepare products pricing lookup
        tld_pricing = {}
        if "ProductPricing" in pricing_result:
            products = pricing_result["ProductPricing"]
            if not isinstance(products, list):
                products = [products]

            for product in products:
                if isinstance(product, dict) and "ProductName" in product and "Price" in product:
                    tld = product["ProductName"]
                    price = product.get("Price", 0)
                    if isinstance(price, str):
                        try:
                            price = float(price)
                        except ValueError:
                            price = 0
                    tld_pricing[tld] = price

        # Combine the results
        result = {"DomainCheckResult": []}

        domain_results = availability_result.get("DomainCheckResult", [])
        if not isinstance(domain_results, list):
            domain_results = [domain_results]

        for domain_info in domain_results:
            if not isinstance(domain_info, dict):
                continue

            domain = domain_info.get("Domain", "")
            tld = "." + domain.split(".", 1)[1] if "." in domain else ""

            # Get pricing for this TLD
            regular_price = tld_pricing.get(tld, 0.0)

            # Use premium price if it's a premium domain, otherwise use regular price
            is_premium = domain_info.get("IsPremiumName", False)
            premium_price = domain_info.get("PremiumRegistrationPrice", 0.0)

            if is_premium and premium_price > 0:
                final_price = premium_price
            else:
                final_price = regular_price

            # Create enhanced result
            enhanced_info = {
                "Domain": domain,
                "Available": domain_info.get("Available", False),
                "IsPremiumName": is_premium,
                "Price": final_price
            }

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
