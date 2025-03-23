"""
Users API operations
"""
from typing import Any, Dict, List, Optional

# Common error codes shared across user operations
COMMON_USER_ERRORS = {
    "2019103": {
        "explanation": "Username not found",
        "fix": "Verify the username exists and is spelled correctly"
    },
    "2017166": {
        "explanation": "User is disabled or locked",
        "fix": "Contact Namecheap support to resolve account access issues"
    },
    "2010335": {
        "explanation": "Invalid password",
        "fix": "Check that the password is correct"
    },
    "UNKNOWN_ERROR": {
        "explanation": "User operation failed",
        "fix": "Verify all parameters are correct and try again"
    }
}


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

        API Documentation: https://www.namecheap.com/support/api/methods/users/get-pricing/

        Error Codes:
            2011170: PromotionCode is invalid
            2011298: ProductType is invalid

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
        # Error codes for getting pricing
        error_codes = {
            **COMMON_USER_ERRORS,
            "2011170": {
                "explanation": "PromotionCode is invalid",
                "fix": "Verify the promotion code is valid and not expired"
            },
            "2011298": {
                "explanation": "ProductType is invalid",
                "fix": "Use one of the supported product types: DOMAIN, SSLCERTIFICATE, WHOISGUARD"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get pricing information",
                "fix": "Verify that all parameters are valid and try again"
            }
        }

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

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.users.getPricing",
            params,
            error_codes,
            {"product_type": product_type}
        )

    def get_balances(self) -> Dict[str, Any]:
        """
        Get account balances

        API Documentation: https://www.namecheap.com/support/api/methods/users/get-balances/

        Error Codes:
            4022312: Balance information is not available

        Returns:
            Dictionary with account balance information

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for getting balances
        error_codes = {
            **COMMON_USER_ERRORS,
            "4022312": {
                "explanation": "Balance information is not available",
                "fix": "Try again later or contact Namecheap support"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get account balances",
                "fix": "Verify that your account is in good standing and try again"
            }
        }

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.users.getBalances",
            {},
            error_codes,
            {}
        )

    def change_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change account password

        API Documentation: https://www.namecheap.com/support/api/methods/users/change-password/

        Error Codes:
            2010302: OldPassword is missing
            4022335: Unable to change password
            5050900: Unhandled exceptions

        Args:
            old_password: Current password
            new_password: New password

        Returns:
            Dictionary with password change result

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for changing password
        error_codes = {
            **COMMON_USER_ERRORS,
            "2010302": {
                "explanation": "OldPassword is missing",
                "fix": "Provide the current password"
            },
            "4022335": {
                "explanation": "Unable to change password",
                "fix": "Ensure the old password is correct and the new password meets requirements"
            },
            "5050900": {
                "explanation": "Unhandled exception occurred",
                "fix": "Try again later or contact Namecheap support"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to change password",
                "fix": "Verify both passwords are correct and try again"
            }
        }

        params = {
            "OldPassword": old_password,
            "NewPassword": new_password
        }

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.users.changePassword",
            params,
            error_codes,
            {}
        )
