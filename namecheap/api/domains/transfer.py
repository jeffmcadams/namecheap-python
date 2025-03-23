"""
Domain transfer operations for domains API
"""
from typing import Dict, Optional

from ...base import BaseClient, ResponseDict

# Common error codes shared across transfer operations
COMMON_TRANSFER_ERRORS = {
    "2019166": {
        "explanation": "Transfer ID not found",
        "fix": "Verify the transfer ID is correct and exists in your account"
    },
    "2016166": {
        "explanation": "Domain is not associated with your account",
        "fix": "Check that the domain is registered with your Namecheap account"
    },
    "UNKNOWN_ERROR": {
        "explanation": "Transfer operation failed",
        "fix": "Verify all parameters are correct and try again"
    }
}


class TransferAPI:
    """Transfer API methods for domains namespace"""

    def __init__(self, client: BaseClient) -> None:
        """
        Initialize the transfer API

        Args:
            client: The Namecheap API client instance
        """
        self.client = client

    def create(
        self,
        domain_name: str,
        years: int = 1,
        epp_code: Optional[str] = None,
        promotion_code: Optional[str] = None,
        **kwargs: str
    ) -> ResponseDict:
        """
        Transfers a domain to Namecheap

        API Documentation: https://www.namecheap.com/support/api/methods/domains-transfer/create/

        Error Codes:
            2011170: Validation error from promotion code
            2011280: TLD is not valid
            2030280: TLD is not supported for API
            2528166: Order creation failed

        Args:
            domain_name: Domain to transfer
            years: Number of years to renew during transfer (default: 1)
            epp_code: EPP/Auth code for the domain
            promotion_code: Promotion code for the transfer
            **kwargs: Additional parameters to pass to the API

        Returns:
            Dictionary with transfer creation result

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for transfer creation
        error_codes = {
            **COMMON_TRANSFER_ERRORS,
            "2011170": {
                "explanation": "Validation error from promotion code",
                "fix": "Ensure the promotion code is valid and applicable for domain transfers"
            },
            "2011280": {
                "explanation": "TLD is not valid",
                "fix": "Check that the domain's top-level domain (TLD) is supported for transfers"
            },
            "2030280": {
                "explanation": "TLD is not supported for API",
                "fix": "Verify that the domain's TLD is among those allowed for API transfers"
            },
            "2528166": {
                "explanation": "Order creation failed",
                "fix": "Double-check all transfer parameters and try the request again"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Transfer creation failed",
                "fix": "Verify that '{domain_name}' exists and all parameters are correct"
            }
        }

        # Removed unused extract variable
        # extract = tldextract.extract(domain_name)

        params = {
            "DomainName": domain_name,
            "Years": years
        }

        if epp_code:
            params["EPPCode"] = epp_code

        if promotion_code:
            params["PromotionCode"] = promotion_code

        # Add any additional parameters
        params.update(kwargs)

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.domains.transfer.create",
            params,
            error_codes,
            {"domain_name": domain_name}
        )

    def get_status(self, transfer_id: int) -> ResponseDict:
        """
        Gets the status of a domain transfer

        API Documentation: https://www.namecheap.com/support/api/methods/domains-transfer/get-status/

        Error Codes:
            2019166: Transfer ID not found
            4019329: TransferStatus not available

        Args:
            transfer_id: The transfer ID to check

        Returns:
            Dictionary with transfer status information

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for getting transfer status
        error_codes = {
            **COMMON_TRANSFER_ERRORS,
            "4019329": {
                "explanation": "TransferStatus not available",
                "fix": "Ensure the transfer ID is correct and in a valid state for status retrieval"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get transfer status",
                "fix": "Verify that transfer ID '{transfer_id}' exists and is valid"
            }
        }

        params = {"TransferID": transfer_id}

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.domains.transfer.getStatus",
            params,
            error_codes,
            {"transfer_id": transfer_id}
        )

    def update_status(self, transfer_id: int, resubmit: bool = False) -> ResponseDict:
        """
        Updates the status of a domain transfer

        API Documentation: https://www.namecheap.com/support/api/methods/domains-transfer/update-status/

        Error Codes:
            2019166: Transfer ID not found
            2019167: Invalid transfer status update

        Args:
            transfer_id: The transfer ID to update
            resubmit: Whether to resubmit the transfer

        Returns:
            Dictionary with transfer update result

        Raises:
            NamecheapException: If the API returns an error
        """
        # Error codes for updating transfer status
        error_codes = {
            **COMMON_TRANSFER_ERRORS,
            "2019167": {
                "explanation": "Invalid transfer status update",
                "fix": "The transfer may be in a state that cannot be updated or resubmitted"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to update transfer status",
                "fix": "Verify that transfer ID '{transfer_id}' exists and is valid"
            }
        }

        params = {
            "TransferID": transfer_id,
            "Resubmit": "true" if resubmit else "false"
        }

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.domains.transfer.updateStatus",
            params,
            error_codes,
            {"transfer_id": transfer_id}
        )

    def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "TRANSFERDATE",
        list_type: str = "ALL"
    ) -> ResponseDict:
        """
        Gets the list of domain transfers

        API Documentation: https://www.namecheap.com/support/api/methods/domains-transfer/get-list/

        Error Codes:
            2011166: Invalid request parameters
            2012167: Maximum page size exceeded

        Args:
            page: Page number to return (default: 1)
            page_size: Number of transfers to return per page (default: 20)
            sort_by: Column to sort by (TRANSFERDATE, TRANSFERDATE_DESC, DOMAINNAME, DOMAINNAME_DESC)
            list_type: Type of transfers to list (ALL, INPROGRESS, CANCELLED, COMPLETED)

        Returns:
            Dictionary with transfer list information

        Raises:
            ValueError: If parameters are invalid
            NamecheapException: If the API returns an error
        """
        # Error codes for listing transfers
        error_codes = {
            **COMMON_TRANSFER_ERRORS,
            "2011166": {
                "explanation": "Invalid request parameters",
                "fix": "Check the format of all parameters in your request"
            },
            "2012167": {
                "explanation": "Maximum page size exceeded",
                "fix": "Reduce the page size to a maximum of 100"
            },
            "UNKNOWN_ERROR": {
                "explanation": "Failed to get transfer list",
                "fix": "Verify that all parameters are valid and try again"
            }
        }

        if page_size > 100:
            raise ValueError("Maximum page size is 100")

        valid_sort_options = [
            "TRANSFERDATE",
            "TRANSFERDATE_DESC",
            "DOMAINNAME",
            "DOMAINNAME_DESC",
        ]
        if sort_by not in valid_sort_options:
            raise ValueError(f"sort_by must be one of {valid_sort_options}")

        valid_list_types = ["ALL", "INPROGRESS", "CANCELLED", "COMPLETED"]
        if list_type not in valid_list_types:
            raise ValueError(f"list_type must be one of {valid_list_types}")

        params = {
            "Page": page,
            "PageSize": page_size,
            "SortBy": sort_by,
            "ListType": list_type,
        }

        # Make the API call with centralized error handling
        return self.client._make_request(
            "namecheap.domains.transfer.getList",
            params,
            error_codes,
            {}
        )
