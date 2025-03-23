"""
Enhanced domain operations
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Set, TypedDict, Union

import tldextract

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
        # Get basic availability info
        domain_results = self.client.domains.check(domains)

        # Ensure domain_results is a list
        domain_results_list = self.client.ensure_list(domain_results)

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
                "Price": 0.0,  # Default price
            }

            # Update price if domain is available
            if is_available and "." in domain:
                enhanced_info["Price"] = self._determine_domain_price(
                    domain, domain_info, pricing_info
                )

            domain_check_results.append(enhanced_info)

        # Create the result with the updated domain_check_results
        result: DomainCheckResult = {"DomainCheckResult": domain_check_results}
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

                # Call the API with parameters according to the documentation
                # Only supply the minimum required parameters as per the API documentation
                price_response = self.client.users.get_pricing(
                    product_type="DOMAIN",
                    action_name="REGISTER",
                    product_name=tld_name,
                )

                # Log the pricing response basic info for debugging
                self.client.log(
                    "PRICING.DEBUG", f"Received pricing response for {tld_name}", "DEBUG",
                    {"ResponseKeys": str(list(price_response.keys()))}
                )
                
                # Get price directly from the parsed XML response using XML path
                try:
                    # Use the extract_value method to navigate the XML structure
                    product_type = self.client.extract_value(
                        price_response,
                        "UserGetPricingResult.ProductType", 
                        {}, 
                        log_context=f"pricing response for {tld_name}"
                    )
                    
                    if not isinstance(product_type, dict):
                        self.client.log(
                            "PRICING.WARNING", 
                            f"Invalid ProductType data for {tld_name}", 
                            "WARNING"
                        )
                        continue
                    
                    # First try to find a matching product in the REGISTER category
                    found_price = False
                    
                    # Get all product categories
                    categories = self.client.ensure_list(
                        self.client.extract_value(product_type, "ProductCategory", [])
                    )
                    
                    for category in categories:
                        if not isinstance(category, dict):
                            continue
                            
                        category_name = self.client.extract_value(category, "@Name", "")
                        
                        # Check if this is the REGISTER category
                        if category_name.upper() == "REGISTER":
                            # Get products in this category
                            products = self.client.ensure_list(
                                self.client.extract_value(category, "Product", [])
                            )
                            
                            # Find the product matching our TLD
                            for product in products:
                                if not isinstance(product, dict):
                                    continue
                                    
                                product_name = self.client.extract_value(product, "@Name", "")
                                
                                # Check if this product matches our TLD
                                if product_name.lower() == tld_name.lower():
                                    # Get prices for this product
                                    prices = self.client.ensure_list(
                                        self.client.extract_value(product, "Price", [])
                                    )
                                    
                                    # Look for 1-year registration price
                                    for price_obj in prices:
                                        if not isinstance(price_obj, dict):
                                            continue
                                            
                                        duration = self.client.extract_value(price_obj, "@Duration", "")
                                        duration_type = self.client.extract_value(price_obj, "@DurationType", "")
                                        
                                        if duration == "1" and duration_type.upper() == "YEAR":
                                            # Try each price field in order of priority
                                            price_value = 0.0
                                            
                                            # First try YourPrice (personalized price)
                                            price_value = self.client.extract_value(
                                                price_obj, "@YourPrice", 0.0, float
                                            )
                                            
                                            # If not found, try regular Price field
                                            if price_value == 0.0:
                                                price_value = self.client.extract_value(
                                                    price_obj, "@Price", 0.0, float
                                                )
                                            
                                            # If not found, try RegularPrice
                                            if price_value == 0.0:
                                                price_value = self.client.extract_value(
                                                    price_obj, "@RegularPrice", 0.0, float
                                                )
                                            
                                            # If we found a price, use it
                                            if price_value > 0.0:
                                                pricing_info[tld] = price_value
                                                self.client.log(
                                                    "PRICING.INFO", 
                                                    f"Found price for {tld}: ${price_value}", 
                                                    "INFO"
                                                )
                                                found_price = True
                                                break
                                    
                                    # If we found a price, stop looking for more products
                                    if found_price:
                                        break
                        
                        # If we found a price, stop looking through categories
                        if found_price:
                            break
                    
                    # If we still didn't find a price, try any category with a matching product
                    if not found_price:
                        for category in categories:
                            if not isinstance(category, dict):
                                continue
                                
                            products = self.client.ensure_list(
                                self.client.extract_value(category, "Product", [])
                            )
                            
                            for product in products:
                                if not isinstance(product, dict):
                                    continue
                                    
                                product_name = self.client.extract_value(product, "@Name", "")
                                
                                if product_name.lower() == tld_name.lower():
                                    prices = self.client.ensure_list(
                                        self.client.extract_value(product, "Price", [])
                                    )
                                    
                                    for price_obj in prices:
                                        if not isinstance(price_obj, dict):
                                            continue
                                            
                                        # Try each price field in order of priority
                                        price_value = 0.0
                                        
                                        # First try YourPrice (personalized price)
                                        price_value = self.client.extract_value(
                                            price_obj, "@YourPrice", 0.0, float
                                        )
                                        
                                        # If not found, try regular Price field
                                        if price_value == 0.0:
                                            price_value = self.client.extract_value(
                                                price_obj, "@Price", 0.0, float
                                            )
                                        
                                        # If not found, try RegularPrice
                                        if price_value == 0.0:
                                            price_value = self.client.extract_value(
                                                price_obj, "@RegularPrice", 0.0, float
                                            )
                                        
                                        # If we found a price, use it
                                        if price_value > 0.0:
                                            pricing_info[tld] = price_value
                                            category_name = self.client.extract_value(category, "@Name", "UNKNOWN")
                                            self.client.log(
                                                "PRICING.INFO", 
                                                f"Found fallback price for {tld} in category {category_name}: ${price_value}", 
                                                "INFO"
                                            )
                                            found_price = True
                                            break
                                    
                                    if found_price:
                                        break
                            
                            if found_price:
                                break
                            
                    if not found_price:
                        self.client.log(
                            "PRICING.WARNING", 
                            f"No pricing data found for {tld_name}", 
                            "WARNING"
                        )
                except Exception as e:
                    self.client.log(
                        "PRICING.ERROR", f"Error parsing price for {tld_name}", "ERROR",
                        {"Error": str(e)}
                    )
            except Exception as e:
                self.client.log(
                    "PRICING.ERROR",
                    f"Error getting pricing for {tld}",
                    "ERROR",
                    {"Error": str(e)},
                )

        return pricing_info


    def _determine_domain_price(
        self,
        domain: str,
        domain_info: Dict[str, Union[str, bool, float]],
        pricing_info: Dict[str, float],
    ) -> float:
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
        is_premium = domain_info.get("IsPremiumName", False)

        # Handle premium price if available
        premium_price_str = domain_info.get("PremiumRegistrationPrice", "0.0")
        if premium_price_str and premium_price_str != "0" and premium_price_str != "0.0":
            try:
                premium_price = float(premium_price_str)
            except (ValueError, TypeError):
                premium_price = 0.0

        # Log the prices for debugging
        self.client.log(
            "PRICING.DEBUG",
            f"Domain: {domain}, Regular: ${regular_price}, Premium: ${premium_price}, IsPremium: {is_premium}",
            "DEBUG",
        )

        # Determine final price
        if is_premium and premium_price > 0:
            self.client.log(
                "PRICING.INFO",
                f"Using premium price for {domain}: ${premium_price}",
                "INFO",
            )
            return premium_price
        elif regular_price > 0:
            self.client.log(
                "PRICING.INFO",
                f"Using regular price for {domain}: ${regular_price}",
                "INFO",
            )
            return regular_price
        else:
            self.client.log(
                "PRICING.WARNING",
                f"No price found for {domain} with TLD {tld}",
                "WARNING",
            )
            return 0.0

    def search_available(
        self,
        keyword: str,
        tlds: Optional[List[str]] = None,
        include_premium: bool = False,
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
                f"Maximum of 50 domains can be checked at once, but you're trying to check {total_domains} domains"
            )

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
                api_result, result_key="DomainCheckResult", return_type="list"
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
