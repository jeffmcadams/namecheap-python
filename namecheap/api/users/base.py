"""
Users API operations
"""
from typing import Any, Dict, List, Optional


class UsersAPI:
    """Users API methods"""

    def __init__(self, client):
        """
        Initialize the users API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def get_pricing(
        self,
        product_type: str,
        product_category: Optional[str] = None,
        promotion_code: Optional[str] = None,
        action_name: Optional[str] = None,
        product_name: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get pricing information for Namecheap products

        Args:
            product_type: Type of product (DOMAIN, SSLCERTIFICATE, WHOISGUARD)
            product_category: Product category (REGISTER, RENEW, REACTIVATE, TRANSFER, WHOISGUARD)
            promotion_code: Promotional (coupon) code for the product
            action_name: Name of the action (REGISTER, RENEW, REACTIVATE, TRANSFER, WHOISGUARD)
            product_name: List of product names (e.g., [".com", ".net"] for domains)

        Returns:
            Dictionary with pricing information

        Raises:
            ValueError: If parameters are invalid
            NamecheapException: If the API returns an error
        """
        valid_product_types = ["DOMAIN", "SSLCERTIFICATE", "WHOISGUARD"]
        if product_type not in valid_product_types:
            raise ValueError(
                f"product_type must be one of {valid_product_types}")

        params = {"ProductType": product_type}

        if product_category:
            valid_categories = ["REGISTER", "RENEW",
                                "REACTIVATE", "TRANSFER", "WHOISGUARD"]
            if product_category not in valid_categories:
                raise ValueError(
                    f"product_category must be one of {valid_categories}")
            params["ProductCategory"] = product_category

        if action_name:
            valid_actions = ["REGISTER", "RENEW",
                             "REACTIVATE", "TRANSFER", "WHOISGUARD"]
            if action_name not in valid_actions:
                raise ValueError(f"action_name must be one of {valid_actions}")
            params["ActionName"] = action_name

        if promotion_code:
            params["PromotionCode"] = promotion_code

        if product_name:
            if isinstance(product_name, list):
                params["ProductName"] = ",".join(product_name)
            else:
                params["ProductName"] = product_name

        return self.client._make_request("namecheap.users.getPricing", params)

    def get_balances(self) -> Dict[str, Any]:
        """
        Get account balances

        Returns:
            Dictionary with account balance information

        Raises:
            NamecheapException: If the API returns an error
        """
        return self.client._make_request("namecheap.users.getBalances")

    def change_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change account password

        Args:
            old_password: Current password
            new_password: New password

        Returns:
            Dictionary with password change result

        Raises:
            NamecheapException: If the API returns an error
        """
        params = {
            "OldPassword": old_password,
            "NewPassword": new_password
        }
        return self.client._make_request("namecheap.users.changePassword", params)
