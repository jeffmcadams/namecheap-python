"""
Enhanced functionality module that combines multiple API calls for common operations
"""

from .dns import EnhancedDnsAPI
from .domains import EnhancedDomainsAPI

__all__ = ["EnhancedDomainsAPI", "EnhancedDnsAPI"]
