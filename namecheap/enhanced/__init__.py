"""
Enhanced functionality module that combines multiple API calls for common operations
"""

from .domains import EnhancedDomainsAPI
from .dns import EnhancedDnsAPI

__all__ = ["EnhancedDomainsAPI", "EnhancedDnsAPI"]
