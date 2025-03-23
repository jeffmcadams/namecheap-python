"""
Enhanced domain operations
"""
from typing import Dict, List, Optional, Set, TYPE_CHECKING, TypedDict, Union

import tldextract

from ..base import JsonValue, ResponseDict, ResponseItem, ResponseList

# Import needed for type hints
if TYPE_CHECKING:
    from ..client import NamecheapClient


class DomainCheckInfo(TypedDict, total=False):
    """Type for domain check information"""
    Domain: str
    Available: bool
    IsPremiumName: bool
    Price: float
    PremiumRegistrationPrice: str


class DomainCheckResult(TypedDict):
    """Type for domain check result"""
    DomainCheckResult: List[DomainCheckInfo]


class AvailableDomainsResult(TypedDict):
    """Type for available domains result"""
    AvailableDomains: List[DomainCheckInfo]


class EnhancedDomainsAPI:
    """
    Enhanced domain operations that combine multiple API calls
    """

    def __init__(self, client: "NamecheapClient") -> None:
        """
        Initialize enhanced domain operations

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def check_with_pricing(self, domains: List[str]) -> DomainCheckResult:
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
        # Import utility functions
        from ..utils import ensure_list
        
        # Get basic availability info
        domain_results = self.client.domains.check(domains)
        
        # Ensure domain_results is a list
        domain_results_list = ensure_list(domain_results)

        # Extract unique TLDs from available domains
        tlds = set()
        available_domains = []

        for domain_info in domain_results_list:
            if isinstance(domain_info, dict) and domain_info.get("Available", False):
                domain = domain_info.get("Domain", "")
                if isinstance(domain, str) and domain:
                    available_domains.append(domain)
                    extract = tldextract.extract(domain)
                    tld = f".{extract.suffix}"
                    tlds.add(tld)

        # Get pricing info for TLDs of available domains
        pricing_info = self._get_tld_pricing(tlds)

        # Build the final result
        domain_check_results: List[DomainCheckInfo] = []
        result: DomainCheckResult = {"DomainCheckResult": domain_check_results}
        
        for domain_info in domain_results_list:
            if not isinstance(domain_info, dict):
                continue

            domain = domain_info.get("Domain", "")
            if not isinstance(domain, str):
                continue
                
            is_available = domain_info.get("Available", False)
            is_premium = domain_info.get("IsPremiumName", False)

            enhanced_info: DomainCheckInfo = {
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

            domain_check_results.append(enhanced_info)

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
                    product_name=[tld_name],  # Wrap in a list as required by the API
                    product_category="REGISTER"
                )

                # Convert from nested type to Dict[str, object]
                price_dict: Dict[str, object] = {}
                if isinstance(price_response, dict):
                    # Use a copy to avoid type issues
                    for key, value in price_response.items():
                        price_dict[key] = value
                # Then extract price
                price = self._extract_price_from_response(price_dict, tld_name)
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

    def _extract_price_from_response(self, response: Dict[str, object], tld_name: str) -> float:
        """
        Extract 1-year registration price from pricing API response

        Args:
            response: API response dictionary
            tld_name: TLD name without leading dot

        Returns:
            Price as float, or 0.0 if not found
        """
        # Import utility functions
        from ..utils import ensure_list
        
        # Get the pricing result safely
        result = response.get("UserGetPricingResult")
        if not result:
            return 0.0

        # Log the raw result for debugging
        self.client.log(
            "PRICING.DEBUG",
            f"Raw pricing data for {tld_name}: {result}",
            "DEBUG"
        )

        # Safely check for ProductType
        if not isinstance(result, dict):
            return 0.0
            
        product_type = result.get("ProductType")
        if not product_type or not isinstance(product_type, dict):
            return 0.0
            
        # Check for ProductCategory
        product_category = product_type.get("ProductCategory")
        if not product_category:
            return 0.0

        # Find register category
        register_category = None
        
        if isinstance(product_category, list):
            # It's a list, search for the REGISTER category
            for category in product_category:
                if isinstance(category, dict) and category.get("@Name", "").upper() == "REGISTER":
                    register_category = category
                    break
        elif isinstance(product_category, dict) and product_category.get("@Name", "").upper() == "REGISTER":
            # It's already the REGISTER category
            register_category = product_category

        if not register_category:
            return 0.0
            
        # Get the Product safely
        product = register_category.get("Product")
        if not product:
            return 0.0
            
        # Find the product for our TLD
        tld_product = None
        product_list = ensure_list(product)
        
        for prod in product_list:
            if isinstance(prod, dict) and prod.get("@Name", "").lower() == tld_name.lower():
                tld_product = prod
                break

        if not tld_product:
            return 0.0
            
        # Get prices safely
        prices = tld_product.get("Price")
        if not prices:
            return 0.0
            
        # Ensure prices is a list
        price_list = ensure_list(prices)

        for price_data in price_list:
            if not isinstance(price_data, dict):
                continue
                
            # Check for 1-year duration
            if (price_data.get("@Duration") == "1" and
                    price_data.get("@DurationType", "").upper() == "YEAR"):
                try:
                    # Find price attribute regardless of capitalization
                    price_value_attr = None
                    for attr in price_data:
                        if isinstance(attr, str) and attr.lstrip('@').lower() == "price":
                            price_value_attr = attr
                            break

                    if price_value_attr:
                        return float(price_data[price_value_attr])
                except (ValueError, TypeError):
                    pass

        return 0.0

    def _determine_domain_price(self, domain: str, domain_info: Dict[str, Union[str, bool, float]],
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
    ) -> AvailableDomainsResult:
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
        available_domains: List[DomainCheckInfo] = []
        for domain in results.get("DomainCheckResult", []):
            if domain.get("Available", False):
                if not domain.get("IsPremiumName", False) or include_premium:
                    available_domains.append(domain)

        return {"AvailableDomains": available_domains}

    def bulk_check(self, keywords: List[str], tlds: List[str]) -> Dict[str, bool]:
        """
        Check availability for multiple domain combinations

        Args:
            keywords: List of keywords/names to check
            tlds: List of TLDs to check for each keyword

        Returns:
            Dictionary mapping domain names to their availability status
            (e.g., {"example.com": True, "example.net": False})

        Raises:
            ValueError: If too many domains would be checked at once
            NamecheapException: If the API returns an error
        """
        # Validate inputs
        if not keywords or not isinstance(keywords, list):
            raise ValueError("Keywords must be a non-empty list")
        if not tlds or not isinstance(tlds, list):
            raise ValueError("TLDs must be a non-empty list")

        # Calculate total number of domains to check
        total_domains = len(keywords) * len(tlds)
        if total_domains > 50:
            raise ValueError(
                f"Maximum of 50 domains can be checked at once, but you're trying to check {total_domains} domains")

        # Generate all domain combinations
        domains = []
        for keyword in keywords:
            for tld in tlds:
                # Handle if the TLD already includes a dot or not
                if isinstance(tld, str) and tld.startswith("."):
                    domains.append(f"{keyword}{tld}")
                else:
                    domains.append(f"{keyword}.{tld}")

        # Use the API to check availability
        result: Dict[str, bool] = {}
        api_result = self.client.domains.check(domains)

        # Use our client's normalize_api_response to get a properly typed result
        domain_check_results: List[Dict[str, object]] = []
        if isinstance(api_result, dict):
            domain_check_results = self.client.normalize_api_response(
                api_result,
                result_key="DomainCheckResult",
                return_type="list"
            )

        # Process the results into a simpler format
        for domain_data in domain_check_results:
            if not isinstance(domain_data, dict):
                continue
                
            domain = domain_data.get("Domain", "")
            if not isinstance(domain, str):
                continue
                
            available = domain_data.get("Available", False)
            
            # Convert to boolean regardless of original type
            if isinstance(available, bool):
                is_available = available
            elif isinstance(available, str):
                is_available = available.lower() in ("true", "yes", "1")
            else:
                is_available = bool(available)
                
            result[domain] = is_available

        return result
